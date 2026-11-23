import argparse

from esctl.commands import EsctlLister, ListerResult
from esctl.formatter import JSONToCliffFormatter


class MigrationDeprecations(EsctlLister):
    """Retrieve information about different cluster, node, and index level settings that use
    deprecated features that will be removed or changed in a future version.
    """

    def take_action(self, parsed_args: argparse.Namespace) -> ListerResult:
        response = self.request("GET", "/_migration/deprecations", None)
        if not isinstance(response, dict):
            msg = f"Unexpected deprecations response: {response!r}"
            raise TypeError(msg)

        deprecations = self.transform(response)

        return JSONToCliffFormatter(deprecations).format_for_lister(
            columns=[
                ("kind"),
                ("level",),
                ("message"),
                ("url", "Doc"),
            ],
        )

    def transform(
        self,
        deprecations: dict[str, list[dict[str, str]] | dict[str, list[dict[str, str]]]],
    ) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []

        for kind, elements in deprecations.items():
            # Some kinds (index_settings, data_streams, templates, ilm_policies...)
            # group their deprecations by resource name: prefix messages with it
            kind_deprecations = (
                [
                    {**deprecation, "message": f"[{name}] {deprecation['message']}"}
                    for name, resource_deprecations in elements.items()
                    for deprecation in resource_deprecations
                ]
                if isinstance(elements, dict)
                else elements
            )

            rows.extend(
                {
                    "kind": kind,
                    "level": deprecation["level"],
                    "message": deprecation["message"],
                    "url": deprecation["url"],
                }
                for deprecation in kind_deprecations
            )

        return rows
