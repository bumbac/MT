import numpy as np
import mesa

from .utils.portrayal import create_color
from .utils.constants import KO
from .agent import Agent
from .directed import DirectedAgent


class LeaderAgent(Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.name = "Leader: " + str(self.unique_id)
        # leader tries to go around
        self.k[KO] = 1.0

    def step(self) -> None:
        self.reset()
        sff = self.model.sff["Leader"]
        return self.select_cell(sff)

    def move(self):
        # if self.finished_move:
        #     return None
        cell = self.next_cell
        self.model.sff_update([cell.pos, cell.pos], "Follower")
        return super().move()


class SwitchingAgent(LeaderAgent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        # self.name = "Switching " + self.name

    def advance(self) -> None:
        agent = self.next_cell.agent
        if not agent:
            return
        if agent.tail:
            agent.tail.head = None
        # switching mechanism
        agent.head = None
        agent.tail = None
        agent.next_cell = self.cell
        self.cell.winner = agent


class LeaderDirectedAgent(DirectedAgent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.name = "Leader directed: " + str(self.unique_id)
        self.color = create_color(self)

    def step(self) -> None:
        self.reset()
        sff = self.model.sff["Leader"]
        self.select_cell(sff)

    def move(self):
        if self.next_cell:
            cell = self.next_cell
        else:
            return None
        self.model.sff_update([cell.pos, cell.pos], "Follower")
        return super().move(cell)
