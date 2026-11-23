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


EXPLAIN = {
    "index": "logs",
    "can_allocate": "no",
    "allocate_explanation": "cannot allocate",
    "unassigned_info": {"reason": "NODE_LEFT", "last_allocation_status": "no_attempt"},
    "node_allocation_decisions": [
        {"node_name": "node-1", "node_decision": "no", "deciders": [{"explanation": "disk watermark"}]},
        {"node_name": "node-2", "node_decision": "yes"},
    ],
}


def test_allocation_explain(run_esctl, fake_es):
    fake_es.on("POST", "/_cluster/allocation/explain", EXPLAIN)

    result = run_esctl("cluster", "allocation", "explain", "-f", "json")

    assert result.code == 0, result.err
    rows = result.json()
    assert rows["node-1"] == "disk watermark"
    assert rows["node-2"] == "yes"
    assert rows["reason"] == "NODE_LEFT"


def test_allocation_explain_table_has_one_row_per_attribute(run_esctl, fake_es):
    fake_es.on("POST", "/_cluster/allocation/explain", EXPLAIN)

    result = run_esctl("cluster", "allocation", "explain", "-f", "value")

    assert result.code == 0, result.err
    assert result.out.splitlines() == [
        "logs",
        "no",
        "cannot allocate",
        "no_attempt",
        "NODE_LEFT",
        "disk watermark",
        "yes",
    ]


def test_allocation_explain_without_unassigned_shards(run_esctl, fake_es):
    fake_es.on(
        "POST",
        "/_cluster/allocation/explain",
        {"error": {"type": "illegal_argument_exception", "reason": "unable to find any unassigned shards"}},
        status=400,
    )

    result = run_esctl("cluster", "allocation", "explain")

    assert result.code == 0, result.err
    assert "Unable to find any unassigned shards" in result.err


def test_allocation_explain_reports_other_errors(run_esctl, fake_es):
    fake_es.on("POST", "/_cluster/allocation/explain", {"error": "boom"}, status=403)

    result = run_esctl("cluster", "allocation", "explain")

    assert result.code == 1
    assert "AuthorizationException" in result.err or "403" in result.err
