import pytest

TASKS = {
    "nodes": {
        "node-id": {
            "name": "node-1",
            "tasks": {
                "node-id:1": {
                    "node": "node-id",
                    "id": 1,
                    "type": "transport",
                    "action": "indices:data/read/search",
                    "start_time_in_millis": 1700000000050,
                    "running_time_in_nanos": 1000,
                    "cancellable": True,
                    "headers": {},
                },
            },
        },
    },
}


@pytest.mark.parametrize(("argv", "expected"), [((), "false"), (("--detailed",), "true")])
def test_detailed_follows_the_flag(run_esctl, fake_es, argv, expected):
    fake_es.on("GET", "/_tasks", TASKS)

    result = run_esctl("task", "list", *argv, "-f", "json")

    assert result.code == 0, result.err
    assert fake_es.last("GET", "/_tasks").query["detailed"] == [expected]


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    [
        (1700000000000, "2023-11-14 22:13:20.000"),
        (1700000000050, "2023-11-14 22:13:20.050"),
        (1700000000123, "2023-11-14 22:13:20.123"),
        (1700000000999, "2023-11-14 22:13:20.999"),
    ],
)
def test_start_time_keeps_three_digit_milliseconds(timestamp, expected):
    from esctl.cmd.task import TaskList

    assert TaskList(None, None).convert_timestamp_in_ms_to_human_readable(timestamp) == expected
