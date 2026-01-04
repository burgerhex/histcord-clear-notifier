import itertools
import sys
from collections import defaultdict

import helpers
from constants import DiffType, MAP_PREFIXES_TO_IGNORE, MIN_PLAYER_COL_INDEX, FIRST_REAL_MAP_ROW_INDEX, \
    FIRST_REAL_MAP_STAR_DIFFICULTY


def get_current_state_and_maps_from_sheet_values(all_values):
    if len(all_values) < 1 or len(all_values[0]) < MIN_PLAYER_COL_INDEX:
        print("ERROR: Sheet is too small or doesn't follow the ID/Label structure.")
        sys.exit(1)

    # includes the column label cells, but we utilize this so we don't have to mess with column indices
    player_names = all_values[0]
    map_difficulties = {}
    current_state = {}
    previous_map_empty = False
    map_star_difficulty = FIRST_REAL_MAP_STAR_DIFFICULTY

    # use islice to start at a certain index. more efficient than making a copy of the entire table
    # (i.e. all_values[first_i:]) or skipping every row up to the first one (if row_i < first_i: continue).
    for row in itertools.islice(all_values, FIRST_REAL_MAP_ROW_INDEX, None):
        # skip empty rows (shouldn't happen, but just in case)
        if not row:
            continue

        map_name = row[0]

        # skip weird rows
        if any(map_name.startswith(prefix) for prefix in MAP_PREFIXES_TO_IGNORE):
            continue

        # two empty map names in a row means we've reached a new star difficulty
        if not map_name:
            if previous_map_empty:
                map_star_difficulty -= 1
                previous_map_empty = False
            else:
                previous_map_empty = True
            continue

        map_difficulties[map_name] = map_star_difficulty
        first_player_i = MIN_PLAYER_COL_INDEX
        helpers.parse_data_row(row, first_player_i, current_state, player_names)

    return current_state, map_difficulties


