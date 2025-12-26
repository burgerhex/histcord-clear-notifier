import enum

MIN_PLAYER_COL_INDEX = 4
MIN_REQUIRED_ROWS = 2
FIRST_REAL_MAP_ROW_INDEX = 9
FIRST_REAL_MAP_STAR_DIFFICULTY = 8
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
    RENAMED_PLAYER = 6
    ADDED_MAP = 7
    REMOVED_MAP = 8
    RENAMED_MAP = 9


class ClearType(enum.Enum):
    NO_VIDEO = 1
    VIDEO = 2
    NO_VIDEO_FC = 3
    VIDEO_FC = 4
    VIDEO_AND_FC = 5
    GOLDEN = 6
    GOLDEN_FC = 7
    GOLDEN_AND_FC = 8
    ALL_SILVERS = 9
    ALL_SILVERS_AND_FC = 10
    CREATOR = 11
    CREATOR_FC = 12
    OTHER = -1


class NotificationType(enum.Enum):
    PRIMARY = 1
    SECONDARY = 2
