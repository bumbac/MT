import os
import numpy as np
import matplotlib.pyplot as plt


import mesa

# from roommodel.visualization.server import server
from roommodel.model import RoomModel
from roommodel.utils.portrayal import agent_portrayal
from roommodel.file_loader import FileLoader


def visualize():
    server.launch()


def batch():
    filename = "./maps/topology/gaps_short.txt"
    filename = os.path.abspath(filename)
    fl = FileLoader(filename)
    for i in range(1):
        print(i)
        model = RoomModel(ks=3.0, ko=0.0, kd=0.0, leader_movement_duration=2, agent_movement_duration=3,
                          penalization_orientation=1.0, leader_front_location_switch=True,
                          fileloader=fl)
        model.run_model()


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
