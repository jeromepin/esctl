import logging
import os
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

import cerberus
import yaml


class Context:
    def __init__(self, name, user, cluster, settings):
        super().__init__()
        self.log = logging.getLogger(__name__)
        self.name = name
        self.user = user
        self.cluster = cluster
        self.settings = settings


class ConfigFileParser:
    log = logging.getLogger(__name__)

    def __init__(self):
        self.users = {}
        self.contexts = {}
        self.clusters = {}
        self.settings = {}

    def write_config_file(self, content):
        with open(self.path, "w") as config_file:
            yaml.dump(content, config_file, default_flow_style=False)

    def _create_default_config_file(self) -> "OrderedDict[str, Any]":
        self.log.info(
            "{} config file does not exists. Creating a default one...".format(
                self.path
            )
        )
        default_config = OrderedDict(
            {
                "settings": {},
                "clusters": {"localhost": {"servers": ["http://localhost:9200"]}},
                "users": {},
                "contexts": {"localhost": {"cluster": "localhost"}},
                "default-context": "localhost",
            }
        )

        self.write_config_file(default_config)

        return default_config

    def _ensure_config_file_is_valid(self, document):
        settings_schema = {
            "no_check_certificate": {"type": "boolean"},
            "max_retries": {"type": "integer"},
            "timeout": {"type": "integer"},
        }
        schema = {
            "settings": {"type": "dict", "schema": settings_schema},
            "clusters": {
                "type": "dict",
                "keysrules": {},
                "valuesrules": {
                    "type": "dict",
                    "schema": {
                        "servers": {"type": "list"},
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
                    },
                },
            },
            "contexts": {
                "type": "dict",
                "keysrules": {"type": "string"},
                "valuesrules": {
                    "type": "dict",
                    "schema": {
                        "cluster": {"type": "string"},
                        "user": {"type": "string"},
                    },
                },
            },
            "default-context": {"type": "string"},
        }
        cerberus_validator = cerberus.Validator(schema)

        if not cerberus_validator.validate(document):
            for root_error in cerberus_validator._errors:
                for inner_error in root_error.info[0]:
                    self.log.error(
                        "Unknown configuration : {}".format(
                            ".".join(inner_error.document_path)
                        )
                    )
                self.log.error(
                    (
                        "Invalid type or schema for configuration field '{0}'."
                        " Should be {1}. Got '{2}'"
                    ).format(root_error.field, root_error.constraint, root_error.value)
                )

            raise SyntaxError("{} doesn't match expected schema".format(self.path))

    def load_configuration(self, path: str = "~/.esctlrc") -> OrderedDict:
        self.path = os.path.expanduser(path)
        self.log.debug("Trying to load config file : {}".format(self.path))
        expected_config_blocks = [
            "clusters",
            "contexts",
            "default-context",
            "settings",
            "users",
        ]

        if Path(self.path).is_file():
            with open(self.path, "r") as config_file:
                try:
                    raw_config_file = OrderedDict(yaml.safe_load(config_file))
                except yaml.YAMLError as err:
                    self.log.critical("Cannot read YAML from {}".format(self.path))
                    self.log.critical(str(err.problem) + str(err.problem_mark))
                    sys.exit(1)
        else:
            raw_config_file = self._create_default_config_file()

        try:
            self._ensure_config_file_is_valid(raw_config_file)
        except SyntaxError:
            sys.exit(1)

        for config_block in expected_config_blocks:
            self.__setattr__(config_block, raw_config_file.get(config_block))

            self.log.debug(
                "Loaded {}: {}".format(
                    config_block, self.__getattribute__(config_block)
                )
            )

        return raw_config_file

    def get_context_informations(self, context_name: str):
        user = self.users.get(self.contexts.get(context_name).get("user"))
        cluster = self.clusters.get(self.contexts.get(context_name).get("cluster"))

        # Merge global settings and per-cluster settings.
        # Cluster-level settings override global settings
        if "settings" in cluster:
            settings = {**self.settings, **cluster.get("settings")}
        else:
            settings = {**self.settings}

        return Context(context_name, user, cluster, settings)

    def create_context(self, context_name: str = None) -> Context:
        if context_name:
            self.log.debug("Using provided context : {}".format(context_name))
        else:
            context_name = self.__getattribute__("default-context")
            self.log.debug(
                "No context provided. Using default context : {}".format(context_name)
            )

        try:
            context = self.get_context_informations(context_name)
        except AttributeError:
            self.log.fatal("Cannot load context '{}'.".format(context_name))
            sys.exit(1)

        return context
