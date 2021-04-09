import logging
import os
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List

import cerberus
import yaml


class Context:
    def __init__(self, name, user, cluster, settings, **kwargs):
        super().__init__()
        self.log = logging.getLogger(__name__)
        self.name = name
        self.user = user
        self.cluster = cluster
        self.settings = settings

        for k, v in kwargs.items():
            setattr(self, k, v)

    def __repr__(self):
        return f"<Context {self.name} user={self.user} cluster={self.cluster} settings={self.settings}>"


class ConfigFileParser:
    log = logging.getLogger(__name__)

    def __init__(self):
        self.users = {}
        self.contexts = {}
        self.clusters = {}
        self.settings = {}

    def write_config_file(self, content):
        def setup_yaml():
            """ https://stackoverflow.com/a/8661021 """
            yaml.add_representer(
                OrderedDict,
                lambda self, data: self.represent_mapping(
                    "tag:yaml.org,2002:map", data.items()
                ),
            )

        setup_yaml()

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

        external_credentials_schema = {
            "type": "dict",
            "schema": {
                "command": {
                    "type": "dict",
                    "schema": {
                        "run": {
                            "type": "string",
                            "required": True,
                        }
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
                                    "command": {"type": "string"},
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
        raw_context = self.contexts.get(context_name)
        user = self.users.get(raw_context.get("user"))
        cluster = self.clusters.get(raw_context.get("cluster"))

        if cluster is None:
            self.log.error(
                f"Malformed context `{context_name}` in configuration file : "
                f"it requires a cluster named `{raw_context.get('cluster')}` but none could be found ! "
                f"Here are the clusters I know : {', '.join(list(self.clusters.keys()))}"
            )
            sys.exit(1)

        # Merge global settings and per-cluster settings.
        # Cluster-level settings override global settings
        if "settings" in cluster:
            settings = {**self.settings, **cluster.get("settings")}
        else:
            settings = {**self.settings}

        pre_commands: List[Dict] = []
        if "pre_commands" in raw_context:
            pre_commands = raw_context.get("pre_commands")

            for i in range(len(pre_commands)):
                pre_command = pre_commands[i]
                pre_command = {
                    **{"wait_for_exit": True, "wait_for_output": ""},
                    **pre_command,
                }

                pre_commands[i] = pre_command

        context = Context(
            context_name, user, cluster, settings, pre_commands=pre_commands
        )

        return context

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