def get_state_diff_list(previous_state, current_state, map_difficulties):
    # player_name -> set { map_name }
    old_player_clears = defaultdict(set)
    new_player_clears = defaultdict(set)
    # map_name -> set { player_name }
    old_map_clearers = defaultdict(set)
    new_map_clearers = defaultdict(set)

    # populate old clear info
    for (player_name, map_name), old_val in previous_state.items():
        old_player_clears[player_name].add(map_name)
        old_map_clearers[map_name].add(player_name)

    # populate new clear info
    for (player_name, map_name), new_val in current_state.items():
        new_player_clears[player_name].add(map_name)
        new_map_clearers[map_name].add(player_name)

    # renaming dicts are new -> old name
    added_players, removed_players, player_renamings = (
        old_and_new_entities_to_added_removed_renamed(old_player_clears, new_player_clears))
    added_maps, removed_maps, map_renamings = (
        old_and_new_entities_to_added_removed_renamed(old_map_clearers, new_map_clearers))

    player_diffs = [(DiffType.ADDED_PLAYER, player) for player in added_players] + \
                   [(DiffType.REMOVED_PLAYER, player) for player in removed_players] + \
                   [(DiffType.RENAMED_PLAYER, old_player, new_player) for new_player, old_player in
                    player_renamings.items()]
    # can't really get star value of a removed map unless we also store that in the state sheet. which we could do,
    # but doesn't really seem necessary right now.
    map_diffs = [(DiffType.ADDED_MAP, map_name, map_difficulties[map_name]) for map_name in added_maps] + \
                [(DiffType.REMOVED_MAP, map_name) for map_name in removed_maps] + \
                [(DiffType.RENAMED_MAP, old_map_name, new_map_name, map_difficulties[new_map_name]) for
                 new_map_name, old_map_name in map_renamings.items()]

    old_renamed_player_names = player_renamings.values()
    old_renamed_map_names = map_renamings.values()

    # this won't have duplicates since any (player, map) combinations will be unioned. the only exception is renamed
    # maps or players, which is skipped in the for loop below (for the old name, then we do check the new name).
    old_and_new_keys = previous_state.keys() | current_state.keys()

    # first, store new clears by player/map key. this will allow us to ignore "clears" of [FC] entries as duplicates
    # of "full clears" of [C] entries. then we can properly format the diff list.
    # (player, trimmed_map_name) -> set { (diff_type, clear_type, *vals) }
    # diff_type will be a DiffType, clear_type will be a str "[C]" or "[FC]" or something else, vals will be other
    # values to pass along
    clear_diffs_by_player_and_map = defaultdict(set)

    for new_key in old_and_new_keys:
        player_name, map_name = new_key

        if player_name in old_renamed_player_names or map_name in old_renamed_map_names:
            # skip renamed entries - we will get these from the new entries
            continue
        elif player_name in removed_players or map_name in removed_maps:
            # skip removed (not renamed) players or maps
            continue

        new_val = current_state.get(new_key, "")
        # before accessing the old state, adjust the key to account for renamings
        old_player_name, old_map_name = new_key
        if player_name in player_renamings:
            old_player_name = player_renamings[player_name]
        if map_name in map_renamings:
            old_map_name = map_renamings[map_name]
        old_key = (old_player_name, old_map_name)
        old_val = previous_state.get(old_key, "")

        map_difficulty = map_difficulties[map_name]
        trimmed_map_name, clear_type = helpers.trim_map_name(map_name)

        if new_val and not old_val:
            clear_diffs_by_player_and_map[(player_name, trimmed_map_name)].add((
                DiffType.ADDED_CLEAR, clear_type, new_val, map_difficulty))
        elif not new_val and old_val:
            clear_diffs_by_player_and_map[(player_name, trimmed_map_name)].add(
                (DiffType.REMOVED_CLEAR, clear_type, old_val, map_difficulty))
        elif new_val != old_val:
            clear_diffs_by_player_and_map[(player_name, trimmed_map_name)].add(
                (DiffType.CHANGED_CLEAR, clear_type, old_val, new_val, map_difficulty))

    clear_diffs = []
    # we only care about if a set has 2 entries, one is FC and one is C, the FC one is DiffType.ADDED_CLEAR,
    # and the C one is CHANGED_CLEAR or ADDED_CLEAR.
    # as of the time of writing, there can only be 3 "clear types": "[C]", "[FC]", and "[All Maps]" (specific to
    # devil's den). these should *probably* never increase, and the devil's den only has one entry, so the most we
    # should see per set is two (c and fc).
    for (player_name, trimmed_map_name), clear_entries in clear_diffs_by_player_and_map.items():
        add_all_entries = True
        clear_types = {clear_entry[1] for clear_entry in clear_entries}
        if len(clear_entries) == 2 and clear_types == {"[C]", "[FC]"}:
            clear_entry1, clear_entry2 = clear_entries
            non_fc_clear_entry, fc_clear_entry = \
                (clear_entry1, clear_entry2) if clear_entry1[1] == "[C]" else (clear_entry2, clear_entry1)
            # if we have 2 entries, one C which is added or changed, and one FC which is added, then we can count
            # this as essentially one new full clear with one diff. we want to get the "fc" cell value from the
            # entry for the non-fc row. this could be CHANGED (which has 3 values) or ADDED (which has 2 value),
            # but either way it's the second to last value.
            if (non_fc_clear_entry[0] in {DiffType.ADDED_CLEAR, DiffType.CHANGED_CLEAR} and
                    fc_clear_entry[0] == DiffType.ADDED_CLEAR):
                add_all_entries = False
                clear_diffs.append(
                    (DiffType.ADDED_CLEAR, player_name, trimmed_map_name, fc_clear_entry[1], *non_fc_clear_entry[-2:]))

        if add_all_entries:
            # otherwise, add a diff for each entry
            for clear_entry in clear_entries:
                clear_diffs.append((clear_entry[0], player_name, trimmed_map_name, *clear_entry[1:]))

    return player_diffs + map_diffs + clear_diffs


