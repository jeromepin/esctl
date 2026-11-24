"""Commands sending a body to Elasticsearch."""

import io

import pytest


@pytest.mark.parametrize(("flag", "persistency"), [((), "transient"), (("--persistent",), "persistent")])
def test_cluster_settings_set(run_esctl, fake_es, flag, persistency):
    fake_es.on("PUT", "/_cluster/settings", {"acknowledged": True})
    fake_es.on("GET", "/_cluster/settings", {"transient": {}, "persistent": {}, "defaults": {}})

    result = run_esctl("cluster", "settings", "set", *flag, "indices.recovery.max_bytes_per_sec", "100mb")

    assert result.code == 0, result.err
    assert fake_es.last("PUT", "/_cluster/settings").body == {
        persistency: {"indices.recovery.max_bytes_per_sec": "100mb"}
    }


def test_index_settings_set(run_esctl, fake_es):
    fake_es.on("PUT", "/logs/_settings", {"acknowledged": True})

    result = run_esctl("index", "settings", "set", "logs", "number_of_replicas", "2")

    assert result.code == 0, result.err
    assert fake_es.last("PUT", "/logs/_settings").body == {"index.number_of_replicas": "2"}


def test_index_reindex(run_esctl, fake_es):
    fake_es.on("POST", "/_reindex", {"took": 1})

    result = run_esctl("index", "reindex", "old", "new", "--conflicts", "proceed")

    assert result.code == 0, result.err
    assert fake_es.last("POST", "/_reindex").body == {
        "source": {"index": "old"},
        "dest": {"index": "new", "version_type": "internal", "op_type": "index"},
        "conflicts": "proceed",
    }


def test_index_create_from_a_file(run_esctl, fake_es, tmp_path):
    configuration = tmp_path / "index.json"
    configuration.write_text('{"settings": {"number_of_shards": 1}, "mappings": {"properties": {}}}')
    fake_es.on("PUT", "/logs", {"acknowledged": True})

    result = run_esctl("index", "create", "logs", "--configuration", str(configuration))

    assert result.code == 0, result.err
    assert fake_es.last("PUT", "/logs").body == {"settings": {"number_of_shards": 1}, "mappings": {"properties": {}}}


def test_index_create_rejects_unknown_keys(run_esctl, fake_es, tmp_path):
    configuration = tmp_path / "index.json"
    configuration.write_text('{"setings": {}}')  # spellchecker:disable-line

    result = run_esctl("index", "create", "logs", "--configuration", str(configuration))

    assert result.code == 1
    assert "Unknown index configuration keys: setings" in result.err  # spellchecker:disable-line
    assert fake_es.requests == []


def test_timeout_setting_is_used_per_request(run_esctl, fake_es, default_config):
    default_config["settings"]["timeout"] = 42
    fake_es.on("GET", "/_cluster/health", {"status": "green"})

    result = run_esctl("cluster", "health", config=default_config)

    assert result.code == 0, result.err


def test_index_create_with_an_empty_configuration_uses_defaults(run_esctl, fake_es, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    fake_es.on("PUT", "/logs", {"acknowledged": True})

    result = run_esctl("index", "create", "logs")

    assert result.code == 0, result.err
    assert fake_es.last("PUT", "/logs").body is None
