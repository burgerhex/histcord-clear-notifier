import sys

from constants import DiffType, MIN_PLAYER_COL_INDEX, MAP_PREFIXES_TO_IGNORE, ClearType


def get_current_state_from_sheet_values(all_values):
    if len(all_values) < 1 or len(all_values[0]) < MIN_PLAYER_COL_INDEX:
        print("ERROR: Sheet is too small or doesn't follow the ID/Label structure.")
        sys.exit(1)

    player_names = all_values[0]  # player names
    current_state = {}

    for row_i, row in enumerate(all_values):
        # skip player names row or empty rows
        if row_i == 0 or not row:
            continue

        map_name = row[0]

        # skip star label rows
        if not map_name or any(map_name.startswith(prefix) for prefix in MAP_PREFIXES_TO_IGNORE):
            continue

        for player_index, cell_value in enumerate(row):
            if player_index < MIN_PLAYER_COL_INDEX:
                continue

            unique_key = (player_names[player_index], map_name)
            current_state[unique_key] = cell_value.strip()

    return current_state


def get_state_diff_list(previous_state, current_state):
    clear_diffs = []

    old_player_clears = {}
    new_player_clears = {}
    old_map_clearers = {}
    new_map_clearers = {}

    # populate old clear info
    for key, new_val in previous_state.items():
        if key[0] not in old_player_clears:
            old_player_clears[key[0]] = set()
        old_player_clears[key[0]].add(key[1])

        if key[1] not in old_map_clearers:
            old_map_clearers[key[1]] = set()
        old_map_clearers[key[1]] = key[0]

        # we could track old player clears that are not present in the new state, but we don't really need to.
        # the only situations where this happens are if a map or player is deleted (in which case we don't actually
        # want to notify on the "removed" clears) or a map or player is renamed (which is handled below)

    # populate new clear info
    for key, new_val in current_state.items():
        if key[0] not in new_player_clears:
            new_player_clears[key[0]] = set()
        new_player_clears[key[0]].add(key[1])

        if key[1] not in new_map_clearers:
            new_map_clearers[key[1]] = set()
        new_map_clearers[key[1]].add(key[0])

    # renaming dicts are new -> old name
    player_diffs, player_renamings = entity_diff_list(old_player_clears, new_player_clears, DiffType.ADDED_PLAYER, DiffType.REMOVED_PLAYER, DiffType.RENAMED_PLAYER)
    map_diffs, map_renamings = entity_diff_list(old_map_clearers, new_map_clearers, DiffType.ADDED_MAP, DiffType.REMOVED_MAP, DiffType.RENAMED_MAP)
    old_renamed_player_names = player_renamings.values()
    old_renamed_map_names = map_renamings.values()

    old_and_new_keys = previous_state.keys() | current_state.keys()

    for new_key in old_and_new_keys:
        player_name, map_name = new_key

        if player_name in old_renamed_player_names or map_name in old_renamed_map_names:
            # skip renamed entries - we will get these from the new entries
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

        if new_val and not old_val:
            clear_diffs.append((DiffType.ADDED_CLEAR, player_name, map_name, (get_clear_type(new_val), new_val)))

        elif not new_val and old_val:
            clear_diffs.append((DiffType.REMOVED_CLEAR, player_name, map_name, (get_clear_type(old_val), old_val)))

        elif new_val != old_val:
            clear_diffs.append((DiffType.CHANGED_CLEAR, player_name, map_name, (get_clear_type(old_val), old_val),
                                (get_clear_type(new_val), new_val)))

    return player_diffs + map_diffs + clear_diffs


def entity_diff_list(old_entities, new_entities, added_type, removed_type, renamed_type):
    diff_list = []

    added_entities, removed_entities, entity_renamings = old_and_new_entities_to_added_removed_renamed(old_entities, new_entities)

    for entity in added_entities:
        diff_list.append((added_type, entity))
    for entity in removed_entities:
        diff_list.append((removed_type, entity))
    for new_entity, old_entity in entity_renamings.items():
        diff_list.append((renamed_type, old_entity, new_entity))

    # renaming dict is new -> old name
    return diff_list, entity_renamings


def old_and_new_entities_to_added_removed_renamed(old_entities, new_entities):
    removed_or_renamed_entities = old_entities.keys() - new_entities.keys()
    added_or_renamed_entities = new_entities.keys() - old_entities.keys()
    removed_or_renamed_entity_values = {player_name: old_entities[player_name] for player_name in
                                        removed_or_renamed_entities}
    added_or_renamed_entity_values = {player_name: new_entities[player_name] for player_name in
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
# TODO: doesn't seem to pair well. add heuristic?
def maybe_pair_removed_and_added_entities(removed_dict, added_dict):
    if not removed_dict or not added_dict:
        return {}

    m = len(removed_dict)
    n = len(added_dict)
    # adjacency list
    graph = {}

    # populate edges: a removed entity can be mapped to an added entity if its set is a subset of the added entity's set
    # IMPORTANT NOTE: this assumes that when a player or map is renamed, no clears are removed from them. if a clear
    # is removed from a renamed player or map, this script will consider it to be a removal of the old name and an
    # addition of the new name. LIST HELPERS AND MODS SHOULD THEREFORE TRY TO AVOID REMOVING CLEARS AT THE SAME TIME AS
    # RENAMING A PLAYER OR MAP. this is an extremely rare scenario, but they should know just in case.
    # another possible rare scenario is that a player was truly removed and another player with the same clears was
    # truly added, but this is also extremely rare. helpers and mods should still be told this.
    for removed_entity, clears in removed_dict.items():
        if removed_entity not in graph:
            graph[removed_entity] = set()
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


# returns true if cell_value follows "pattern1 pattern2 ..."
# should not be used with patterns that have spaces
def is_repeated_and_numbered(cell_value, pattern):
    parts = cell_value.split(" ")
    if len(parts) < 2:
        return False
    for i, part in enumerate(parts):
        if part != f"{pattern}{i + 1}":
            return False
    return True


def is_clear_type(val, pattern):
    return val == pattern


def is_clear_type_or_repeated(val, pattern):
    return is_clear_type(val, pattern) or is_repeated_and_numbered(val, pattern)


def get_clear_type(cell_value):
    val = cell_value.strip().lower()

    if is_clear_type(val, "nv"):
        return ClearType.NO_VIDEO
    elif is_clear_type_or_repeated(val, "v"):
        return ClearType.VIDEO
    elif is_clear_type(val, "nv fc"):
        return ClearType.NO_VIDEO_FC
    elif is_clear_type_or_repeated(val, "fc"):
        return ClearType.VIDEO_FC
    elif is_clear_type(val, "v fc"):
        return ClearType.VIDEO_AND_FC
    elif is_clear_type(val, "g"):
        return ClearType.GOLDEN
    elif is_clear_type(val, "fcg"):
        return ClearType.GOLDEN_FC
    elif is_clear_type(val, "g & fc"):
        return ClearType.GOLDEN_AND_FC
    elif is_clear_type_or_repeated(val, "s"):
        return ClearType.ALL_SILVERS
    elif val.endswith(" & fc") and is_clear_type_or_repeated(val.removesuffix(" & fc"), "s"):
        return ClearType.ALL_SILVERS_AND_FC
    elif is_clear_type(val, "creator"):
        return ClearType.CREATOR
    elif is_clear_type(val, "creator [fc]"):
        return ClearType.CREATOR_FC

    return ClearType.OTHER
