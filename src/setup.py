import os

import mesa

from roommodel.model import RoomModel
from roommodel.utils.portrayal import agent_portrayal
from roommodel.file_loader import FileLoader

if __name__ == '__main__':
    filename = "./maps/topology/long_left.txt"
    filename = os.path.abspath(filename)
    fl = FileLoader(filename)
    width, height = fl.dimensions()
    grid = mesa.visualization.CanvasGrid(agent_portrayal, width, height, 800, 800)
    server = mesa.visualization.ModularServer(
        RoomModel, [grid], "Room Model SETUP", {"filename": filename}
    )
    server.port = 8521  # The default
    server.launch()
