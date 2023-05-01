import io
import os

import mesa
import numpy as np
import pandas as pd
import pickle
import matplotlib

import matplotlib.pyplot as plt
import matplotlib.animation as animation

import ffmpeg

from .utils.constants import SFF_OBSTACLE, KS, KO, KD, GAMMA, OCCUPIED_CELL, EMPTY_CELL

FIGSIZESQUARE = (8, 8)
FIGSIZEWIDE = (20, 5)
FIGSIZE4_3 = (8, 6)

location = "./out/"
# matplotlib.use('tkagg')


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
        if not os.path.isdir(self.data_location):
            os.mkdir(self.data_location[:-1])
        if not os.path.isdir(self.graphs_location):
            os.mkdir(self.graphs_location[:-1])
        if name is not None:
            self.name = name
        else:
            self.name = self.__class__.__name__
        self.counter = None
        self.data_location = self.data_location + self.name
        self.graphs_location = self.graphs_location + self.name
        self.data = self.load()
        self.do_save = True
        self.do_show = False
        self.figsize = FIGSIZE4_3
        self.compatible_maps = []

    def compatible(self):
        return self.filename in self.compatible_maps

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

    def n_sims(self):
        ctr = self.model.datacollector.counter
        if self.name in ctr:
            return str(ctr[self.name])
        else:
            return str(1)


class ExperimentDistanceHeatmap(Experiment):
    def __init__(self, model):
        super().__init__(model)

    def compatible(self):
        return True

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
        plt.title("Frequency of occupied cells, " + self.n_sims() + " simulations")
        n_runs = int(self.n_sims())
        im = ax.imshow(data/n_runs)
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)
        fig.colorbar(im, orientation="horizontal", ax=ax).set_label("# of visits")


        if save or self.do_save:
            plt.savefig(self.graphs_location + ".png")
            plt.savefig(self.graphs_location + ".pdf")
        if show or self.do_show:
            plt.show(block=False)
            plt.pause(5)


class ExperimentDistanceToLeader(Experiment):
    def __init__(self, model):
        super().__init__(model)
        self.compatible_maps = ["any"]

    def compatible(self):
        return True

    def load(self):
        if os.path.exists(self.data_location + ".dat"):
            with open(self.data_location + ".dat", "rb") as f:
                return pickle.load(f)
        else:
            return {}

    def save(self):
        key = 0
        with open(self.data_location + ".dat", "wb") as f:
            pickle.dump(self.data[key], f)

    def update(self):
        key = 0
        if key not in self.data:
            self.data[key] = {uid: [] for uid in self.model.schedule.get_agents()}
        data = self.data[key]

        for agent in self.model.schedule.agents:
            if agent.name.startswith("Follower"):
                uid = agent.unique_id
                d_to_leader = agent.leader_dist()
                data[uid].append(d_to_leader)
        self.data[key] = data

    def visualize(self, save=False, show=False):
        key = 0
        data = self.data[key]
        fig, ax = plt.subplots(figsize=self.figsize)
        x_pos = []
        for uid in data:
            if len(data[uid]) < 1:
                continue
            x_pos.append((uid, np.mean(data[uid])))
        x_pos = sorted(x_pos, key=lambda x: x[1])
        pos_ctr = 1
        for uid, pos in x_pos:
            ax.boxplot(data[uid], positions=[pos_ctr], showfliers=False)
            pos_ctr += 1
        plt.xlabel("Ranked averaged distance to leader")
        plt.ylabel("Distance to leader")
        plt.title(self.n_sims() + " simulations")
        pos_ctr = 1
        for uid, pos in x_pos:
            # ax.scatter(pos_ctr, data[uid][0])
            pos_ctr += 1
        # ax.xaxis.set_major_formatter(plt.FormatStrFormatter('%.2f'))
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
        plt.title("Rolling average, window size 2, " + self.n_sims() + " simulations")

        if save or self.do_save:
            plt.savefig(self.graphs_location + "Plot.png")
            plt.savefig(self.graphs_location + "Plot.pdf")
        if show or self.do_show:
            plt.show(block=False)
            plt.pause(1)


