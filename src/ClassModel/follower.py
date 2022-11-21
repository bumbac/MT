import mesa
import numpy as np

from .utils.portrayal import create_color


class FollowerAgent(mesa.Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.name = "Follower: " + str(uid)
        self.model = model
        self.color = create_color(self)
        self.head = None
        self.tail = None
        self.cell = None

    def step(self):
        values = []
        c = []
        sff = self.model.follower_sff
        for coords in self.model.grid.get_neighborhood(self.pos, moore=True):
            np_coords = coords[1], coords[0]
            static_value = sff[np_coords]
            values.append(static_value)
            c.append(coords)
        choice = np.argmin(values)
        coords = c[choice]
        cell = self.model.grid[coords[0]][coords[1]][0]
        cell.enter(self)

    def move(self, cell):
        self.model.grid.move_agent(self, cell.pos)
        prev_cell = self.cell
        self.cell.leave()
        self.cell = cell
        self.head = None
        if self.tail:
            self.tail.move(prev_cell)
            self.tail = None

    def __repr__(self):
        return self.name + " " + str(self.pos)
