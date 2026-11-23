"""Colors are for humans: only the table formatter may contain ANSI codes."""

import pytest

THREAD_POOLS = [
    {"node_name": "node-1", "name": "search", "active": "3", "queue": "0", "rejected": "1", "type": "fixed"}
]
SNAPSHOTS = [
    {"id": "snap-1", "status": "PARTIAL", "failed_shards": "2"},
    {"id": "snap-2", "status": "IN_PROGRESS", "failed_shards": "0"},
]


def routes(fake_es):
    fake_es.on("GET", "/_cat/thread_pool", THREAD_POOLS)
    fake_es.on("GET", "/_cat/snapshots/backups", SNAPSHOTS)


COMMANDS = [
    ("cat", "thread-pool"),
    ("snapshot", "list", "backups"),
    ("config", "context", "list"),
]


@pytest.mark.parametrize("argv", COMMANDS)
@pytest.mark.parametrize("formatter", ["json", "csv", "yaml", "value"])
def test_machine_readable_formats_have_no_color_codes(run_esctl, fake_es, argv, formatter):
    routes(fake_es)

    result = run_esctl(*argv, "-f", formatter)

    assert result.code == 0, result.err
    # JSON and YAML escape the control character itself: look for the reset sequence
    assert "[0m" not in result.out


@pytest.mark.parametrize("argv", COMMANDS)
def test_tables_are_still_colored(run_esctl, fake_es, argv):
    routes(fake_es)

    result = run_esctl(*argv)

    assert result.code == 0, result.err
    assert "\x1b[" in result.out
