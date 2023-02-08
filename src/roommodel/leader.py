import numpy as np
import mesa

from .utils.portrayal import create_color
from .follower import FollowerAgent
from .directed import DirectedAgent


class LeaderAgent(FollowerAgent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.name = "Leader: " + str(self.unique_id)
        self.color = create_color(self)

    def advance(self) -> None:
        if self.next_cell.winner == self:
            if self.next_cell.agent:
                self.model.graph[0].add(self.unique_id)
                if self.unique_id in self.model.graph[1]:
                    self.model.graph[1][self.unique_id].append(self.next_cell.agent.unique_id)
                else:
                    self.model.graph[1][self.unique_id] = [self.next_cell.agent.unique_id]

    def step(self) -> None:
        sff = self.model.sff["Leader"]
        self.select_cell(sff)

    def move(self, cell):
        self.model.sff_update([cell.pos, cell.pos], "Follower")
        return super().move(cell)


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
        sff = self.model.sff["Leader"]
        self.select_cell(sff)

    def move(self, cell):
        self.model.sff_update([cell.pos, cell.pos], "Follower")
        super().move(cell)
