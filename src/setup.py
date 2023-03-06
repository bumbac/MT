import os

import mesa

from roommodel.model import RoomModel
from roommodel.utils.portrayal import agent_portrayal
from roommodel.file_loader import FileLoader

if __name__ == '__main__':
    filename = "./maps/topology/conflict.txt"
    filename = os.path.abspath(filename)
    fl = FileLoader(filename)
    canvas = fl.get_canvas()
    server = mesa.visualization.ModularServer(
        RoomModel, [canvas], "Room Model SETUP", {"filename": filename}
    )
    server.port = 8521  # The default
    server.launch()
