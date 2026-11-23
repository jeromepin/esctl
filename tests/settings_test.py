import json
import unittest.mock
from pathlib import Path

from elastic_transport import ObjectApiResponse

import esctl.settings

from .base_test_class import EsctlTestCase


class TestClusterSettingsRetrieval(EsctlTestCase):
    def setUp(self):
        super().setUp()
        patcher = unittest.mock.patch("esctl.settings.Settings.es")
        self.mock = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock.cluster.get_settings.return_value = ObjectApiResponse(body=self.fixtures(), meta=None)

    def fixtures(self):
        return {
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

    def test_settings_get(self):
        cluster_settings = esctl.settings.ClusterSettings()
        self.assertEqual(
            cluster_settings.get(
                "thread_pool.estimated_time_interval",
                persistency="transient",
            ).value,
            "100ms",
        )
        self.assertEqual(
            cluster_settings.get(
                "thread_pool.estimated_time_interval",
                persistency="persistent",
            ).value,
            "200ms",
        )
        self.assertEqual(
            cluster_settings.get(
                "cluster.routing.allocation.allow_rebalance",
                persistency="persistent",
            ).value,
            "indices_all_active",
        )
        self.assertEqual(
            cluster_settings.get(
                "cluster.routing.allocation.allow_rebalance",
                persistency="transient",
            ).value,
            "always",
        )
        self.assertEqual(
            cluster_settings.get(
                "cluster.routing.allocation.disk.watermark.high",
                persistency="transient",
            ).value,
            "90%",
        )
        self.assertEqual(
            cluster_settings.get(
                "cluster.routing.allocation.disk.watermark.high",
                persistency="persistent",
            ).value,
            "90%",
        )
        self.assertEqual(
            cluster_settings.get(
                "cluster.routing.allocation.foobar",
                persistency="transient",
            ).value,
            None,
        )


class TestIndexSettingsRetrieval(EsctlTestCase):
    def setUp(self):
        super().setUp()
        patcher = unittest.mock.patch("esctl.settings.Settings.es")
        self.mock = patcher.start()
        self.addCleanup(patcher.stop)
        self.mock.indices.get_settings.return_value = ObjectApiResponse(body=self.fixtures(), meta=None)

    def fixtures(self):
        return json.loads(Path(f"{self.fixtures_path}/index_settings.json").read_text())

    def test_settings_list(self):
        index_settings = esctl.settings.IndexSettings()

        self.assertEqual(
            index_settings.get(
                "foobar,qux",
                "index.analysis.analyzer.trigram.tokenizer",
            )["foobar"][0].value,
            "standard",
        )
