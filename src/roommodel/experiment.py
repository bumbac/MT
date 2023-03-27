import os

import mesa
import numpy as np
import pandas as pd
import pickle

import matplotlib

matplotlib.use('tkagg')
import matplotlib.pyplot as plt

from .utils.constants import SFF_OBSTACLE, KS, KO, KD, GAMMA, OCCUPIED_CELL, EMPTY_CELL


FIGSIZESQUARE = (8, 8)
FIGSIZEWIDE = (20, 5)
FIGSIZE4_3 = (8, 6)

location = "./out/"


def minmax_norm(arr):
    return (arr - min(arr)) / (max(arr) - min(arr))


def rolling_avg(x, N):
    cumsum = np.cumsum(np.insert(x, 0, 0))
    return (cumsum[N:] - cumsum[:-N]) / float(N)


class Experiment:
    def __init__(self, model, name=None):
        self.model = model
        self.filename = str(model.filename).split(sep="/")[-1]
        self.location = location + self.filename[:-4]
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
        self.figsize = FIGSIZE4_3

    def update(self):
        pass

    def save(self):
        key = 0
        np.save(self.data_location + ".npy", self.data[key])

    def load(self):
        if os.path.exists(self.data_location + ".npy"):
            return {0: np.load(self.data_location + ".npy", allow_pickle=True)}
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
        fig, ax = plt.subplots(figsize=self.figsize)
        plt.title("Frequency of occupied cells")
        ax.imshow(data)
        if save or self.do_save:
            plt.savefig(self.graphs_location + ".png")
            plt.savefig(self.graphs_location + ".pdf")
        if show or self.do_show:
            plt.show(block=False)
            plt.pause(5)


class ExperimentDistanceToLeader(Experiment):
    def __init__(self, model):
        super().__init__(model)
        self.do_show = False

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

    def visualize(self, save=True, show=False):
        key = 0
        data = self.data[key]
        fig, ax = plt.subplots(figsize=self.figsize)
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
        fig, ax = plt.subplots(figsize=self.figsize)
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
        plt.xlabel("Step of model")
        plt.ylabel("Distance to leader")
        plt.title("Rolling average, window size 2")

        if save or self.do_save:
            plt.savefig(self.graphs_location + "Plot.png")
            plt.savefig(self.graphs_location + "Plot.pdf")
        if show or self.do_show:
            plt.show(block=False)
            plt.pause(1)


class ExperimentGaps(Experiment):

    def load(self):
        return {}

    def save(self):
        pass

    def update(self):
        key = 0
        if key not in self.data:
            self.data[key] = {uid: [] for uid in self.model.schedule.get_agents()}
            self.data[key][-1] = True
            del self.data[key][self.model.leader.unique_id]
            del self.data[key][self.model.virtual_leader.unique_id]
        event_data = self.model.datacollector.get_events()
        if len(event_data) < 1:
            return
        data = self.data[key]
        if len(event_data) == 1:
            ctr = 0
            for agent in self.model.schedule.agents:
                if agent.partner is not None:
                    if agent.leader:
                        uid = agent.unique_id
                        if len(data[uid]) > 0:
                            data[uid].append((agent.pos, agent.partner.pos, data[uid][0][2]))
                        elif data[-1]:
                            data[uid].append((agent.pos, agent.partner.pos, ctr))
                        ctr += 1
            data[-1] = False
        self.data[key] = data

    def finalize(self):
        key = 0
        data = self.data[key]
        del data[-1]
        leader_uids = []
        leader_ctr = []
        for uid in data:
            if len(data[uid]) > 0:
                leader_uids.append(uid)
                leader_ctr.append(data[uid][0][2])
        leader_starts = {uid: [] for uid in leader_uids}
        n_dist = len(leader_starts)
        test_length = 20
        for uid in leader_uids:
            for item in data[uid]:
                leader, partner, ctr = item
                leader_starts[uid].append((leader[0] + partner[0]) / 2)
        if os.path.exists(self.data_location + ".dat"):
            with open(self.data_location + ".dat", "rb") as f:
                distances = pickle.load(f)
        else:
            distances = [[] for _ in range(n_dist)]
        for i in range(test_length):
            p = []
            for uid in leader_starts:
                if len(leader_starts[uid]) <= i:
                    continue
                else:
                    p.append(leader_starts[uid][i])
            p = sorted(p)
            low_p = p[0]
            for j, pp in enumerate(p):
                distances[j].append(pp - low_p)
        return distances

    def visualize(self, save=True, show=False):
        distances = self.finalize()
        if self.do_save:
            with open(self.data_location + ".dat", "wb") as f:
                pickle.dump(distances, f)

        fig, axs = plt.subplots(nrows=4, ncols=1, figsize=self.figsize, sharex="col")
        for i, array in enumerate(distances):
            axs[i].hist(array)
        plt.xlabel("Distance to leader")
        if save or self.do_save:
            plt.savefig(self.graphs_location + ".png")
            plt.savefig(self.graphs_location + ".pdf")
        show = False
        if show or self.do_show:
            plt.show(block=False)
            plt.pause(10)


