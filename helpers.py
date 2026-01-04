# returns trimmed map name and clear type (most likely "[C]" or "[FC]")
import itertools


def trim_map_name(map_name):
    # get rid of author and weird newlines
    map_name_no_author = map_name.replace("\n", " ").replace("  ", " ").split(" by ")[0]
    clear_type = "[C]"  # default
    trimmed_map_name = map_name_no_author
    if map_name_no_author.endswith("]"):
        i = map_name_no_author.rfind("[")
        clear_type = map_name_no_author[i:]
        trimmed_map_name = map_name_no_author[:i - 1]
    return trimmed_map_name, clear_type


# data_row should not be empty. mutates state
def parse_data_row(data_row, start_index, state, player_names):
    map_name = data_row[0]
    for player_index, value in enumerate(itertools.islice(data_row, start_index, None), start=start_index):
        value = value.strip()
        if player_index < len(player_names) and value:
            unique_key = (player_names[player_index], map_name)
            state[unique_key] = value
