from esctl.commands import EsctlLister
from esctl.main import Esctl
from esctl.utils import Color
from esctl.formatter import JSONToCliffFormatter


class CatAllocation(EsctlLister):
    """Show shard allocation.

    Provides a snapshot of how shards are located around the cluster and the
    state of disk usage.
    """

    def take_action(self, parsed_args):
        allocation = self.transform(Esctl._es.cat.allocation(format="json"))

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
            ]
        )

    def transform(self, allocation):
        nodes = []

        for node in allocation:
            if int(node.get("disk.percent")) > 85:
                node["disk.percent"] = Color.colorize(
                    node.get("disk.percent"), Color.RED
                )

            elif int(node.get("disk.percent")) > 70:
                node["disk.percent"] = Color.colorize(
                    node.get("disk.percent"), Color.YELLOW
                )

            nodes.append(node)

        return nodes
