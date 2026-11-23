import argparse

from esctl.commands import EsctlShowOne, ShowOneResult
from esctl.formatter import JSONToCliffFormatter
from esctl.utils import flatten_dict


class DocumentGet(EsctlShowOne):
    """Retrieves the specified JSON document from an index."""

    def take_action(self, parsed_args: argparse.Namespace) -> ShowOneResult:
        self.response = self.es.get(index=parsed_args.index, id=parsed_args.id).body
        document = flatten_dict(self.response)

        return JSONToCliffFormatter(document, pretty_key=self.pretty_keys).to_show_one(lines=list(document.keys()))

    def get_parser(self, prog_name: str) -> argparse.ArgumentParser:
        parser = super().get_parser(prog_name)

        parser.add_argument("index", help="The name of the index")
        parser.add_argument("id", help="The document ID")

        return parser
