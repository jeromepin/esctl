from esctl.commands import EsctlCommand, EsctlCommandIndex, EsctlLister
from esctl.formatter import JSONToCliffFormatter
from esctl.utils import Color

from typing import Any, Dict


class IndexCreate(EsctlCommand):
    """Create an index.

    Read the index configuration as a JSON document from either stdin or a path.
    """

    def take_action(self, parsed_args):
        configuration = self.read_from_file_or_stdin(parsed_args.configuration)

        self.log.info("Creating index {}".format(parsed_args.index))
        print(self.es.indices.create(index=parsed_args.index, body=configuration))

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument("index", help="Name of the index to create")
        parser.add_argument(
            "--configuration",
            metavar="PATH",
            help="Path to the JSON document containing the index configuration (mapping, aliases, settings)",
        )
        return parser


class IndexList(EsctlLister):
    """Returns information about indices: number of primaries and replicas, document counts, disk size, ..."""

    def take_action(self, parsed_args):
        indices = self.transform(
            self.es.cat.indices(format="json", index=parsed_args.index)
        )
        return JSONToCliffFormatter(indices).format_for_lister(
            columns=[
                ("index"),
                ("health",),
                ("status"),
                ("uuid", "UUID"),
                ("pri", "Primary"),
                ("rep", "Replica"),
                ("docs.count"),
                ("docs.deleted"),
                ("store.size"),
                ("pri.store.size", "Primary Store Size"),
            ]
        )

    def transform(self, indices):
        if self.uses_table_formatter():
            for idx, indice in enumerate(indices):
                if indice.get("health"):
                    indices[idx]["health"] = Color.colorize(
                        indice.get("health"),
                        getattr(Color, indice.get("health").upper()),
                    )

                if indice.get("status") == "close":
                    indices[idx]["status"] = Color.colorize(
                        indice.get("status"), Color.ITALIC
                    )

        return indices

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "index",
            help="A comma-separated list of index names to limit the returned information",
            nargs="?",
        )
        return parser


class IndexClose(EsctlCommandIndex):
    """Close an index."""

    def take_action(self, parsed_args):
        self.log.info("Closing index " + parsed_args.index)
        print(self.es.indices.close(index=parsed_args.index))


class IndexDelete(EsctlCommandIndex):
    """Delete an index."""

    def take_action(self, parsed_args):
        self.log.info("Deleting index " + parsed_args.index)
        print(self.es.indices.delete(index=parsed_args.index))


class IndexOpen(EsctlCommandIndex):
    """Open an index."""

    def take_action(self, parsed_args):
        self.log.info("Opening index " + parsed_args.index)
        print(self.es.indices.open(index=parsed_args.index))


class IndexReindex(EsctlCommand):
    """Reindex a given index into another one."""

    def _build_request_body(self, args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "source": {
                "index": args.get("source_index"),
            },
            "dest": {
                "index": args.get("destination_index"),
                "version_type": args.get("version_type"),
                "op_type": args.get("op_type"),
            },
            "conflicts": args.get("conflicts"),
        }

    def take_action(self, parsed_args):
        print(self.es.reindex(body=self._build_request_body(vars(parsed_args))))

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "source_index", help="Name of the index to index document from"
        )
        parser.add_argument(
            "destination_index", help="Name of the index to index document to"
        )
        parser.add_argument(
            "--conflicts",
            help="Set to `proceed` to continue reindexing even if there are conflicts (default: abort)",
            choices=["abort", "proceed"],
            default="abort",
        )
        parser.add_argument(
            "--version-type",
            help=(
                "The versioning to use for the indexing operation (default: internal), "
                "valid choices are: `internal`, `external`, `external_gt`, `external_gte`"
            ),
            choices=["internal", "external", "external_gt", "external_gte"],
            default="internal",
        )
        parser.add_argument(
            "--op-type",
            help=(
                "Set to `create` to only index documents that do not already exist (default: index), "
                "valid choices are: `index`, `create`"
            ),
            choices=["index", "create"],
            default="index",
        )

        return parser
