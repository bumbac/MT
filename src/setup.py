import os

import mesa

from roommodel.visualization.server import server
from roommodel.model import RoomModel
from roommodel.utils.portrayal import agent_portrayal
from roommodel.file_loader import FileLoader


def visualize():
    server.launch()


if __name__ == '__main__':
    visualize()
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
