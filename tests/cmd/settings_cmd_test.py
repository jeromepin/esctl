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
