import unittest
from unittest.mock import MagicMock, patch

from notifier.clears import get_current_state_and_maps_from_sheet_values, get_state_diff_list, save_state_as_grid
from parameterized import parameterized

from notifier.constants import DiffType


class TestClears(unittest.TestCase):

    @parameterized.expand([
        ("too_few_rows", []),
        ("too_few_cols", [
            ["", "p1"],
            ["map", "clears"]
        ])
    ])
    @patch('notifier.clears.sys.exit')
    def test_get_current_state_and_maps_from_sheet_values_exits(self, _test_name, all_values, mock_exit):
        mock_exit.side_effect = SystemExit

        with self.assertRaises(SystemExit):
            get_current_state_and_maps_from_sheet_values(all_values)

        mock_exit.assert_called_once_with(1)

    @parameterized.expand([
        (
                "normal",
                [1, 1, 1],
                [
                    ["", "p1", "p2", "p3"],
                    ["m1", "", "v", "fc"],
                    ["m2", "fcg", "", "s"]
                ],
                {("p1", "m2"): "fcg", ("p2", "m1"): "v", ("p3", "m1"): "fc", ("p3", "m2"): "s"},
                {"m1": 1, "m2": 1},
        ),
        (
                "starts_at_first_map_row_index",
                [1, 2, 1],
                [
                    ["", "p1", "p2", "p3"],
                    ["m1", "", "v", "fc"],
                    ["m2", "fcg", "", "s"]
                ],
                {("p1", "m2"): "fcg", ("p3", "m2"): "s"},
                {"m2": 1},
        ),
        (
                "starts_at_first_player_col_index",
                [2, 1, 1],
                [
                    ["", "p1", "p2", "p3"],
                    ["m1", "", "v", "fc"],
                    ["m2", "fcg", "", "s"]
                ],
                {("p2", "m1"): "v", ("p3", "m1"): "fc", ("p3", "m2"): "s"},
                {"m1": 1, "m2": 1},
        ),
        (
                "skips_skip_prefixes",
                [1, 1, 1],
                [
                    ["", "p1", "p2", "p3"],
                    ["skip", "", "v", "fc"],
                    ["m2", "fcg", "", "s"]
                ],
                {("p1", "m2"): "fcg", ("p3", "m2"): "s"},
                {"m2": 1},
        ),
        (
                "skips_empty_rows",
                [1, 1, 1],
                [
                    ["", "p1", "p2", "p3"],
                    ["m1", "", "v", "fc"],
                    [],
                    ["m2", "fcg", "", "s"]
                ],
                {("p1", "m2"): "fcg", ("p2", "m1"): "v", ("p3", "m1"): "fc", ("p3", "m2"): "s"},
                {"m1": 1, "m2": 1},
        ),
        (
                "decreases_map_difficulty",
                [1, 1, 3],
                [
                    ["", "p1", "p2", "p3"],
                    ["m1", "v", "", ""],
                    ["", "v", "", ""],
                    ["", "fc", "", ""],
                    ["m2", "", "v", ""],
                    ["", "", "s", ""],
                    ["", "", "g", ""],
                    ["m3", "", "", "v"],
                ],
                {("p1", "m1"): "v", ("p2", "m2"): "v", ("p3", "m3"): "v"},
                {"m1": 3, "m2": 2, "m3": 1},
        ),
    ])
    @patch('notifier.clears.constants')
    def test_get_current_state_and_maps_from_sheet_values(self, _test_name, consts, all_values, exp_state, exp_diffs,
                                                          mock_constants):
        mock_constants.MIN_PLAYER_COL_INDEX = consts[0]
        mock_constants.FIRST_REAL_MAP_ROW_INDEX = consts[1]
        mock_constants.FIRST_REAL_MAP_STAR_DIFFICULTY = consts[2]
        mock_constants.MAP_PREFIXES_TO_IGNORE = ["skip"]

        state, map_diffs = get_current_state_and_maps_from_sheet_values(all_values)

        self.assertEqual(state, exp_state)
        self.assertEqual(map_diffs, exp_diffs)

    @parameterized.expand([
        (
            "added_clear",
            {("p1", "m1"): "v", ("p2", "m2"): "v"},
            {("p1", "m1"): "v", ("p2", "m2"): "v", ("p1", "m2"): "v"},
            [(DiffType.ADDED_CLEAR, "p1", "m2", "[C]", "v", 2)],
        ),
        (
            "removed_clear",
            {("p1", "m1"): "v", ("p2", "m2"): "v", ("p1", "m2"): "v"},
            {("p1", "m1"): "v", ("p2", "m2"): "v"},
            [(DiffType.REMOVED_CLEAR, "p1", "m2", "[C]", "v", 2)],
        ),
        (
            "changed_clear",
            {("p1", "m1"): "v", ("p2", "m2"): "v"},
            {("p1", "m1"): "v", ("p2", "m2"): "fc"},
            [(DiffType.CHANGED_CLEAR, "p2", "m2", "[C]", "v", "fc", 2)],
        ),
        (
            "added_c_and_fc_clear",
            {("p1", "m4 [C]"): "v", ("p2", "m4 [C]"): "fc", ("p2", "m4 [FC]"): "v", ("p3", "m1"): "v"},
            {("p1", "m4 [C]"): "v", ("p2", "m4 [C]"): "fc", ("p2", "m4 [FC]"): "v", ("p3", "m1"): "v",
             ("p3", "m4 [C]"): "fc", ("p3", "m4 [FC]"): "v"},
            [(DiffType.ADDED_CLEAR, "p3", "m4", "[FC]", "fc", 5)],
        ),
        (
            "added_fc_clear",
            {("p1", "m4 [C]"): "v", ("p2", "m4 [C]"): "fc", ("p2", "m4 [FC]"): "v"},
            {("p1", "m4 [C]"): "fc", ("p1", "m4 [FC]"): "v", ("p2", "m4 [C]"): "fc", ("p2", "m4 [FC]"): "v"},
            [(DiffType.ADDED_CLEAR, "p1", "m4", "[FC]", "fc", 5)],
        ),
        (
            "added_map",
            {("p1", "m1"): "v", ("p2", "m2"): "v"},
            {("p1", "m1"): "v", ("p2", "m2"): "v", ("p1", "m3"): "v"},
            [(DiffType.ADDED_MAP, "m3", 3), (DiffType.ADDED_CLEAR, "p1", "m3", "[C]", "v", 3)],
        ),
        (
            "removed_map",
            {("p1", "m1"): "v", ("p2", "m2"): "v", ("p1", "m3"): "v"},
            {("p1", "m1"): "v", ("p2", "m2"): "v"},
            [(DiffType.REMOVED_MAP, "m3")],
        ),
        (
            "renamed_map",
            {("p1", "m1"): "v", ("p2", "m3"): "v", ("p1", "m3"): "v"},
            {("p1", "m1"): "v", ("p2", "m3new"): "v", ("p1", "m3new"): "v"},
            [(DiffType.RENAMED_MAP, "m3", "m3new", 3)],
        ),
        (
            "added_player",
            {("p1", "m1"): "v", ("p2", "m2"): "v"},
            {("p1", "m1"): "v", ("p2", "m2"): "v", ("p3", "m2"): "v"},
            [(DiffType.ADDED_PLAYER, "p3"), (DiffType.ADDED_CLEAR, "p3", "m2", "[C]", "v", 2)],
        ),
        (
            "removed_player",
            {("p1", "m1"): "v", ("p2", "m2"): "v", ("p3", "m2"): "v"},
            {("p1", "m1"): "v", ("p2", "m2"): "v"},
            [(DiffType.REMOVED_PLAYER, "p3")],
        ),
        (
            "renamed_player",
            {("p1", "m1"): "v", ("p2", "m2"): "v", ("p1", "m2"): "v"},
            {("p1new", "m1"): "v", ("p2", "m2"): "v", ("p1new", "m2"): "v"},
            [(DiffType.RENAMED_PLAYER, "p1", "p1new")],
        ),
        (
            "removed_and_added_player",
            {("p1", "m1"): "v", ("p2", "m2"): "v", ("p3", "m2"): "v"},
            {("p1", "m1"): "v", ("p2", "m2"): "v", ("p4", "m1"): "v"},
            [(DiffType.ADDED_PLAYER, "p4"), (DiffType.REMOVED_PLAYER, "p3"),
             (DiffType.ADDED_CLEAR, "p4", "m1", "[C]", "v", 1)],
        ),
        (
            "removed_and_added_map",
            {("p1", "m1"): "v", ("p2", "m2"): "v", ("p1", "m3"): "v", ("p2", "m3"): "v"},
            {("p1", "m1"): "v", ("p2", "m2"): "v", ("p1", "m4"): "v"},
            [(DiffType.ADDED_MAP, "m4", 4), (DiffType.REMOVED_MAP, "m3"),
             (DiffType.ADDED_CLEAR, "p1", "m4", "[C]", "v", 4)],
        ),
        (
            "added_player_and_map",
            {("p1", "m1"): "v", ("p2", "m2"): "v"},
            {("p1", "m1"): "v", ("p2", "m2"): "v", ("p3", "m3"): "v"},
            [(DiffType.ADDED_PLAYER, "p3"), (DiffType.ADDED_MAP, "m3", 3),
             (DiffType.ADDED_CLEAR, "p3", "m3", "[C]", "v", 3)],
        ),
        (
            "renamed_player_and_map",
            {("p1", "m3"): "v", ("p2", "m3"): "v", ("p1", "m2"): "v"},
            {("p1new", "m3new"): "v", ("p2", "m3new"): "v", ("p1new", "m2"): "v"},
            [(DiffType.RENAMED_PLAYER, "p1", "p1new"), (DiffType.RENAMED_MAP, "m3", "m3new", 3)],
        ),
    ])
    def test_get_state_diff_list(self, _test_name, prev_state, curr_state, exp_diffs):
        map_diffs = {"m1": 1, "m2": 2, "m3": 3, "m3new": 3, "m4": 4, "m4 [C]": 4, "m4 [FC]": 5}

        diff_list = get_state_diff_list(prev_state, curr_state, map_diffs)

        self.assertEqual(diff_list, exp_diffs)

    @parameterized.expand([
        (
            "normal",
            {("p1", "m1"): "v", ("p2", "m1"): "fc", ("p2", "m2"): "s", ("p3", "m3"): "g"},
            [
                ["", "p1", "p2", "p3"],
                ["m1", "v", "fc", ""],
                ["m2", "", "s", ""],
                ["m3", "", "", "g"],
            ]
        ),
    ])
    def test_save_state_as_grid(self, _test_name, curr_state, exp_grid):
        grid = save_state_as_grid(curr_state)

        self.assertEqual(grid, exp_grid)
