import fnmatch
import logging
from typing import Any, Literal

from elastic_transport import ObjectApiResponse
from elasticsearch import Elasticsearch

from esctl.elasticsearch import Client
from esctl.utils import Color

# Where a cluster setting is written
Persistency = Literal["transient", "persistent"]


class Settings:
    """Base class of the settings helpers."""

    log = logging.getLogger(__name__)

    @property
    def es(self) -> Elasticsearch:
        return Client.get()


class Setting:
    def __init__(self, name: str, value: Any, persistency: str = "defaults"):
        self.name = name
        self.value = value
        self.persistency = persistency

    def __str__(self) -> str:
        return f"{self.name}={self.value}({self.persistency})"


class ClusterSettings(Settings):
    """Handle cluster-level settings."""

    def list_(self) -> dict[str, dict[str, Any]]:
        return self.es.cluster.get_settings(include_defaults=True, flat_settings=True).body

    def get(self, key: str, persistency: str = "transient") -> Setting:
        settings = self.list_()

        if key in settings.get(persistency, {}):
            return Setting(key, settings[persistency][key], persistency)
        # If the setting cannot be found in the requested persistency
        # look for it in the "defaults" values
        if key in settings.get("defaults", {}):
            return Setting(key, settings["defaults"][key], "defaults")
        return Setting(key, None)

    def __get_setting_for_persistency(
        self,
        settings: dict[str, dict[str, Any]],
        key: str,
        persistency: str,
    ) -> Setting:
        if key in settings.get(persistency, {}):
            return Setting(key, settings[persistency][key], persistency)

        return Setting(key, None)

    def mget(self, key: str) -> dict[str, Setting]:
        settings = self.list_()

        return {
            "transient": self.__get_setting_for_persistency(settings, key, "transient"),
            "persistent": self.__get_setting_for_persistency(
                settings,
                key,
                "persistent",
            ),
            "defaults": self.__get_setting_for_persistency(settings, key, "defaults"),
        }

    def set(self, sections: str, value: Any, persistency: Persistency = "transient") -> ObjectApiResponse[Any]:
        self.log.info(
            "Changing %s's %s to : %s",
            persistency,
            Color.colorize(sections, Color.ITALIC),
            Color.colorize(value, Color.ITALIC),
        )
        if persistency == "persistent":
            return self.es.cluster.put_settings(persistent={sections: value}, flat_settings=True)
        return self.es.cluster.put_settings(transient={sections: value}, flat_settings=True)


class IndexSettings(Settings):
    """Handle index-level settings."""

    def list_(self, index: str) -> dict[str, dict[str, Setting]]:
        self.log.debug("Retrieving settings list for indices : %s", index)

        settings: dict[str, dict[str, Setting]] = {}

        for index_name, index_settings in self.es.indices.get_settings(
            index=index,
            include_defaults=True,
            flat_settings=True,
        ).body.items():
            settings[index_name] = {}
            for setting_name, setting_value in index_settings.get("settings", {}).items():
                settings[index_name][setting_name] = Setting(
                    setting_name,
                    setting_value,
                    "settings",
                )
            for setting_name, setting_value in index_settings.get("defaults", {}).items():
                settings[index_name][setting_name] = Setting(
                    setting_name,
                    setting_value,
                    "defaults",
                )

        return settings

    def get(self, index: str, key: str) -> dict[str, list[Setting]]:
        """Get settings of one or several indices.

        `key` is a comma-separated list of setting names, each one possibly
        containing `*` wildcards.
        """
        self.log.debug("Retrieving setting(s) '%s' for indices : %s", key, index)

        response = self.list_(index)
        # Indices can define different settings: match patterns against all of them
        known_settings = sorted({name for index_settings in response.values() for name in index_settings})

        requested_settings: list[str] = []
        for pattern in key.split(","):
            matches = fnmatch.filter(known_settings, pattern) if "*" in pattern else [pattern]
            requested_settings.extend(name for name in matches if name not in requested_settings)

        return {
            index_name: [index_settings.get(name) or Setting(name, None) for name in requested_settings]
            for index_name, index_settings in response.items()
        }

    def set(self, setting: str, value: Any, index: str) -> ObjectApiResponse[Any]:
        return self.es.indices.put_settings(index=index, settings={setting: value})
