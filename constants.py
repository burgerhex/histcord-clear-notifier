import enum

MIN_PLAYER_COL_INDEX = 4
MIN_REQUIRED_ROWS = 2
MAP_PREFIXES_TO_IGNORE = [
    "# of Challenges / People / Clears",
    "⭐⭐⭐⭐⭐"
]


class DiffType(enum.Enum):
    ADDED_CLEAR = 1
    REMOVED_CLEAR = 2
    CHANGED_CLEAR = 3
    ADDED_PLAYER = 4
    REMOVED_PLAYER = 5
    ADDED_MAP = 6
    REMOVED_MAP = 7