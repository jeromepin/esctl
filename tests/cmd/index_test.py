from esctl.cmd.index import IndexReindex

from ..base_test_class import EsctlTestCase


class TestIndexReindex(EsctlTestCase):
    def test_build_request_body(self):
        cases = [
            {
                "input": {
                    "source_index": "foo",
                    "destination_index": "bar",
                    "version_type": "internal",
                    "op_type": "index",
                    "conflicts": "abort",
                },
                "expected_output": {
                    "source": {
                        "index": "foo",
                    },
                    "dest": {
                        "index": "bar",
                        "version_type": "internal",
                        "op_type": "index",
                    },
                    "conflicts": "abort",
                },
            },
        ]

        index_reindex_cmd = IndexReindex(self.app, [])
        for case in cases:
            self.assertEqual(
                index_reindex_cmd._build_request_body(case.get("input")),
                case.get("expected_output"),
            )
