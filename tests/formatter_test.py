from esctl.formatter import TableKey

from .base_test_class import EsctlTestCase


class TestCreateColumnNameFromId(EsctlTestCase):
    def test_name_interpolation(self):
        cases = [
            {"input": "index.uuid", "expected_output": "Index UUID"},
            {"input": "index.id", "expected_output": "Index ID"},
            {"input": "index.gc_deletes", "expected_output": "Index GC Deletes"},
            {"input": "foo.bar", "expected_output": "Foo Bar"},
            {"input": "index.provided_name", "expected_output": "Index Provided Name"},
            {
                "input": "index.soft_deletes.retention_lease.period",
                "expected_output": "Index Soft Deletes Retention Lease Period",
            },
            {"input": "FooBar", "expected_output": "FooBar"},
            {"input": "foo_bar", "expected_output": "Foo Bar"},
            {"input": "foo-bar", "expected_output": "Foo-bar"},
            {"input": "foo.percent", "expected_output": "Foo %"},
            {
                "input": "_source._metadata.createTime",
                "expected_output": "_Source _Metadata CreateTime",
            },
        ]

        for case in cases:
            self.assertEqual(
                TableKey(case.get("input"))._create_name_from_id(),
                case.get("expected_output"),
            )
