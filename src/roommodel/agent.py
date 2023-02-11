import mesa
import numpy as np

from .utils.portrayal import create_color
from .utils.constants import SFF_OBSTACLE, KS, KO, KD, GAMMA, OCCUPIED, EMPTY


class Agent(mesa.Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.name = str(uid)
        self.color = create_color(self)
        self.head = None
        self.tail = None
        self.cell = None
        self.next_cell = None
        self.confirm_move = False
        self.moved = False
        self.finished_move = False
        self.partner = None
        self.k = {KS: 30,
                  KO: 0.5,
                  KD: 0.5,
                  GAMMA: 0.1}

    def __repr__(self):
        return self.name + " " + str(self.pos)

    def update_color(self, value):
        self.color = create_color(self)

    def reset(self):
        self.head = None
        self.tail = None
        self.confirm_move = False
        self.next_cell = None
        self.finished_move = False
        self.moved = False

    def select_cell(self, sff):
        cells = self.model.grid.get_neighborhood(self.pos, moore=True)
        attraction = self.attraction(sff, cells)
        coords = self.stochastic_choice(attraction)
        cell = self.model.grid[coords[0]][coords[1]][0]
        self.next_cell = cell
        cell.enter(self)
        return cell

    def advance(self):
        if self.next_cell is not None:
            if self.next_cell.winner == self:
                self.confirm_move = True
            else:
                self.bubbledown()
        else:
            self.bubbledown()

    def bubbledown(self):
        if self.next_cell is not None:
            if self.next_cell.winner == self:
                self.next_cell.winner = None
            self.next_cell = None
        self.confirm_move = None
        if self.partner is not None:
            if self.partner.next_cell is not None:
                self.partner.bubbledown()
        if self.head:
            self.head.tail = None
            self.head = None
        if self.tail is not None:
            self.tail.bubbledown()

    def move(self):
        cell = self.next_cell
        self.model.grid.move_agent(self, cell.pos)
        self.model.of[cell.pos[1], cell.pos[0]] = OCCUPIED
        # prev cell
        prev_cell = self.cell
        self.cell.leave()
        self.model.of[self.cell.pos[1], self.cell.pos[0]] = EMPTY
        # current cell
        self.cell = cell
        self.next_cell = None
        self.cell.agent = self
        self.cell.winner = None
        if self.tail is not None:
            self.tail.head = None
            self.tail.move()
            self.tail = None
        self.cell.evacuate()
        self.finished_move = True
        return prev_cell

    def attraction(self, sff, cells):
        """
        Calculate attraction of each position of cells in :param cells based on static field, occupancy,
        diagonal movement, etc.
        :param sff: np.array(height, width) of static field values
        :param cells: list of xy coordinates for next moves
        :return: Dictionary of coordinates(key): attraction(value)
        """
        ks = self.k[KS]
        ko = self.k[KO]
        kd = self.k[KD]

        # mixing P_s and P_o based od ko sensitivity
        P_s = {'top': {}, 'bottom_sum': 0}
        attraction_static = {}
        P_o = {'top': {}, 'bottom_sum': 0}
        attraction_static_occupancy = {}
        # results
        attraction_final = {}
        for pos in cells:
            # S belongs to [0, 1]
            S = sff[pos[1], pos[0]]
            # O is 0 or 1
            Occupy = 0
            if len(self.model.grid.grid[pos[0]][pos[1]]) > 1:
                Occupy = 1
            # D is 0 or 1
            D = self.is_diagonal(pos)
            # notice the missing occupancy factor (ko and Occupy)
            P_s['top'][pos] = np.exp((-ks) * S) * (1 - kd * D)
            P_s['bottom_sum'] += P_s['top'][pos]
            # notice the missing ko parameter
            P_o['top'][pos] = np.exp((-ks) * S) * (1 - Occupy) * (1 - kd * D)
            P_o['bottom_sum'] += P_o['top'][pos]

        for pos in cells:
            attraction_static[pos] = P_s['top'][pos] / P_s['bottom_sum']
            if P_o['bottom_sum'] == 0:
                attraction_static_occupancy[pos] = 0
            else:
                attraction_static_occupancy[pos] = P_o['top'][pos] / P_o['bottom_sum']

        # normalize
        for pos in cells:
            attraction_final[pos] = ko * attraction_static_occupancy[pos] + (1 - ko) * attraction_static[pos]
        return attraction_final

    def stochastic_choice(self, attraction):
        coords = list(attraction.keys())
        probabilities = list(attraction.values())
        idx = np.random.choice(len(coords), p=probabilities)
        return coords[idx]

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

    def is_diagonal(self, pos, agent_pos=None):
        if agent_pos is None:
            agent_pos = self.pos
        return (agent_pos[0] != pos[0]) and (agent_pos[1] != pos[1])
