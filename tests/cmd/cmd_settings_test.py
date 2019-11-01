import unittest.mock

import base_test_class
import esctl.cmd.settings
import esctl.settings
import esctl.exceptions
from esctl.utils import Color


class TestSettingsGetCommand(base_test_class.EsctlTestCase):
    def setUp(self):
        self.mock = unittest.mock.patch(
            "esctl.cmd.settings.ClusterSettingsGet.settings.get"
        ).start()

        self.cluster_settings_get_command = esctl.cmd.settings.ClusterSettingsGet(
            self.app, {}
        )

    def test_output(self):
        cases = [
            {
                "input": esctl.settings.Setting("whatever", "foo", "transient"),
                "expected_output": "foo",
            },
            {
                "input": esctl.settings.Setting("whatever", "foo", "defaults"),
                "expected_output": "{} ({})".format(
                    "foo", Color.colorize("default", Color.ITALIC)
                ),
            },
        ]

        for case in cases:
            self.mock.return_value = case.get("input")
            self.assertEqual(
                self.cluster_settings_get_command.retrieve_setting(
                    case.get("input").name, case.get("input").value
                ),
                case.get("expected_output"),
            )

    def test_exception(self):
        self.mock.return_value = esctl.settings.Setting("whatever", None, "defaults")
        self.assertRaises(
            esctl.exceptions.SettingNotFoundError,
            self.cluster_settings_get_command.retrieve_setting,
            "whatever",
            "persistent",
        )
