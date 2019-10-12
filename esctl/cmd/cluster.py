import elasticsearch as elasticsearch

from esctl.main import Esctl
from esctl.utils import Color, flatten_dict
from esctl.commands import (
    EsctlCommandWithPersistency,
    EsctlLister,
    EsctlShowOne,
)


class ClusterAllocationExplain(EsctlLister):
    """Provide explanations for shard allocations failures."""

    def take_action(self, parsed_args):
        try:
            response = Esctl._es.cluster.allocation_explain()
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
        health = self._sort_and_order_dict(Esctl._es.cluster.health())

        health["status"] = Color.colorize(
            health.get("status"), getattr(Color, health.get("status").upper())
        )

        return (tuple(health.keys()), tuple(health.values()))


class ClusterStats(EsctlShowOne):
    """Show cluster stats."""

    def take_action(self, parsed_args):
        cluster_stats = self._sort_and_order_dict(
            self.transform(flatten_dict(Esctl._es.cluster.stats()))
        )

        return (tuple(cluster_stats.keys()), tuple(cluster_stats.values()))

    def objects_list_to_flat_dict(self, lst):
        """ Convert a list of dict to a flattened dict with full name.

        :Example:
                node.jvm.versions = [{"version":"12.0.1","vm_name":"OpenJDK 64-Bit Server VM","vm_version":"12.0.1+12","vm_vendor":"Oracle Corporation","bundled_jdk":true,"using_bundled_jdk":true,"count":1}]
            becomes
                {
                    "node.jvm.versions[0].version": "12.0.1",
                    "node.jvm.versions[0].vm_name": "OpenJDK 64-Bit Server VM"
                }

        :param lst: A list of dict to flatten
        :paramtype lst: list
        :return: A dict
        :rtype: dict
        """
        flat_dict = {}
        for (index, element) in enumerate(lst):
            for (attribute, value) in element.items():
                flat_dict["[{}].{}".format(index, attribute)] = value

        return flat_dict

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


class ClusterRoutingAllocationEnable(EsctlCommandWithPersistency):
    """Get and set the routing allocation policy."""

    def take_action(self, parsed_args):
        persistency = "persistent" if parsed_args.persistent else "transient"
        self.log.debug("Persistency is " + persistency)

        if parsed_args.status is None:
            setting = self.settings.get(
                "cluster.routing.allocation.enable", persistency=persistency
            )

            if setting.value is not None:
                if setting.persistency is "defaults":
                    output = "{} ({})".format(
                        setting.value, Color.colorize("default", Color.ITALIC)
                    )
                else:
                    output = setting.value

                print(output)

            else:
                self.log.error(
                    "{} does not exists in {} cluster settings.".format(
                        Color.colorize(setting.name, Color.ITALIC),
                        Color.colorize(persistency, Color.ITALIC),
                    )
                )

        else:
            print(
                (
                    "Changing cluster routing"
                    " allocation policy ({}) to : {}"
                ).format(
                    Color.colorize(
                        "cluster.routing.allocation.enable", Color.ITALIC
                    ),
                    Color.colorize(parsed_args.status, Color.ITALIC),
                )
            )
            print(
                self.settings.set(
                    "cluster.routing.allocation.enable",
                    parsed_args.status,
                    persistency=persistency,
                )
            )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "status",
            metavar="<status>",
            nargs="?",
            help=("Routing allocation status"),
            choices=["all", "primaries", "new_primaries", "none"],
        )

        return parser
