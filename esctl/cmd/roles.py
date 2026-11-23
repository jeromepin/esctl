import argparse
from typing import Any

from esctl.commands import EsctlLister, ListerResult
from esctl.formatter import JSONToCliffFormatter


class SecurityRolesGet(EsctlLister):
    """Retrieves roles in the native realm."""

    def take_action(self, parsed_args: argparse.Namespace) -> ListerResult:
        roles = self.transform(
            self._sort_and_order_dict(
                self.es.security.get_role(name=parsed_args.roles).body,
            ),
        )

        return JSONToCliffFormatter(roles).format_for_lister(
            columns=[
                ("role",),
                ("cluster", "Cluster-level permissions"),
                ("indices", "Index-level permissions"),
                ("applications",),
                ("run_as",),
            ],
        )

    def transform(self, raw_roles: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        roles = []

        for role_name, role_definition in raw_roles.items():
            role_definition["cluster"] = ", ".join(role_definition.get("cluster", []))
            roles.append({"role": role_name, **role_definition})

        return roles

    def get_parser(self, prog_name: str) -> argparse.ArgumentParser:
        parser = super().get_parser(prog_name)

        parser.add_argument(
            "roles",
            help=("A comma-separated list of roles"),
            nargs="?",
            default=None,
        )

        return parser
