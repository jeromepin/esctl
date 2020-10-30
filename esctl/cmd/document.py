from esctl.commands import EsctlShowOne
from esctl.formatter import JSONToCliffFormatter
from esctl.utils import flatten_dict


class DocumentGet(EsctlShowOne):
    """Retrieves the specified JSON document from an index."""

    def take_action(self, parsed_args):
        document = flatten_dict(
            self.es.get(format="json", index=parsed_args.index, id=parsed_args.id)
        )

        return JSONToCliffFormatter(document).to_show_one(lines=list(document.keys()))

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)

        parser.add_argument("index", help="The name of the index")
        parser.add_argument("id", help="The document ID")

        return parser
