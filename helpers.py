# returns trimmed map name and clear type (most likely "[C]" or "[FC]")
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
