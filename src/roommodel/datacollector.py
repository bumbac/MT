import mesa
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use('tkagg')
import matplotlib.pyplot as plt

from .utils.constants import SFF_OBSTACLE, KS, KO, KD, GAMMA, OCCUPIED_CELL, EMPTY_CELL

FIGSIZE = (20, 5)


def minmax_norm(arr):
    return (arr - min(arr))/(max(arr) - min(arr))


def rolling_avg(x, N):
    cumsum = np.cumsum(np.insert(x, 0, 0))
    return (cumsum[N:] - cumsum[:-N]) / float(N)


class RoomDataCollector(mesa.DataCollector):
    def __init__(self, model, model_reporters=None, agent_reporters=None, tables=None):
        super().__init__(model_reporters, agent_reporters, tables)
        plt.close("all")
        self.model = model
        self.__name__ = "RoomDataCollector " + str(self.model.generate_uid())
        self.data = {}

    def events(self, event):
        key = self.events.__name__
        if key not in self.data:
            self.data[key] = {}
        data = self.data[key]
        step = self.model.schedule.steps
        name = str(event)
        data[step] = name

    def distance_heatmap(self):
        occupancy_grid = self.model.of
        key = self.distance_heatmap.__name__
        if key not in self.data:
            self.data[key] = np.zeros_like(occupancy_grid)
        data = self.data[key]
        data += occupancy_grid == OCCUPIED_CELL
        self.data[key] = data

    def visualize_distance_heatmap(self):
        key = self.distance_heatmap.__name__
        data = self.data[key]
        data = np.flip(data, axis=0)
        plt.figure(figsize=(10, 20))
        plt.imshow(data)
        plt.show(block=False)
        plt.pause(1)

    def distance_to_leader(self):
        key = self.distance_to_leader.__name__
        if key not in self.data:
            self.data[key] = {uid: [] for uid in self.model.schedule.get_agents()}
        data = self.data[key]
        virtual_leader = self.model.virtual_leader

        sff = self.model.sff["Follower"]
        for agent in self.model.schedule.agents:
            if agent.name.startswith("Follower"):
                uid = agent.unique_id
                d_to_leader = abs(sff[agent.pos[1], agent.pos[0]] - sff[virtual_leader.pos[1], virtual_leader.pos[0]])
                data[uid].append(d_to_leader)
        self.data[key] = data

    def boxplot_distance_to_leader(self):
        key = self.distance_to_leader.__name__
        data = self.data[key]
        fig, ax = plt.subplots(figsize=(10, 20))
        for uid in data:
            if len(data[uid]) < 51:
                continue
            x_pos = data[uid][50]
            if x_pos == 0:
                continue
            print(x_pos, uid, data[uid])
            ax.boxplot(data[uid], positions=[x_pos], showfliers=False)
            ax.scatter(x_pos, data[uid][0])
        plt.show(block=False)
        plt.pause(1)

    def visual_distance_to_leader(self):
        key = self.distance_to_leader.__name__
        data = self.data[key]
        plt.figure(figsize=(10, 20))
        y = []
        low_limit = 0
        hi_limit = -1
        for uid in data:
            y.append(len(data[uid]))
        for agent in self.model.schedule.agents:
            if agent.partner is not None:
                uid = agent.unique_id
                data[uid] = rolling_avg(data[uid], 30)
        for uid in data:
            data[uid] = np.array(data[uid][low_limit:hi_limit])
        y = minmax_norm(np.array(y))
        cm = plt.get_cmap("jet")
        y = [cm(a) for a in y]
        for uid in data:
            data[uid] = np.array(data[uid])
            plt.plot(data[uid], c=y.pop())
        for xtick in [step for step in self.data[self.events.__name__]]:
            plt.axvline(x=xtick)
        plt.show(block=False)
        plt.pause(1)

    def visual_ranking_dist_to_leader(self):
        key = self.distance_to_leader.__name__
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
        self.boxplot_distance_to_leader()
        self.visual_distance_to_leader()
        self.visualize_distance_heatmap()
        return self.data

    def flush(self):
        print(self.__name__, "flushed.")
        self.data = {}
