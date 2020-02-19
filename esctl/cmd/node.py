from esctl.commands import EsctlCommand, EsctlLister
from esctl.formatter import JSONToCliffFormatter
from esctl.utils import Color


class NodeExclude(EsctlCommand):
    """Define a list of excluded nodes from routing."""

    def take_action(self, parsed_args):
        setting_name = "cluster.routing.allocation.exclude.{}".format(parsed_args.by)

        if parsed_args.list is None:
            setting = self.cluster_settings.get(setting_name, persistency="transient")

            if setting.value is None:
                setting.value = ""

            self.print_success(setting.value)

        else:
            self.print_output(
                ("Changing node exclusion list" " ({}) to : {}").format(
                    Color.colorize(setting_name, Color.ITALIC),
                    Color.colorize(parsed_args.list, Color.ITALIC),
                )
            )
            self.print_success(
                self.cluster_settings.set(
                    setting_name, parsed_args.list, persistency="transient"
                )
            )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)

        parser.add_argument(
            "--by",
            help=(
                "Attribute to filter by (default: _ip). "
                "This can be a custom string or one of the built-ins: "
                " _ip, _name, _host."
            ),
            default="_ip",
        )
        parser.add_argument(
            "list",
            metavar="<list>",
            nargs="?",
            help=(
                "Comma-separated list of values nodes should have to be"
                " excluded from shard allocation"
            ),
        )

        return parser


class NodeHotThreads(EsctlCommand):
    """Print hot threads on each nodes."""

    def take_action(self, parsed_args):
        print(self.es.nodes.hot_threads(type=parsed_args.type))

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
        return JSONToCliffFormatter(self.es.cat.nodes(format="json")).format_for_lister(
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
