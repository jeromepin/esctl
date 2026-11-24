import pytest

from esctl.formatter import TableKey

PRETTY_NAMES = [
    ("index.uuid", "Index UUID"),
    ("index.id", "Index ID"),
    ("index.gc_deletes", "Index GC Deletes"),
    ("foo.bar", "Foo Bar"),
    ("index.provided_name", "Index Provided Name"),
    ("index.soft_deletes.retention_lease.period", "Index Soft Deletes Retention Lease Period"),
    ("FooBar", "FooBar"),
    ("foo_bar", "Foo Bar"),
    ("foo-bar", "Foo-bar"),
    ("foo.percent", "Foo %"),
    ("_index", "_Index"),
    ("_seq_no", "_Seq_no"),
    ("_", "_"),
    ("_source._metadata.createTime", "_Source _Metadata CreateTime"),
]

# Keys of `node stats` start with a node ID, which should be kept as-is
NODE_ID_KEYS = [
    ("b4XevSayQNCx_-1mrroUzw.index.uuid", "b4XevSayQNCx_-1mrroUzw Index UUID"),
    ("BfTa0i_sQQmyFsVzjOtApQ.index.uuid", "BfTa0i_sQQmyFsVzjOtApQ Index UUID"),  # spellchecker:disable-line
    ("Xggkx0fORHO_vgJ-WBp0bw.index.uuid", "Xggkx0fORHO_vgJ-WBp0bw Index UUID"),
]


@pytest.mark.parametrize(("key", "expected"), PRETTY_NAMES)
def test_pretty_name(key, expected):
    assert TableKey(key).name == expected


@pytest.mark.xfail(reason="node IDs are split on underscores and title-cased", strict=True)
@pytest.mark.parametrize(("key", "expected"), NODE_ID_KEYS)
def test_pretty_name_keeps_node_ids(key, expected):
    assert TableKey(key).name == expected


@pytest.mark.parametrize("key", [key for key, _ in PRETTY_NAMES + NODE_ID_KEYS])
def test_raw_name(key):
    assert TableKey(key, pretty_key=False).name == key