def old_and_new_entities_to_added_removed_renamed(old_entities, new_entities):
    removed_or_renamed_entities = old_entities.keys() - new_entities.keys()
    added_or_renamed_entities = new_entities.keys() - old_entities.keys()
    removed_or_renamed_entity_values = {entity_name: old_entities[entity_name] for entity_name in
                                        removed_or_renamed_entities}
    added_or_renamed_entity_values = {entity_name: new_entities[entity_name] for entity_name in
                                      added_or_renamed_entities}

    entity_matchings = maybe_pair_removed_and_added_entities(removed_or_renamed_entity_values,
                                                             added_or_renamed_entity_values)
    new_renamed_entities = set(entity_matchings.keys())
    old_renamed_entities = set(entity_matchings.values())
    removed_entities = removed_or_renamed_entities - old_renamed_entities
    added_entities = added_or_renamed_entities - new_renamed_entities

    # renaming dict is new -> old name
    return added_entities, removed_entities, entity_matchings


# try to pair up removed players or maps with added players or maps to see if they were renamed
# use kuhn's algorithm for a maximum bipartite matching
# returns a dict of new name -> old name
def maybe_pair_removed_and_added_entities(removed_dict, added_dict):
    if not removed_dict or not added_dict:
        return {}

    m = len(removed_dict)
    n = len(added_dict)
    # adjacency list
    graph = defaultdict(set)

    # populate edges: a removed entity can be mapped to an added entity if its set is a subset of the added entity's set
    # IMPORTANT NOTE: this assumes that when a player or map is renamed, no clears are removed from them. if a clear
    # is removed from a renamed player or map, this script will consider it to be a removal of the old name and an
    # addition of the new name. LIST HELPERS AND MODS SHOULD THEREFORE TRY TO AVOID REMOVING CLEARS AT THE SAME TIME AS
    # RENAMING A PLAYER OR MAP. this is an extremely rare scenario, but they should know just in case.
    # another possible rare scenario is that a player was truly removed and another player with the same clears was
    # truly added, but this is also extremely rare. helpers and mods should still be told this.
    for removed_entity, clears in removed_dict.items():
        for added_entity, new_clears in added_dict.items():
            if clears <= new_clears:
                graph[removed_entity].add(added_entity)

    # maps from an added entity to a removed entity
    matching = {}

    # side effect: mutates matching
    # noinspection PyShadowingNames
    def dfs(removed_entity, visited):
        for added_entity in graph[removed_entity]:
            if added_entity not in visited:
                visited.add(added_entity)

                if added_entity not in matching or dfs(matching[added_entity], visited):
                    matching[added_entity] = removed_entity
                    return True
        return False

    for removed_entity in removed_dict:
        dfs(removed_entity, set())

    # maps from new -> old name
    return matching


def save_state_as_grid(current_state):
    player_names = set()
    map_names = set()

    for (player_name, map_name), value in current_state.items():
        player_names.add(player_name)
        map_names.add(map_name)

    player_names = list(sorted(player_names))
    map_names = list(sorted(map_names))

    # add 1 to each index to account for the label row/col
    player_col_indices = {player_name: i + 1 for i, player_name in enumerate(player_names)}
    map_row_indices = {map_name: i + 1 for i, map_name in enumerate(map_names)}

    num_players = len(player_names)

    # top left cell should be empty
    header_row = [""] + player_names
    map_rows = [[map_name] + [""] * num_players for map_name in map_names]
    state_grid = [header_row] + map_rows

    for (player_name, map_name), value in current_state.items():
        col_index = player_col_indices[player_name]
        row_index = map_row_indices[map_name]
        state_grid[row_index][col_index] = value

    return state_grid
