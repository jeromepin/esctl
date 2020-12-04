from esctl.commands import EsctlCommand, EsctlLister, EsctlShowOne
from esctl.formatter import JSONToCliffFormatter
from esctl.utils import Color, flatten_dict


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
        print(self.es.nodes.hot_threads(doc_type=parsed_args.type))

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


class NodeStats(EsctlShowOne):
    """Returns statistical information about nodes in the cluster."""

    def take_action(self, parsed_args):
        stats = self.es.nodes.stats(
            format="json",
            node_id=parsed_args.node,
            metric=parsed_args.metric,
            index_metric=parsed_args.index_metric,
            level=parsed_args.level,
        ).get("nodes")

        if parsed_args.jmespath is not None:
            path = self.jmespath_search(parsed_args.jmespath, stats)

            return (tuple(["Result"]), tuple([path]))

        stats = self.transform(stats)

        return JSONToCliffFormatter(
            stats, pretty_key=not parsed_args.no_pretty
        ).to_show_one(lines=list(stats.keys()))

    def transform(self, raw_stats):
        if self.uses_table_formatter():
            return flatten_dict(raw_stats)

        return raw_stats

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "--node",
            help="A comma-separated list of node IDs or names to limit the returned information.",
            default=None,
        )
        parser.add_argument(
            "--metric",
            help=(
                "A comma-separated list of metrics you wish returned. Valid choices are: "
                "_all, breaker, fs, http, indices, jvm, os, process, "
                "thread_pool, transport, discovery, indexing_pressure."
            ),
            default=None,
        )
        parser.add_argument(
            "--index-metric",
            help=(
                "A comma-separated list of indices metrics you wish returned. "
                "Isn’t used if indices (or all) metric isn’t specified."
                "Valid choices are: "
                "_all, completion, docs, fielddata, query_cache, flush, get, indexing, merge, "
                "request_cache, refresh, search, segments, store, warmer, suggest."
            ),
            default=None,
        )
        parser.add_argument(
            "--level",
            help=(
                "Return indices stats aggregated at index, node or shard level. "
                "Valid choices are: indices, node, shards."
            ),
            default="node",
        )

        return parser