class ExperimentGaps(Experiment):
    def __init__(self, model):
        super().__init__(model)
        self.compatible_maps = ["gaps.txt", "gaps_back.txt"]
                                # "gaps_short.txt", "gaps_short_back.txt"]
        self.distances = None

    def load(self):
        return {}

    def save(self):
        self.distances = self.finalize()
        if self.do_save:
            with open(self.data_location + ".dat", "wb") as f:
                pickle.dump(self.distances, f)

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
        test_length = 60
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
            if len(p) == 0:
                continue
            p = sorted(p)
            distances[0].append(0)
            for j in range(1, len(p)):
                current = p[j]
                previous = p[j-1]
                distances[j].append(current - previous)
        return distances

    def visualize(self, save=False, show=False):
        distances = self.distances
        if distances is None:
            return
        fig, axs = plt.subplots(nrows=4, ncols=1, figsize=self.figsize, sharex="col")
        axs[0].set_title(self.n_sims() + " simulations")
        for i, array in enumerate(distances):
            axs[i].hist(array)
        plt.xlabel("Distance to the previous paired agents")
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
        self.compatible_maps = ["any"]

    def compatible(self):
        return True

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
        max_distance = 50
        if key not in self.data:
            self.data[key] = np.zeros_like(self.model.room)
        if key2 not in self.data:
            self.data[key2] = np.zeros((3, max_distance))

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
        max_distance = 50
        data = np.zeros_like(self.model.room)
        data2 = np.zeros((3, max_distance))
        if os.path.exists(self.data_location + "_selected.npy"):
            incorrect_orientation_ctr_map = np.load(self.data_location + "_selected.npy", allow_pickle=True)
            data += incorrect_orientation_ctr_map
        if os.path.exists(self.data_location + "_distance.npy"):
            incorrect_orientation_distance = np.load(self.data_location + "_distance.npy", allow_pickle=True)
            data2 += incorrect_orientation_distance
        d = {key: data,
             key2: data2}
        return d

    def save(self):
        key = "incorrect_orientation_selected"
        key2 = "incorrect_orientation_distance"
        data = self.data[key]
        data2 = self.data[key2]
        np.save(self.data_location + "_selected.npy", data)
        np.save(self.data_location + "_distance.npy", data2)

    def visualize(self, save=False, show=False):
        key = "incorrect_orientation_selected"
        key2 = "incorrect_orientation_distance"
        data = self.data[key]
        data2 = self.data[key2]

        fig, ax = plt.subplots(figsize=self.figsize)
        data = np.flip(data, axis=0)
        ax.set_title("Frequency of Incorrect Orientation Maneuvers, " + self.n_sims() + " simulations")
        n_runs = int(self.n_sims())
        im = ax.imshow(data / n_runs)
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)
        fig.colorbar(im, orientation="horizontal", ax=ax).set_label("# of incorrect maneuvers")

        if save or self.do_save:
            plt.savefig(self.graphs_location + "Heatmap.png")
            plt.savefig(self.graphs_location + "Heatmap.pdf")
        if show or self.do_show:
            plt.show(block=False)
            plt.pause(2)

        fig, ax = plt.subplots(figsize=self.figsize)
        ax.set_xlabel("Distance to Leader")
        ax.set_ylabel("Penalization")
        plt.title(self.n_sims() + " simulations")
        trailing_end = 0
        total = data2[1][1:]
        for i in range(len(total)):
            if total[i] < 10:
                trailing_end = i
                break
        total = total[:trailing_end]
        hits = data2[0][1:trailing_end + 1]
        xticks = range(1, len(total) + 1)
        ax.plot(xticks, total / hits)
        plt.xticks(xticks)
        if save or self.do_save:
            plt.savefig(self.graphs_location + "Penalization.png")
            plt.savefig(self.graphs_location + "Penalization.pdf")
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
        ax.plot(xticks, hits / total, label="Incorrect m. out of all m.")
        plt.title(self.n_sims() + " simulations")
        plt.xticks(xticks)
        plt.legend()

        if save or self.do_save:
            plt.savefig(self.graphs_location + "Ratio.png")
            plt.savefig(self.graphs_location + "Ratio.pdf")
        if show or self.do_show:
            plt.show(block=False)
            plt.pause(2)


