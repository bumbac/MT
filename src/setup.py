import os
import sys

import mesa

from ClassModel.model import RoomModel
from ClassModel.utils.portrayal import agent_portrayal
if __name__ == '__main__':
    width, height = 15, 10
    gate = (7, 2)

    grid = mesa.visualization.CanvasGrid(agent_portrayal, width, height, 500, 500)
    server = mesa.visualization.ModularServer(
        RoomModel, [grid], "Money Model", {"width": width, "height": height, "gate":gate}
    )
    server.port = 8521  # The default
    server.launch()
