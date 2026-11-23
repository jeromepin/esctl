import argparse
import json
from typing import Any

from typing_extensions import override

from esctl.commands import EsctlCommand, EsctlCommandIndex, EsctlLister, ListerResult
from esctl.formatter import JSONToCliffFormatter
from esctl.utils import Color

# Top-level keys of the create index API body
INDEX_CONFIGURATION_KEYS = {"aliases", "mappings", "settings"}


class IndexCreate(EsctlCommand):
    """Create an index.

    Read the index configuration as a JSON document from either stdin or a path.
    """

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> None:
        raw_configuration = self.read_from_file_or_stdin(parsed_args.configuration)
        # No configuration at all: create the index with the cluster's defaults
        configuration = json.loads(raw_configuration) if raw_configuration.strip() else {}

        unknown_keys = set(configuration) - INDEX_CONFIGURATION_KEYS
        if unknown_keys:
            msg = (
                f"Unknown index configuration keys: {', '.join(sorted(unknown_keys))}. "
                f"Expected any of: {', '.join(sorted(INDEX_CONFIGURATION_KEYS))}"
            )
            raise ValueError(msg)

        self.log.info("Creating index %s", parsed_args.index)
        self.print_output(self.es.indices.create(index=parsed_args.index, **configuration))

    @override
    def get_parser(self, prog_name: str) -> argparse.ArgumentParser:
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

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ListerResult:
        indices = self.transform(
            self.rows(self.es.cat.indices(format="json", index=parsed_args.index)),
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
            ],
        )

    def transform(self, indices: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if self.uses_table_formatter():
            for idx, indice in enumerate(indices):
                if indice.get("health"):
                    indices[idx]["health"] = Color.colorize(
                        indice["health"],
                        getattr(Color, indice["health"].upper()),
                    )

                if indice.get("status") == "close":
                    indices[idx]["status"] = Color.colorize(
                        indice.get("status"),
                        Color.ITALIC,
                    )

        return indices

    @override
    def get_parser(self, prog_name: str) -> argparse.ArgumentParser:
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "index",
            help="A comma-separated list of index names to limit the returned information",
            nargs="?",
        )
        return parser


class IndexClose(EsctlCommandIndex):
    """Close an index."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> None:
        self.log.info("Closing index %s", parsed_args.index)
        self.print_output(self.es.indices.close(index=parsed_args.index))


class IndexDelete(EsctlCommandIndex):
    """Delete an index."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> None:
        self.log.info("Deleting index %s", parsed_args.index)
        self.print_output(self.es.indices.delete(index=parsed_args.index))


class IndexOpen(EsctlCommandIndex):
    """Open an index."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> None:
        self.log.info("Opening index %s", parsed_args.index)
        self.print_output(self.es.indices.open(index=parsed_args.index))


class IndexReindex(EsctlCommand):
    """Reindex a given index into another one."""

    def _build_request_body(self, args: dict[str, Any]) -> dict[str, Any]:
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

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> None:
        self.print_output(self.es.reindex(**self._build_request_body(vars(parsed_args))))

    @override
    def get_parser(self, prog_name: str) -> argparse.ArgumentParser:
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "source_index",
            help="Name of the index to index document from",
        )
        parser.add_argument(
            "destination_index",
            help="Name of the index to index document to",
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
