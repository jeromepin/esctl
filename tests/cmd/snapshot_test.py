# from ..base_test_class import EsctlTestCase

# from esctl.cmd.snapshot import SnapshotList


# class TestSnapshotList(EsctlTestCase):
#     def test_value_based_color(self):
#         cases = [
#             {
#                 "input": {"status": "SUCCESS", "failed_shards": "0"},
#                 "expected_output": {"status": "SUCCESS", "failed_shards": "0"},
#             },
#             {
#                 "input": {"status": "PARTIAL", "failed_shards": "0"},
#                 "expected_output": {
#                     "status": "\x1b[93mPARTIAL\x1b[0m",
#                     "failed_shards": "\x1b[91m0\x1b[0m",
#                 },
#             },
#             {
#                 "input": {"status": "IN_PROGRESS", "failed_shards": "0"},
#                 "expected_output": {
#                     "status": "\x1b[96mIN_PROGRESS\x1b[0m",
#                     "failed_shards": "0",
#                 },
#             },
#         ]

#         snapshot_list_cmd = SnapshotList(self.app, [])
#         for case in cases:
#             self.assertEqual(
#                 snapshot_list_cmd.transform([case.get("input")])[0],
#                 case.get("expected_output"),
#             )
