from esctl.commands import EsctlLister
from esctl.formatter import JSONToCliffFormatter


class MigrationDeprecations(EsctlLister):
    """Retrieve information about different cluster, node, and index level settings that use
    deprecated features that will be removed or changed in a future version."""

    def take_action(self, parsed_args):
        deprecations = self.transform(
            self.request("GET", "/_migration/deprecations", None)
        )

        return JSONToCliffFormatter(deprecations).format_for_lister(
            columns=[
                ("kind"),
                ("level",),
                ("message"),
                ("url", "Doc"),
            ]
        )

    def transform(
        self,
        deprecations: dict[str, list[dict[str, str]] | dict[str, list[dict[str, str]]]],
    ) -> list[dict[str, str]]:
        foo: list[dict[str, str]] = []

        # Convert index_settings which is a dict[str, list[dict[str, str]]] to the same format
        # as other keys (i.e list[dict[str, str]])
        if "index_settings" in deprecations and len(deprecations["index_settings"]) > 0:
            flattened_index_settings_deprecations = []
            for index_name, deprecation_list in deprecations["index_settings"].items():
                for deprecation in deprecation_list:
                    deprecation["message"] = f"[{index_name}] {deprecation['message']}"
                    flattened_index_settings_deprecations.append(deprecation)

            deprecations["index_settings"] = flattened_index_settings_deprecations

        for kind, elements in deprecations.items():
            for deprecation in elements:
                foo.append(
                    {
                        "kind": kind,
                        "level": deprecation["level"],
                        "message": deprecation["message"],
                        "url": deprecation["url"],
                    }
                )

        return foo
