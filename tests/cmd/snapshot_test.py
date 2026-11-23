import pytest
from cliff.formatters.table import TableFormatter

from esctl.cmd.snapshot import SnapshotList


@pytest.mark.parametrize(
    ("snapshot", "expected"),
    [
        ({"status": "SUCCESS", "failed_shards": "0"}, {"status": "SUCCESS", "failed_shards": "0"}),
        (
            {"status": "PARTIAL", "failed_shards": "0"},
            {"status": "\x1b[93mPARTIAL\x1b[0m", "failed_shards": "\x1b[91m0\x1b[0m"},
        ),
        (
            {"status": "IN_PROGRESS", "failed_shards": "0"},
            {"status": "\x1b[96mIN_PROGRESS\x1b[0m", "failed_shards": "0"},
        ),
    ],
)
def test_value_based_color(snapshot, expected):
    command = SnapshotList(None, None)
    command.formatter = TableFormatter()

    assert command.transform([snapshot])[0] == expected
