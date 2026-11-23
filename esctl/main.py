import argparse
import importlib.metadata
import logging
import os
import re
import shlex
import subprocess
import sys

import urllib3
from cliff.app import App
from cliff.commandmanager import CommandManager

from esctl import utils
from esctl.config import ConfigFileParser
from esctl.elasticsearch import Client
from esctl.exceptions import ExternalCommandError
from esctl.interactive import InteractiveApp

# `configure_logging` and `build_option_parser` methods comes from cliff
# and are modified


class Esctl(App):
    log = App.LOG

    def __init__(self):
        os.environ["COLUMNS"] = "120"
        super().__init__(
            description=importlib.metadata.metadata(self.__class__.__name__)["Summary"],
            version=importlib.metadata.version(self.__class__.__name__),
            command_manager=CommandManager("esctl"),
            deferred_help=True,
            interactive_app_factory=InteractiveApp,
        )
        self.interactive_mode = False
        self.config_file_parser = ConfigFileParser()
        self.config = None
        self._connected = False

    def configure_logging(self):
        """Create logging handlers for any log output."""
        root_logger = logging.getLogger("")
        root_logger.setLevel(logging.DEBUG)
        logging.getLogger("stevedore.extension").setLevel(logging.WARNING)

        # Disable urllib's warnings
        # See https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
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
                logging.getLevelName(logging.WARNING),
                utils.Color.YELLOW,
            ),
        )
        logging.addLevelName(
            logging.ERROR,
            utils.Color.colorize(
                logging.getLevelName(logging.ERROR),
                utils.Color.PURPLE,
            ),
        )
        logging.addLevelName(
            logging.CRITICAL,
            utils.Color.colorize(
                logging.getLevelName(logging.CRITICAL),
                utils.Color.RED,
            ),
        )
        formatter = logging.Formatter(
            "[%(levelname)-8s] " + self.CONSOLE_MESSAGE_FORMAT,
        )
        console.setFormatter(formatter)
        root_logger.addHandler(console)

    def resolve_external_credentials(self):
        """Replace `external_username`/`external_password` by the output of their command."""
        for field in ("username", "password"):
            definition = self.context.user.pop(f"external_{field}", None)
            if definition is not None:
                self.context.user[field] = self._run_os_system_command(
                    definition["command"]["run"],
                    purpose=field,
                )

    def initialize_app(self, argv):
        self.config = self.config_file_parser.load_configuration(
            self.options.config_file,
        )
        self.context = self.config_file_parser.create_context(self.options.context)

    @staticmethod
    def _requires_cluster(cmd) -> bool:
        # cliff's own commands (help, complete) don't define it and are local too
        return getattr(cmd, "requires_cluster", False)

    def connect(self):
        """Resolve the credentials and configure the Elasticsearch client, once."""
        if self._connected:
            return

        http_auth = None

        if self.context.user is not None:
            self.resolve_external_credentials()

            http_auth = (
                (self.context.user.get("username"), self.context.user.get("password"))
                if self.context.user.get("username") and self.context.user.get("password")
                else None
            )

        Client.configure(self.context, http_auth)
        self._connected = True

    def _run_os_system_command(self, raw_command: str, purpose: str) -> str:
        """Run a shell command from the configuration file and return its output."""
        self.log.debug(f"Running command : {raw_command}")
        # Running through a shell is intended: users write pipelines in their config file
        completed = subprocess.run(  # noqa: S602
            raw_command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
        )

        if completed.returncode != 0:
            raise ExternalCommandError(
                f"The command retrieving the {purpose} failed with exit code {completed.returncode}: "
                f"`{raw_command}`\n{completed.stderr.strip()}",
            )

        value = completed.stdout.strip()
        if not value:
            raise ExternalCommandError(f"The command retrieving the {purpose} printed nothing: `{raw_command}`")

        return value

    def _run_shell_subcommand(self, command):
        command = shlex.split(command)
        self.log.debug(f"Running pre-command : {command}")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        return process

    def prepare_to_run_command(self, cmd):
        if not self._requires_cluster(cmd):
            return

        self.connect()

        if hasattr(self.context, "pre_commands"):
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
                                f"Expecting command output to match `{string_to_look_for}` but got `{line}`...",
                            )
                        else:
                            self.log.debug(
                                f"Got `{string_to_look_for}` from `{command_block.get('command')}`",
                            )
                            break

                self.context.pre_commands[i]["process"] = process

    def clean_up(self, cmd, result, err):
        if self._requires_cluster(cmd) and hasattr(self.context, "pre_commands"):
            for pre_command in self.context.pre_commands:
                pre_command.get("process").terminate()

        if err:
            self.log.debug("got an error: %s", err)

    def build_option_parser(self, description, version, argparse_kwargs=None):
        """Return an argparse option parser for this application."""
        argparse_kwargs = argparse_kwargs or {}
        parser = argparse.ArgumentParser(
            description=description,
            add_help=False,
            **argparse_kwargs,
        )
        parser.add_argument(
            "--version",
            action="version",
            version=f"%(prog)s {version}",
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

        parser.add_argument(
            "--debug",
            default=False,
            action="store_true",
            help="Show tracebacks on errors.",
        )
        parser.add_argument(
            "--es-version",
            action="store",
            help="Elasticsearch version.",
        )

        parser.add_argument(
            "--context",
            action="store",
            help="Context to use",
            type=str,
        )

        return parser


def main(argv=sys.argv[1:]):
    esctl = Esctl()
    return esctl.run(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
