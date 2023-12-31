import os

import mesa

from roommodel.model import RoomModel
from roommodel.file_loader import FileLoader


def batch(filename, n=10):
    # this method runs n simulations of filename map. The global parameters can be set in the declaration of model
    # variable
    filename = os.path.abspath(filename)
    fl = FileLoader(filename)
    print("\t", filename)
    for i in range(n):
        print(i)
        model = RoomModel(ks=3.0, ko=0.0, kd=0.0, leader_movement_duration=2, agent_movement_duration=3,
                          penalization_orientation=1.0, leader_front_location_switch=True,
                          fileloader=fl)
        model.run_model()


def visualize(filename):
    # this method starts a web browser visualization of simulation in filename map
    # the global parameters can be set in model_params
    filename = os.path.abspath(filename)
    fl = FileLoader(filename)
    # model visualization resolution
    canvas = fl.get_canvas(1080)
    # global parameters, the values are:
    # default value, bottom range, upper range, size of step
    model_params = {
        "ks": mesa.visualization.Slider("Sensitivity to static potential kS", 3, 1.0, 10.0, 0.5),
        "ko": mesa.visualization.Slider("Sensitivity to occupied cell kO", 0.0, 0.0, 1.0, 0.1),
        "kd": mesa.visualization.Slider("Sensitivity to diagonal movement kD", 0.5, 0.0, 1.0, 0.1),
        "leader_movement_duration": mesa.visualization.Slider("Movement duration for leader", 2, 2, 6, 1),
        "agent_movement_duration": mesa.visualization.Slider("Movement duration for followers", 3, 2, 6, 1),
        "penalization_orientation": mesa.visualization.Slider("Penalization for incorrect orientation", 1.0, 0.0, 1.0, 0.1),
        "leader_front_location_switch": mesa.visualization.Checkbox("Switch for leader location at the front", False),
        "fileloader": fl
    }

    server = mesa.visualization.ModularServer(
        RoomModel,
        [canvas],
        "Room Model",
        model_params,
    )
    server.port = 8521  # The default port
    server.launch()


if __name__ == '__main__':
    # filename examples of provided maps

    # simple situations for analyzing the movement of pairs
    experiments1 = [
        "./maps/topology/gaps.txt",
        "./maps/topology/gaps_back.txt",
        "./maps/topology/gaps_short.txt",
        "./maps/topology/gaps_short_back.txt",
        "./maps/topology/right_turn_short.txt",
        "./maps/topology/right_turn_short_back.txt"
    ]

    # complex maps with various scenarios
    experiments2 = [
        "./maps/topology/map01.txt",
        "./maps/topology/map02.txt",
        "./maps/topology/map03.txt",
        "./maps/topology/map11.txt",
        "./maps/topology/map12.txt",
        "./maps/topology/map13.txt",
        "./maps/topology/map21.txt",
        "./maps/topology/map22.txt",
        "./maps/topology/map23.txt",
    ]

    # mirrored maps with scenarios
    experiments3 = [
        "./maps/topology/map01_mirror.txt",
        "./maps/topology/map02_mirror.txt",
        "./maps/topology/map03_mirror.txt",
        "./maps/topology/map11_mirror.txt",
        "./maps/topology/map12_mirror.txt",
        "./maps/topology/map13_mirror.txt",
        "./maps/topology/map21_mirror.txt",
        "./maps/topology/map22_mirror.txt",
        "./maps/topology/map23_mirror.txt",
    ]
    filename = "./maps/topology/map22.txt"
    visualize(filename)
    # n = 1
    # for filename in experiments1:
    #     batch(filename, n)
    # for filename in experiments2:
    #     batch(filename, n)
