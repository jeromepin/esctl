def test_cat_shards_lists_every_shard_of_an_index_on_a_node(run_esctl, fake_es):
    fake_es.on("GET", "/_cat/nodes", [{"name": "node-1"}, {"name": "node-2"}])
    fake_es.on(
        "GET",
        "/_cat/shards",
        [
            {"index": "logs", "node": "node-1", "shard": "0", "prirep": "p"},
            {"index": "logs", "node": "node-1", "shard": "1", "prirep": "r"},
            {"index": "logs", "node": "node-2", "shard": "0", "prirep": "r"},
            {"index": "logs", "node": None, "shard": "1", "prirep": "p"},
            {"index": "logs", "node": None, "shard": "2", "prirep": "p"},
        ],
    )

    result = run_esctl("cat", "shards", "-f", "json")

    assert result.code == 0, result.err
    assert result.json() == [{"Index": "logs", "node-1": "0p, 1r", "node-2": "0r", "UNASSIGNED": "1p, 2p"}]
