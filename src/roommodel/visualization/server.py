import os
import mesa

from ..model import RoomModel
from ..file_loader import FileLoader


def get_model_step(model):
    return f"Model step: {model.schedule.steps}"


filename = "./maps/topology/map21.txt"
filename = os.path.abspath(filename)
fl = FileLoader(filename)
canvas = fl.get_canvas(1080)

model_params = {
    "ks": mesa.visualization.Slider("Sensitivity to static potential kS", 3.5, 1.0, 10.0, 0.5),
    "ko": mesa.visualization.Slider("Sensitivity to occupied cell kO", 0.5, 0.0, 1.0, 0.1),
    "kd": mesa.visualization.Slider("Sensitivity to diagonal movement kD", 0.5, 0.0, 1.0, 0.1),
    "leader_movement_duration": mesa.visualization.Slider("Movement duration for leader", 2, 2, 6, 1),
    "agent_movement_duration": mesa.visualization.Slider("Movement duration for followers", 3, 2, 6, 1),
    "penalization_orientation": mesa.visualization.Slider("Penalization for incorrect orientation", 1.0, 0.0, 1.0, 0.1),
    "leader_front_location_switch": mesa.visualization.Checkbox("Switch for leader location at the front", False),
    "filename": filename
}

server = mesa.visualization.ModularServer(
    RoomModel,
    [canvas],
    "Room Model",
    model_params,
)
server.port = 8521  # The default