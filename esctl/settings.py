import fnmatch
import logging
from abc import ABC
from typing import Any, Dict, List, Union

from esctl.elasticsearch import Client
from esctl.utils import Color


class Settings(ABC):
    """Abstract class for settings management."""

    log = logging.getLogger(__name__)
    es = Client().es


class Setting:
    def __init__(self, name: str, value: Any, persistency: str = "defaults"):
        self.name = name
        self.value = value
        self.persistency = persistency

    def __str__(self) -> str:
        return f"{self.name}={self.value}({self.persistency})"


class ClusterSettings(Settings):
    """Handle cluster-level settings."""

    def list(self) -> Dict[str, Dict[str, Any]]:
        return self.es.cluster.get_settings(include_defaults=True, flat_settings=True)

    def get(self, key: str, persistency: str = "transient") -> Setting:
        settings: Dict[str, Dict[str, Any]] = self.list()

        if key in settings.get(persistency):
            return Setting(key, settings.get(persistency).get(key), persistency)
        else:
            # If the setting cannot be found in the requested persistency
            # look for it in the "defaults" values
            if key in settings.get("defaults"):
                return Setting(key, settings.get("defaults").get(key), "defaults")
            else:
                return Setting(key, None)

    def __get_setting_for_persistency(
        self, settings: Dict[str, Dict[str, Any]], key: str, persistency: str
    ) -> Setting:
        if key in settings.get(persistency):
            return Setting(key, settings.get(persistency).get(key), persistency)

        return Setting(key, None)

    def mget(self, key: str) -> Dict[str, Setting]:
        settings: Dict[str, Dict[str, Any]] = self.list()

        return {
            "transient": self.__get_setting_for_persistency(settings, key, "transient"),
            "persistent": self.__get_setting_for_persistency(
                settings, key, "persistent"
            ),
            "defaults": self.__get_setting_for_persistency(settings, key, "defaults"),
        }

    def set(self, sections: str, value, persistency: str = "transient"):
        self.log.info(
            "Changing {}'s {} to : {}".format(
                persistency,
                Color.colorize(sections, Color.ITALIC),
                Color.colorize(value, Color.ITALIC),
            )
        )
        return self.es.cluster.put_settings(
            body={persistency: {sections: value}},
            flat_settings=True,
        )


class IndexSettings(Settings):
    """Handle index-level settings."""

    def list(self, index: str) -> Dict[str, Dict[str, Setting]]:
        self.log.debug("Retrieving settings list for indices : {}".format(index))

        settings: Dict[str, Dict[str, Setting]] = {}

        for index_name, index_settings in self.es.indices.get_settings(
            index=index, include_defaults=True, flat_settings=True
        ).items():
            settings[index_name] = {}
            for setting_name, setting_value in index_settings.get("settings").items():
                settings[index_name][setting_name] = Setting(
                    setting_name, setting_value, "settings"
                )
            for setting_name, setting_value in index_settings.get("defaults").items():
                settings[index_name][setting_name] = Setting(
                    setting_name, setting_value, "defaults"
                )

        return settings

    def get(self, index: str, key: Union[str, None]) -> Dict[str, List[Setting]]:
        self.log.debug("Retrieving setting(s) '{}' for indices : {}".format(key, index))

        response = self.list(index)
        settings: Dict[str, List[Setting]] = {}
        requested_settings: List[str] = []

        known_settings = [
            list(index_settings.keys()) for _, index_settings in response.items()
        ][0]

        if "*" in key:
            requested_settings = fnmatch.filter(known_settings, key)

        elif "," in key:
            requested_settings = key.split(",")
        else:
            requested_settings = [key]

        for index_name, index_settings in response.items():
            settings[index_name] = []

            for setting_name in requested_settings:
                if setting_name in known_settings:
                    settings[index_name].append(index_settings.get(setting_name))
                else:
                    settings[index_name].append(Setting(setting_name, None))

        return settings

    def set(self, setting: str, value: Any, index: str):
        return self.es.indices.put_settings(index=index, body={setting: value})
