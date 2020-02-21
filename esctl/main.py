import argparse
import logging
import sys

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
    log = App.LOG

    def __init__(self):
        super(Esctl, self).__init__(
            description=pkg_resources.require("Esctl")[0].project_name,
            version=pkg_resources.require("Esctl")[0].version,
            command_manager=CommandManager("esctl"),
            deferred_help=True,
            interactive_app_factory=InteractiveApp,
        )
        self.interactive_mode = False

    def configure_logging(self):
        """Create logging handlers for any log output.
        """
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

    def initialize_app(self, argv):
        self.config_file_parser = ConfigFileParser()
        Esctl._config = self.config_file_parser.load_configuration(
            self.options.config_file
        )
        self.context = self.config_file_parser.create_context(self.options.context)

        http_auth = None

        if self.context.user is not None:
            http_auth = (
                (self.context.user.get("username"), self.context.user.get("password"))
                if self.context.user.get("username")
                and self.context.user.get("password")
                else None
            )

        Client(self.context, http_auth, self.find_scheme())

    def prepare_to_run_command(self, cmd):
        pass

    def clean_up(self, cmd, result, err):
        if err:
            self.log.debug("got an error: %s", err)

    def build_option_parser(self, description, version, argparse_kwargs=None):
        """Return an argparse option parser for this application.
        """
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