class ExperimentIncorrectOrientation(Experiment):
    def __init__(self, model):
        super().__init__(model)
        self.do_save = True
        self.do_show = True

    def incorrect_orientation(self, uid, cells):
        key3 = "incorrect_orientation"
        if key3 not in self.data:
            self.data[key3] = {}
        data = self.data[key3]
        if uid not in data:
            data[uid] = {}
        for choice in cells:
            if choice not in data[uid]:
                data[uid][choice] = []
            data[uid][choice].append(cells[choice])
        self.data[key3] = data

    def incorrect_orientation_selected(self, uid, choice_pos):
        key = "incorrect_orientation_selected"
        key2 = "incorrect_orientation_distance"
        test_length = 20
        if key not in self.data:
            self.data[key] = np.zeros_like(self.model.room)
        if key2 not in self.data:
            self.data[key2] = np.zeros((3, test_length))

        key3 = "incorrect_orientation"
        data = self.data[key3]
        if uid in data:
            for choice in data[uid]:
                penalization, distance = data[uid][choice][-1]
                leader, partner = choice_pos
                leader_pos, _ = leader
                partner_pos, _ = partner
                if choice_pos == choice:
                    self.data[key2][0, round(distance)] += 1
                    self.data[key2][1, round(distance)] += penalization
                    self.data[key][leader_pos[1], leader_pos[0]] += 1
                    self.data[key][partner_pos[1], partner_pos[0]] += 1
            self.data[key2][2, round(distance)] += 1

    def load(self):
        key = "incorrect_orientation_selected"
        key2 = "incorrect_orientation_distance"
        test_length = 20
        data = np.zeros_like(self.model.room)
        data2 = np.zeros((3, test_length))
        if os.path.exists(self.data_location+"_selected.npy"):
            incorrect_orientation_ctr_map = np.load(self.data_location+"_selected.npy", allow_pickle=True)
            data += incorrect_orientation_ctr_map
        if os.path.exists(self.data_location+"_distance.npy"):
            incorrect_orientation_distance = np.load(self.data_location+"_distance.npy", allow_pickle=True)
            data2 += incorrect_orientation_distance
        d = {key: data,
             key2: data2}
        return d

    def save(self):
        key = "incorrect_orientation_selected"
        key2 = "incorrect_orientation_distance"
        data = self.data[key]
        data2 = self.data[key2]
        if os.path.exists(self.data_location+"_selected.npy"):
            incorrect_orientation_ctr_map = np.load(self.data_location+"_selected.npy", allow_pickle=True)
            data += incorrect_orientation_ctr_map
        if os.path.exists(self.data_location+"_distance.npy"):
            incorrect_orientation_distance = np.load(self.data_location+"_distance.npy", allow_pickle=True)
            data2 += incorrect_orientation_distance

        np.save(self.data_location+"_selected.npy", data)
        np.save(self.data_location+"_distance.npy", data2)

    def visualize(self, save=False, show=False):
        key = "incorrect_orientation_selected"
        key2 = "incorrect_orientation_distance"
        data = self.data[key]
        data2 = self.data[key2]

        fig, ax = plt.subplots(figsize=self.figsize)
        data = np.flip(data, axis=0)
        ax.set_title("Frequency of Incorrect Orientation Maneuvers")
        ax.imshow(data)
        if save or self.do_save:
            plt.savefig(self.graphs_location + "Heatmap.png")
            plt.savefig(self.graphs_location + "Heatmap.pdf")
        if show or self.do_show:
            plt.show(block=False)
            plt.pause(2)

        fig, ax = plt.subplots(figsize=self.figsize)
        ax.set_xlabel("Distance to Leader")
        ax.set_ylabel("Penalization")
        xticks = range(len(data2[1]))
        ax.plot(xticks, data2[1] / data2[0])
        plt.xticks(xticks)
        if save or self.do_save:
            plt.savefig(self.graphs_location + "Penalization.png")
        if show or self.do_show:
            plt.show(block=False)
            plt.pause(2)

        fig, ax = plt.subplots(figsize=self.figsize)
        trailing_end = 0
        total = data2[2][1:]
        for i in range(len(total)):
            if total[i] < 10:
                trailing_end = i
                break
        total = total[:trailing_end]
        norm_data = total / sum(total)
        xticks = range(1, len(norm_data) + 1)
        ax.scatter(y=norm_data, x=xticks, label="All maneuvers", alpha=0.5, color='orange')
        hits = data2[0][1:trailing_end + 1]
        ax.set_xlabel("Distance to Leader")
        ax.set_ylabel("Ratio")
        # ax.scatter(y=hits / total, x=xticks, label="Incorrect maneuvers", alpha=0.5, color='blue')
        ax.plot(xticks, hits/total, label="Incorrect maneuvers")
        plt.xticks(xticks)
        plt.legend()

        if save or self.do_save:
            plt.savefig(self.graphs_location + "Ratio.png")
        if show or self.do_show:
            plt.show(block=False)
            plt.pause(2)
