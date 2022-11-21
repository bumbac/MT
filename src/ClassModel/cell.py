import mesa
import numpy as np

from .utils.portrayal import rgb_to_hex, create_color


class Cell(mesa.Agent):
    def __init__(self, uid, model, coords):
        super().__init__(uid, model)
        self.name = "Cell:(" + str(coords[0]) + ", " + str(coords[1]) + ") " + str(uid)
        self.model = model
        self.coords = coords
        self.color = create_color(self)
        self.empty = True
        self.agent = None
        self.q = []

    def step(self):
        print(self.q)
        print(self.empty)
        if self.empty and len(self.q) > 0:
            winner = self.q[0]
            self.empty = False
            self.agent = winner
            winner.cell = self
            winner.move(self)

    def leave(self):
        self.empty = True
        self.agent = None

    def __repr__(self):
        return self.name

    def enter(self, agent):
        self.q.append(agent)
        agent.head = self.agent

    def get_agent(self):
        return self.agent

    def evacuate(self):
        if self.empty:
            raise ValueError("Tried to evacuate empty exit.")
        self.empty = True
        agent = self.agent
        self.agent = None
        return agent
