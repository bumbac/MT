import mesa
import numpy as np
import matplotlib

matplotlib.use('tkagg')
import matplotlib.pyplot as plt

from .scheduler import SequentialActivation
from .utils.constants import SFF_OBSTACLE, KS, KO, KD, GAMMA, OCCUPIED_CELL, EMPTY_CELL

FIGSIZE = (10, 20)


def minmax_norm(arr):
    return (arr - min(arr))/(max(arr) - min(arr))


class RoomDataCollector(mesa.DataCollector):
    def __init__(self, model, model_reporters=None, agent_reporters=None, tables=None):
        super().__init__(model_reporters, agent_reporters, tables)
        plt.close("all")
        self.model = model
        self.__name__ = "RoomDataCollector " + str(self.model.generate_uid())
        self.data = {}

    def distance_heatmap(self):
        occupancy_grid = self.model.of
        height, width = occupancy_grid.shape
        key = self.distance_heatmap.__name__
        if key not in self.data:
            self.data[key] = np.zeros(shape=(height, width))
        data = self.data[key]
        for y, x in np.argwhere(occupancy_grid == OCCUPIED_CELL):
            data[height - y, x] += 1
        if self.model.schedule.steps % 16 == 0:
            plt.imshow(data)
            plt.show(block=False)
            plt.pause(0.1)
        self.data[key] = data

    def dist_to_leader(self):
        key = self.dist_to_leader.__name__
        if key not in self.data:
            self.data[key] = {uid: [] for uid in self.model.schedule.get_agents()}
        data = self.data[key]
        virtual_leader = self.model.virtual_leader

        sff = self.model.sff["Follower"]
        for agent in self.model.schedule.agents:
            if agent.partner is not None:
                uid = agent.unique_id
                d_to_leader = abs(sff[agent.pos[1], agent.pos[0]] - sff[virtual_leader.pos[1], virtual_leader.pos[0]])
                data[uid].append(d_to_leader)
        self.data[key] = data

    def visual_dist_to_leader(self):
        key = self.dist_to_leader.__name__
        data = self.data[key]
        plt.figure(figsize=(10, 20))
        y = []
        low_limit = 0
        hi_limit = -1
        for uid in data:
            y.append(len(data[uid]))
        for uid in data:
            data[uid] = np.array(data[uid][low_limit:hi_limit])
        y = minmax_norm(np.array(y))
        cm = plt.get_cmap("jet")
        y = [cm(a) for a in y]
        for uid in data:
            data[uid] = np.array(data[uid])
            plt.plot(data[uid], c=y.pop())
        plt.show(block=False)
        plt.pause(1)

    def visual_ranking_dist_to_leader(self):
        key = self.dist_to_leader.__name__
        data = self.data[key]
        plt.figure(figsize=FIGSIZE)
        y = []
        low_limit = 0
        hi_limit = -1
        for uid in data:
            y.append(len(data[uid]))
        for uid in data:
            data[uid] = np.array(data[uid][low_limit:hi_limit])
        y_max = np.max(y)
        # for i in range(y_max):
            # if i < len(data[uid])
        cm = plt.get_cmap("jet")
        y = [cm(a) for a in y]
        for uid in data:
            data[uid] = np.array(data[uid])
            plt.plot(data[uid], c=y.pop())
        plt.show(block=False)

    def get_data(self):
        self.visual_dist_to_leader()
        return self.data

    def flush(self):
        print(self.__name__, "flushed.")
        self.data = {}
