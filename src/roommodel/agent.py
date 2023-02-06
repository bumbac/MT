import mesa
import numpy as np

from .utils.portrayal import create_color
from .utils.constants import SFF_OBSTACLE


class Agent(mesa.Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.name = str(uid)
        self.color = create_color(self)
        self.partner = None
        self.head = None
        self.tail = None
        self.cell = None
        self.next_cell = None

    def cross_obstacle(self, pos):
        # non diagonal movement
        if not self.is_diagonal(pos):
            return False
        corners = []
        if self.pos[0] < pos[0]:
            corners.append((self.pos[0] + 1, self.pos[1]))
        else:
            corners.append((self.pos[0] - 1, self.pos[1]))

        if self.pos[1] < pos[1]:
            corners.append((self.pos[0], self.pos[1] + 1))
        else:
            corners.append((self.pos[0], self.pos[1] - 1))

        for x, y in corners:
            if self.model.sff["Follower"][y][x] == SFF_OBSTACLE:
                return True
        return False

    def select_cell(self, sff):
        self.head = None
        self.tail = None
        values = []
        c = []
        for coords in self.model.grid.get_neighborhood(self.pos, moore=True):
            if sff[coords[1], coords[0]] == SFF_OBSTACLE:
                continue
            if self.cross_obstacle(coords):
                continue
            static_value = sff[coords[1], coords[0]]
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

    def move(self, cell) -> None:
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
        self.cell.evacuate()

    def is_diagonal(self, pos, agent_pos=None):
        if agent_pos is None:
            agent_pos = self.pos
        return (agent_pos[0] != pos[0]) and (agent_pos[1] != pos[1])

    def __repr__(self):
        return self.name + " " + str(self.pos)
