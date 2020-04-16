import json
import unittest.mock

from .base_test_class import EsctlTestCase


class TestClusterSettingsRetrieval(EsctlTestCase):
    def setUp(self):
        super().setUp()
        self.mock = unittest.mock.patch("esctl.settings.Settings.es").start()
        self.mock.cluster.get_settings.return_value = self.fixtures()

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
        import esctl.settings

        cluster_settings = esctl.settings.ClusterSettings()
        self.assertEqual(
            cluster_settings.get(
                "thread_pool.estimated_time_interval", persistency="transient"
            ).value,
            "100ms",
        )
        self.assertEqual(
            cluster_settings.get(
                "thread_pool.estimated_time_interval", persistency="persistent"
            ).value,
            "200ms",
        )
        self.assertEqual(
            cluster_settings.get(
                "cluster.routing.allocation.allow_rebalance", persistency="persistent"
            ).value,
            "indices_all_active",
        )
        self.assertEqual(
            cluster_settings.get(
                "cluster.routing.allocation.allow_rebalance", persistency="transient"
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
                "cluster.routing.allocation.foobar", persistency="transient"
            ).value,
            None,
        )


class TestIndexSettingsRetrieval(EsctlTestCase):
    def setUp(self):
        super().setUp()
        self.mock = unittest.mock.patch("esctl.settings.Settings.es").start()
        self.mock.indices.get_settings.return_value = self.fixtures()

    def fixtures(self):
        with open("{}/index_settings.json".format(self.fixtures_path)) as json_file:
            return json.load(json_file)

    def test_settings_list(self):
        import esctl.settings

        index_settings = esctl.settings.IndexSettings()

        self.assertEqual(
            index_settings.get(
                "foobar,qux", "index.analysis.analyzer.trigram.tokenizer"
            )
            .get("foobar")[0]
            .value,
            "standard",
        )
