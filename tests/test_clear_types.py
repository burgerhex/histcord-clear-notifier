import unittest

from parameterized import parameterized

from notifier.clear_types import cell_value_to_clear_type
from notifier.constants import ClearType


# noinspection SpellCheckingInspection
class TestClearTypes(unittest.TestCase):

    @parameterized.expand([
        ("no_video_fc", "nv fc", "[C]", ClearType.NO_VIDEO_FC),
        ("no_video_fc_map", "nv", "[FC]", ClearType.NO_VIDEO_FC),
        ("no_video_fc_repeated_invalid", "nv fc1 nv fc2", "[C]", ClearType.OTHER),
        ("no_video_fc_map_repeated_invalid", "nv1 nv2", "[FC]", ClearType.OTHER),
        ("no_video", "nv", "[C]", ClearType.NO_VIDEO),
        ("no_video_repeated_invalid", "nv1 nv2", "[C]", ClearType.OTHER),
        ("video_fc", "fc", "[C]", ClearType.VIDEO_FC),
        ("video_fc_repeated", "fc1 fc2", "[C]", ClearType.VIDEO_FC),
        ("video_fc_map", "v", "[FC]", ClearType.VIDEO_FC),
        ("video_fc_map_repeated", "v1 v2", "[FC]", ClearType.VIDEO_FC),
        ("video_fc_repeated_bad", "fc1 fc3", "[C]", ClearType.OTHER),
        ("video_fc_map_repeated_bad", "v1 v3", "[FC]", ClearType.OTHER),
        ("video_and_fc", "v fc", "[C]", ClearType.VIDEO_AND_FC),
        ("video_and_fc_repeated_invalid", "v fc1 v fc2", "[C]", ClearType.OTHER),
        ("video", "v", "[C]", ClearType.VIDEO),
        ("video_repeated", "v1 v2", "[C]", ClearType.VIDEO),
        ("video_repeated_bad", "v1 v3", "[C]", ClearType.OTHER),
        ("creator_fc", "creator [fc]", "[C]", ClearType.CREATOR_FC),
        ("creator_fc_map", "creator", "[FC]", ClearType.CREATOR_FC),
        ("creator_fc_map_repeated_invalid", "creator1 creator2", "[FC]", ClearType.OTHER),
        ("creator", "creator", "[C]", ClearType.CREATOR),
        ("creator_repeated_invalid", "creator1 creator2", "[C]", ClearType.OTHER),
        ("fc_golden", "fcg", "[C]", ClearType.GOLDEN_FC),
        ("fc_golden_map", "g", "[FC]", ClearType.GOLDEN_FC),
        ("fc_golden_repeated_invalid", "fcg1 fcg2", "[C]", ClearType.OTHER),
        ("fc_golden_map_repeated_invalid", "g1 g2", "[FC]", ClearType.OTHER),
        ("golden_and_fc", "g & fc", "[C]", ClearType.GOLDEN_AND_FC),
        ("golden_and_fc_repeated_invalid", "g & fc1 g & fc2", "[C]", ClearType.OTHER),
        ("golden", "g", "[C]", ClearType.GOLDEN),
        ("golden_repeated_invalid", "g1 g2", "[C]", ClearType.OTHER),
        ("silvers", "s", "[C]", ClearType.ALL_SILVERS),
        ("silvers_repeated", "s1 s2", "[C]", ClearType.ALL_SILVERS),
        ("silvers_repeated_bad", "s1 s3", "[C]", ClearType.OTHER),
        ("silvers_and_fc", "s & fc", "[C]", ClearType.ALL_SILVERS_AND_FC),
        ("silvers_and_fc_repeated", "s1 s2 & fc", "[C]", ClearType.ALL_SILVERS_AND_FC),
        ("silvers_and_fc_repeated_invalid", "s & fc1 s & fc2", "[C]", ClearType.OTHER),
        ("silvers_and_fc_repeated_bad", "s1 s3 & fc", "[C]", ClearType.OTHER),
    ])
    def test_cell_value_to_clear_type(self, _test_name, cell_value, map_clear_type, exp_type):
        act_type = cell_value_to_clear_type(cell_value, map_clear_type)
        self.assertEqual(act_type, exp_type)
