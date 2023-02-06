import mesa
import numpy as np

from .directed import DirectedAgent
from .utils.constants import ORIENTATION, SFF_OBSTACLE, MANEUVERS
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

    def dist(self, start, goal):
        return np.abs(start[0]-goal[0]) + np.abs(start[1]-goal[1])

    def offset_maneuvers(self):
        leader_pos = self.pos
        partner_pos = self.partner.pos
        maneuvers = []
        for move in MANEUVERS[self.orientation]:
            leader_offset, leader_orientation = move[0]
            partner_offset, partner_orientation = move[1]

            leader_move = leader_pos[0]+leader_offset[0], leader_pos[1] + leader_offset[1]
            partner_move = leader_pos[0]+partner_offset[0], leader_pos[1] + partner_offset[1]
            # partner_move = partner_pos[0]+partner_offset[0], partner_pos[1] + partner_offset[1]

            offset_move = (leader_move, leader_orientation), (partner_move, partner_orientation)

            maneuvers.append(offset_move)
        return maneuvers

    def evaluate_maneuvers(self, maneuvers, sff):
        choices = []
        for move in maneuvers:
            leader_position, orientation = move[0]
            partner_position, orientation = move[1]
            leader_sf = sff[leader_position[1], leader_position[0]]
            partner_sf = sff[partner_position[1], partner_position[0]]
            next_move = (leader_sf+partner_sf, leader_position, partner_position, orientation)
            choices.append(next_move)
        return sorted(choices, key=lambda x: x[0])

    def select_cell(self, sff):
        if not self.partner:
            super().select_cell(sff)
            return
        self.head = None
        self.tail = None
        maneuvers = self.offset_maneuvers()
        sorted_maneuvers = self.evaluate_maneuvers(maneuvers, sff)
        sff, coords, p_coords, orientation = sorted_maneuvers[0]
        leader_cell = self.model.grid.grid[coords[0]][coords[1]][0]
        self.next_cell = leader_cell
        leader_cell.enter(self)
        partner_cell = self.model.grid.grid[p_coords[0]][p_coords[1]][0]
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
        orientation = ORIENTATION.NORTH
        sx, sy = self.pos
        px, py = partner.pos
        if sx == px and sy < py:
            orientation = ORIENTATION.NORTH
        if sx > px and sy == py:
            orientation = ORIENTATION.WEST
        if sx == px and sy > py:
            orientation = ORIENTATION.SOUTH
        if sx < px and sy == py:
            orientation = ORIENTATION.EAST
        # NORTH
        # LEADER PARTNER
        # partner is on the right side of leader
        self.orientation = ORIENTATION((len(ORIENTATION) + orientation - 1) % len(ORIENTATION))
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
