import mesa
import numpy as np

from .directed import DirectedAgent
from .utils.constants import ORIENTATION
from .utils.portrayal import create_color


class DirectedPartnerAgent(DirectedAgent):
    def __init__(self, uid: int, model: mesa.Model):
        super().__init__(uid, model)
        self.name = "Follower Pair: " + self.name
        self.leader = True
        self.confirm_move = False
        self.moved = False

    def step(self) -> None:
        self.confirm_move = False
        self.moved = False
        if not self.leader:
            return
        if not self.partner:
            super().step()
        sff = self.model.sff["Follower"]
        self.select_cell(sff)

    def advance(self) -> None:
        if self.next_cell.winner == self:
            self.confirm_move = True

    def move(self, cell) -> None:
        # executes only when cell is empty
        if not self.partner:
            super().move(cell)
            return

        if self.leader:
            if self.partner.confirm_move:
                self.moved = True
                self.partner.next_cell.advance()
                if self.partner.moved:
                    super().move(cell)
                    return
                else:
                    self.next_cell = None
                    self.confirm_move = False
                    self.moved = False
                    return
            else:
                self.confirm_move = False
                self.next_cell = None
                return
        else:
            # partner
            if self.partner.moved:
                super().move(cell)
                self.moved = True
                return

    def stride(self, coords, p_coords):
        if self.partner.cross_obstacle(p_coords):
            pass
        if self.cross_obstacle(coords):
            pass

    def left(self):
        if self.orientation == ORIENTATION.NORTH:
            return self.pos[0] - 1, self.pos[1]
        if self.orientation == ORIENTATION.SOUTH:
            return self.pos[0] + 1, self.pos[1]
        if self.orientation == ORIENTATION.WEST:
            return self.pos[0], self.pos[1] - 1
        if self.orientation == ORIENTATION.EAST:
            return self.pos[0], self.pos[1] + 1

    def right(self):
        if self.orientation == ORIENTATION.NORTH:
            return self.pos[0] + 1, self.pos[1]
        if self.orientation == ORIENTATION.SOUTH:
            return self.pos[0] - 1, self.pos[1]
        if self.orientation == ORIENTATION.WEST:
            return self.pos[0], self.pos[1] + 1
        if self.orientation == ORIENTATION.EAST:
            return self.pos[0], self.pos[1] - 1

    def select_cell(self, sff):
        if not self.partner:
            super().select_cell(sff)
            return
        self.head = None
        self.tail = None
        values = []
        c = []
        extended_neighbourhood = \
            list(set(self.model.grid.get_neighborhood(self.pos, moore=True))
                 | set((self.model.grid.get_neighborhood(self.partner.pos, moore=True))))

        extended_neighbourhood = self.model.grid.get_neighborhood(self.pos, moore=True)
        for coords in extended_neighbourhood:
            if sff[coords[1], coords[0]] == np.inf:
                continue
            p_coords = self.next_partner_coords(cell=coords, np_coords=False)
            if sff[p_coords[1], p_coords[0]] == np.inf:
                continue
            if self.partner.cross_obstacle(p_coords) and self.cross_obstacle(coords):
                continue
            if self.partner.cross_obstacle(p_coords):
                p_coords = self.pos
                coords = self.left()
            elif self.cross_obstacle(coords):
                coords = self.partner.pos
                p_coords = self.partner.right()
            if sff[coords[1], coords[0]] == np.inf:
                continue
            if sff[p_coords[1], p_coords[0]] == np.inf:
                continue

            leader_sf = sff[coords[1], coords[0]]
            partner_sf = sff[p_coords[1], p_coords[0]]
            values.append((leader_sf + partner_sf) / 2)
            c.append((coords, p_coords))
        if len(values) == 0:
            return None
        choice = np.argmin(values)
        coords, p_coords = c[choice]
        leader_cell = self.model.grid[coords[0]][coords[1]][0]
        self.next_cell = leader_cell
        leader_cell.enter(self)
        partner_cell = self.model.grid[p_coords[0]][p_coords[1]][0]
        self.partner.next_cell = partner_cell
        partner_cell.enter(self.partner)
        return leader_cell, partner_cell

    def add_partner(self, partner):
        if self.partner:
            raise ValueError("Partner already assigned.")
        distance = np.linalg.norm(np.array(self.pos) - np.array(partner.pos))
        if distance > 1:
            raise ValueError("Partner is too far to assign.")

        self.partner = partner
        partner.partner = self
        self.leader = True
        self.partner.leader = False
        self.name = self.name + " " + str(partner.unique_id)
        partner.name = partner.name + " " + str(self.unique_id)
        self.color = create_color(self)
        partner.color = self.color
        position = ORIENTATION.NORTH
        sx, sy = self.pos
        px, py = partner.pos
        if sx == px and sy < py:
            position = ORIENTATION.NORTH
        if sx > px and sy == py:
            position = ORIENTATION.WEST
        if sx == px and sy > py:
            position = ORIENTATION.SOUTH
        if sx < px and sy == py:
            position = ORIENTATION.EAST
        # NORTH
        # LEADER PARTNER
        # partner is on the right side of leader
        self.orientation = ORIENTATION((len(ORIENTATION) + position - 1) % len(ORIENTATION))
        partner.orientation = self.orientation

    def partner_coords(self, leader=None, np_coords=True):
        coords = None
        if not leader:
            leader = self.pos
        if self.orientation == ORIENTATION.NORTH:
            coords = leader[0] + 1, leader[1]
        if self.orientation == ORIENTATION.SOUTH:
            coords = leader[0] - 1, leader[1]
        if self.orientation == ORIENTATION.EAST:
            coords = leader[0], leader[1] - 1
        if self.orientation == ORIENTATION.WEST:
            coords = leader[0], leader[1] + 1
        if np_coords:
            return coords[1], coords[0]
        return coords

    def next_partner_coords(self, cell=None, np_coords=True):
        coords = None
        # orientation of leader in pair for next move
        orientation = self.calculate_orientation(cell)
        if orientation == ORIENTATION.NORTH:
            coords = cell[0] + 1, cell[1]
        if orientation == ORIENTATION.SOUTH:
            coords = cell[0] - 1, cell[1]
        if orientation == ORIENTATION.EAST:
            coords = cell[0], cell[1] - 1
        if orientation == ORIENTATION.WEST:
            coords = cell[0], cell[1] + 1
        if np_coords:
            return coords[1], coords[0]
        return coords
