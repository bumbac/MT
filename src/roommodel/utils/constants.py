from enum import IntEnum


class ORIENTATION(IntEnum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    def __repr__(self):
        return self.name

    def heading(self, pos):
        if self == ORIENTATION.NORTH:
            return [0, 1]
        if self == ORIENTATION.EAST:
            return [1, 0]
        if self == ORIENTATION.SOUTH:
            return [0, -1]
        if self == ORIENTATION.WEST:
            return [-1, 0]


AREA_STATIC_BOOSTER = 1.1
PAIR_DISTANCE_THRESHOLD = 2.0

MAX_GROUPS = 10
GATE = "G"
OBSTACLE = "#"
GROUP = [str(i) for i in range(MAX_GROUPS)]
EMPTY = " "
LEADER = "L"
FOLLOWER = "F"
DIRECTED = "D"
PAIR_DIRECTED = "P"

EXIT_GOAL_SYMBOL = "E"
AREA_GOAL_SYMBOL = "A"

MAP_SYMBOLS = {str(i): i for i in range(MAX_GROUPS)}
MAP_SYMBOLS[GATE] = 100
MAP_SYMBOLS[OBSTACLE] = -1
MAP_SYMBOLS[EMPTY] = 0

MAP_VALUES = {v: k for k, v in MAP_SYMBOLS.items()}
