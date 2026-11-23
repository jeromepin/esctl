"""--jmespath queries the API response and --no-pretty disables key prettifying, on every key/value command."""

import pytest

SETTINGS = {
    "transient": {"cluster.routing.allocation.enable": "primaries"},
    "persistent": {"cluster.routing.allocation.exclude._ip": "10.0.0.1"},
    "defaults": {"a.b": "c"},
}

# (argv, routes, JMESPath query, expected result)
CASES = [
    (("cluster", "health"), [("GET", "/_cluster/health", {"status": "green"})], "status", "green"),
    (("cluster", "info"), [("GET", "/", {"version": {"number": "8.15.0"}})], "version.number", "8.15.0"),
    (("cluster", "stats"), [("GET", "/_cluster/stats", {"nodes": {"count": {"total": 12}}})], "nodes.count.total", 12),
    (
        ("cluster", "allocation", "explain"),
        [("POST", "/_cluster/allocation/explain", {"index": "logs", "node_allocation_decisions": []})],
        "index",
        "logs",
    ),
    (
        ("cluster", "routing", "allocation", "enable"),
        [("GET", "/_cluster/settings", SETTINGS)],
        "transient",
        "primaries",
    ),
    (("cluster", "settings", "get", "a.b"), [("GET", "/_cluster/settings", SETTINGS)], "defaults", "c"),
    (("cluster", "settings", "list"), [("GET", "/_cluster/settings", SETTINGS)], '"a.b"', "c"),
    (
        ("cluster", "settings", "set", "a.b", "d"),
        [("PUT", "/_cluster/settings", {}), ("GET", "/_cluster/settings", SETTINGS)],
        "defaults",
        "c",
    ),
    (
        ("cluster", "settings", "reset", "a.b"),
        [("PUT", "/_cluster/settings", {}), ("GET", "/_cluster/settings", SETTINGS)],
        "defaults",
        "c",
    ),
    (("node", "exclude"), [("GET", "/_cluster/settings", SETTINGS)], "persistent", "10.0.0.1"),
    (
        ("node", "stats"),
        [("GET", "/_nodes/stats", {"nodes": {"abc": {"jvm": {"mem": {"heap_used_percent": 42}}}}})],
        "*.jvm.mem.heap_used_percent",
        [42],
    ),
    (
        ("document", "get", "logs", "42"),
        [("GET", "/logs/_doc/42", {"_index": "logs", "_source": {"msg": "hi"}})],
        "_source.msg",
        "hi",
    ),
    (
        ("repository", "show", "backups"),
        [("GET", "/_snapshot/backups", {"backups": {"type": "fs", "settings": {"location": "/mnt"}}})],
        "settings.location",
        "/mnt",
    ),
    (
        ("index", "settings", "list"),
        [
            ("GET", "/_cat/indices", [{"index": "logs"}]),
            ("GET", "/logs/_settings", {"logs": {"settings": {"index.number_of_shards": "1"}, "defaults": {}}}),
        ],
        '"index.number_of_shards"',
        "1",
    ),
]


@pytest.mark.parametrize(("argv", "routes", "query", "expected"), CASES, ids=[" ".join(c[0]) for c in CASES])
def test_jmespath_queries_the_api_response(run_esctl, fake_es, argv, routes, query, expected):
    for method, path, body in routes:
        fake_es.on(method, path, body)

    result = run_esctl(*argv, "--jmespath", query, "-f", "json")

    assert result.code == 0, result.err
    assert result.json() == {"Result": expected}


def test_no_pretty_shows_raw_keys(run_esctl, fake_es):
    fake_es.on("GET", "/logs/_doc/42", {"found": True, "_source": {"msg": "hi"}})

    pretty = run_esctl("document", "get", "logs", "42", "-f", "json")
    raw = run_esctl("document", "get", "logs", "42", "--no-pretty", "-f", "json")

    assert pretty.json() == {"Found": True, "_Source Msg": "hi"}
    assert raw.json() == {"found": True, "_source.msg": "hi"}


def test_no_pretty_on_settings(run_esctl, fake_es):
    fake_es.on("GET", "/_cluster/settings", SETTINGS)

    result = run_esctl("cluster", "settings", "get", "a.b", "--no-pretty", "-f", "json")

    assert result.json() == {"transient": None, "persistent": None, "defaults": "c"}


def test_commands_with_raw_keys_are_unchanged_by_no_pretty(run_esctl, fake_es):
    fake_es.on("GET", "/_cluster/health", {"cluster_name": "prod", "status": "green"})

    assert (
        run_esctl("cluster", "health", "-f", "json").json()
        == run_esctl("cluster", "health", "--no-pretty", "-f", "json").json()
        == {"cluster_name": "prod", "status": "green"}
    )
