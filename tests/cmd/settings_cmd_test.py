def test_index_settings_list(run_esctl, fake_es):
    fake_es.on("GET", "/_cat/indices", [{"index": "logs"}, {"index": "metrics"}])
    fake_es.on(
        "GET",
        "/logs/_settings",
        {
            "logs": {
                "settings": {"index.number_of_shards": "1"},
                "defaults": {"index.refresh_interval": "1s", "index.routing.allocation.include._tier_preference": []},
            },
        },
    )

    result = run_esctl("index", "settings", "list", "-f", "json")

    assert result.code == 0, result.err
    assert result.json() == {
        "index.number_of_shards": "1",
        "index.refresh_interval": "1s",
        "index.routing.allocation.include._tier_preference": "[]",
    }


def test_index_settings_list_without_any_index(run_esctl, fake_es):
    fake_es.on("GET", "/_cat/indices", [])

    result = run_esctl("index", "settings", "list", "-f", "json")

    assert result.code == 0, result.err
    assert "no index" in result.err


INDEX_SETTINGS = {
    "logs": {
        "settings": {"index.number_of_replicas": "1", "index.refresh_interval": "5s"},
        "defaults": {"index.number_of_shards": "1"},
    },
    "metrics": {
        "settings": {"index.number_of_replicas": "0", "index.routing.allocation.require.box": "hot"},
        "defaults": {"index.number_of_shards": "1", "index.refresh_interval": "1s"},
    },
}


def get_settings(run_esctl, fake_es, setting):
    fake_es.on("GET", "/logs,metrics/_settings", INDEX_SETTINGS)
    result = run_esctl("index", "settings", "get", "logs,metrics", setting, "-f", "json")
    assert result.code == 0, result.err
    return {(row["Index"], row["Setting"]): row["Value"] for row in result.json()}


def test_settings_only_set_on_some_indices_are_found(run_esctl, fake_es):
    rows = get_settings(run_esctl, fake_es, "routing.allocation.*")

    assert rows == {("metrics", "index.routing.allocation.require.box"): "hot"}


def test_mixing_wildcards_and_names(run_esctl, fake_es):
    rows = get_settings(run_esctl, fake_es, "number_of_r*,refresh_interval")

    assert set(rows) == {
        ("logs", "index.number_of_replicas"),
        ("logs", "index.refresh_interval"),
        ("metrics", "index.number_of_replicas"),
        ("metrics", "index.refresh_interval"),
    }


def test_index_prefix_is_added_to_every_name(run_esctl, fake_es):
    rows = get_settings(run_esctl, fake_es, "number_of_replicas,refresh_interval")

    assert rows[("logs", "index.refresh_interval")] == "5s"


def test_no_matching_index(run_esctl, fake_es):
    fake_es.on("GET", "/nope*/_settings", {})

    result = run_esctl("index", "settings", "get", "nope*", "-f", "json")

    assert result.code == 0, result.err
    assert result.json() == []