class ExperimentFlow(Experiment):
    def __init__(self, model):
        super().__init__(model)
        self.compatible_maps = ["any"]

    def compatible(self):
        return True

    def load(self):
        key = 0
        if os.path.exists(self.data_location + ".npy"):
            data = np.load(self.data_location + ".npy")
        else:
            t = 1000
            data = np.zeros(shape=(t, *self.model.room.shape))
        return {key: data}

    def save(self):
        key = 0
        data = self.data[key]
        np.save(self.data_location + ".npy", data)

    def update(self):
        key = 0
        data = self.data[key]
        of = self.model.of
        t = self.model.schedule.steps
        if t >= data.shape[0]:
            _data = np.zeros(shape=(2 * t, *of.shape))
            _data[:t] = data
            data = _data
        data[t] += of
        self.data[key] = data

    def visualize(self, save=True, show=False):
        key = 0
        data = self.data[key]
        t = data.shape[0]
        t_max = 0
        max_n_agents = 0
        n_runs = -data[0][0][0]
        print("# of simulations:", n_runs)
        for i in range(t):
            n = np.max(data[i])
            max_n_agents = n if n > max_n_agents else max_n_agents
            d = np.flip(data[i], axis=0)
            d[d < 0] = 0
            if np.sum(d).all() == 0:
                t_max = i
                print(t_max)
                break
        data = data[:t_max]
        n_agents = np.sum(data[0] > 0)

        norm = max_n_agents

        fig, ax = plt.subplots(figsize=self.figsize)
        ax.set_title("Flow at step 0")
        im = ax.imshow(np.flip(data[0], axis=0), vmin=0, vmax=np.ceil(norm))
        ax.xaxis.set_visible(False)
        ax.yaxis.set_visible(False)
        fig.colorbar(im, orientation="horizontal", ax=ax).set_label("# of visits")

        def animate(i):
            d = np.flip(data[i], axis=0)
            d[d < 0] = 0
            ax.set_title("Flow at step " + str(i))
            im.set_data(d)
            return im

        ani = animation.FuncAnimation(fig, animate, frames=t_max)
        FFwriter = animation.FFMpegWriter(fps=20)
        ani.save(self.graphs_location + ".mp4", writer=FFwriter)


class ExperimentSpecificFlow(Experiment):
    def __init__(self, model):
        super().__init__(model)
        self.compatible_maps = ["see self.gates"]
        self.data_location = self.data_location[:-len(self.name)] + "ExperimentFlow"
        self.gates = {
            "map01.txt": [[(18, 13), (18, 14)],
                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)]],
            "map02.txt": [[(18, 13), (18, 14)],
                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)]],
            "map03.txt": [[(18, 13), (18, 14)],
                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)]],
            "map11.txt": [[(18, 13), (18, 14)],
                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)]],
            "map12.txt": [[(18, 13), (18, 14)],
                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)]],
            "map13.txt": [[(18, 13), (18, 14)],
                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)]],
            "map21.txt": [[(18, 13), (18, 14)],
                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)],
                          [(58, 6), (59, 6), (60, 6), (61, 6), (62, 6)]],
            "map22.txt": [[(18, 13), (18, 14)],
                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)],
                          [(58, 6), (59, 6), (60, 6), (61, 6), (62, 6)]],
            "map23.txt": [[(18, 13), (18, 14)],
                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)],
                          [(58, 6), (59, 6), (60, 6), (61, 6), (62, 6)]],

            "map01_mirror.txt": [[(18, 13), (18, 14)],                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)]],
            "map02_mirror.txt": [[(18, 13), (18, 14)],                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)]],
            "map03_mirror.txt": [[(18, 13), (18, 14)],                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)]],
            "map11_mirror.txt": [[(18, 13), (18, 14)],                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)]],
            "map12_mirror.txt": [[(18, 13), (18, 14)],                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)]],
            "map13_mirror.txt": [[(18, 13), (18, 14)],                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)]],
            "map21_mirror.txt": [[(18, 13), (18, 14)],                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)],                          [(58, 6), (59, 6), (60, 6), (61, 6), (62, 6)]],
            "map22_mirror.txt": [[(18, 13), (18, 14)],                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)],                          [(58, 6), (59, 6), (60, 6), (61, 6), (62, 6)]],
            "map23_mirror.txt": [[(18, 13), (18, 14)],                          [(50, 11), (50, 12), (50, 13), (50, 14), (50, 15)],                          [(58, 6), (59, 6), (60, 6), (61, 6), (62, 6)]],
        }

    def compatible(self):
        return self.filename in self.gates

    def load(self):
        return {}

    def update(self):
        pass

    def save(self):
        pass

    def visualize(self, save=False, show=False):
        key = 0
        data = None
        if os.path.exists(self.data_location + ".npy"):
            data = np.load(self.data_location + ".npy")
        else:
            raise FileNotFoundError(self.name + " data not found.")
        t = data.shape[0]
        t_max = 0
        max_n_agents = 0
        n_runs = -data[0][0][0]
        print("# of simulations:", n_runs)
        for i in range(t):
            n = np.max(data[i])
            max_n_agents = n if n > max_n_agents else max_n_agents
            d = np.flip(data[i], axis=0)
            d[d < 0] = 0
            if np.sum(d).all() == 0:
                t_max = i
                print(t_max)
                break
        data = data[:t_max]
        gate_data = []
        cell_size_norm = 0.4*0.4
        for gate in self.gates[self.filename]:
            rho = []
            for i in range(t_max):
                flow = 0
                for x, y in gate:
                    flow += data[i, y, x]
                rho.append(flow / n_runs / (len(gate)*cell_size_norm))
            gate_data.append(rho)
        fig, ax = plt.subplots(figsize=self.figsize)
        ax.set_title("Specific flow at gates, " + self.n_sims() + " simulations")
        for i, gd in enumerate(gate_data):
            ax.plot(gd, label="Gate " + str(i))
        ax.set_xlabel("Step of the model")
        ax.set_ylabel("Average flow at gate")

        plt.legend()
        plt.savefig(self.graphs_location + ".png")
        plt.savefig(self.graphs_location + ".pdf")


