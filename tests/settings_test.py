import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from elastic_transport import ObjectApiResponse

from esctl.settings import ClusterSettings, IndexSettings, Settings

FIXTURES = Path(__file__).parent / "files"

CLUSTER_SETTINGS = {
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


@pytest.fixture
def es(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr(Settings, "es", client)
    return client


@pytest.mark.parametrize(
    ("key", "persistency", "expected"),
    [
        ("thread_pool.estimated_time_interval", "transient", "100ms"),
        ("thread_pool.estimated_time_interval", "persistent", "200ms"),
        ("cluster.routing.allocation.allow_rebalance", "persistent", "indices_all_active"),
        ("cluster.routing.allocation.allow_rebalance", "transient", "always"),
        # Not set in the requested persistency: falls back to the default value
        ("cluster.routing.allocation.disk.watermark.high", "transient", "90%"),
        ("cluster.routing.allocation.disk.watermark.high", "persistent", "90%"),
        ("cluster.routing.allocation.foobar", "transient", None),
    ],
)
def test_cluster_setting_get(es, key, persistency, expected):
    es.cluster.get_settings.return_value = ObjectApiResponse(body=CLUSTER_SETTINGS, meta=None)

    assert ClusterSettings().get(key, persistency=persistency).value == expected


def test_index_setting_get(es):
    index_settings = json.loads((FIXTURES / "index_settings.json").read_text())
    es.indices.get_settings.return_value = ObjectApiResponse(body=index_settings, meta=None)

    settings = IndexSettings().get("foobar,qux", "index.analysis.analyzer.trigram.tokenizer")

    assert settings["foobar"][0].value == "standard"
