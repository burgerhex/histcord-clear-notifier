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

    old_players = set()
    new_players = set()
    old_maps = set()
    new_maps = set()

    for key, new_val in previous_state.items():
        old_players.add(key[0])
        old_maps.add(key[1])

    for key, new_val in current_state.items():
        new_players.add(key[0])
        new_maps.add(key[1])

        old_val = previous_state.get(key, "")
        player_name, map_name = key

        if new_val and not old_val:
            clear_diffs.append((DiffType.ADDED_CLEAR, player_name, map_name, (get_clear_type(new_val), new_val)))

        elif not new_val and old_val:
            clear_diffs.append((DiffType.REMOVED_CLEAR, player_name, map_name, (get_clear_type(old_val), old_val)))

        elif new_val != old_val:
            clear_diffs.append((DiffType.CHANGED_CLEAR, player_name, map_name, (get_clear_type(old_val), old_val),
                                (get_clear_type(new_val), new_val)))

    player_map_diffs = []

    for player_name in old_players - new_players:
        # TODO: have better handling here. do something from the following:
        #  - remove any other diffs for this removed player
        #  - have some part of the sheet where verifiers can specify if a player is renamed
        #  - if there are an equal amount of removed and added players,
        #    and they can be paired up sufficiently similarly, "transfer" the clears over?
        player_map_diffs.append((DiffType.REMOVED_PLAYER, player_name))
    for player_name in new_players - old_players:
        player_map_diffs.append((DiffType.ADDED_PLAYER, player_name))

    for map_name in old_maps - new_maps:
        # TODO: have better handling here, similar to above
        player_map_diffs.append((DiffType.REMOVED_MAP, map_name))
    for map_name in new_maps - old_maps:
        player_map_diffs.append((DiffType.ADDED_MAP, map_name))

    return player_map_diffs + clear_diffs


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
