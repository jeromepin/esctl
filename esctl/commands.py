import logging
from typing import Any, Dict, List

from cliff.command import Command
from cliff.lister import Lister
from cliff.show import ShowOne

from esctl.settings import ClusterSettings, IndexSettings
from esctl.utils import Color


class EsctlCommon:
    log = logging.getLogger(__name__)
    cluster_settings = ClusterSettings()
    index_settings = IndexSettings()

    def _sort_and_order_dict(self, dct):
        return {e[0]: e[1] for e in sorted(dct.items())}

    def print_success(self, message):
        print("{} {}".format(Color.colorize("==>", Color.GREEN), message))

    def print_output(self, message):
        print("{}".format(message))

    def uses_table_formatter(self):
        return self.formatter.__class__.__name__ == "TableFormatter"

    def objects_list_to_flat_dict(self, lst: List[Dict[str, Any]]) -> Dict[str, Any]:
        """ Convert a list of dict to a flattened dict with full name.

        :Example:
                node.jvm.versions = [{"version":"12.0.1","vm_name":"OpenJDK 64-Bit Server VM","vm_version":"12.0.1+12","vm_vendor":"Oracle Corporation","bundled_jdk":true,"using_bundled_jdk":true,"count":1}] # noqa: E501
            becomes
                {
                    "node.jvm.versions[0].version": "12.0.1",
                    "node.jvm.versions[0].vm_name": "OpenJDK 64-Bit Server VM"
                }

        :param lst: A list of dict to flatten
        :paramtype lst: list
        :return: A dict
        :rtype: dict
        """
        flat_dict = {}
        for (index, element) in enumerate(lst):
            for (attribute, value) in element.items():
                flat_dict["[{}].{}".format(index, attribute)] = value

        return flat_dict


class EsctlCommand(Command, EsctlCommon):
    """Simple command to run. Doesn’t expect any output."""


class EsctlCommandWithPersistency(EsctlCommand):
    """Add mutually exclusive arguments `transient` and `persistent` to
    be used when working with settings, logging, etc...
    """

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        persistency_group = parser.add_mutually_exclusive_group()
        persistency_group.add_argument(
            "--transient",
            action="store_true",
            help=("Set setting as transient (default)"),
        )
        persistency_group.add_argument(
            "--persistent", action="store_true", help=("Set setting as persistent"),
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


class EsctlListerIndexSetting(EsctlLister):
    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument("index", metavar="<index>", help=("Index"))
        parser.add_argument("setting", metavar="<setting>", help=("Setting"))
        return parser


class EsctlShowOne(ShowOne, EsctlCommon):
    """Expect a key-value list to create a two-columns table."""
