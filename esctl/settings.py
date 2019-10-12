import logging
import elasticsearch as elasticsearch
from abc import ABC

from esctl.main import Esctl
from esctl.utils import Color


class Settings(ABC):
    """Abstract class for settings management."""

    log = logging.getLogger(__name__)


class Setting:
    def __init__(self, name, value, persistency="defaults"):
        self.name = name
        self.value = value
        self.persistency = persistency


class ClusterSettings(Settings):
    """Handle cluster-level settings."""

    def get(self, key, persistency="transient"):
        settings = Esctl._es.cluster.get_settings(
            include_defaults=True, flat_settings=True
        )

        if key in settings.get(persistency):
            return Setting(
                key, settings.get(persistency).get(key), persistency
            )
        else:
            # If the setting cannot be found in the requested persistency
            # look for it in the "defaults" values
            if key in settings.get("defaults"):
                return Setting(
                    key, settings.get("defaults").get(key), "defaults"
                )
            else:
                return Setting(key, None, None)

    def set(self, sections, value, persistency="transient"):
        return Esctl._es.cluster.put_settings(
            body={persistency: {sections: value}}
        )
