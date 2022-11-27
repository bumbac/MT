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
        self.heading = [0, 0]

    def step(self) -> None:
        sff = self.model.sff["Leader"]
        self.select_cell(sff)

    def calculate_orientation(self, cell):
        if self.pos[0] == cell.pos[0]:
            if self.pos[1] > cell.pos[1]:
                return ORIENTATION.SOUTH
            else:
                return ORIENTATION.NORTH
        if self.pos[0] > cell.pos[0]:
            return ORIENTATION.WEST
        else:
            return ORIENTATION.EAST

    def move(self, cell):
        self.orientation = self.calculate_orientation(cell)
        super().move(cell)

    def update_color(self, value):
        self.color = create_color(self)

    def __repr__(self):
        return self.name + " " + str(self.pos) + " " + str(self.orientation)
