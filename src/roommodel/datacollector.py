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
            # ExperimentDistanceHeatmap(self.model),
            # ExperimentDistanceToLeader(self.model),
            # ExperimentGaps(self.model),
            ExperimentIncorrectOrientation(self.model)
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

    def get_events(self):
        key = self.events.__name__
        if key not in self.data:
            self.data[key] = {}
        return self.data[key]

    def incorrect_orientation(self, uid, cells):
        experiment = None
        for e in self.experiments:
            if e.name == ExperimentIncorrectOrientation.__name__:
                experiment = e
        if experiment is None:
            return
        experiment.incorrect_orientation(uid, cells)

    def incorrect_orientation_selected(self, uid, choice_pos):
        experiment = None
        for e in self.experiments:
            if e.name == ExperimentIncorrectOrientation.__name__:
                experiment = e
        if experiment is None:
            return
        experiment.incorrect_orientation_selected(uid, choice_pos)

    def get_data(self):
        pass
    #     # self.boxplot_distance_to_leader()
    #     # self.visual_distance_to_leader()
    #     # self.visualize_distance_heatmap()
    #     self.save_incorrect_orientation()
    #     return self.data

    def flush(self):
        self.model.logger.info(str(self.__name__)+" flushed.")
        self.data = {}
