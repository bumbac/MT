import mesa
import numpy as np

from .utils.portrayal import create_color


class Agent(mesa.Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.name = str(uid)
        self.color = create_color(self)
        self.head = None
        self.tail = None
        self.cell = None
        self.next_cell = None

    def inform(self):
        pass

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
        self.next_cell = cell
        cell.enter(self)
        return cell

    def update_color(self, value):
        self.color = create_color(self)

    def move(self, cell):
        self.model.grid.move_agent(self, cell.pos)
        # prev cell
        prev_cell = self.cell
        self.next_cell = None
        self.cell.leave()
        # current cell
        self.cell = cell
        self.cell.agent = self
        self.cell.winner = None
        if self.tail:
            self.tail.head = None
            prev_cell.advance()
            self.tail = None

    def __repr__(self):
        return self.name + " " + str(self.pos)
