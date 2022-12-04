import mesa
import numpy as np


from .agent import Agent
from .utils.portrayal import rgb_to_hex


class Cell(Agent):
    def __init__(self, uid, model, coords):
        super().__init__(uid, model)
        self.name = "Cell: " + self.name
        self.coords = coords
        self.agent = None
        self.winner = None
        self.q = []

    # prev cell
    def step(self):
        if len(self.q) > 0:
            self.winner = self.q[0]
            # winner can be cancelled
            self.winner.inform()
            self.q = []
            if self.agent and self.winner:
                self.winner.head = self.agent
                self.agent.tail = self.winner

    # next cell
    def advance(self) -> None:
        if self.winner:
            if not self.winner.head:
                self.winner.move(self)
                self.evacuate()
            elif self.winner.head == self.winner.tail and self.winner.head:
                self.evacuate()
                self.winner.head = None
                a = self.winner.tail
                self.winner.tail.tail = None
                self.winner.tail = None
                b = self.winner
                a.cell.advance()
                b.move(self)
                self.evacuate()

    def update_color(self, value):
        color = [0, 255, 0]
        if 0 <= value <= 1:
            color = [0, 255, 255 - int(128*value)]
        self.color = rgb_to_hex(*color)

    def leave(self):
        self.agent = None
        self.model.schedule.remove_cell(self)

    def enter(self, agent):
        self.q.append(agent)
        self.model.schedule.add_cell(self)

    def get_agent(self):
        return self.agent

    def evacuate(self):
        if self != self.model.cell_gate:
            return
        if not self.agent:
            raise ValueError("Empty evacuation.")
        if self.agent.name.startswith("Follower"):
            self.model.n_evacuated_followers += 1
        else:
            self.model.n_evacuated_leaders += 1
        self.model.schedule.remove_agent(self.agent)
        self.agent = None