class ExperimentTET(Experiment):
    def __init__(self, model):
        super().__init__(model)
        self.compatible_maps = ["any"]

    def compatible(self):
        return True

    def load(self):
        key = "TET"
        key2 = "N_AGENTS"
        if os.path.exists(self.data_location + ".dat"):
            with open(self.data_location + ".dat", "rb") as f:
                return pickle.load(f)
        else:
            upper_limit_steps = 1000
            return {key: [],
                    key2: [[] for _ in range(upper_limit_steps)]}

    def save(self):
        key = "TET"
        key2 = "N_AGENTS"
        data = self.data
        n_runs = len(data[key])
        if n_runs > 0:
            max_steps = max(data[key])
        else:
            max_steps = 0
        n_steps = self.model.schedule.steps
        if n_steps < max_steps:
            for s in range(n_steps, max_steps):
                # fill remaining steps up to the longest run with zeros
                data[key2][s].append(0)
        data[key].append(self.model.schedule.steps)
        with open(self.data_location + ".dat", "wb") as f:
            pickle.dump(data, f)

    def update(self):
        key = "TET"
        key2 = "N_AGENTS"
        data = self.data
        n_runs = len(data[key])
        if n_runs > 0:
            max_steps = max(data[key])
        else:
            max_steps = 0
        n_agents = len(self.model.schedule._agents)
        n_steps = self.model.schedule.steps
        if n_steps >= max_steps:
            # double the number of longest run
            data[key2].extend([[] for _ in range(n_steps)])
        if len(data[key2][n_steps]) == 0:
            # this is the longest run, fill other shorter runs with zeros
            data[key2][n_steps] = [0 for _ in range(n_runs)]
        # add current number of agents
        data[key2][n_steps].append(n_agents)

    def visualize(self, save=False, show=False):
        key = "TET"
        key2 = "N_AGENTS"
        data = self.data
        max_steps = max(data[key])
        min_steps = min(data[key])
        bins = max_steps - min_steps
        if bins < 1:
            bins = 10
        n_runs = len(data[key])
        fig, ax = plt.subplots(figsize=self.figsize)
        ax.hist(data[key], label=self.filename,
                bins=bins)
        plt.title(self.n_sims()
                  + " simulations: std="
                  + '%.2f' % np.std(data[key])
                  + ", avg="
                  + '%.2f' % np.mean(data[key]))
        plt.xlabel("TET")
        plt.legend()
        if save or self.do_save:
            plt.savefig(self.graphs_location + ".png")
            plt.savefig(self.graphs_location + ".pdf")
