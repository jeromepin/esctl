from .base_test_class import EsctlTestCase

from esctl.formatter import TableKey


class TestCreateColumnNameFromId(EsctlTestCase):
    def test_name_interpolation(self):
        cases = [
            {"input": "foobar", "expected_output": "Foobar"},
            {"input": "foo_bar", "expected_output": "Foo Bar"},
            {"input": "foo.bar", "expected_output": "Foo Bar"},
            {"input": "foo-bar", "expected_output": "Foo-Bar"},
            {"input": "foo.percent", "expected_output": "Foo %"},
        ]

        for case in cases:
            self.assertEqual(
                TableKey(case.get("input"))._create_name_from_id(),
                case.get("expected_output"),
            )
