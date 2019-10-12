import logging

from cliff.command import Command
from cliff.lister import Lister
from cliff.show import ShowOne

from esctl.settings import ClusterSettings
from esctl.utils import Color


class EsctlCommon:
    log = logging.getLogger(__name__)

    def _sort_and_order_dict(self, dct):
        return {e[0]: e[1] for e in sorted(dct.items())}

    def print_success(self, message):
        print("{} {}".format(Color.colorize("SUCCESS", Color.GREEN), message))

    def print_output(self, message):
        print("{}".format(message))


class EsctlCommand(Command, EsctlCommon):
    """Simple command to run. Doesn’t expect any output."""


class EsctlCommandWithPersistency(EsctlCommand):
    """Add mutually exclusive arguments `transient` and `persistent` to
    be used when working with settings, logging, etc...
    """

    log = logging.getLogger(__name__)
    settings = ClusterSettings()

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        persistency_group = parser.add_mutually_exclusive_group()
        persistency_group.add_argument(
            "--transient",
            action="store_true",
            help=("Set setting as transient (default)"),
        )
        persistency_group.add_argument(
            "--persistent",
            action="store_true",
            help=("Set setting as persistent"),
        )
        return parser


class EsctlCommandIndex(EsctlCommand):
    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument("index", metavar="<index>", help=("Index"))
        return parser


class EsctlCommandLogging(EsctlCommandWithPersistency):
    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument("logger", metavar="<logger>", help=("Logger"))
        return parser


class EsctlCommandSetting(EsctlCommandWithPersistency):
    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument("setting", metavar="<setting>", help=("Setting"))
        return parser


class EsctlLister(Lister, EsctlCommon):
    """Expect a list of elements in order to create a multi-columns table."""


class EsctlShowOne(ShowOne, EsctlCommon):
    """Expect a key-value list to create a two-columns table."""
