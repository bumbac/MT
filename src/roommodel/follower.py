import mesa
import numpy as np

from .agent import Agent
from .utils.portrayal import create_color


class FollowerAgent(Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.name = "Follower: " + self.name
        self.color = create_color(self)

    def step(self) -> None:
        sff = self.model.sff["Follower"]
        self.select_cell(sff)
