from .base_test_class import EsctlTestCase

from esctl.config import Context
from esctl.main import Esctl


class TestFindScheme(EsctlTestCase):
    def setUp(self):
        self.esctl = Esctl()
        self.esctl.context = Context("foo", "bar", "baz", {})

    def test_scheme_discovery(self):
        cases = [
            {"input": ["https://foo.example.com:8200"], "expected_output": "https"},
            {"input": ["http://foo.example.com:8200"], "expected_output": "http"},
            {
                "input": [
                    "https://foo.example.com:8200"
                    "http://bar.example.com:8200"
                    "http://baz.example.com:8200"
                ],
                "expected_output": "https",
            },
            {"input": ["foo://foo.example.com:8200"], "expected_output": "https"},
            {"input": ["foo.example.com:8200"], "expected_output": "https"},
        ]

        for case in cases:
            self.esctl.context.cluster = {"servers": case.get("input")}
            self.assertEqual(self.esctl.find_scheme(), case.get("expected_output"))
