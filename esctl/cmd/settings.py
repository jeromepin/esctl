import collections

from esctl.commands import EsctlCommandIndex, EsctlListerIndexSetting, EsctlShowOne
from esctl.formatter import JSONToCliffFormatter
from esctl.utils import Color


class AbstractClusterSettings(EsctlShowOne):
    def _settings_set(self, setting: str, value: str, persistency: str):
        self.log.debug("Persistency is " + persistency)

        self.log.debug(
            self.cluster_settings.set(setting, value, persistency=persistency)
        )

    def _settings_get(self, setting: str):
        s = self.cluster_settings.mget(setting)

        return JSONToCliffFormatter(
            {
                "transient": s.get("transient").value,
                "persistent": s.get("persistent").value,
                "defaults": s.get("defaults").value,
            }
        ).to_show_one(
            lines=[("transient"), ("persistent"), ("defaults")],
            none_as="" if self.uses_table_formatter() else None,
        )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)

        parser.add_argument("setting", metavar="<setting>", help=("Setting"))

        return parser


class ClusterSettingsGet(AbstractClusterSettings):
    """Get a setting value."""

    def take_action(self, parsed_args):
        return self._settings_get(parsed_args.setting)


class ClusterSettingsList(EsctlShowOne):
    """[Experimental] List available settings."""

    def take_action(self, parsed_args):
        default_settings = {}
        settings_list = self.cluster_settings.list().get("defaults")

        for (setting_name, setting_value) in settings_list.items():
            if type(setting_value).__name__ == "list":
                if len(setting_value) > 0:
                    setting_value = ",\n".join(setting_value)
                else:
                    setting_value = "[]"

            default_settings[setting_name] = setting_value

        return (tuple(default_settings.keys()), tuple(default_settings.values()))


class ClusterSettingsReset(AbstractClusterSettings):
    """Reset a setting value."""

    def take_action(self, parsed_args):
        self._settings_set(
            parsed_args.setting,
            None,
            persistency="persistent" if parsed_args.persistent else "transient",
        )
        return self._settings_get(parsed_args.setting)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)

        persistency_group = parser.add_mutually_exclusive_group()
        persistency_group.add_argument(
            "--transient",
            action="store_true",
            help=("Set setting as transient (default)"),
        )
        persistency_group.add_argument(
            "--persistent", action="store_true", help=("Set setting as persistent")
        )

        return parser


class ClusterSettingsSet(AbstractClusterSettings):
    """Set a setting value."""

    def take_action(self, parsed_args):
        self._settings_set(
            parsed_args.setting,
            parsed_args.value,
            persistency="persistent" if parsed_args.persistent else "transient",
        )
        return self._settings_get(parsed_args.setting)

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)

        persistency_group = parser.add_mutually_exclusive_group()
        persistency_group.add_argument(
            "--transient",
            action="store_true",
            help=("Set setting as transient (default)"),
        )
        persistency_group.add_argument(
            "--persistent", action="store_true", help=("Set setting as persistent")
        )

        parser.add_argument("value", metavar="<value>", help=("Setting value"))

        return parser


class IndexSettingsGet(EsctlListerIndexSetting):
    """Get an index-level setting value."""

    def retrieve_setting(self, setting_name, index):
        if not setting_name.startswith("index."):
            setting_name = "index.{}".format(setting_name)

        raw_settings = self.index_settings.get(index, setting_name)
        settings = []

        for index_name, settings_list in raw_settings.items():
            for setting in settings_list:
                if setting.value is not None:
                    if setting.persistency == "defaults":
                        value = f"{setting.value} ({Color.colorize('default', Color.ITALIC)})"
                    else:
                        value = setting.value

                    settings.append(
                        {"index": index_name, "setting": setting.name, "value": value}
                    )

        return settings

    def take_action(self, parsed_args):
        return JSONToCliffFormatter(
            self.retrieve_setting(parsed_args.setting, parsed_args.index)
        ).format_for_lister(columns=[("index",), ("setting",), ("value",)])


class IndexSettingsList(EsctlShowOne):
    """[Experimental] List available settings in an index."""

    def take_action(self, parsed_args):
        settings = {}
        sample_index_name = self.es.cat.indices(format="json", h="index")[0].get(
            "index"
        )

        settings_list = self.index_settings.list(sample_index_name)
        settings_list = collections.OrderedDict(
            sorted(
                {
                    **settings_list.get("settings"),
                    **settings_list.get("defaults"),
                }.items()
            )
        )

        for (setting_name, setting_value) in settings_list.items():
            if type(setting_value).__name__ == "list":
                if len(setting_value) > 0:
                    setting_value = ",\n".join(setting_value)
                else:
                    setting_value = "[]"

            settings[setting_name] = setting_value

        return (tuple(settings.keys()), tuple(settings.values()))


class IndexSettingsSet(EsctlCommandIndex):
    """Set an index-level setting value."""

    def take_action(self, parsed_args):
        setting_name = parsed_args.setting

        if not setting_name.startswith("index."):
            setting_name = "index.{}".format(setting_name)

        print(
            "Changing {} to {} in index {}".format(
                Color.colorize(setting_name, Color.ITALIC),
                Color.colorize(parsed_args.value, Color.ITALIC),
                Color.colorize(parsed_args.index, Color.ITALIC),
            )
        )

        print(
            self.index_settings.set(setting_name, parsed_args.value, parsed_args.index)
        )

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument("setting", metavar="<setting>", help=("Setting"))
        parser.add_argument("value", metavar="<value>", help=("Setting value"))
        return parser
