from esctl.commands import EsctlLister
from esctl.formatter import JSONToCliffFormatter


class AliasList(EsctlLister):
    """List all aliases."""

    def take_action(self, parsed_args):
        aliases = self.es.cat.aliases(name=parsed_args.alias, format="json")

        return JSONToCliffFormatter(aliases).format_for_lister(
            columns=[("index",), ("alias",)]
        )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "alias",
            help="A comma-separated list of alias names to return",
            default=None,
            nargs="?",
        )

        return parser
