import os
import sys

import mesa

from roommodel.model import RoomModel
from roommodel.utils.portrayal import agent_portrayal
if __name__ == '__main__':
    width, height = 15, 15
    gate = (7, 1)

    grid = mesa.visualization.CanvasGrid(agent_portrayal, width, height, 1000, 1000)
    server = mesa.visualization.ModularServer(
        RoomModel, [grid], "Room Model SETUP", {"width": width, "height": height, "gate": gate}
    )
    server.port = 8521  # The default
    server.launch()
