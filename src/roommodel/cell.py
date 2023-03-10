import mesa
import numpy as np


from .agent import Agent
from .utils.portrayal import rgb_to_hex


class Cell(Agent):
    def __init__(self, uid: int, model: mesa.Model, coords: (int, int)):
        super().__init__(uid, model)
        self.name = "Cell: " + self.name
        self.coords = coords
        self.agent = None
        self.winner = None
        self.q = []

    def step(self) -> None:
        if len(self.q) > 0:
            self.winner = np.random.permutation(self.q)[0]
            self.q = []
            if self.agent is not None:
                if self.winner != self.agent:
                    self.winner.head = self.agent
                    self.agent.tail = self.winner

    def bubbleup(self):
        head = self.winner
        origin = self.winner
        while head.head is not None:
            head = head.head
            # found cycle, back at beginning
            if head is origin:
                # split the cycle
                origin.head.tail = None
                origin.head = None
        return head

    def advance(self):
        if self.winner is not None:
            head = self.bubbleup()
            if head.next_cell:
                if head.next_cell.winner is head:
                    head.move()

    def update_color(self, value):
        """Updates the color to present SFF value.
        Args:
            value: float, SFF value
        """
        color = [0, 0, 0]
        if 0 <= value <= 1:
            color = [0, 255, int(255*value)]
        self.color = rgb_to_hex(*color)

    def leave(self):
        self.agent = None

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

        if self.agent.partner:
            self.agent.partner.remove_partner()
        self.model.grid.remove_agent(self.agent)
        self.model.schedule.remove_agent(self.agent)
        self.agent = None
