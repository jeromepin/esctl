import unittest.mock

import base_test_class

import esctl.settings


class TestSettingsRetrieval(base_test_class.EsctlTestCase):
    def setUp(self):
        self.mock = unittest.mock.patch("esctl.settings.Esctl").start()
        self.mock._es.cluster.get_settings.return_value = self.fixtures()

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
