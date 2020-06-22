from ward import test
from fixtures import Cases, dummy_esctl_with_dummy_context

c = Cases(
    [
        {
            "input": {"status": "SUCCESS", "failed_shards": "0"},
            "expected_output": {"status": "SUCCESS", "failed_shards": "0"},
        },
        {
            "input": {"status": "PARTIAL", "failed_shards": "0"},
            "expected_output": {
                "status": "\x1b[93mPARTIAL\x1b[0m",
                "failed_shards": "\x1b[91m0\x1b[0m",
            },
        },
        {
            "input": {"status": "IN_PROGRESS", "failed_shards": "0"},
            "expected_output": {
                "status": "\x1b[96mIN_PROGRESS\x1b[0m",
                "failed_shards": "0",
            },
        },
    ]
)


@test("Snapshot list coloring : {input[status]}", tags=["snapshot"])
def _(
    esctl=dummy_esctl_with_dummy_context,
    input=c.input(),
    expected_output=c.expected_output(),
):
    from esctl.cmd.snapshot import SnapshotList

    snapshot_list_cmd = SnapshotList(esctl, [])

    assert snapshot_list_cmd.transform([input])[0] == expected_output
