from collections.abc import Iterable, Mapping
from typing import Any

from typing_extensions import override


class TableKey:
    def __init__(self, key: str, name: str | None = None, *, pretty_key: bool = True) -> None:
        self.key = key
        if name is None:
            self.name = self._create_name_from_key(pretty_key=pretty_key)
        else:
            self.name = name

    def _format_special_word(self, word: str) -> str:
        if word.lower() in ["percent", "gc", "id", "uuid"]:
            if word == "percent":
                word = "%"

            elif word == "gc":
                word = "GC"

            elif word == "id":
                word = "ID"

            elif word == "uuid":
                word = "UUID"

        return word

    def _split_string(self, string: str) -> list[str]:
        """Split a key into words on dots, then on underscores.

        A leading underscore is part of the word (`_source`, `_index`) and is kept.
        """
        words: list[str] = []

        for part in string.split("."):
            if "_" in part and not part.startswith("_"):
                words.extend(part.split("_"))
            else:
                words.append(part)

        return words

    def _create_name_from_key(self, *, pretty_key: bool = True) -> str:
        """Extrapolate the column's name based on its ID."""
        if not pretty_key:
            return self.key

        name = self._split_string(self.key)

        for idx in range(len(name)):
            # Format some special words like "percent" -> %
            name[idx] = self._format_special_word(name[idx])

            # Put the word to titlecase unless it contains at least an uppercase letter
            if all(char.islower() for char in name[idx]):
                name[idx] = name[idx].title()
            # If the word contains an uppercase letter somewhere, maintain the case
            # but uppercase the first letter
            elif name[idx].startswith("_") and len(name[idx]) > 1:
                name[idx] = name[idx][0] + name[idx][1].upper() + name[idx][2:]
            else:
                name[idx] = name[idx][0].upper() + name[idx][1:]

        return " ".join(name)

    @override
    def __repr__(self) -> str:
        return f"({self.key}, {self.name})"


class JSONToCliffFormatter:
    """Format a JSON object to one of the cliff's class expected inputs."""

    def __init__(self, json: Mapping[str, Any] | Iterable[Mapping[str, Any]], *, pretty_key: bool = True) -> None:
        self.json = json
        self.pretty_key = pretty_key

    def _format_columns(self, columns: Iterable[str | tuple[str, ...]]) -> list[TableKey]:
        """Ensure all elements given as column names are formatted as needed.

        Each element must finally be a TableKey object containing the column ID
        and the column name.

        :Example:
            [
                ("disk.total"),
                ("disk.percent", "Disk %"),
            ]

            becomes

            [
                TableKey("disk.total", "Disk Total"),
                TableKey("disk.percent", "Disk %"),
            ]

        :param columns: The columns to format as a list of tuples containing
                        two elements : the original column ID as given in the
                        JSON object and an optional string defining the new
                        column name (otherwise it will be extrapolated from
                        the column ID)
        :paramtype columns: list
        :return: A list of TableKey objects
        :rtype: list
        """
        return [
            TableKey(*((column,) if isinstance(column, str) else column), pretty_key=self.pretty_key)
            for column in columns
        ]

    def format_for_lister(
        self, columns: Iterable[str | tuple[str, ...]] = (), none_as: object = None
    ) -> tuple[tuple[str, ...], tuple[tuple[object, ...], ...]]:
        """Convert a JSON object to an object compliant with
        cliff's Lister class.

        :Example:
            json :
                [{
                    'shards': '0',
                    'disk.indices': '0b',
                    'disk.used': '13.3gb',
                    'disk.avail': '45gb',
                    'disk.total': '58.4gb',
                    'disk.percent': '22',
                    'host': '172.17.0.2',
                    'ip': '172.17.0.2',
                    'node': '1b5a7b9edd01'
                }]
            columns :
                [
                    'shards',
                    'disk.indices',
                    'disk.used',
                    'disk.avail',
                    'disk.total',
                    ('disk.percent', 'Disk %'),
                    'host',
                    ('ip', 'IP'),
                    'node'
                ]

        :param columns: The columns to format as a list of tuples containing
                        two elements : the original column ID as given in the
                        JSON object and an optional string defining the new
                        column name
        :paramtype columns: list
        :return: A tuple containing two tuples : the first one contains the
        columns' headers and the second one the lines to display
        :rtype: tuple
        """
        if isinstance(self.json, Mapping):
            msg = "Expected a list of rows to format for a lister"
            raise TypeError(msg)

        keys = self._format_columns(columns)

        lst = []
        # For every line in the JSON object, pick the value corresponding to
        # the given column ID
        for raw_line in self.json:
            line = []
            for column in keys:
                element = raw_line.get(column.key)

                if element is None:
                    element = none_as

                line.append(element)

            lst.append(tuple(line))

        return (tuple([c.name for c in keys]), tuple(lst))

    def to_show_one(
        self, lines: Iterable[str | tuple[str, ...]] = (), none_as: object = None
    ) -> tuple[tuple[str, ...], tuple[object, ...]]:
        """For every given element, retrieve the value in the original
        json object based on the key provided

        :param lines: The columns to format as a list of tuples containing
                        two elements : the original column ID as given in the
                        JSON object and an optional string defining the
                        new column name
        :paramtype lines: list
        :return: A tuple containing two tuples : the first one contains the
        keys and the second one the values to display
        :rtype: tuple
        """
        if not isinstance(self.json, Mapping):
            msg = "Expected a mapping to format for a show-one"
            raise TypeError(msg)

        keys = []
        values = []

        for line in self._format_columns(lines):
            keys.append(line.name)

            element = self.json.get(line.key)
            if element is None:
                element = none_as

            values.append(element)

        return (tuple(keys), tuple(values))
