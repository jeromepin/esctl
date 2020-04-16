import os
from unittest import TestCase

import esctl.main


class Options:
    pass


class EsctlTestCase(TestCase):
    def setUp(self):
        self.tests_path = os.path.dirname(os.path.realpath(__file__))
        self.fixtures_path = "{}/fixtures".format(self.tests_path)
        self.app = esctl.main.Esctl()
        self.app.options = Options()
        self.app.options.config_file = "{}/fixtures/valid_esctlrc.yml".format(
            self.tests_path
        )
        self.app.options.verbose_level = 3
        self.app.options.context = "localhost"
        self.app.initialize_app([])
