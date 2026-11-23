import argparse

from typing_extensions import override

from esctl.commands import EsctlLister, ListerResult
from esctl.formatter import JSONToCliffFormatter


class AliasList(EsctlLister):
    """List all aliases."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ListerResult:
        aliases = self.rows(self.es.cat.aliases(name=parsed_args.alias, format="json"))

        return JSONToCliffFormatter(aliases).format_for_lister(
            columns=[("index",), ("alias",)],
        )

    @override
    def get_parser(self, prog_name: str) -> argparse.ArgumentParser:
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "alias",
            help="A comma-separated list of alias names to return",
            default=None,
            nargs="?",
        )

        return parser
