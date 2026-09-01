import unittest

from notifier.helpers import trim_map_name, parse_data_row
from parameterized import parameterized


# noinspection SpellCheckingInspection
class TestHelpers(unittest.TestCase):

    @parameterized.expand([
        ("no_type", "Adagio Sostenuto by Schnippi", "Adagio Sostenuto", "[C]"),
        ("b_side", "Avian Ascension (B-Side) by Parrot Dash", "Avian Ascension (B-Side)", "[C]"),
        ("c_type", "Nowhere to Stand [C] by antondep", "Nowhere to Stand", "[C]"),
        ("fc_type", "Geodesic [FC] by smoothee", "Geodesic", "[FC]"),
        ("newline", "Dragonfruit Decline [FC]\nby #mapping-grandmaster", "Dragonfruit Decline", "[FC]"),
        ("newline_spaces", "Dragonfruit Decline [FC] \n by #mapping-grandmaster", "Dragonfruit Decline", "[FC]"),
        ("collab_fc", "[IC] Thulecite Ruins [FC] by SummitBadeline", "[IC] Thulecite Ruins", "[FC]"),
    ])
    def test_trim_map_name(self, _test_name, map_name, exp_name, exp_type):
        act_name, act_type = trim_map_name(map_name)
        self.assertEqual(act_name, exp_name)
        self.assertEqual(act_type, exp_type)

    @parameterized.expand([
        (
                "no_clears",
                ["", "hyper", "dan", "olivia"],
                ["MENACE by Viridity", "", "", ""],
                1,
                {}
        ),
        (
                "different_clears",
                ["", "hyper", "dan", "olivia"],
                ["MENACE by Viridity", "fc", "v", "g"],
                1,
                {("hyper", "MENACE by Viridity"): "fc", ("dan", "MENACE by Viridity"): "v",
                 ("olivia", "MENACE by Viridity"): "g"}
        ),
        (
                "later_player_index",
                ["", "hyper", "dan", "olivia"],
                ["MENACE by Viridity", "fc", "v", "g"],
                2,
                {("dan", "MENACE by Viridity"): "v", ("olivia", "MENACE by Viridity"): "g"}
        ),
        (
                "out_of_bounds_player_index_ignored",
                ["", "hyper", "dan", "olivia"],
                ["MENACE by Viridity", "fc", "v", "g", "s"],
                1,
                {("hyper", "MENACE by Viridity"): "fc", ("dan", "MENACE by Viridity"): "v",
                 ("olivia", "MENACE by Viridity"): "g"}
        ),
    ])
    def test_parse_data_row(self, _test_name, player_names, data_row, start_index, expected_state):
        state = {}
        parse_data_row(data_row, start_index, state, player_names)
        self.assertEqual(state, expected_state)
