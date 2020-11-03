from typing import List


class TableKey:
    def __init__(self, id, name=None):
        self.id = id
        if name is None:
            self.name = self._create_name_from_id()
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

    def _split_string(self, string: str) -> List[str]:
        splitted_string: List[str]

        if "." in string:
            splitted_string = string.split(".")

            # Check if words can also be splitted on underscores
            for idx in range(len(splitted_string)):
                # If there is an underscore anywhere in the word except at the beginning
                if "_" in splitted_string[idx] and not splitted_string[idx].startswith(
                    "_"
                ):
                    splitted_string[idx] = splitted_string[idx].split("_")

            flat_list = []
            for sublist in splitted_string:
                if sublist.__class__.__name__ == "list":
                    for item in sublist:
                        flat_list.append(item)
                else:
                    flat_list.append(sublist)

            splitted_string = flat_list

        elif "_" in string:
            splitted_string = string.split("_")

        else:
            splitted_string = [string]

        return splitted_string

    def _create_name_from_id(self):
        """Extrapolate the column's name based on its ID."""
        name = self._split_string(self.id)

        for idx in range(len(name)):
            # Format some special words like "percent" -> %
            name[idx] = self._format_special_word(name[idx])

            # Put the word to titlecase unless it contains at least an uppercase letter
            if all(char.islower() for char in name[idx]):
                name[idx] = name[idx].title()
            else:
                # If the word contains an uppercase letter somewhere, maintain the case
                # but uppercase the first letter
                if name[idx].startswith("_"):
                    name[idx] = name[idx][0] + name[idx][1].upper() + name[idx][2:]
                else:
                    name[idx] = name[idx][0].upper() + name[idx][1:]

        name = " ".join(name)

        return name

    def __repr__(self):
        return "({}, {})".format(self.id, self.name)


class JSONToCliffFormatter:
    """ Format a JSON object to one of the cliff's class expected inputs."""

    def __init__(self, json):
        self.json = json

    def _format_columns(self, columns):
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
        valid_list = []

        for column in columns:
            if isinstance(column, str):
                column = (column,)

            valid_list.append(TableKey(*column))

        return valid_list

    def format_for_lister(self, columns=[]):
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

        columns = self._format_columns(columns)

        lst = []
        # For every line in the JSON object, pick the value corresponding to
        # the given column ID
        for line in self.json:
            lst.append(tuple([line.get(column.id) for column in columns]))

        return (tuple([c.name for c in columns]), tuple(lst))

    def to_show_one(self, lines=[]):
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
        lines = self._format_columns(lines)

        keys = []
        values = []

        for line in lines:
            keys.append(line.name)
            values.append(self.json.get(line.id))

        return (tuple(keys), tuple(values))
