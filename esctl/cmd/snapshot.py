from esctl.commands import EsctlLister
from esctl.formatter import JSONToCliffFormatter
from esctl.utils import Color


class SnapshotList(EsctlLister):
    """Returns all snapshots in a specific repository."""

    def take_action(self, parsed_args):
        snapshots = self.transform(
            self.es.cat.snapshots(repository=parsed_args.repository, format="json")
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
            ]
        )

    def transform(self, snapshots):
        for idx in range(len(snapshots)):
            if snapshots[idx].get("status") == "PARTIAL":
                snapshots[idx]["status"] = Color.colorize(
                    snapshots[idx].get("status"), Color.YELLOW
                )
                snapshots[idx]["failed_shards"] = Color.colorize(
                    snapshots[idx].get("failed_shards"), Color.RED
                )
            elif snapshots[idx].get("status") == "IN_PROGRESS":
                snapshots[idx]["status"] = Color.colorize(
                    snapshots[idx].get("status"), Color.CYAN
                )

        return snapshots

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "repository",
            help=(
                "Comma-separated list or wildcard expression of "
                "repository names used to limit the request."
            ),
        )

        return parser
