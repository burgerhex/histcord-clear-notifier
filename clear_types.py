from constants import ClearType


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


def cell_value_to_clear_type(cell_value):
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
