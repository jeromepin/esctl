def test_harness_runs_a_command_against_the_real_client(run_esctl, fake_es):
    fake_es.on("GET", "/_cluster/health", {"cluster_name": "test", "status": "green"})

    result = run_esctl("cluster", "health", "-f", "json")

    assert result.code == 0, result.err
    assert result.json() == {"cluster_name": "test", "status": "green"}
    request = fake_es.last("GET", "/_cluster/health")
    assert request.headers["authorization"].startswith("Basic ")
