import logging
import sys
import argparse
import pkg_resources
import urllib3
import importlib
import ssl

from cliff.app import App
from cliff.commandmanager import CommandManager
from elasticsearch.connection import create_ssl_context
from elasticsearch import Elasticsearch

from esctl import utils
from esctl import config
from esctl.interactive import InteractiveApp
from esctl.override import EsctlTransport

# `configure_logging` and `build_option_parser` methods comes from cliff
# and are modified


class Esctl(App):

    _es = None
    _config = config.ConfigFileParser()
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
        logging.getLogger("elasticsearch").setLevel(logging.WARNING)

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
            utils.Color.colorize(
                logging.getLevelName(logging.DEBUG), utils.Color.END
            ),
        )
        logging.addLevelName(
            logging.INFO,
            utils.Color.colorize(
                logging.getLevelName(logging.INFO), utils.Color.BLUE
            ),
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
            "%(levelname)-8s " + self.CONSOLE_MESSAGE_FORMAT
        )
        console.setFormatter(formatter)
        root_logger.addHandler(console)

        return

    def create_context(self):
        if self.options.context:
            context_name = str(self.options.context)
            self.log.debug("Using provided context : {}".format(context_name))
        else:
            context_name = self._config.__getattribute__("default-context")
            self.log.debug(
                "No context provided. Using default context : {}".format(
                    context_name
                )
            )

        try:
            self.context = self._config.get_context_informations(context_name)
        except AttributeError:
            self.log.fatal("Cannot load context '{}'.".format(context_name))
            sys.exit(1)

    def find_scheme(self):
        scheme = "https"

        if self.context.cluster.get("servers")[0].startswith("http:"):
            scheme = self.context.cluster.get("servers")[0].split(":")[0]

        self.log.debug("Using {} scheme".format(scheme))

        return scheme

    def _initialize_es_client(self, servers, es_client_settings):
        es_version = ""
        if self.options.es_version is not None:
            es_version = self.options.es_version

        try:
            elasticsearch = importlib.import_module(
                "elasticsearch{}".format(es_version)
            )
        except ModuleNotFoundError:
            self.log.error(
                (
                    "You asked to connect to an elasticsearch cluster in"
                    " version {} but the required python module"
                    " 'elasticsearch{}' is not installed. You should install"
                    " the appropriate python module. Trying to use the default"
                    " module but its version may not match the cluster's"
                    " version..."
                ).format(
                    es_version, es_version
                )
            )
            elasticsearch = importlib.import_module("elasticsearch")

        return elasticsearch.Elasticsearch(servers, **es_client_settings)

    def initialize_app(self, argv):
        self._config.load_configuration()
        self.create_context()

        servers = self.context.cluster.get("servers")
        http_auth = None

        if self.context.user is not None:
            http_auth = (
                (
                    self.context.user.get("username"),
                    self.context.user.get("password"),
                )
                if self.context.user.get("username")
                and self.context.user.get("password")
                else None
            )

        elasticsearch_client_kwargs = {
            "http_auth": http_auth,
            "scheme": self.find_scheme(),
            "transport_class": EsctlTransport,
        }

        if self.find_scheme() == "https":
            if self.context.settings.get("no_check_certificate"):
                ssl_context = create_ssl_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                elasticsearch_client_kwargs["ssl_context"] = ssl_context

        if "max_retries" in self.context.settings:
            elasticsearch_client_kwargs[
                "max_retries"
            ] = self.context.settings.get("max_retries")

        if "timeout" in self.context.settings:
            elasticsearch_client_kwargs["timeout"] = self.context.settings.get(
                "timeout"
            )

        Esctl._es = Elasticsearch(servers, **elasticsearch_client_kwargs)

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
            "--version",
            action="version",
            version="%(prog)s {0}".format(version),
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

        parser.add_argument("--context", action="store", help="Context to use")

        return parser


def main(argv=sys.argv[1:]):
    esctl = Esctl()
    return esctl.run(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
