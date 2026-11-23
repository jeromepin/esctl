from esctl.commands import EsctlLister
from esctl.formatter import JSONToCliffFormatter
from esctl.utils import Color

# Disk usage above which `cat allocation` highlights a node. 85% is Elasticsearch's default
# low disk watermark: no new shard is allocated to the node beyond it.
DISK_PERCENT_CRITICAL = 85
DISK_PERCENT_WARNING = 70


class CatAllocation(EsctlLister):
    """Show the number of shards allocated to each node.

    Provides a snapshot of the number of shards allocated to each data node
    and their disk space.
    """

    def take_action(self, parsed_args):
        allocation = self.transform(self.rows(self.es.cat.allocation(format="json")))

        return JSONToCliffFormatter(allocation).format_for_lister(
            columns=[
                ("shards"),
                ("disk.indices"),
                ("disk.used"),
                ("disk.avail"),
                ("disk.total"),
                ("disk.percent"),
                ("host"),
                ("ip", "IP"),
                ("node"),
            ],
        )

    def transform(self, allocation):
        nodes = []

        for node in allocation:
            if self.uses_table_formatter() and node.get("disk.percent") is not None:
                if int(node.get("disk.percent")) > DISK_PERCENT_CRITICAL:
                    node["disk.percent"] = Color.colorize(
                        node.get("disk.percent"),
                        Color.RED,
                    )

                elif int(node.get("disk.percent")) > DISK_PERCENT_WARNING:
                    node["disk.percent"] = Color.colorize(
                        node.get("disk.percent"),
                        Color.YELLOW,
                    )

            nodes.append(node)

        return nodes


class CatPlugins(EsctlLister):
    """Returns informations about installed plugins across nodes."""

    def take_action(self, parsed_args):
        plugins = self.transform(self.rows(self.es.cat.plugins(format="json")))

        return JSONToCliffFormatter(plugins).format_for_lister(
            columns=[("name", "node"), ("component", "plugin"), ("version")],
        )

    def transform(self, plugins):
        return sorted(plugins, key=lambda i: i["name"])


class CatShards(EsctlLister):
    """Provides a detailed view of shard allocation on nodes."""

    def take_action(self, parsed_args):
        nodes = [n["name"] for n in self.rows(self.es.cat.nodes(format="json", h="name"))]
        shards = self.transform(
            self.rows(
                self.es.cat.shards(
                    format="json",
                    index=parsed_args.index,
                    h="index,node,shard,prirep",
                )
            ),
            nodes,
        )

        columns = [("index",)] + [
            (
                n,
                n.lower(),
            )
            for n in nodes
        ]

        if self.has_unassigned_shards:
            columns = [*columns, ("UNASSIGNED",)]

        return JSONToCliffFormatter(shards).format_for_lister(columns=columns)

    def transform(self, shards_list: list[dict[str, str]], nodes: list[str]):
        indices = {}
        self.has_unassigned_shards: bool = False

        for shard in shards_list:
            shard_index = shard.get("index")

            if shard_index not in indices:
                indices[shard_index] = {
                    "index": shard_index,
                    **dict.fromkeys(nodes, ""),
                }

            shard_node = shard.get("node") or "UNASSIGNED"

            if shard_node == "UNASSIGNED":
                self.has_unassigned_shards = True

            # An index can have several shards on the same node: list them all
            shard_name = f"{shard.get('shard')}{shard.get('prirep')}"
            existing = indices[shard_index].get(shard_node)
            indices[shard_index][shard_node] = f"{existing}, {shard_name}" if existing else shard_name

        return list(indices.values())

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "index",
            help="A comma-separated list of index names to limit the returned information",
            nargs="?",
        )
        return parser


class CatThreadpool(EsctlLister):
    """Show cluster-wide thread pool statistics per node.

    Thread pools reference : https://www.elastic.co/guide/en/elasticsearch/reference/6.8/modules-threadpool.html  # noqa
    """

    _default_headers = "node_name,name,active,queue,rejected,type"

    def take_action(self, parsed_args):
        headers = parsed_args.headers or self._default_headers

        thread_pools = self.transform(
            self.rows(
                self.es.cat.thread_pool(
                    format="json",
                    h=headers,
                    thread_pool_patterns=parsed_args.thread_pool_patterns,
                )
            ),
        )

        return JSONToCliffFormatter(thread_pools).format_for_lister(
            columns=[(h,) for h in headers.split(",")],
        )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)

        parser.add_argument(
            "--thread-pool-patterns",
            help=("A comma-separated list of regular-expressions or strings to filter the thread pools in the output"),
        )
        parser.add_argument(
            "--headers",
            help=("A comma-separated list of column names to display"),
            default=self._default_headers,
            type=str,
        )

        return parser

    def transform(self, raw_thread_pools):
        if not self.uses_table_formatter():
            return raw_thread_pools

        modified_thread_pools = []

        for thread_pool in raw_thread_pools:
            for column, value in thread_pool.items():
                # Colorize any number above 0 in the following columns
                if column in ["active", "queue", "rejected"] and int(value) > 0:
                    thread_pool[column] = Color.colorize(value, Color.RED)

            modified_thread_pools.append(thread_pool)

        return modified_thread_pools


class CatTemplates(EsctlLister):
    """Returns information about existing templates."""

    def take_action(self, parsed_args):
        templates = self.rows(self.es.cat.templates(name=parsed_args.name, format="json"))

        return JSONToCliffFormatter(templates).format_for_lister(
            columns=[("name",), ("index_patterns",), ("order",), ("version")],
        )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "name",
            help="A pattern that returned template names must match",
            nargs="?",
        )
        return parser
