import logging
from abc import ABC
from typing import Any, Dict

from esctl.main import Esctl


class Settings(ABC):
    """Abstract class for settings management."""

    log = logging.getLogger(__name__)


class Setting:
    def __init__(self, name: str, value: Any, persistency: str = "defaults"):
        self.name = name
        self.value = value
        self.persistency = persistency


class ClusterSettings(Settings):
    """Handle cluster-level settings."""

    def list(self) -> Dict[str, Dict[str, Any]]:
        return Esctl._es.cluster.get_settings(include_defaults=True, flat_settings=True)

    def get(self, key: str, persistency: str = "transient") -> Setting:
        settings = self.list()

        if key in settings.get(persistency):
            return Setting(key, settings.get(persistency).get(key), persistency)
        else:
            # If the setting cannot be found in the requested persistency
            # look for it in the "defaults" values
            if key in settings.get("defaults"):
                return Setting(key, settings.get("defaults").get(key), "defaults")
            else:
                return Setting(key, None)

    def set(self, sections: str, value, persistency: str = "transient"):
        return Esctl._es.cluster.put_settings(body={persistency: {sections: value}})
