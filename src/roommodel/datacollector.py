import mesa
import numpy as np

from .experiment import *


class RoomDataCollector(mesa.DataCollector):
    def __init__(self, model, model_reporters=None, agent_reporters=None, tables=None):
        super().__init__(model_reporters, agent_reporters, tables)
        plt.close("all")
        self.model = model
        self.__name__ = "RoomDataCollector " + str(self.model.generate_uid())
        self.data = {}
        self.experiments = [
            ExperimentDistanceHeatmap(self.model),
            ExperimentDistanceToLeader(self.model),
            ExperimentIncorrectOrientation(self.model),
            ExperimentFlow(self.model),
            ExperimentGaps(self.model),
            ExperimentSpecificFlow(self.model),
            ExperimentTET(self.model)
        ]
        self.counter = None

    def update(self):
        for experiment in self.experiments:
            if experiment.compatible():
                experiment.update()

    def save(self):
        for experiment in self.experiments:
            if experiment.compatible():
                experiment.save()
        self.update_experiment_counter()

    def visualize(self):
        # return
        for experiment in self.experiments:
            if experiment.compatible():
                experiment.visualize()

    def flush(self):
        self.save_experiment_counter()
        self.model.logger.info(str(self.__name__)+" flushed.")
        self.data = {}

    def update_experiment_counter(self):
        if len(self.experiments) == 0:
            return
        exp = self.experiments[0]
        if os.path.exists(exp.location + "/data/counter.dat"):
            with open(exp.location + "/data/counter.dat", "rb") as f:
                self.counter = pickle.load(f)
        else:
            self.counter = {}
        for e in self.experiments:
            if e.name in self.counter:
                self.counter[e.name] += 1
            else:
                self.counter[e.name] = 1

    def save_experiment_counter(self):
        if len(self.experiments) == 0:
            return
        exp = self.experiments[0]
        with open(exp.location + "/data/counter.dat", "wb") as f:
            pickle.dump(self.counter, f)

    def events(self, event):
        key = self.events.__name__
        if key not in self.data:
            self.data[key] = {}
        data = self.data[key]
        step = self.model.schedule.steps
        data[step] = str(event)

    def get_events(self):
        key = self.events.__name__
        if key not in self.data:
            self.data[key] = {}
        return self.data[key]

    def incorrect_orientation(self, uid, cells):
        for e in self.experiments:
            if e.name == ExperimentIncorrectOrientation.__name__:
                e.incorrect_orientation(uid, cells)

    def incorrect_orientation_selected(self, uid, choice_pos):
        for e in self.experiments:
            if e.name == ExperimentIncorrectOrientation.__name__:
                e.incorrect_orientation_selected(uid, choice_pos)
