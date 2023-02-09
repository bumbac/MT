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
            if self.agent:
                if self.winner != self.agent:
                    self.winner.head = self.agent
                    self.agent.tail = self.winner

    def decycle(self):
        if self.winner.head == self.winner.partner:
            self.winner.head = None
            self.winner.partner.tail = None
            self.winner.partner.next_cell.advance()
        head = self.winner
        origin = self.winner
        if head:
            while head.head is not None:
                print(head, head.head)
                head = head.head
                if head == origin:
                    head.head.tail = None
                    head.head = None
            if head.next_cell:
                head.next_cell.advance()
        return

    def advance(self) -> None:
        if self.winner:
            print(self.winner.unique_id, "advance")
            if self.winner.head:
                self.decycle()
            else:
                # can be successful or unsuccessful
                prev_cell = self.winner.move(self)
                if prev_cell is not None:
                    prev_cell.advance()
                return

    def update_color(self, value):
        color = [0, 255, 0]
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
            self.agent.partner.partner = None
            self.agent.partner.leader = True
        self.model.grid.remove_agent(self.agent)
        self.model.schedule.remove_agent(self.agent)
        self.agent = None
