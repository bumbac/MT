import numpy as np
import mesa

from .utils.portrayal import create_color
from .follower import FollowerAgent


class LeaderAgent(FollowerAgent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.name = "Leader: " + self.name
        self.color = create_color(self)

    def step(self):
        sff = self.model.sff["Leader"]
        self.select_cell(sff)

    def move(self, cell):
        self.model.sff_update([cell.pos, cell.pos], "Follower")
        super().move(cell)
