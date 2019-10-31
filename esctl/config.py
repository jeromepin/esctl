import logging
import os
import yaml
import sys
from pathlib import Path

import cerberus


class Context:
    def __init__(self, name, **kwargs):
        super().__init__()
        self.log = logging.getLogger(__name__)
        self.name = name

        for key, value in kwargs.items():
            setattr(self, key, value)


class ConfigFileParser:
    log = logging.getLogger(__name__)

    def __init__(self):
        super().__init__()
        self.path = os.path.expanduser("~") + "/.esctlrc"
        self.log.debug("Trying to load config file : {}".format(self.path))

    def _create_default_config_file(self):
        self.log.info(
            "{} config file does not exists. Creating a default one...".format(
                self.path
            )
        )
        default_config = {
            "settings": {},
            "clusters": {"localhost": {"servers": ["http://localhost:9200"]}},
            "users": {},
            "contexts": {"localhost": {"cluster": "localhost"}},
            "default-context": "localhost",
        }

        with open(self.path, "w") as config_file:
            yaml.dump(default_config, config_file, default_flow_style=False)

    def _ensure_config_file_is_valid(self, document):
        schema = {
            "settings": {
                "type": "dict",
                "schema": {
                    "no_check_certificate": {"type": "boolean"},
                    "max_retries": {"type": "integer"},
                    "timeout": {"type": "integer"},
                },
            },
            "clusters": {"type": "dict"},
            "users": {"type": "dict"},
            "contexts": {"type": "dict"},
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
                    ).format(
                        root_error.field, root_error.constraint, root_error.value,
                    )
                )

            raise SyntaxError("{} doesn't match expected schema".format(self.path))

    def load_configuration(self):
        self.log.debug("Loading configuration...")
        expected_config_blocks = [
            "clusters",
            "contexts",
            "default-context",
            "settings",
            "users",
        ]

        if not Path(self.path).is_file():
            self._create_default_config_file()

        with open(self.path, "r") as config_file:
            try:
                raw_config_file = yaml.safe_load(config_file)
            except yaml.YAMLError as err:
                self.log.critical("Cannot read YAML from {}".format(self.path))
                self.log.critical(str(err.problem) + str(err.problem_mark))
                sys.exit(1)

        try:
            self._ensure_config_file_is_valid(raw_config_file)
        except SyntaxError:
            sys.exit(1)

        for config_block in expected_config_blocks:
            if not hasattr(self, config_block):
                setattr(self, config_block, None)
            self.load_config_block_from_json(raw_config_file, config_block)
            self.log.debug("{}: {}".format(config_block, getattr(self, config_block)))

    def load_config_block_from_json(self, raw_config, key):
        if key in raw_config:
            setattr(self, key, raw_config.get(key))
        else:
            self.log.debug("Cannot find config block : " + key)

    def get_context_informations(self, context_name):
        user = self.users.get(self.contexts.get(context_name).get("user"))
        cluster = self.clusters.get(self.contexts.get(context_name).get("cluster"))

        # Merge global settings and per-cluster settings.
        # Cluster-level settings override global settings
        if "settings" in cluster:
            settings = {**self.settings, **cluster.get("settings")}
        else:
            settings = {**self.settings}

        return Context(context_name, user=user, cluster=cluster, settings=settings)
