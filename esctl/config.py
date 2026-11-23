import copy
import logging
from collections import OrderedDict
from pathlib import Path
from typing import Any

import cerberus
import yaml

from esctl.exceptions import ConfigurationError
from esctl.utils import setup_yaml

DEFAULT_CONFIGURATION_PATH = "~/.esctlrc"


def _flatten_validation_errors(errors: dict, path: tuple[str, ...] = ()):
    """Turn cerberus' nested `errors` into ("clusters.foo.servers", "must be of list type") pairs."""
    for field, problems in errors.items():
        for problem in problems:
            if isinstance(problem, dict):
                yield from _flatten_validation_errors(problem, (*path, str(field)))
            else:
                yield ".".join((*path, str(field))), problem


class Context:
    def __init__(
        self,
        name: str,
        user: dict[str, Any] | None,
        cluster: dict[str, Any],
        settings: dict[str, Any],
        pre_commands: list[dict[str, Any]] | None = None,
    ) -> None:
        self.name = name
        self.user = user
        self.cluster = cluster
        self.settings = settings
        self.pre_commands = pre_commands or []

    def __repr__(self) -> str:
        return f"<Context {self.name} user={self.user} cluster={self.cluster} settings={self.settings}>"


class ConfigFileParser:
    log = logging.getLogger(__name__)

    def __init__(self):
        # Replaced by load_configuration()
        self.path = Path(DEFAULT_CONFIGURATION_PATH).expanduser()
        self.users = {}
        self.contexts = {}
        self.clusters = {}
        self.settings = {}

    def write_config_file(self, content):
        setup_yaml()

        with self.path.open("w") as config_file:
            yaml.dump(content, config_file, default_flow_style=False, width=500)

    def _create_default_config_file(self) -> "OrderedDict[str, Any]":
        self.log.info(
            "%s config file does not exists. Creating a default one...",
            self.path,
        )
        default_config = OrderedDict(
            {
                "settings": {},
                "clusters": {"localhost": {"servers": ["http://localhost:9200"]}},
                "users": {},
                "contexts": {"localhost": {"cluster": "localhost"}},
                "default-context": "localhost",
            },
        )

        self.write_config_file(default_config)

        return default_config

    def _ensure_config_file_is_valid(self, document):
        settings_schema = {
            "no_check_certificate": {"type": "boolean"},
            "max_retries": {"type": "integer"},
            "timeout": {"type": "integer"},
        }

        external_credentials_schema = {
            "type": "dict",
            "schema": {
                "command": {
                    "type": "dict",
                    "required": True,
                    "schema": {
                        "run": {
                            "type": "string",
                            "required": True,
                        },
                    },
                },
            },
        }

        schema = {
            "settings": {"type": "dict", "schema": settings_schema},
            "clusters": {
                "type": "dict",
                "required": True,
                "keysrules": {},
                "valuesrules": {
                    "type": "dict",
                    "schema": {
                        "servers": {"type": "list", "required": True, "minlength": 1, "schema": {"type": "string"}},
                        "settings": {"type": "dict", "schema": settings_schema},
                    },
                },
            },
            "users": {
                "type": "dict",
                "keysrules": {"type": "string"},
                "valuesrules": {
                    "type": "dict",
                    "schema": {
                        "username": {"type": "string"},
                        "password": {"type": "string"},
                        "external_username": external_credentials_schema,
                        "external_password": external_credentials_schema,
                    },
                },
            },
            "contexts": {
                "type": "dict",
                "required": True,
                "keysrules": {"type": "string"},
                "valuesrules": {
                    "type": "dict",
                    "schema": {
                        "cluster": {"type": "string"},
                        "user": {"type": "string"},
                        "pre_commands": {
                            "type": "list",
                            "schema": {
                                "type": "dict",
                                "schema": {
                                    "command": {"type": "string", "required": True, "empty": False},
                                    "wait_for_exit": {"type": "boolean"},
                                    "wait_for_output": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
            "default-context": {"type": "string"},
        }
        cerberus_validator = cerberus.Validator(schema)

        if not cerberus_validator.validate(document):
            for field, problem in _flatten_validation_errors(cerberus_validator.errors):
                self.log.error("Invalid configuration at '%s': %s", field, problem)

            msg = f"{self.path} doesn't match expected schema"
            raise ConfigurationError(msg)

    def load_configuration(self, path: str = DEFAULT_CONFIGURATION_PATH) -> OrderedDict:
        self.path = Path(path).expanduser()
        self.log.debug("Trying to load config file : %s", self.path)
        expected_config_blocks = [
            "clusters",
            "contexts",
            "default-context",
            "settings",
            "users",
        ]

        if self.path.is_file():
            with self.path.open() as config_file:
                try:
                    # An empty file loads as None
                    raw_config_file = OrderedDict(yaml.safe_load(config_file) or {})
                except yaml.YAMLError as err:
                    msg = f"Cannot read YAML from {self.path}: {err}"
                    raise ConfigurationError(msg) from err
        else:
            raw_config_file = self._create_default_config_file()

        self._ensure_config_file_is_valid(raw_config_file)

        for config_block in expected_config_blocks:
            value = raw_config_file.get(config_block)
            # Optional blocks may be omitted: treat them as empty
            if value is None and config_block != "default-context":
                value = {}
            self.__setattr__(config_block, value)

            self.log.debug(
                "Loaded %s: %s",
                config_block,
                self.__getattribute__(config_block),
            )

        return raw_config_file

    def get_context_informations(self, context_name: str):
        # The context gets mutated at runtime (resolved credentials, defaults,
        # running processes...) while the raw configuration may be written back
        # to disk: never share objects between them.
        if context_name not in self.contexts:
            msg = f"Unknown context `{context_name}`. Here are the contexts I know : {', '.join(self.contexts.keys())}"
            raise ConfigurationError(msg)

        raw_context = copy.deepcopy(self.contexts[context_name])
        cluster = copy.deepcopy(self.clusters.get(raw_context.get("cluster")))
        user = None
        if raw_context.get("user") is not None:
            if raw_context.get("user") not in self.users:
                msg = (
                    f"Malformed context `{context_name}` in configuration file : "
                    f"it requires a user named `{raw_context.get('user')}` but none could be found ! "
                    f"Here are the users I know : {', '.join(self.users.keys())}"
                )
                raise ConfigurationError(msg)
            user = copy.deepcopy(self.users.get(raw_context.get("user")))

        if cluster is None:
            msg = (
                f"Malformed context `{context_name}` in configuration file : "
                f"it requires a cluster named `{raw_context.get('cluster')}` but none could be found ! "
                f"Here are the clusters I know : {', '.join(list(self.clusters.keys()))}"
            )
            raise ConfigurationError(msg)

        # Merge global settings and per-cluster settings.
        # Cluster-level settings override global settings
        settings = {**self.settings, **(cluster.get("settings") or {})}

        pre_commands = [
            {"wait_for_exit": True, "wait_for_output": "", **pre_command}
            for pre_command in raw_context.get("pre_commands", [])
        ]

        context = Context(
            context_name,
            user,
            cluster,
            settings,
            pre_commands=pre_commands,
        )

        return context

    def create_context(self, context_name: str | None = None) -> Context:
        if context_name:
            self.log.debug("Using provided context : %s", context_name)
        else:
            context_name = self.__getattribute__("default-context")
            if context_name is None:
                msg = "No context selected: pass --context or set `default-context` in the configuration file."
                raise ConfigurationError(msg)
            self.log.debug("No context provided. Using default context")

        context = self.get_context_informations(context_name)
        self.log.debug(context)

        return context
