import argparse
from typing import Any

from typing_extensions import override

from esctl.commands import EsctlLister, ListerResult
from esctl.formatter import JSONToCliffFormatter
from esctl.utils import Color


class SnapshotList(EsctlLister):
    """Returns all snapshots in a specific repository."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ListerResult:
        snapshots = self.transform(
            self.rows(self.es.cat.snapshots(repository=parsed_args.repository, format="json")),
        )

        return JSONToCliffFormatter(snapshots).format_for_lister(
            columns=[
                ("id"),
                ("status"),
                ("start_time"),
                ("end_time"),
                ("duration"),
                ("indices"),
                ("successful_shards"),
                ("failed_shards"),
                ("total_shards"),
            ],
        )

    def transform(self, snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.uses_table_formatter():
            return snapshots

        for idx in range(len(snapshots)):
            if snapshots[idx].get("status") == "PARTIAL":
                snapshots[idx]["status"] = Color.colorize(
                    snapshots[idx].get("status"),
                    Color.YELLOW,
                )
                snapshots[idx]["failed_shards"] = Color.colorize(
                    snapshots[idx].get("failed_shards"),
                    Color.RED,
                )
            elif snapshots[idx].get("status") == "IN_PROGRESS":
                snapshots[idx]["status"] = Color.colorize(
                    snapshots[idx].get("status"),
                    Color.CYAN,
                )

        return snapshots

    @override
    def get_parser(self, prog_name: str) -> argparse.ArgumentParser:
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "repository",
            help=("Comma-separated list or wildcard expression of repository names used to limit the request."),
        )

        return parser
