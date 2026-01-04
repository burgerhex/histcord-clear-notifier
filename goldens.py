import functools
import itertools

import helpers
import sheets
from constants import MAX_STAR_DIFFICULTY, CLD_COLS_PER_STAR, CLD_MAP_NAME_OFFSET, CLD_INFO_END_OFFSET


def str_to_tier(s):
    tier = 0  # default for untiered/undetermined
    if s.startswith("Tier"):
        space_index = s.rindex(" ")
        tier_str = s[space_index + 1:]
        tier = int(tier_str)
    return tier


def populate_golden_tier(golden_tiers, trimmed_map_name, index, new_tier_str):
    tier_list = golden_tiers[trimmed_map_name]
    if new_tier_str.startswith("Tier") or new_tier_str in ["Undetermined", "Untiered"]:
        if tier_list[index] is None:
            tier_list[index] = new_tier_str
        elif tier_list[index] != new_tier_str:
            old_tier = str_to_tier(tier_list[index])
            new_tier = str_to_tier(new_tier_str)
            # assume the higher tier. we have no way of knowing which golden they did.
            if old_tier < new_tier:
                tier_list[index] = new_tier_str


@functools.cache
def get_golden_tiers():
    cld = sheets.load_cld_from_main_sheet()

    golden_tiers = {}

    # prevent a copy
    cld_rows = itertools.islice(cld, 9, None)

    for cld_row in cld_rows:
        for i in range(MAX_STAR_DIFFICULTY):
            map_name, c_tier, fc_tier = cld_row[CLD_COLS_PER_STAR * i + CLD_MAP_NAME_OFFSET:
                                                CLD_COLS_PER_STAR * i + CLD_INFO_END_OFFSET]
            trimmed_map_name, clear_type = helpers.trim_map_name(map_name)
            if clear_type == "[FC]":
                c_tier, fc_tier = "", c_tier
            elif not fc_tier or fc_tier == "<<<":
                fc_tier = c_tier

            if trimmed_map_name not in golden_tiers:
                golden_tiers[trimmed_map_name] = [None, None]

            populate_golden_tier(golden_tiers, trimmed_map_name, 0, c_tier)
            populate_golden_tier(golden_tiers, trimmed_map_name, 1, fc_tier)

    return golden_tiers
