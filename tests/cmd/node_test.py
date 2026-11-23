import pytest

EXCLUDE = "cluster.routing.allocation.exclude._ip"


def test_node_exclude_shows_transient_and_persistent_exclusions(run_esctl, fake_es):
    fake_es.on(
        "GET",
        "/_cluster/settings",
        {"transient": {}, "persistent": {EXCLUDE: "10.0.0.1"}, "defaults": {}},
    )

    result = run_esctl("node", "exclude", "-f", "json")

    assert result.code == 0, result.err
    assert result.json() == {"Transient": None, "Persistent": "10.0.0.1", "Defaults": None}


@pytest.mark.parametrize(("flags", "persistency"), [((), "transient"), (("--persistent",), "persistent")])
def test_node_exclude_sets_the_selected_persistency(run_esctl, fake_es, flags, persistency):
    fake_es.on("PUT", "/_cluster/settings", {"acknowledged": True})
    fake_es.on("GET", "/_cluster/settings", {"transient": {}, "persistent": {}, "defaults": {}})

    result = run_esctl("node", "exclude", *flags, "--by", "_name", "node-1,node-2")

    assert result.code == 0, result.err
    assert fake_es.last("PUT", "/_cluster/settings").body == {
        persistency: {"cluster.routing.allocation.exclude._name": "node-1,node-2"},
    }
