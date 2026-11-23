from collections import OrderedDict
from collections.abc import Mapping
from typing import Any

import yaml


class Color:
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    END = "\033[0m"
    GREEN = "\033[92m"
    ITALIC = "\033[3m"
    PURPLE = "\033[95m"
    RED = "\033[91m"
    UNDERLINE = "\033[4m"
    YELLOW = "\033[93m"

    @classmethod
    def colorize(cls, text: object, color: str) -> str:
        return f"{color}{text}{cls.END}"


def flatten_dict(dictionary: Mapping[str, Any]) -> dict[str, Any]:
    def expand(key: str, value: object) -> list[tuple[str, Any]]:
        if isinstance(value, dict):
            return [(key + "." + k, v) for k, v in flatten_dict(value).items()]
        return [(key, value)]

    items = [item for k, v in dictionary.items() for item in expand(k, v)]

    return dict(items)


def setup_yaml() -> None:
    """https://stackoverflow.com/a/8661021"""
    yaml.add_representer(
        OrderedDict,
        lambda self, data: self.represent_mapping(
            "tag:yaml.org,2002:map",
            data.items(),
        ),
    )
