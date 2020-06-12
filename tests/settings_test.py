import json
import unittest.mock

from ward import test, fixture, Scope
from fixtures import FIXTURES_PATH, dummy_esctl_with_dummy_context


@fixture
def fake_cluster_settings(scope=Scope.Global):
    mock = unittest.mock.patch("esctl.settings.Settings.es").start()
    mock.cluster.get_settings.return_value = {
        "persistent": {
            "thread_pool.estimated_time_interval": "200ms",
            "cluster.routing.allocation.allow_rebalance": "indices_all_active",
        },
        "transient": {
            "thread_pool.estimated_time_interval": "100ms",
            "cluster.routing.allocation.allow_rebalance": "always",
        },
        "defaults": {"cluster.routing.allocation.disk.watermark.high": "90%"},
    }

    import esctl.settings

    return esctl.settings.ClusterSettings()


@test(
    "[Cluster Settings] Get transient thread_pool.estimated_time_interval",
    tags=["settings", "cluster"],
)
def _(esctl=dummy_esctl_with_dummy_context, cluster_settings=fake_cluster_settings):
    assert (
        cluster_settings.get(
            "thread_pool.estimated_time_interval", persistency="transient"
        ).value
        == "100ms"
    )


@test(
    "[Cluster Settings] Get persistent thread_pool.estimated_time_interval",
    tags=["settings", "cluster"],
)
def _(esctl=dummy_esctl_with_dummy_context, cluster_settings=fake_cluster_settings):
    assert (
        cluster_settings.get(
            "thread_pool.estimated_time_interval", persistency="persistent"
        ).value
        == "200ms"
    )


@test(
    "[Cluster Settings] Get transient cluster.routing.allocation.allow_rebalance",
    tags=["settings", "cluster"],
)
def _(esctl=dummy_esctl_with_dummy_context, cluster_settings=fake_cluster_settings):
    assert (
        cluster_settings.get(
            "cluster.routing.allocation.allow_rebalance", persistency="transient"
        ).value
        == "always"
    )


@test(
    "[Cluster Settings] Get persistent cluster.routing.allocation.allow_rebalance",
    tags=["settings", "cluster"],
)
def _(esctl=dummy_esctl_with_dummy_context, cluster_settings=fake_cluster_settings):
    assert (
        cluster_settings.get(
            "cluster.routing.allocation.allow_rebalance", persistency="persistent"
        ).value
        == "indices_all_active"
    )


@test(
    "[Cluster Settings] Get transient thread_pool.estimated_time_interval",
    tags=["settings", "cluster"],
)
def _(esctl=dummy_esctl_with_dummy_context, cluster_settings=fake_cluster_settings):
    assert (
        cluster_settings.get(
            "thread_pool.estimated_time_interval", persistency="transient"
        ).value
        == "100ms"
    )


@test(
    "[Cluster Settings] Get transient cluster.routing.allocation.disk.watermark.high",
    tags=["settings", "cluster"],
)
def _(esctl=dummy_esctl_with_dummy_context, cluster_settings=fake_cluster_settings):
    assert (
        cluster_settings.get(
            "cluster.routing.allocation.disk.watermark.high", persistency="transient"
        ).value
        == "90%"
    )


@test(
    "[Cluster Settings] Get transient cluster.routing.allocation.foobar",
    tags=["settings", "cluster"],
)
def _(esctl=dummy_esctl_with_dummy_context, cluster_settings=fake_cluster_settings):
    assert (
        cluster_settings.get(
            "cluster.routing.allocation.foobar", persistency="transient"
        ).value
        == None
    )


@fixture
def fake_index_settings(scope=Scope.Global):
    mock = unittest.mock.patch("esctl.settings.Settings.es").start()
    with open("{}/index_settings.json".format(FIXTURES_PATH)) as json_file:
        mock.indices.get_settings.return_value = json.load(json_file)

    import esctl.settings

    return esctl.settings.IndexSettings()


@test(
    "[Index Settings] Get index.analysis.analyzer.trigram.tokenizer",
    tags=["index", "cluster"],
)
def _(esctl=dummy_esctl_with_dummy_context, index_settings=fake_index_settings):
    assert (
        index_settings.get("foobar,qux", "index.analysis.analyzer.trigram.tokenizer")
        .get("foobar")[0]
        .value
        == "standard"
    )
