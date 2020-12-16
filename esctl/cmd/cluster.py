import elasticsearch as elasticsearch

from esctl.cmd.settings import AbstractClusterSettings
from esctl.commands import EsctlLister, EsctlShowOne
from esctl.utils import Color, flatten_dict


class ClusterAllocationExplain(EsctlLister):
    """Provide explanations for shard allocations failures."""

    def take_action(self, parsed_args):
        try:
            response = self.es.cluster.allocation_explain()
        except elasticsearch.TransportError as transport_error:
            if transport_error.args[0] == 400:
                self.log.warn(
                    (
                        "Unable to find any unassigned shards to explain."
                        " This may indicate that all shards are allocated."
                    )
                )

                return (("Attribute", "Value"), tuple())
        else:
            output = {
                "index": response.get("index"),
                "can_allocate": response.get("can_allocate"),
                "explanation": response.get("allocate_explanation"),
                "last_allocation_status": response.get("unassigned_info").get(
                    "last_allocation_status"
                ),
                "reason": response.get("unassigned_info").get("reason"),
            }

            for node in response.get("node_allocation_decisions"):
                output[node.get("node_name")] = node.get("deciders")[0].get(
                    "explanation"
                )

            return (("Attribute", "Value"), tuple(output.items()))


class ClusterHealth(EsctlShowOne):
    """Show the cluster health."""

    def take_action(self, parsed_args):
        health = self._sort_and_order_dict(self.es.cluster.health())

        if self.uses_table_formatter():
            health["status"] = Color.colorize(
                health.get("status"), getattr(Color, health.get("status").upper())
            )

        return (tuple(health.keys()), tuple(health.values()))


class ClusterInfo(EsctlShowOne):
    """Show basic informations about the cluster."""

    def take_action(self, parsed_args):
        infos = self.es.info()

        if self.uses_table_formatter():
            infos = self._delete_and_merge_inner_dict_into_parent(infos, "version")

        return (tuple(infos.keys()), tuple(infos.values()))


class ClusterStats(EsctlShowOne):
    """Show cluster stats."""

    def take_action(self, parsed_args):
        cluster_stats = self._sort_and_order_dict(
            self.transform(flatten_dict(self.es.cluster.stats()))
        )

        return (tuple(cluster_stats.keys()), tuple(cluster_stats.values()))

    def transform(self, stats):
        for attribute in [
            "nodes.jvm.versions",
            "nodes.os.cpu",
            "nodes.plugins",
            "nodes.os.names",
            "nodes.os.pretty_names",
            "nodes.packaging_types",
        ]:
            if attribute in stats:
                for key, value in self.objects_list_to_flat_dict(
                    stats.get(attribute)
                ).items():
                    stats.update({"{}{}".format(attribute, key): value})

                del stats[attribute]

        return stats


class ClusterRoutingAllocationEnable(AbstractClusterSettings):
    """Get and set the cluster's routing allocation policy."""

    def take_action(self, parsed_args):
        if parsed_args.status is not None:
            self._settings_set(
                "cluster.routing.allocation.enable",
                parsed_args.status,
                persistency="persistent" if parsed_args.persistent else "transient",
            )

        return self._settings_get("cluster.routing.allocation.enable")

    def get_parser(self, prog_name):
        parser = super(AbstractClusterSettings, self).get_parser(prog_name)

        persistency_group = parser.add_mutually_exclusive_group()
        persistency_group.add_argument(
            "--transient",
            action="store_true",
            help=("Set setting as transient (default)"),
        )
        persistency_group.add_argument(
            "--persistent", action="store_true", help=("Set setting as persistent")
        )

        parser.add_argument(
            "status",
            nargs="?",
            help=("Routing allocation status"),
            choices=["all", "primaries", "new_primaries", "none"],
        )

        return parser
