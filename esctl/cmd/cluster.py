import argparse
from typing import Any

import elasticsearch
from typing_extensions import override

from esctl.cmd.settings import AbstractClusterSettings
from esctl.commands import EsctlShowOne, ShowOneResult, add_persistency_arguments, selected_persistency
from esctl.utils import Color, flatten_dict


class ClusterAllocationExplain(EsctlShowOne):
    """Provide explanations for shard allocations failures."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ShowOneResult:
        try:
            response = self.es.cluster.allocation_explain()
            self.response = response.body
        except elasticsearch.BadRequestError:
            # Without a body, Elasticsearch explains the first unassigned shard
            # and answers 400 when there is none
            self.log.warning(
                "Unable to find any unassigned shards to explain. This may indicate that all shards are allocated.",
            )

            return ((), ())

        unassigned_info = response.get("unassigned_info") or {}
        output = {
            "index": response.get("index"),
            "can_allocate": response.get("can_allocate"),
            "explanation": response.get("allocate_explanation"),
            "last_allocation_status": unassigned_info.get("last_allocation_status"),
            "reason": unassigned_info.get("reason"),
        }

        for node in response.get("node_allocation_decisions") or []:
            # Nodes where the shard could be allocated have no deciders
            deciders = node.get("deciders") or [{}]
            output[node.get("node_name")] = deciders[0].get("explanation", node.get("node_decision"))

        return (tuple(output.keys()), tuple(output.values()))


class ClusterHealth(EsctlShowOne):
    """Show the cluster health."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ShowOneResult:
        self.response = self.es.cluster.health().body
        health = self._sort_and_order_dict(self.response)

        if self.uses_table_formatter():
            health["status"] = Color.colorize(
                health["status"],
                getattr(Color, health["status"].upper()),
            )

        return (tuple(health.keys()), tuple(health.values()))


class ClusterInfo(EsctlShowOne):
    """Show basic informations about the cluster."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ShowOneResult:
        self.response = self.es.info().body
        # Flattening edits the top-level keys: keep the response intact for --jmespath
        infos = dict(self.response)

        if self.uses_table_formatter():
            infos = self._delete_and_merge_inner_dict_into_parent(infos, "version")

        return (tuple(infos.keys()), tuple(infos.values()))


class ClusterStats(EsctlShowOne):
    """Show cluster stats."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ShowOneResult:
        self.response = self.es.cluster.stats().body
        cluster_stats = self._sort_and_order_dict(
            self.transform(flatten_dict(self.response)),
        )

        return (tuple(cluster_stats.keys()), tuple(cluster_stats.values()))

    def transform(self, stats: dict[str, Any]) -> dict[str, Any]:
        for attribute in [
            "nodes.jvm.versions",
            "nodes.os.cpu",
            "nodes.plugins",
            "nodes.os.names",
            "nodes.os.pretty_names",
            "nodes.packaging_types",
        ]:
            if attribute in stats:
                for key, value in self.objects_list_to_flat_dict(stats[attribute]).items():
                    stats.update({f"{attribute}{key}": value})

                del stats[attribute]

        return stats


class ClusterRoutingAllocationEnable(AbstractClusterSettings):
    """Get and set the cluster's routing allocation policy."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ShowOneResult:
        if parsed_args.status is not None:
            self._settings_set(
                "cluster.routing.allocation.enable",
                parsed_args.status,
                persistency=selected_persistency(parsed_args),
            )

        return self._settings_get("cluster.routing.allocation.enable")

    @override
    def get_parser(self, prog_name: str) -> argparse.ArgumentParser:
        parser = add_persistency_arguments(super().get_parser(prog_name))

        parser.add_argument(
            "status",
            nargs="?",
            help=("Routing allocation status"),
            choices=["all", "primaries", "new_primaries", "none"],
        )

        return parser
