import mesa
import numpy as np

from .utils.portrayal import create_color
from .utils.constants import KS, KO, OCCUPIED_CELL
from .agent import Agent

import matplotlib

matplotlib.use('tkagg')
import matplotlib.pyplot as plt


class LeaderAgent(Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.color = create_color(self)
        self.name = "Leader: " + str(self.unique_id)
        self.movement_duration = 1
        # leader tries to go around
        self.k[KO] = 0.1
        self.k[KS] = 5

    def step(self):
        self.reset()
        distance, pos = self.most_distant()
        if distance == 0:
            sff = self.model.sff["Leader"]
        else:
            sff = self.model.sff_compute([pos, pos])
        return self.select_cell(sff)

    def middle_crowd(self):
        distances = []
        for uid in self.model.schedule._agents:
            agent = self.model.schedule._agents[uid]
            d = self.dist(self.pos, agent.pos)
            distances.append((d, agent.pos))
        distances = sorted(distances, key=lambda x: x[0], reverse=True)
        return distances[0]

    def most_distant(self):
        distances = [(0, self.pos)]
        occupancy_grid = self.model.of
        sff = self.model.sff["Leader"]
        for x, y in np.argwhere(occupancy_grid == OCCUPIED_CELL):
            if (y, x) == self.pos:
                continue
            distances.append((sff[x, y], [y, x]))
        distances = sorted(distances, key=lambda dist_pos: dist_pos[0], reverse=True)
        return distances[0]


class VirtualLeader(LeaderAgent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.color = "w"
        self.name = "Virtual " + self.name
        self.k[KO] = 0
        self.k[KS] = 10
        self.data = None

    def distance_heatmap(self):
        occupancy_grid = self.model.of
        height, width = occupancy_grid.shape
        if self.data is None:
            self.data = np.zeros(shape=(height, width))
        for y, x in np.argwhere(occupancy_grid == OCCUPIED_CELL):
            self.data[height - y, x] += 1
        if self.model.schedule.epochs % 16 == 0:
            plt.imshow(self.data)
            plt.show(block=False)
            plt.pause(0.1)

    def step(self):
        self.reset()
        self.distance_heatmap()
        cells = self.model.grid.get_neighborhood(self.pos, include_center=True, moore=True)
        sff = self.model.sff["Leader"]
        attraction = self.attraction(sff, cells)
        coords = self.stochastic_choice(attraction)
        cell = self.model.grid[coords[0]][coords[1]][0]
        self.pos = cell.pos

    def advance(self):
        self.model.sff_update([self.pos, self.pos], "Follower")
