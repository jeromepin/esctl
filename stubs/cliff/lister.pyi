import argparse
from collections.abc import Iterable, Sequence

from cliff.display import DisplayCommandBase

class Lister(DisplayCommandBase):
    def take_action(self, parsed_args: argparse.Namespace) -> tuple[Sequence[str], Iterable[Sequence[object]]]: ...
    def produce_output(
        self,
        parsed_args: argparse.Namespace,
        column_names: Sequence[str],
        data: Iterable[Sequence[object]],
    ) -> int: ...
