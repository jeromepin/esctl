import logging
import os
import sys
from typing import Any, Dict, List

import jmespath
from cliff.command import Command
from cliff.lister import Lister
from cliff.show import ShowOne

from esctl.elasticsearch import Client
from esctl.settings import ClusterSettings, IndexSettings
from esctl.utils import Color


class EsctlCommon:
    log = logging.getLogger(__name__)
    es = Client().es
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

    def read_from_file_or_stdin(self, path: str) -> str:
        """ Read some content from a file if the path is defined otherwise read from stdin. """
        if path is not None:
            with open(os.path.expanduser(path)) as reader:
                return reader.read()
        else:
            return sys.stdin.read()

    def objects_list_to_flat_dict(self, lst: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Convert a list of dict to a flattened dict with full name.

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

    def _delete_and_merge_inner_dict_into_parent(
        self, parent_dict: Dict[str, Any], key: str
    ) -> Dict[str, Any]:
        """Merge a inner dictionnary into it's parent.

        :Example:
                {
                    "name" : "prod-monolith-us-searchill-es-01",
                    "cluster_name" : "prod-lumsites-cluster",
                    "cluster_uuid" : "Z0FeT4oVSw2GQ3bMs0vEZw",
                    "version" : {
                        "number" : "7.0.1",
                        "build_flavor" : "default",
                        "build_type" : "deb",
                        "build_hash" : "e4efcb5",
                        "build_date" : "2019-04-29T12:56:03.145736Z",
                        "build_snapshot" : false,
                        "lucene_version" : "8.0.0",
                        "minimum_wire_compatibility_version" : "6.7.0",
                        "minimum_index_compatibility_version" : "6.0.0-beta1"
                    },
                    "tagline" : "You Know, for Search"
                }
            becomes
                {
                    "name" : "prod-monolith-us-searchill-es-01",
                    "cluster_name" : "prod-lumsites-cluster",
                    "cluster_uuid" : "Z0FeT4oVSw2GQ3bMs0vEZw",
                    "version.number" : "7.0.1",
                    "version.build_flavor" : "default",
                    "version.build_type" : "deb",
                    "version.build_hash" : "e4efcb5",
                    "version.build_date" : "2019-04-29T12:56:03.145736Z",
                    "version.build_snapshot" : false,
                    "version.lucene_version" : "8.0.0",
                    "version.minimum_wire_compatibility_version" : "6.7.0",
                    "version.minimum_index_compatibility_version" : "6.0.0-beta1",
                    "tagline" : "You Know, for Search"
                }

        :param parent_dict: The parent dict containing an inner dict
        :paramtype parent_dict: dict
        :param key: The key where the inner dict stands
        :paramtype key: str
        :return: The parent dict with the merged inner dict
        :rtype: dict
        """
        for k, v in parent_dict.get(key).items():
            parent_dict[f"{key}.{k}"] = v
        del parent_dict[key]

        return parent_dict


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
            "--persistent", action="store_true", help=("Set setting as persistent")
        )
        return parser


class EsctlCommandIndex(EsctlCommand):
    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "index",
            help=(
                "Comma-separated list or wildcard expression of "
                "index names used to limit the request."
            ),
        )
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
        parser.add_argument(
            "setting", metavar="<setting>", help=("Setting"), nargs="?", default="*"
        )
        return parser


class EsctlShowOne(ShowOne, EsctlCommon):
    """Expect a key-value list to create a two-columns table."""

    def jmespath_search(self, expression, data, options=None):
        return jmespath.search(expression, data, options=options)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "--no-pretty",
            action="store_true",
            help=(
                "Don't format keys. (Like `ingest.total.count` into `Ingest Total Count`)"
            ),
        )
        parser.add_argument(
            "--jmespath",
            help=(
                "[Experimental] Execute a JMESPath query on the response. See https://jmespath.org for help."
            ),
        )
        return parser
