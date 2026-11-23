from esctl.cmd.settings import AbstractClusterSettings
from esctl.commands import EsctlCommand, EsctlLister, EsctlShowOne, add_persistency_arguments, selected_persistency
from esctl.formatter import JSONToCliffFormatter
from esctl.utils import flatten_dict


class NodeExclude(AbstractClusterSettings):
    """Show or define the list of nodes excluded from shard allocation."""

    def take_action(self, parsed_args):
        setting_name = f"cluster.routing.allocation.exclude.{parsed_args.by}"

        if parsed_args.list is not None:
            self.log.info("Changing node exclusion list (%s) to : %s", setting_name, parsed_args.list)
            self._settings_set(setting_name, parsed_args.list, persistency=selected_persistency(parsed_args))

        # Show both: an exclusion can be set as transient, persistent, or both
        return self._settings_get(setting_name)

    def get_parser(self, prog_name):
        parser = add_persistency_arguments(super().get_parser(prog_name))

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
            help=("Comma-separated list of values nodes should have to be excluded from shard allocation"),
        )

        return parser


class NodeHotThreads(EsctlCommand):
    """Print hot threads on each nodes."""

    def take_action(self, parsed_args):
        self.print_output(self.es.nodes.hot_threads(type=parsed_args.type))

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "--type",
            help=("The type to sample (default: cpu), valid choices are: 'cpu', 'wait', 'block'"),
            choices=["cpu", "wait", "block"],
            default="cpu",
        )
        return parser


class NodeList(EsctlLister):
    """List nodes."""

    def take_action(self, parsed_args):
        return JSONToCliffFormatter(self.rows(self.es.cat.nodes(format="json"))).format_for_lister(
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
            ],
        )


class NodeStats(EsctlShowOne):
    """Returns statistical information about nodes in the cluster."""

    def take_action(self, parsed_args):
        stats = self.es.nodes.stats(
            node_id=parsed_args.node,
            metric=parsed_args.metric,
            index_metric=parsed_args.index_metric,
            level=parsed_args.level,
        ).get("nodes")
        self.response = stats

        stats = self.transform(stats)

        return JSONToCliffFormatter(stats, pretty_key=self.pretty_keys).to_show_one(lines=list(stats.keys()))

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
                "Isn't used if indices (or all) metric isn't specified."
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
