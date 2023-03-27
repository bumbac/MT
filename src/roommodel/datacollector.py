import mesa
import numpy as np
import pandas as pd
import matplotlib
import os
matplotlib.use('tkagg')
import matplotlib.pyplot as plt

from .experiment import *
from .utils.constants import SFF_OBSTACLE, KS, KO, KD, GAMMA, OCCUPIED_CELL, EMPTY_CELL

FIGSIZE = (20, 5)
data_location = "./out/data/"
graph_location = "./out/graphs/"

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
        self.experiments = [
            ExperimentDistanceHeatmap(self.model),
            ExperimentDistanceToLeader(self.model)
        ]

    def update(self):
        for experiment in self.experiments:
            experiment.update()

    def save(self):
        for experiment in self.experiments:
            experiment.save()

    def visualize(self):
        for experiment in self.experiments:
            experiment.visualize()

    def events(self, event):
        key = self.events.__name__
        if key not in self.data:
            self.data[key] = {}
        data = self.data[key]
        step = self.model.schedule.steps
        name = str(event)
        data[step] = name

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

    def incorrect_orientation(self, uid, cells):
        key = self.incorrect_orientation.__name__
        if key not in self.data:
            self.data[key] = {}
        data = self.data[key]
        if uid not in data:
            data[uid] = {}
        for choice in cells:
            if choice not in data[uid]:
                data[uid][choice] = []
            data[uid][choice].append(cells[choice])

    def incorrect_orientation_selected(self, uid, choice_pos):
        key = self.incorrect_orientation_selected.__name__
        key2 = "incorrect_orientation_distance"
        if key not in self.data:
            self.data[key] = np.zeros_like(self.model.room)
        if key2 not in self.data:
            self.data[key2] = np.zeros((3, 20))

        source_key = self.incorrect_orientation.__name__
        data = self.data[source_key]
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

    def save_incorrect_orientation(self):
        key = self.incorrect_orientation_selected.__name__
        key2 = "incorrect_orientation_distance"
        data = self.data[key]
        data2 = self.data[key2]
        if os.path.exists(data_location+"incorrect_orientation.npy"):
            incorrect_orientation_ctr_map = np.load(data_location+"incorrect_orientation.npy", allow_pickle=True)
            data += incorrect_orientation_ctr_map
        if os.path.exists(data_location+"incorrect_orientation_distance.npy"):
            incorrect_orientation_distance = np.load(data_location+"incorrect_orientation_distance.npy", allow_pickle=True)
            data2 += incorrect_orientation_distance

        visualize = False
        if visualize:
            plt.figure(figsize=FIGSIZE)
            plt.imshow(data)
            plt.show(block=False)
            plt.pause(0.1)
            plt.figure(figsize=FIGSIZE)
            plt.plot(data2[0]/data2[2])
            plt.show(block=False)
            plt.pause(0.1)
            plt.figure(figsize=FIGSIZE)
            plt.plot(data2[1]/data2[0])
            plt.show(block=False)
            plt.pause(0.1)

        np.save(data_location+"incorrect_orientation.npy", data)
        np.save(data_location+"incorrect_orientation_distance.npy", data2)

    def gaps_between_agents(self):
        key = self.gaps_between_agents.__name__
        if key not in self.data:
            self.data[key] = {uid: [] for uid in self.model.schedule.get_agents()}
            self.data[key][-1] = True
            del self.data[key][self.model.leader.unique_id]
            del self.data[key][self.model.virtual_leader.unique_id]
        if self.events.__name__ in self.data:
            event_data = self.data[self.events.__name__]
        else:
            return
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

    def visualize_gaps_between_agents(self):
        key = self.gaps_between_agents.__name__
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
                leader_starts[uid].append((leader[0]+partner[0])/2)
        if os.path.exists(data_location+"gaps.npy"):
            distances = list(np.load(data_location+"gaps.npy", allow_pickle=True))
            distances = [list(a) for a in distances]
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
        np.save(data_location+"gaps.npy", distances)

    def boxplot_distance_to_leader(self):
        key = self.distance_to_leader.__name__
        data = self.data[key]
        fig, ax = plt.subplots(figsize=FIGSIZE)
        for uid in data:
            if len(data[uid]) < 51:
                continue
            x_pos = data[uid][50]
            if x_pos == 0:
                continue
            ax.boxplot(data[uid], positions=[x_pos], showfliers=False)
            ax.scatter(x_pos, data[uid][0])
        plt.show(block=False)
        plt.pause(1)

    def visual_distance_to_leader(self):
        key = self.distance_to_leader.__name__
        data = self.data[key]
        del data[self.model.leader.unique_id]
        del data[self.model.virtual_leader.unique_id]
        plt.figure(figsize=FIGSIZE)
        y = []
        low_limit = 0
        hi_limit = -1
        smoothing_level = 5
        for uid in data:
            y.append(len(data[uid]))
            data[uid] = rolling_avg(data[uid], smoothing_level)[low_limit:hi_limit]
        y = minmax_norm(np.array(y))
        cm = plt.get_cmap("viridis")
        y = [cm(a) for a in y]
        for uid in data:
            data[uid] = np.array(data[uid])
            plt.plot(data[uid], c=y.pop())
        for xtick in [step for step in self.data[self.events.__name__]]:
            plt.axvline(x=xtick)
        plt.show(block=False)
        plt.pause(0.1)

    def get_data(self):
        pass
    #     # self.boxplot_distance_to_leader()
    #     # self.visual_distance_to_leader()
    #     # self.visualize_distance_heatmap()
    #     # self.visualize_gaps_between_agents()
    #     self.save_incorrect_orientation()
    #     return self.data

    def flush(self):
        self.model.logger.info(str(self.__name__)+" flushed.")
        self.data = {}
