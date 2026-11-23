def test_raw_get(run_esctl, fake_es):
    fake_es.on("GET", "/_cluster/health", {"status": "green"})

    result = run_esctl("raw", "/_cluster/health")

    assert result.code == 0, result.err
    assert result.json() == {"status": "green"}


def test_raw_route_without_leading_slash(run_esctl, fake_es):
    fake_es.on("GET", "/_cluster/health", {"status": "green"})

    result = run_esctl("raw", "_cluster/health")

    assert result.code == 0, result.err
    assert result.json() == {"status": "green"}


def test_raw_sends_a_json_body(run_esctl, fake_es):
    fake_es.on("PUT", "/_cluster/settings", {"acknowledged": True})

    result = run_esctl("raw", "-X", "put", "-d", '{"persistent": {"a": 1}}', "/_cluster/settings")

    assert result.code == 0, result.err
    request = fake_es.last("PUT", "/_cluster/settings")
    assert request.body == {"persistent": {"a": 1}}
    assert "json" in request.headers["content-type"]


def test_raw_prints_text_responses_as_is(run_esctl, fake_es):
    fake_es.on("GET", "/_nodes/hot_threads", "::: {node-1}\n   Hot threads", content_type="text/plain")

    result = run_esctl("raw", "/_nodes/hot_threads")

    assert result.code == 0, result.err
    assert result.out == "::: {node-1}\n   Hot threads\n"


def test_migration_deprecations(run_esctl, fake_es):
    fake_es.on(
        "GET",
        "/_migration/deprecations",
        {
            "cluster_settings": [{"level": "critical", "message": "m", "url": "u", "details": "d"}],
            "node_settings": [],
            "index_settings": {},
        },
    )

    result = run_esctl("migration", "deprecations", "-f", "json")

    assert result.code == 0, result.err
    assert result.json() == [{"Kind": "cluster_settings", "Level": "critical", "Message": "m", "Doc": "u"}]
