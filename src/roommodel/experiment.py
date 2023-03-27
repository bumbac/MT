import mesa
import numpy as np
import pandas as pd
import matplotlib
import os
matplotlib.use('tkagg')
import matplotlib.pyplot as plt

from .utils.constants import SFF_OBSTACLE, KS, KO, KD, GAMMA, OCCUPIED_CELL, EMPTY_CELL

FIGSIZE = (20, 5)
location = "./out/"


def minmax_norm(arr):
    return (arr - min(arr))/(max(arr) - min(arr))


def rolling_avg(x, N):
    cumsum = np.cumsum(np.insert(x, 0, 0))
    return (cumsum[N:] - cumsum[:-N]) / float(N)


class Experiment:
    def __init__(self, model, name=None):
        self.model = model
        self.filename = str(model.filename).split(sep="/")[-1]
        self.location = location+self.filename[:-4]
        self.data_location = self.location + "/data/"
        self.graphs_location = self.location + "/graphs/"
        if not os.path.isdir(self.location):
            os.mkdir(self.location[2:])
            os.mkdir(self.data_location[:-1])
            os.mkdir(self.graphs_location[:-1])
        if name is not None:
            self.name = name
        else:
            self.name = self.__class__.__name__
        self.data_location = self.data_location + self.name
        self.graphs_location = self.graphs_location + self.name
        self.data = self.load()
        self.do_save = True
        self.do_show = False

    def update(self):
        pass

    def save(self):
        key = 0
        np.save(self.data_location+".npy", self.data[key])

    def load(self):
        if os.path.exists(self.data_location+".npy"):
            return {0: np.load(self.data_location+".npy", allow_pickle=True)}
        else:
            return {}

    def visualize(self, save=True, show=False):
        pass


class ExperimentDistanceHeatmap(Experiment):
    def __init__(self, model):
        super().__init__(model)
        self.do_show = False

    def update(self):
        occupancy_grid = self.model.of
        key = 0
        if key not in self.data:
            self.data[key] = np.zeros_like(occupancy_grid)
        data = self.data[key]
        data += occupancy_grid == OCCUPIED_CELL
        self.data[key] = data

    def visualize(self, save=False, show=False):
        key = 0
        data = self.data[key]
        data = np.flip(data, axis=0)
        fig, ax = plt.subplots(figsize=FIGSIZE)
        plt.title("Frequency of occupied cells")
        ax.imshow(data)
        if save or self.do_save:
            plt.savefig(self.graphs_location+".png")
            plt.savefig(self.graphs_location + ".pdf")
        if show or self.do_show:
            plt.show(block=False)
            plt.pause(5)


class ExperimentDistanceToLeader(Experiment):
    def __init__(self, model):
        super().__init__(model)
        self.do_show = True

    def update(self):
        key = 0
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

    def load(self):
        return {}

    def save(self):
        pass

    def visualize(self, save=True, show=False):
        key = 0
        data = self.data[key]
        fig, ax = plt.subplots(figsize=FIGSIZE)
        for uid in data:
            if len(data[uid]) < 51:
                continue
            x_pos = data[uid][50]
            if x_pos == 0:
                continue
            ax.boxplot(data[uid], positions=[x_pos], showfliers=False)
            plt.xlabel("Distance to leader at event 1")
            plt.ylabel("Distance to leader")
            ax.scatter(x_pos, data[uid][0])
        ax.xaxis.set_major_formatter(plt.FormatStrFormatter('%.2f'))
        if save or self.do_save:
            plt.savefig(self.graphs_location + "Boxplot.png")
            plt.savefig(self.graphs_location + "Boxplot.pdf")
        if show or self.do_show:
            plt.show(block=False)
            plt.pause(1)

        data = self.data[key]
        del data[self.model.leader.unique_id]
        del data[self.model.virtual_leader.unique_id]
        fig, ax = plt.subplots(figsize=FIGSIZE)
        y = []
        low_limit = 0
        hi_limit = -1
        smoothing_level = 2
        for uid in data:
            y.append(len(data[uid]))
            data[uid] = rolling_avg(data[uid], smoothing_level)[low_limit:hi_limit]
        y = minmax_norm(np.array(y))
        cm = plt.get_cmap("viridis")
        y = [cm(a) for a in y]
        for uid in data:
            data[uid] = np.array(data[uid])
            ax.plot(data[uid], c=y.pop())
        # for xtick in [step for step in self.data[self.events.__name__]]:
        #     plt.axvline(x=xtick)
        plt.xlabel("Step of model")
        plt.ylabel("Distance to leader")
        plt.title("Rolling average, window size 2")

        if save or self.do_save:
            plt.savefig(self.graphs_location + "Plot.png")
            plt.savefig(self.graphs_location + "Plot.pdf")
        if show or self.do_show:
            plt.show(block=False)
            plt.pause(1)

