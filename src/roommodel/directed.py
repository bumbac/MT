import mesa
import numpy as np

from .agent import Agent
from .utils.portrayal import create_color
from .utils.constants import ORIENTATION


class DirectedAgent(Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.orientation = ORIENTATION.NORTH

    def step(self) -> None:
        sff = self.model.sff["Leader"]
        self.select_cell(sff)

    def change_orientation(self, cell):
        if self.pos[0] == cell.pos[0]:
            if self.pos[1] > cell.pos[1]:
                self.orientation = ORIENTATION.SOUTH
            else:
                self.orientation = ORIENTATION.NORTH
            return
        if self.pos[0] > cell.pos[0]:
            self.orientation = ORIENTATION.WEST
        else:
            self.orientation = ORIENTATION.EAST
        return

    def move(self, cell):
        self.change_orientation(cell)
        super().move(cell)

    def update_color(self, value):
        self.color = create_color(self)

    def __repr__(self):
        return self.name + " " + str(self.pos) + " " + str(self.orientation)
