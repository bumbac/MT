from enum import IntEnum
import numpy as np


class ORIENTATION(IntEnum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    def __repr__(self):
        return self.name

    def heading(self):
        if self == ORIENTATION.NORTH:
            return [0, 1]
        if self == ORIENTATION.EAST:
            return [1, 0]
        if self == ORIENTATION.SOUTH:
            return [0, -1]
        if self == ORIENTATION.WEST:
            return [-1, 0]

    def twist(self, start, goal):
        # use start as origin (0, 0) for goal
        goal = [goal[0] - start[0], goal[1] - start[1]]
        # select normal heading vector
        start = self.heading()
        dot = start[0] * goal[0] + start[1] * goal[1]
        det = start[0] * goal[1] - start[1] * goal[0]
        # rad is in [-pi, pi]
        rad = np.arctan2(det, dot)
        # straight move and diagonal stride to left or right
        if -np.pi / 4 <= rad <= np.pi / 4:
            return self, 0
        # turn right
        if -3 * np.pi / 4 < rad < - np.pi / 4:
            return self.shift(1), 1
        # turn around
        if rad >= 3 * np.pi / 4 or -3 * np.pi / 4 >= rad:
            return self.shift(2), 2
        # turn left
        # if 3 * np.pi / 4 > rad > np.pi / 4:
        return self.shift(3), 3

    def shift(self, shift):
        return ORIENTATION((self + shift) % len(ORIENTATION))


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

EMPTY_CELL = 0
OCCUPIED_CELL = 1

SFF_MAX_FREE = 1
SFF_MIN_FREE = 0
SFF_OBSTACLE = float("inf")

KS = 0
KO = 1
KD = 2
GAMMA = 3


def possible_moves():
    X = np.array([-1, 0, 1])
    Y = np.array([-1, 0, 1])
    positions = {}
    offset = [(x, y) for x in X for y in Y]
    origin = (0, 0)
    for orientation in ORIENTATION:
        positions[orientation] = []

    # moore neighbourhood
    for orientation in ORIENTATION:
        for cell in offset:
            next_orientation, shift = orientation.twist(origin, cell)
            positions[orientation].append((cell, next_orientation))

    # turning maneuver
    for orientation in ORIENTATION:
        if orientation == ORIENTATION.NORTH or orientation == ORIENTATION.SOUTH:
            cell, next_orientation = (2, 1), ORIENTATION.EAST
            positions[orientation].append((cell, next_orientation))
            cell, next_orientation = (2, -1), ORIENTATION.EAST
            positions[orientation].append((cell, next_orientation))
            cell, next_orientation = (-2, 1), ORIENTATION.WEST
            positions[orientation].append((cell, next_orientation))
            cell, next_orientation = (-2, -1), ORIENTATION.WEST
            positions[orientation].append((cell, next_orientation))
        if orientation == ORIENTATION.EAST or orientation == ORIENTATION.WEST:
            cell, next_orientation = (1, 2), ORIENTATION.NORTH
            positions[orientation].append((cell, next_orientation))
            cell, next_orientation = (-1, 2), ORIENTATION.NORTH
            positions[orientation].append((cell, next_orientation))
            cell, next_orientation = (1, -2), ORIENTATION.SOUTH
            positions[orientation].append((cell, next_orientation))
            cell, next_orientation = (-1, -2), ORIENTATION.SOUTH
            positions[orientation].append((cell, next_orientation))

    # rotation in place
    for orientation in ORIENTATION:
        for next_orientation in ORIENTATION:
            cell, next_orientation = origin, next_orientation
            positions[orientation].append((cell, next_orientation))
        # remove duplicate (0, 0), orientation
        del positions[orientation][positions[orientation].index((origin, orientation))]

    # partner rotates, this agent follows suite
    for orientation in ORIENTATION:
        if orientation == ORIENTATION.NORTH or orientation == ORIENTATION.SOUTH:
            cell, next_orientation = (1, 1), ORIENTATION.EAST
            positions[orientation].append((cell, next_orientation))
            cell, next_orientation = (1, -1), ORIENTATION.EAST
            positions[orientation].append((cell, next_orientation))
            cell, next_orientation = (-1, 1), ORIENTATION.WEST
            positions[orientation].append((cell, next_orientation))
            cell, next_orientation = (-1, -1), ORIENTATION.WEST
            positions[orientation].append((cell, next_orientation))
        if orientation == ORIENTATION.WEST or orientation == ORIENTATION.EAST:
            cell, next_orientation = (1, 1), ORIENTATION.NORTH
            positions[orientation].append((cell, next_orientation))
            cell, next_orientation = (-1, 1), ORIENTATION.NORTH
            positions[orientation].append((cell, next_orientation))
            cell, next_orientation = (1, -1), ORIENTATION.SOUTH
            positions[orientation].append((cell, next_orientation))
            cell, next_orientation = (-1, -1), ORIENTATION.SOUTH
            positions[orientation].append((cell, next_orientation))
    return positions


def expand_moves():
    partner = possible_moves()
    partner_offset = [
        # NORTH
        (1, 0),
        # EAST
        (0, -1),
        # SOUTH
        (-1, 0),
        # WEST
        (0, 1)]
    for orientation in ORIENTATION:
        offset_positions = []
        for partner_move in partner[orientation]:
            partner_position, next_orientation = partner_move
            offset_position = partner_position[0] + partner_offset[orientation][0], \
                              partner_position[1] + partner_offset[orientation][1]
            offset_positions.append((offset_position, next_orientation))
        partner[orientation] = offset_positions
    return partner


def valid_position(combination):
    LEADER = 0
    PARTNER = 1
    POSITION = 0
    ORIENTATION_VALUE = 1
    leader, partner = combination
    if leader[ORIENTATION_VALUE] == ORIENTATION.NORTH or leader[ORIENTATION_VALUE] == ORIENTATION.SOUTH:
        side1 = leader[POSITION][0] - 1, leader[POSITION][1]
        side2 = leader[POSITION][0] + 1, leader[POSITION][1]
        if partner[POSITION] == side1 or partner[POSITION] == side2:
            return True
    if leader[ORIENTATION_VALUE] == ORIENTATION.EAST or leader[ORIENTATION_VALUE] == ORIENTATION.WEST:
        side1 = leader[POSITION][0], leader[POSITION][1] - 1
        side2 = leader[POSITION][0], leader[POSITION][1] + 1
        if partner[POSITION] == side1 or partner[POSITION] == side2:
            return True
    return False


def connected(combination):
    leader, partner = combination[0][0], combination[1][0]
    norm = manhattan(leader, partner)
    return norm == 1


def manhattan(start, end):
    return np.abs(start[0] - end[0]) + np.abs(start[1] - end[1])


def movement_cost(combination, orientation):
    leader_origin = (0, 0)
    partner_origin = ORIENTATION((orientation + 1) % len(ORIENTATION)).heading()
    leader_cost = manhattan(leader_origin, combination[0][0])
    partner_cost = manhattan(partner_origin, combination[1][0])
    return leader_cost + partner_cost, leader_cost, partner_cost


def combine(orientation):
    LEADER = 0
    PARTNER = 1
    POSITION = 0
    ORIENTATION_VALUE = 1
    leader_positions = possible_moves()[orientation]
    partner_positions = expand_moves()[orientation]
    leader_partner = [(l, p) for l in leader_positions for p in partner_positions]

    # leader and partner in the same position
    leader_partner = list(filter(lambda lp: lp[LEADER][POSITION] != lp[PARTNER][POSITION], leader_partner))

    # leader and partner are separated
    leader_partner = list(filter(connected, leader_partner))

    # leader and partner are aligned side by side
    leader_partner = list(filter(valid_position, leader_partner))

    # leader and partner have same direction
    different_dir = list(
        filter(lambda lp: lp[LEADER][ORIENTATION_VALUE] != lp[PARTNER][ORIENTATION_VALUE], leader_partner))

    # leader and partner don't have same direction
    leader_partner = list(
        filter(lambda lp: lp[LEADER][ORIENTATION_VALUE] == lp[PARTNER][ORIENTATION_VALUE], leader_partner))

    # leader and partner are aligned side by side
    leader_partner = list(filter(valid_position, leader_partner))
    for combination in leader_partner:
        together, lc, pc = movement_cost(combination, orientation)
        # if lc == 3 or pc == 3:
        #     print(combination, together, lc, pc)
    return leader_partner


def maneuvers():
    maneuvers = {}
    for orientation in ORIENTATION:
        maneuvers[orientation] = combine(orientation)
    return maneuvers


MANEUVERS = maneuvers()
