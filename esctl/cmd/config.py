from esctl.commands import EsctlLister
from esctl.main import Esctl
from esctl.formatter import JSONToCliffFormatter


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
