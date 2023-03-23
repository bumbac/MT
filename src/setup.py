import os
import numpy as np
import matplotlib.pyplot as plt


import mesa

from roommodel.visualization.server import server
from roommodel.model import RoomModel
from roommodel.utils.portrayal import agent_portrayal
from roommodel.file_loader import FileLoader


def visualize():
    server.launch()


def batch():
    filename = "./maps/topology/gaps.txt"
    filename = os.path.abspath(filename)
    fl = FileLoader(filename)
    for i in range(1):
        model = RoomModel(ks=3.0, ko=0.0, kd=0.0, leader_movement_duration=2, agent_movement_duration=3,
                          penalization_orientation=1.0, leader_front_location_switch=True,
                          fileloader=fl)
        model.run_model()
    distances = np.load("./gaps.npy", allow_pickle=True)
    n_dist = 4
    fig, axs = plt.subplots(n_dist, 1, sharex='col')
    for i, item in enumerate(distances):
        axs[i].hist(item)
    plt.show(block=False)
    plt.pause(100)


if __name__ == '__main__':
    batch()
    # visualize()
    #
    # filename = "./maps/topology/conflict.txt"
    # filename = os.path.abspath(filename)
    # fl = FileLoader(filename)
    # canvas = fl.get_canvas()
    # server = mesa.visualization.ModularServer(
    #     RoomModel, [canvas], "Room Model SETUP", {"filename": filename}
    # )
    # server.port = 8521  # The default
    # server.launch()
