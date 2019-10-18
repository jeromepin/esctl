from esctl.commands import EsctlCommand, EsctlLister
from esctl.main import Esctl
from esctl.formatter import JSONToCliffFormatter


class NodeHotThreads(EsctlCommand):
    """Print hot threads on each nodes."""

    def take_action(self, parsed_args):
        print(Esctl._es.nodes.hot_threads(type=parsed_args.type))

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "--type",
            help=(
                "The type to sample (default: cpu), "
                "valid choices are: ‘cpu’, ‘wait’, ‘block’"
            ),
            choices=["cpu", "wait", "block"],
            default="cpu",
        )
        return parser


class NodeList(EsctlLister):
    """List nodes."""

    def take_action(self, parsed_args):
        return JSONToCliffFormatter(
            Esctl._es.cat.nodes(format="json")
        ).format_for_lister(
            columns=[
                ("ip", "IP"),
                ("heap.percent",),
                ("ram.percent",),
                ("cpu"),
                ("load_1m"),
                ("load_5m"),
                ("load_15m"),
                ("node.role", "Role"),
                ("master"),
                ("name"),
            ]
        )
