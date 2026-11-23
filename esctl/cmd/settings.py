from esctl.commands import (
    EsctlCommandIndex,
    EsctlListerIndexSetting,
    EsctlShowOne,
    add_persistency_arguments,
    selected_persistency,
)
from esctl.formatter import JSONToCliffFormatter
from esctl.settings import ClusterSettings, IndexSettings, Persistency
from esctl.utils import Color


class AbstractClusterSettings(EsctlShowOne):
    cluster_settings: ClusterSettings

    def _settings_set(self, setting: str, value: str | None, persistency: Persistency) -> None:
        self.log.debug("Persistency is " + persistency)

        self.log.debug(
            self.cluster_settings.set(setting, value, persistency=persistency),
        )

    def _settings_get(self, setting: str):
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

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)

        parser.add_argument("setting", metavar="<setting>", help=("Setting"))

        return parser


class ClusterSettingsGet(AbstractClusterSetting):
    """Get a setting value."""

    def take_action(self, parsed_args):
        return self._settings_get(parsed_args.setting)


class ClusterSettingsList(EsctlShowOne):
    """[Experimental] List available settings."""

    cluster_settings: ClusterSettings

    def take_action(self, parsed_args):
        default_settings = {}
        settings_list = self.cluster_settings.list_().get("defaults", {})
        self.response = settings_list

        for setting_name, setting_value in settings_list.items():
            if type(setting_value).__name__ == "list":
                if len(setting_value) > 0:
                    setting_value = ",\n".join(setting_value)
                else:
                    setting_value = "[]"

            default_settings[setting_name] = setting_value

        return (tuple(default_settings.keys()), tuple(default_settings.values()))


class ClusterSettingsReset(AbstractClusterSetting):
    """Reset a setting value."""

    def take_action(self, parsed_args):
        self._settings_set(
            parsed_args.setting,
            None,
            persistency=selected_persistency(parsed_args),
        )
        return self._settings_get(parsed_args.setting)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)

        add_persistency_arguments(parser)

        return parser


class ClusterSettingsSet(AbstractClusterSetting):
    """Set a setting value."""

    def take_action(self, parsed_args):
        self._settings_set(
            parsed_args.setting,
            parsed_args.value,
            persistency=selected_persistency(parsed_args),
        )
        return self._settings_get(parsed_args.setting)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)

        add_persistency_arguments(parser)

        parser.add_argument("value", metavar="<value>", help=("Setting value"))

        return parser


class IndexSettingsGet(EsctlListerIndexSetting):
    """Get an index-level setting value."""

    def retrieve_setting(self, setting_name, index):
        setting_name = ",".join(
            name if name.startswith("index.") else f"index.{name}" for name in setting_name.split(",")
        )

        raw_settings = self.index_settings.get(index, setting_name)
        settings = []

        for index_name, settings_list in raw_settings.items():
            for setting in settings_list:
                if setting.value is not None:
                    settings.append(
                        {
                            "index": index_name,
                            "setting": setting.name,
                            "value": setting.value,
                            "default": setting.persistency == "defaults",
                        },
                    )

        return settings

    def take_action(self, parsed_args):
        return JSONToCliffFormatter(
            self.retrieve_setting(parsed_args.setting, parsed_args.index),
        ).format_for_lister(columns=[("index",), ("setting",), ("value",), ("default",)])


class IndexSettingsList(EsctlShowOne):
    """[Experimental] List available settings in an index."""

    index_settings: IndexSettings

    def take_action(self, parsed_args):
        indices = self.rows(self.es.cat.indices(format="json", h="index"))
        if not indices:
            self.log.warning("There is no index to list settings from.")
            return ((), ())

        sample_index_name = indices[0]["index"]
        # {setting name: Setting}, merged from the index' explicit settings and defaults
        index_settings = self.index_settings.list_(sample_index_name)[sample_index_name]
        self.response = {name: setting.value for name, setting in index_settings.items()}

        settings = {}
        for setting_name, setting in sorted(index_settings.items()):
            setting_value = setting.value
            if isinstance(setting_value, list):
                setting_value = ",\n".join(setting_value) if setting_value else "[]"

            settings[setting_name] = setting_value

        return (tuple(settings.keys()), tuple(settings.values()))


class IndexSettingsSet(EsctlCommandIndex):
    """Set an index-level setting value."""

    index_settings: IndexSettings

    def take_action(self, parsed_args):
        setting_name = parsed_args.setting

        if not setting_name.startswith("index."):
            setting_name = f"index.{setting_name}"

        print(
            f"Changing {Color.colorize(setting_name, Color.ITALIC)} to {Color.colorize(parsed_args.value, Color.ITALIC)} in index {Color.colorize(parsed_args.index, Color.ITALIC)}",
        )

        print(
            self.index_settings.set(setting_name, parsed_args.value, parsed_args.index),
        )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument("setting", metavar="<setting>", help=("Setting"))
        parser.add_argument("value", metavar="<value>", help=("Setting value"))
        return parser
