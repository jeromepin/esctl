import argparse
from typing import Any

import yaml
from typing_extensions import override

from esctl.commands import EsctlCommand, EsctlLister, ListerResult
from esctl.formatter import JSONToCliffFormatter
from esctl.utils import Color, setup_yaml


class ConfigClusterList(EsctlLister):
    """List all configured clusters."""

    requires_cluster = False

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ListerResult:
        clusters = [
            {
                "name": cluster_name,
                "servers": "\n".join(cluster_definition.get("servers")),
            }
            for cluster_name, cluster_definition in self.esctl.config["clusters"].items()
        ]

        return JSONToCliffFormatter(clusters).format_for_lister(
            columns=[("name"), ("servers")],
        )


class ConfigContextList(EsctlLister):
    """List all contexts."""

    requires_cluster = False

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ListerResult:
        contexts = [
            {
                "name": context_name,
                "user": context_definition.get("user"),
                "cluster": context_definition.get("cluster"),
            }
            for context_name, context_definition in self.esctl.config["contexts"].items()
        ]

        return JSONToCliffFormatter(self.transform(contexts)).format_for_lister(
            columns=[("name"), ("user"), ("cluster")],
        )

    def transform(self, raw_contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.uses_table_formatter():
            return raw_contexts

        modified_contexts = []

        for context in raw_contexts:
            if context.get("name") == self.esctl.config.get("default-context"):
                for context_attribute_name, context_attribute_value in context.items():
                    context[context_attribute_name] = Color.colorize(
                        context_attribute_value,
                        Color.UNDERLINE,
                    )

            modified_contexts.append(context)

        return modified_contexts


class ConfigContextSet(EsctlCommand):
    """Set the default context."""

    requires_cluster = False

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> None:
        self.esctl.config["default-context"] = parsed_args.context
        self.esctl.config_file_parser.write_config_file(dict(self.esctl.config))

    @override
    def get_parser(self, prog_name: str) -> argparse.ArgumentParser:
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "context",
            help=("Context to set as default"),
            choices=self.esctl.config.get("contexts"),
        )

        return parser


class ConfigShow(EsctlCommand):
    """Print the config."""

    requires_cluster = False

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> None:
        setup_yaml()
        self.print_output(
            yaml.safe_dump(
                dict(self.esctl.config),
                None,
                default_flow_style=False,
                width=500,
            ),
        )


class ConfigUserList(EsctlLister):
    """List all configured users."""

    requires_cluster = False

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ListerResult:
        users = [
            {
                "name": user_name,
                "username": user_definition.get("username"),
                "password": user_definition.get("password"),
            }
            # `users` is optional
            for user_name, user_definition in (self.esctl.config.get("users") or {}).items()
        ]

        return JSONToCliffFormatter(users).format_for_lister(
            columns=[("name"), ("username"), ("password")],
        )
