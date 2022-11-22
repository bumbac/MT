import mesa
import numpy as np

from .follower import FollowerAgent
from .utils.constants import PAIR_DISTANCE_THRESHOLD


class PartnerAgent(FollowerAgent):
    def __init__(self, uid, model, partner):
        super().__init__(uid, model)
        self.partner = partner
        self.name = "Pair: " + self.name + self.partner.name

    def distance(self, cell=None):
        if not cell:
            cell = self.partner.pos
        return np.linalg.norm(self.pos - cell)

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
        return cell

    def step(self):
        sff = self.model.sff["Follower"]
        cell = self.select_cell(sff)
        if self.partner.distance(cell.pos) <= PAIR_DISTANCE_THRESHOLD:
            cell.enter(self)

    def move(self, cell):
        self.model.grid.move_agent(self, cell.pos)
        # prev cell
        self.cell.leave()
        # current cell
        self.cell = cell
        if self.tail:
            self.tail.head = None
            self.tail.cell.advance()
            self.tail = None
