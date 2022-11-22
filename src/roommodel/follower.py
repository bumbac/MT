import mesa
import numpy as np

from .agent import Agent
from .utils.portrayal import create_color


class FollowerAgent(Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.name = "Follower: " + self.name
        self.color = create_color(self)
        self.head = None
        self.tail = None
        self.cell = None

    def step(self):
        sff = self.model.sff["Follower"]
        self.select_cell(sff)

    def move(self, cell):
        self.model.grid.move_agent(self, cell.pos)
        # prev cell
        self.cell.leave()
        # current cell
        self.cell = cell
        if self.tail:
            self.tail.head = None
            self.tail.cell.advance()
            self.tail = None
