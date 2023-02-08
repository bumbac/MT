import mesa
import numpy as np

from .agent import Agent
from .utils.portrayal import create_color
from .utils.constants import ORIENTATION


class DirectedAgent(Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.name = "Directed " + self.name
        self.orientation = ORIENTATION.NORTH

    def step(self) -> None:
        sff = self.model.sff["Follower"]
        self.select_cell(sff)

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

    def compute_orientation(self, cell):
        next_orientation, shift = self.orientation.twist(self.pos, cell.pos)
        return next_orientation

    def compute_orientation2(self, pos):
        next_orientation, shift = self.orientation.twist(self.pos, pos)
        return next_orientation

    def move(self, cell) -> None:
        self.orientation = self.compute_orientation(cell)
        return super().move(cell)

    def update_color(self, value):
        self.color = create_color(self)

    def __repr__(self):
        return self.name + " " + str(self.pos) + " " + str(self.orientation)
