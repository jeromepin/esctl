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


def test_raw_reads_the_body_from_stdin_with_at_dash(run_esctl, fake_es, monkeypatch):
    import io

    fake_es.on("POST", "/logs/_search", {"hits": {}})
    monkeypatch.setattr("sys.stdin", io.StringIO('{"query": {"match_all": {}}}'))

    result = run_esctl("raw", "-X", "POST", "-d", "@-", "/logs/_search")

    assert result.code == 0, result.err
    assert fake_es.last("POST", "/logs/_search").body == {"query": {"match_all": {}}}


def test_raw_reads_the_body_from_a_file(run_esctl, fake_es, tmp_path):
    body = tmp_path / "query.json"
    body.write_text('{"size": 0}')
    fake_es.on("POST", "/logs/_search", {"hits": {}})

    result = run_esctl("raw", "-X", "POST", "-d", f"@{body}", "/logs/_search")

    assert result.code == 0, result.err
    assert fake_es.last("POST", "/logs/_search").body == {"size": 0}
