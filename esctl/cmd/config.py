from esctl.commands import EsctlCommand, EsctlLister
from esctl.formatter import JSONToCliffFormatter
from esctl.main import Esctl
from esctl.utils import Color


class ConfigClusterList(EsctlLister):
    """List all configured clusters."""

    def take_action(self, parsed_args):
        clusters = [
            {
                "name": cluster_name,
                "servers": "\n".join(cluster_definition.get("servers")),
            }
            for cluster_name, cluster_definition in Esctl._config.get(
                "clusters"
            ).items()
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
            for context_name, context_definition in Esctl._config.get(
                "contexts"
            ).items()
        ]

        return JSONToCliffFormatter(self.transform(contexts)).format_for_lister(
            columns=[("name"), ("user"), ("cluster")]
        )

    def transform(self, raw_contexts):
        modified_contexts = []

        for context in raw_contexts:
            if context.get("name") == Esctl._config.get("default-context"):
                for context_attribute_name, context_attribute_value in context.items():
                    context[context_attribute_name] = Color.colorize(
                        context_attribute_value, Color.UNDERLINE
                    )

            modified_contexts.append(context)

        return modified_contexts


class ConfigContextSet(EsctlCommand):
    """Set the default context."""

    def take_action(self, parsed_args):
        Esctl._config["default-context"] = parsed_args.context
        Esctl._config_file_parser.write_config_file(dict(Esctl._config))

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "context",
            help=("Context to set as default"),
            choices=Esctl._config.get("contexts"),
        )

        return parser


class ConfigUserList(EsctlLister):
    """List all configured users."""

    def take_action(self, parsed_args):
        users = [
            {
                "name": user_name,
                "username": user_definition.get("username"),
                "password": user_definition.get("password"),
            }
            for user_name, user_definition in Esctl._config.get("users").items()
        ]

        return JSONToCliffFormatter(users).format_for_lister(
            columns=[("name"), ("username"), ("password")]
        )
