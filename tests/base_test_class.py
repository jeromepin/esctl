import os
from argparse import Namespace
from unittest import TestCase

import esctl.main


class EsctlTestCase(TestCase):
    def setUp(self):
        self.tests_path = os.path.dirname(os.path.realpath(__file__))
        self.fixtures_path = f"{self.tests_path}/files"

        self.app = esctl.main.Esctl()

        # Command-line arguments
        self.app.options = Namespace()
        self.app.options.config_file = f"{self.fixtures_path}/valid_esctlrc.yml"
        self.app.options.verbose_level = 3
        self.app.options.context = "foobar"
        self.app.initialize_app([])
