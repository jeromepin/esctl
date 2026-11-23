import argparse
from typing import Any

from typing_extensions import override

from esctl.commands import (
    EsctlCommandIndex,
    EsctlListerIndexSetting,
    EsctlShowOne,
    ListerResult,
    ShowOneResult,
    add_persistency_arguments,
    selected_persistency,
)
from esctl.formatter import JSONToCliffFormatter
from esctl.settings import ClusterSettings, IndexSettings, Persistency
from esctl.utils import Color


def displayed_value(value: object) -> object:
    """Show list values one item per line, and `[]` when empty."""
    if isinstance(value, list):
        return ",\n".join(value) if value else "[]"
    return value


class AbstractClusterSettings(EsctlShowOne):
    cluster_settings: ClusterSettings

    def _settings_set(self, setting: str, value: str | None, persistency: Persistency) -> None:
        self.log.debug("Persistency is %s", persistency)

        self.log.debug(
            self.cluster_settings.set(setting, value, persistency=persistency),
        )

    def _settings_get(self, setting: str) -> ShowOneResult:
        s = self.cluster_settings.mget(setting)
        self.response = {
            "transient": s["transient"].value,
            "persistent": s["persistent"].value,
            "defaults": s["defaults"].value,
        }

        return JSONToCliffFormatter(self.response, pretty_key=self.pretty_keys).to_show_one(
            lines=[("transient"), ("persistent"), ("defaults")],
            none_as="" if self.uses_table_formatter() else None,
        )


class AbstractClusterSetting(AbstractClusterSettings):
    """A command acting on the cluster setting given as argument."""

    @override
    def get_parser(self, prog_name: str) -> argparse.ArgumentParser:
        parser = super().get_parser(prog_name)

        parser.add_argument("setting", metavar="<setting>", help=("Setting"))

        return parser


class ClusterSettingsGet(AbstractClusterSetting):
    """Get a setting value."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ShowOneResult:
        return self._settings_get(parsed_args.setting)


class ClusterSettingsList(EsctlShowOne):
    """[Experimental] List available settings."""

    cluster_settings: ClusterSettings

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ShowOneResult:
        settings_list = self.cluster_settings.list_().get("defaults", {})
        self.response = settings_list
        default_settings = {name: displayed_value(value) for name, value in settings_list.items()}

        return (tuple(default_settings.keys()), tuple(default_settings.values()))


class ClusterSettingsReset(AbstractClusterSetting):
    """Reset a setting value."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ShowOneResult:
        self._settings_set(
            parsed_args.setting,
            None,
            persistency=selected_persistency(parsed_args),
        )
        return self._settings_get(parsed_args.setting)

    @override
    def get_parser(self, prog_name: str) -> argparse.ArgumentParser:
        parser = super().get_parser(prog_name)

        add_persistency_arguments(parser)

        return parser


class ClusterSettingsSet(AbstractClusterSetting):
    """Set a setting value."""

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ShowOneResult:
        self._settings_set(
            parsed_args.setting,
            parsed_args.value,
            persistency=selected_persistency(parsed_args),
        )
        return self._settings_get(parsed_args.setting)

    @override
    def get_parser(self, prog_name: str) -> argparse.ArgumentParser:
        parser = super().get_parser(prog_name)

        add_persistency_arguments(parser)

        parser.add_argument("value", metavar="<value>", help=("Setting value"))

        return parser


class IndexSettingsGet(EsctlListerIndexSetting):
    """Get an index-level setting value."""

    def retrieve_setting(self, setting_name: str, index: str) -> list[dict[str, Any]]:
        setting_name = ",".join(
            name if name.startswith("index.") else f"index.{name}" for name in setting_name.split(",")
        )

        raw_settings = self.index_settings.get(index, setting_name)
        return [
            {
                "index": index_name,
                "setting": setting.name,
                "value": setting.value,
                "default": setting.persistency == "defaults",
            }
            for index_name, settings_list in raw_settings.items()
            for setting in settings_list
            if setting.value is not None
        ]

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ListerResult:
        return JSONToCliffFormatter(
            self.retrieve_setting(parsed_args.setting, parsed_args.index),
        ).format_for_lister(columns=[("index",), ("setting",), ("value",), ("default",)])


class IndexSettingsList(EsctlShowOne):
    """[Experimental] List available settings in an index."""

    index_settings: IndexSettings

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> ShowOneResult:
        indices = self.rows(self.es.cat.indices(format="json", h="index"))
        if not indices:
            self.log.warning("There is no index to list settings from.")
            return ((), ())

        sample_index_name = indices[0]["index"]
        # {setting name: Setting}, merged from the index' explicit settings and defaults
        index_settings = self.index_settings.list_(sample_index_name)[sample_index_name]
        self.response = {name: setting.value for name, setting in index_settings.items()}

        settings = {name: displayed_value(setting.value) for name, setting in sorted(index_settings.items())}

        return (tuple(settings.keys()), tuple(settings.values()))


class IndexSettingsSet(EsctlCommandIndex):
    """Set an index-level setting value."""

    index_settings: IndexSettings

    @override
    def take_action(self, parsed_args: argparse.Namespace) -> None:
        setting_name = parsed_args.setting

        if not setting_name.startswith("index."):
            setting_name = f"index.{setting_name}"

        setting = Color.colorize(setting_name, Color.ITALIC)
        value = Color.colorize(parsed_args.value, Color.ITALIC)
        index = Color.colorize(parsed_args.index, Color.ITALIC)
        self.print_output(f"Changing {setting} to {value} in index {index}")

        self.print_output(
            self.index_settings.set(setting_name, parsed_args.value, parsed_args.index),
        )

    @override
    def get_parser(self, prog_name: str) -> argparse.ArgumentParser:
        parser = super().get_parser(prog_name)
        parser.add_argument("setting", metavar="<setting>", help=("Setting"))
        parser.add_argument("value", metavar="<value>", help=("Setting value"))
        return parser
