import copy

import numpy as np
import mesa

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
        # leader tries to go around
        self.k[KO] = 0.1
        self.k[KS] = 5

    def step(self):
        self.reset()
        distance, pos = self.most_distant()
        sff = self.model.sff_compute([pos, pos])
        # sff = self.model.sff["Leader"]
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
        distances = sorted(distances, key=lambda x: x[0], reverse=True)
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
        d = 30
        height = 13
        mid_idx = 6
        resize_const = 2
        if self.data is None:
            prevpos = self.pos
            height_offset = 0
            self.data = (np.zeros(shape=(height, round(resize_const * d))), prevpos, height_offset)

        grid, prevpos, height_offset = self.data
        width_offset = self.pos[1] - prevpos[1]
        height_offset = 0
        height, width = grid.shape
        if 1.2*d > width:
            grid = copy.deepcopy(grid)
            grid.resize((height, round(resize_const * d)))
        occupancy_grid = self.model.of
        for y, x in np.argwhere(occupancy_grid == OCCUPIED_CELL):
            offset_x = self.pos[0] - x + width_offset
            offset_y = self.pos[1] - y + height_offset + mid_idx
            grid[offset_y, offset_x] += 1
        prevpos = self.pos
        self.data = (grid, prevpos, height_offset)
        if self.model.schedule.epochs % 16 == 0:
            plt.imshow(grid)
            plt.show(block=False)
            plt.pause(0.1)

    def step(self):
        self.reset()
        # self.distance_heatmap()
        cells = self.model.grid.get_neighborhood(self.pos, include_center=True, moore=True)
        sff = self.model.sff["Leader"]
        attraction = self.attraction(sff, cells)
        coords = self.stochastic_choice(attraction)
        cell = self.model.grid[coords[0]][coords[1]][0]
        self.pos = cell.pos

    def advance(self):
        self.model.sff_update([self.pos, self.pos], "Follower")
