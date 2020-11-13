import os
from unittest import TestCase

import esctl.main
from esctl.config import Context


class Options:
    pass


class EsctlTestCase(TestCase):
    def setUp(self):
        self.tests_path = os.path.dirname(os.path.realpath(__file__))
        self.fixtures_path = "{}/files".format(self.tests_path)

        self.app = esctl.main.Esctl()

        # Command-line arguments
        self.app.options = Options()
        self.app.options.config_file = "{}/valid_esctlrc.yml".format(self.fixtures_path)
        self.app.options.verbose_level = 3
        self.app.options.context = "localhost"
        self.app.initialize_app([])

        # Dummy context
        self.app.context = Context("foo", "bar", "baz", {})
