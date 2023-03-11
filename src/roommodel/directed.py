import mesa
import numpy as np

from .agent import Agent
from .utils.constants import ORIENTATION, KO, KS


class DirectedAgent(Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.name = "Follower " + self.name
        self.orientation = ORIENTATION.NORTH
        self.next_orientation = ORIENTATION.NORTH
        self.k[KO] = 0
        self.k[KS] = 5
        self.penalization_cross_obstacle = 0.5

    def __repr__(self):
        return self.name + " " + str(self.pos) + " " + str(self.orientation)

    def step(self) -> None:
        self.reset()
        sff = self.model.sff["Follower"]
        self.select_cell(sff)
        if self.next_cell:
            self.next_orientation, shift = self.orientation.twist(self.pos, self.next_cell.pos)

    def move(self):
        self.orientation = self.next_orientation
        return super().move()

    def calculate_orientation(self, cell):
        rotation = False
        diagonal = self.is_diagonal(cell)
        orientation = self.orientation
        if self.pos[0] > cell[0]:
            if self.orientation == ORIENTATION.EAST:
                rotation = True
            orientation = ORIENTATION.WEST
        if self.pos[0] < cell[0]:
            if self.orientation == ORIENTATION.WEST:
                rotation = True
            orientation = ORIENTATION.EAST
        if self.pos[1] > cell[1]:
            if self.orientation == ORIENTATION.NORTH:
                rotation = True
            orientation = ORIENTATION.SOUTH
        if self.pos[1] < cell[1]:
            if self.orientation == ORIENTATION.SOUTH:
                rotation = True
            orientation = ORIENTATION.NORTH

        if diagonal and rotation:
            x = self.pos[0] - cell[0]
            y = self.pos[1] - cell[1]
            return ORIENTATION((self.orientation + (x*y)) % len(ORIENTATION))
        if rotation:
            return ORIENTATION((self.orientation + 2) % len(ORIENTATION))
        if diagonal:
            return self.orientation
        return orientation
