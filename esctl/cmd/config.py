from esctl.commands import EsctlLister
from esctl.formatter import JSONToCliffFormatter
from esctl.main import Esctl


class ConfigClusterList(EsctlLister):
    """List all configured clusters."""

    def take_action(self, parsed_args):
        clusters = [
            {
                "name": cluster_name,
                "servers": "\n".join(cluster_definition.get("servers")),
            }
            for cluster_name, cluster_definition in Esctl._config.clusters.items()
        ]

        return JSONToCliffFormatter(clusters).format_for_lister(
            columns=[("name"), ("servers")]
        )


class ConfigContextList(EsctlLister):
    """List all contexts."""

    def take_action(self, parsed_args):
        contexts = [
            {
                "name": context_name,
                "user": context_definition.get("user"),
                "cluster": context_definition.get("cluster"),
            }
            for context_name, context_definition in Esctl._config.contexts.items()
        ]

        return JSONToCliffFormatter(contexts).format_for_lister(
            columns=[("name"), ("user"), ("cluster")]
        )


class ConfigUserList(EsctlLister):
    """List all configured users."""

    def take_action(self, parsed_args):
        users = [
            {
                "name": user_name,
                "username": user_definition.get("username"),
                "password": user_definition.get("password"),
            }
            for user_name, user_definition in Esctl._config.users.items()
        ]

        return JSONToCliffFormatter(users).format_for_lister(
            columns=[("name"), ("username"), ("password")]
        )
