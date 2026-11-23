import argparse
from typing import Any

from typing_extensions import override

from esctl.commands import EsctlLister, ListerResult
from esctl.formatter import JSONToCliffFormatter


class SecurityUsersGet(EsctlLister):
    """Retrieves information about users in the native realm and built-in users."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ListerResult:
        users = self.transform(
            self._sort_and_order_dict(
                self.es.security.get_user(username=parsed_args.username).body,
            ),
        )

        return JSONToCliffFormatter(users).format_for_lister(
            columns=[
                ("username",),
                ("roles",),
                ("fullname",),
                ("email",),
                ("metadata",),
                ("enabled",),
            ],
        )

    def transform(self, raw_users: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        users: list[dict[str, Any]] = []
        for user in raw_users.values():
            user["roles"] = ", ".join(user.get("roles", []))
            users.append(user)

        return users

    @override
    def get_parser(self, prog_name: str) -> argparse.ArgumentParser:
        parser = super().get_parser(prog_name)

        parser.add_argument(
            "username",
            help=("A comma-separated list of username"),
            nargs="?",
            default=None,
        )

        return parser
