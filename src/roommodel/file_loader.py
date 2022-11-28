import numpy as np
import os

from .agent import Agent
from .follower import FollowerAgent
from .leader import LeaderAgent
from .directed import DirectedAgent
from .partner import DirectedPartnerAgent
from .goal import GateGoal, AreaGoal
from .utils.constants import MAP_SYMBOLS, OBSTACLE, LEADER, FOLLOWER, DIRECTED, PAIR_DIRECTED, EXIT_GOAL_SYMBOL,\
    AREA_GOAL_SYMBOL


class FileLoader:
    def __init__(self, filename):
        if not os.path.isfile(filename):
            raise FileNotFoundError("Map file not found.")
        self.width = 0
        self.height = 0
        self.gate = 0
        self.room = None
        self.goals = []
        with open(filename) as f:
            lines = f.readlines()
            if len(lines) == 0:
                raise ValueError("Map file is empty.")
            lines = [line.rstrip() for line in lines]
            self.width = len(lines[0])
            y = 0
            while y < len(lines) and lines[y][-1] == OBSTACLE:
                y += 1
            self.height = y
            self.room = np.zeros(shape=(self.width, self.height))
            self.pos = {
                LEADER: [],
                FOLLOWER: [],
                DIRECTED: [],
                PAIR_DIRECTED: []
            }
            for _x in range(self.width):
                for _y in range(self.height):
                    point = lines[_y][_x]
                    if point in MAP_SYMBOLS.keys():
                        self.room[_y, _x] = MAP_SYMBOLS[point]
                        continue
                    if point in self.pos.keys():
                        self.pos[point].append((_x, _y))

            for goal_line in lines[y:]:
                tokens = goal_line.split()
                goal_symbol = tokens[0]
                target = tokens[-1]
                lt = (int(tokens[1]), int(tokens[2]))
                rb = lt
                if len(tokens) > 4:
                    rb = (int(tokens[3]), int(tokens[4]))
                if goal_symbol == EXIT_GOAL_SYMBOL:
                    gate_goal = [EXIT_GOAL_SYMBOL, [lt], target]
                    self.gate = lt
                    self.room[lt[1], lt[0]] = 100
                    self.goals.append(gate_goal)
                if goal_symbol == AREA_GOAL_SYMBOL:
                    area_goal = [AREA_GOAL_SYMBOL, [lt, rb], target]
                    self.goals.append(area_goal)
        self.directed_generator = None
        self.leader_generator = None
        self.follower_generator = None
        self.pairs_directed_generator = None
        self.goal_generator = None
        self.sff_generator = None

    def dimensions(self) -> (int, int):
        return self.width, self.height

    def get_room(self):
        return self.room

    def get_gate(self):
        return self.gate

    def get_goals(self, model):
        goals_list = []
        for g in self.goals:
            goal_symbol = g[0]
            if goal_symbol == EXIT_GOAL_SYMBOL:
                lt = g[1]
                target = g[2]
                goals_list.append(GateGoal(model, *lt, target))
            if goal_symbol == AREA_GOAL_SYMBOL:
                lt = g[1][0]
                rb = g[1][1]
                target = g[2]
                goals_list.append(AreaGoal(model, [lt, rb], target))
        return goals_list
