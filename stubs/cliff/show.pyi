import argparse
from collections.abc import Sequence

from cliff.display import DisplayCommandBase

class ShowOne(DisplayCommandBase):
    def take_action(self, parsed_args: argparse.Namespace) -> tuple[Sequence[str], Sequence[object]]: ...
    def produce_output(
        self, parsed_args: argparse.Namespace, column_names: Sequence[str], data: Sequence[object]
    ) -> int: ...
