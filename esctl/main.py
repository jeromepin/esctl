import argparse
import logging
import os
import re
import subprocess
import sys
from typing import List

import pkg_resources
import urllib3
from cliff.app import App
from cliff.commandmanager import CommandManager

from esctl import utils
from esctl.config import ConfigFileParser
from esctl.elasticsearch import Client
from esctl.interactive import InteractiveApp

# `configure_logging` and `build_option_parser` methods comes from cliff
# and are modified


class Esctl(App):

    _es = None
    _config = None
    _config_file_parser = ConfigFileParser()
    log = App.LOG

    def __init__(self):
        os.environ["COLUMNS"] = "120"
        super(Esctl, self).__init__(
            description=pkg_resources.require("Esctl")[0].project_name,
            version=pkg_resources.require("Esctl")[0].version,
            command_manager=CommandManager("esctl"),
            deferred_help=True,
            interactive_app_factory=InteractiveApp,
        )
        self.interactive_mode = False

        self.LOCAL_COMMANDS: List[str] = [
            "ConfigClusterList",
            "ConfigContextList",
            "ConfigContextSet",
            "ConfigUserList",
        ]

    def configure_logging(self):
        """Create logging handlers for any log output."""
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)
        logging.getLogger("stevedore.extension").setLevel(logging.WARNING)

        # Disable urllib's warnings
        # See https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings # noqa: E501
        urllib3.disable_warnings()

        # Set up logging to a file
        if self.options.log_file:
            file_handler = logging.FileHandler(filename=self.options.log_file)
            formatter = logging.Formatter(self.LOG_FILE_MESSAGE_FORMAT)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

        # Always send higher-level messages to the console via stderr
        console = logging.StreamHandler(self.stderr)
        console_level = {
            0: logging.ERROR,  # quiet, with -q flag
            1: logging.WARNING,  # default, without -v or -q flags
            2: logging.INFO,
            3: logging.DEBUG,
        }.get(self.options.verbose_level, logging.DEBUG)
        console.setLevel(console_level)

        logging.addLevelName(
            logging.DEBUG,
            utils.Color.colorize(logging.getLevelName(logging.DEBUG), utils.Color.END),
        )
        logging.addLevelName(
            logging.INFO,
            utils.Color.colorize(logging.getLevelName(logging.INFO), utils.Color.BLUE),
        )
        logging.addLevelName(
            logging.WARNING,
            utils.Color.colorize(
                logging.getLevelName(logging.WARNING), utils.Color.YELLOW
            ),
        )
        logging.addLevelName(
            logging.ERROR,
            utils.Color.colorize(
                logging.getLevelName(logging.ERROR), utils.Color.PURPLE
            ),
        )
        logging.addLevelName(
            logging.CRITICAL,
            utils.Color.colorize(
                logging.getLevelName(logging.CRITICAL), utils.Color.RED
            ),
        )
        formatter = logging.Formatter(
            "[%(levelname)-8s] " + self.CONSOLE_MESSAGE_FORMAT
        )
        console.setFormatter(formatter)
        root_logger.addHandler(console)

        return

    def find_scheme(self):
        scheme = "https"

        if self.context.cluster.get("servers")[0].startswith("http:"):
            scheme = self.context.cluster.get("servers")[0].split(":")[0]

        self.log.debug("Using {} scheme".format(scheme))

        return scheme

    def insert_password_into_context(self):
        external_passowrd_definition = self.context.user.get("external_password")
        del self.context.user["external_password"]

        if "command" in external_passowrd_definition:
            if "run" in external_passowrd_definition.get("command"):
                self.context.user["password"] = self._run_os_system_command(
                    external_passowrd_definition.get("command").get("run")
                )

    def initialize_app(self, argv):
        Esctl._config = Esctl._config_file_parser.load_configuration(
            self.options.config_file
        )
        self.context = Esctl._config_file_parser.create_context(self.options.context)

        http_auth = None

        if self.context.user is not None:
            if "external_password" in self.context.user:
                self.insert_password_into_context()

            http_auth = (
                (self.context.user.get("username"), self.context.user.get("password"))
                if self.context.user.get("username")
                and self.context.user.get("password")
                else None
            )

        Client(self.context, http_auth, self.find_scheme())

    def _run_os_system_command(self, raw_command: str) -> str:
        self.log.debug(f"Running command : {raw_command}")
        return os.popen(raw_command).read().strip()

    def _run_shell_subcommand(self, command):
        command = command.split(" ")
        self.log.debug(f"Running pre-command : {command}")
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        return process

    def prepare_to_run_command(self, cmd):
        if (cmd.__class__.__name__ not in self.LOCAL_COMMANDS) and hasattr(
            self.context, "pre_commands"
        ):
            for i in range(len(self.context.pre_commands)):
                command_block = self.context.pre_commands[i]
                process = self._run_shell_subcommand(command_block.get("command"))

                if command_block.get("wait_for_exit"):
                    process.communicate()

                elif command_block.get("wait_for_output"):
                    string_to_look_for = command_block.get("wait_for_output")
                    pattern = re.compile(string_to_look_for)

                    while True:
                        line = process.stdout.readline()
                        if not line:
                            break

                        line = line.decode("utf-8").strip()

                        match = re.search(pattern, line)

                        if match is None:
                            self.log.debug(
                                f"Expecting command output to match `{string_to_look_for}` but got `{line}`..."
                            )
                        else:
                            self.log.debug(
                                f"Got `{string_to_look_for}` from `{command_block.get('command')}`"
                            )
                            break

                self.context.pre_commands[i]["process"] = process

    def clean_up(self, cmd, result, err):
        if (cmd.__class__.__name__ not in self.LOCAL_COMMANDS) and hasattr(
            self.context, "pre_commands"
        ):
            for pre_command in self.context.pre_commands:
                pre_command.get("process").terminate()

        if err:
            self.log.debug("got an error: %s", err)

    def build_option_parser(self, description, version, argparse_kwargs=None):
        """Return an argparse option parser for this application."""
        argparse_kwargs = argparse_kwargs or {}
        parser = argparse.ArgumentParser(
            description=description, add_help=False, **argparse_kwargs
        )
        parser.add_argument(
            "--version", action="version", version="%(prog)s {0}".format(version)
        )
        verbose_group = parser.add_mutually_exclusive_group()
        verbose_group.add_argument(
            "-v",
            "--verbose",
            action="count",
            dest="verbose_level",
            default=self.DEFAULT_VERBOSE_LEVEL,
            help="Increase verbosity of output. Can be repeated.",
        )
        verbose_group.add_argument(
            "-q",
            "--quiet",
            action="store_const",
            dest="verbose_level",
            const=0,
            help="Suppress output except warnings and errors.",
        )
        parser.add_argument(
            "--log-file",
            action="store",
            default=None,
            help="Specify a file to log output. Disabled by default.",
        )
        parser.add_argument(
            "--config",
            action="store",
            default="~/.esctlrc",
            help="Path to the config file",
            dest="config_file",
        )
        if self.deferred_help:
            parser.add_argument(
                "-h",
                "--help",
                dest="deferred_help",
                action="store_true",
                help="Show help message and exit.",
            )
        # else:
        #     parser.add_argument(
        #         "-h",
        #         "--help",
        #         action=HelpAction,
        #         nargs=0,
        #         default=self,  # tricky
        #         help="Show this help message and exit.",
        #     )
        parser.add_argument(
            "--debug",
            default=False,
            action="store_true",
            help="Show tracebacks on errors.",
        )
        parser.add_argument(
            "--es-version", action="store", help="Elasticsearch version."
        )

        parser.add_argument(
            "--context", action="store", help="Context to use", type=str
        )

        return parser


def main(argv=sys.argv[1:]):
    esctl = Esctl()
    return esctl.run(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
