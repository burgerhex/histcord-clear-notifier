import sys

from constants import DiffType, MIN_PLAYER_COL_INDEX, MAP_PREFIXES_TO_IGNORE


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
    diffs = []

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
            diffs.append((DiffType.ADDED_CLEAR, player_name, map_name, new_val))

        elif not new_val and old_val:
            diffs.append((DiffType.REMOVED_CLEAR, player_name, map_name, old_val))

        elif new_val != old_val:
            diffs.append((DiffType.CHANGED_CLEAR, player_name, map_name, old_val, new_val))


    for player_name in old_players - new_players:
        diffs.append((DiffType.REMOVED_PLAYER, player_name))
    for player_name in new_players - old_players:
        diffs.append((DiffType.ADDED_PLAYER, player_name))

    for map_name in old_maps - new_maps:
        diffs.append((DiffType.REMOVED_MAP, map_name))
    for map_name in new_maps - old_maps:
        diffs.append((DiffType.ADDED_MAP, map_name))

    return diffs


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
