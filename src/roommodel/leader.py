import numpy as np
import mesa

from .utils.portrayal import create_color
from .utils.constants import KO
from .agent import Agent
from .directed import DirectedAgent


class LeaderAgent(Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.color = create_color(self)
        self.name = "Leader: " + str(self.unique_id)
        # leader tries to go around
        self.k[KO] = 0.1

    def step(self):
        self.reset()
        distance, pos = self.most_distant()
        sff = self.model.sff_compute([pos, pos])
        return self.select_cell(sff)

    def most_distant(self):
        distances = []
        for uid in self.model.schedule._agents:
            agent = self.model.schedule._agents[uid]
            d = self.dist(self.pos, agent.pos)
            distances.append((d, agent.pos))
        distances = sorted(distances, key=lambda x: x[0], reverse=True)
        return distances[0]


class VirtualLeader(LeaderAgent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.color = "w"
        self.name = "Virtual " + self.name
        self.k[KO] = 1

    def step(self):
        self.reset()
        cells = self.model.grid.get_neighborhood(self.pos, include_center=True, moore=True)
        sff = self.model.sff["Leader"]
        attraction = self.attraction(sff, cells)
        coords = self.stochastic_choice(attraction)
        cell = self.model.grid[coords[0]][coords[1]][0]
        self.pos = cell.pos

    def advance(self):
        self.model.sff_update([self.pos, self.pos], "Follower")


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
