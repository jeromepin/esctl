INFO = {
    "name": "node-1",
    "cluster_name": "test",
    "version": {"number": "8.15.0", "lucene_version": "9.11.1"},
    "tagline": "You Know, for Search",
}


def test_cluster_info_table(run_esctl, fake_es):
    fake_es.on("GET", "/", INFO)

    result = run_esctl("cluster", "info")

    assert result.code == 0, result.err
    assert "version.number" in result.out
    assert "8.15.0" in result.out


def test_cluster_info_json(run_esctl, fake_es):
    fake_es.on("GET", "/", INFO)

    result = run_esctl("cluster", "info", "-f", "json")

    assert result.code == 0, result.err
    assert result.json()["version"] == INFO["version"]
