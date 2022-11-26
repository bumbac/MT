from enum import IntEnum


class ORIENTATION(IntEnum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    def __repr__(self):
        return self.name


AREA_STATIC_BOOSTER = 5
PAIR_DISTANCE_THRESHOLD = 2.0

MAX_GROUPS = 10
GATE = "G"
OBSTACLE = "#"
GROUP = [str(i) for i in range(MAX_GROUPS)]
EMPTY = " "

MAP_SYMBOLS = {str(i): i for i in range(MAX_GROUPS)}
MAP_SYMBOLS[GATE] = 100
MAP_SYMBOLS[OBSTACLE] = -1
MAP_SYMBOLS[EMPTY] = 0

MAP_VALUES = {v: k for k, v in MAP_SYMBOLS.items()}
