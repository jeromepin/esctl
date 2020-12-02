from typing import Dict, List

from esctl.commands import EsctlLister
from esctl.formatter import JSONToCliffFormatter


class SecurityUsersGet(EsctlLister):
    """Retrieves information about users in the native realm and built-in users."""

    def take_action(self, parsed_args):
        users = self.transform(
            self._sort_and_order_dict(
                self.es.security.get_user(format="json", username=parsed_args.username)
            )
        )

        return JSONToCliffFormatter(users).format_for_lister(
            columns=[
                ("username",),
                ("roles",),
                ("fullname",),
                ("email",),
                ("metadata",),
                ("enabled",),
            ]
        )

    def transform(self, raw_users):
        users: List[Dict[str, str]] = []
        for _, user in raw_users.items():
            user["roles"] = ", ".join(user.get("roles"))
            users.append(user)

        return users

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)

        parser.add_argument(
            "username",
            help=("A comma-separated list of username"),
            nargs="?",
            default=None,
        )

        return parser
