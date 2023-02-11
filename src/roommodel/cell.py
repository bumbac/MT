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

    def decycle(self):
        head = self.winner
        origin = self.winner
        print("decycle", self.winner.unique_id)
        while head.head is not None:
            head = head.head
            # found cycle, back at beginning
            if head is origin:
                # split the cycle
                origin.head.tail = None
                origin.head = None
            if head is self.winner.partner and head is not None:
                self.winner.head = None
                self.winner.partner.tail = None
        if head.confirm_move and head.next_cell is not None:
            head.next_cell.advance()
        return

    def advance(self) -> None:
        if self.winner is not None:
            print(self.winner.unique_id, "advance", self.winner.pos, self.winner.next_cell.pos)
            if self.winner.head is not None:
                self.decycle()
            else:
                if not self.winner.finished_move:
                    # can be successful or unsuccessful
                    prev_cell = self.winner.move()
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
