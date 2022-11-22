import mesa
import numpy as np

from .utils.portrayal import create_color


class Agent(mesa.Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.name = str(uid)
        self.model = model
        self.color = create_color(self)

    def select_cell(self, sff):
        values = []
        c = []
        for coords in self.model.grid.get_neighborhood(self.pos, moore=True):
            np_coords = coords[1], coords[0]
            static_value = sff[np_coords]
            values.append(static_value)
            c.append(coords)
        choice = np.argmin(values)
        coords = c[choice]
        cell = self.model.grid[coords[0]][coords[1]][0]
        cell.enter(self)
        return cell

    def update_color(self, value):
        self.color = create_color(self)

    def __repr__(self):
        return self.name + " " + str(self.pos)
