from esctl.commands import EsctlLister
from esctl.formatter import JSONToCliffFormatter


class SecurityRolesGet(EsctlLister):
    """Retrieves roles in the native realm."""

    def take_action(self, parsed_args):
        roles = self.transform(
            self._sort_and_order_dict(
                self.es.security.get_role(format="json", name=parsed_args.roles)
            )
        )

        return JSONToCliffFormatter(roles).format_for_lister(
            columns=[
                ("role",),
                ("cluster", "Cluster-level permissions"),
                ("indices", "Index-level permissions"),
                ("applications",),
                ("run_as",),
            ]
        )

    def transform(self, raw_roles):
        roles = []

        for role_name, role_definition in raw_roles.items():
            role_definition["cluster"] = ", ".join(role_definition.get("cluster"))
            roles.append({**{"role": role_name}, **role_definition})

        return roles

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)

        parser.add_argument(
            "roles", help=("A comma-separated list of roles"), nargs="?", default=None
        )

        return parser
