import mesa
import numpy as np

from .directed import DirectedAgent
from .utils.constants import ORIENTATION
from .utils.portrayal import create_color


class DirectedPartnerAgent(DirectedAgent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.partner = None
        self.name = "Follower Pair: " + self.name
        self.leader = True

    def step(self) -> None:
        # agent is partner
        if not self.leader:
            return
        # agent is single
        if not self.partner:
            super().step()
        sff = self.model.sff["Follower"]
        self.select_cell(sff)

    def test_enter(self):
        # leader and partner will both enter desired cell
        if self.partner.next_cell.winner == self.partner:
            self.model.schedule.add_cell(self.partner.next_cell)
            return
        # leader can enter, partner not, cancel leader winner
        else:
            self.cell.winner = None
            self.next_cell = None
            self.partner.next_cell = None
            return

    def inform(self):
        if self.partner:
            if self.partner.next_cell:
                if self.partner.next_cell.winner:
                    self.test_enter()
                else:
                    self.partner.next_cell.step()
                    self.test_enter()
        return

    def select_cell(self, sff):
        values = []
        c = []
        for coords in self.model.grid.get_neighborhood(self.pos, moore=True):
            p_coords = self.partner_coords(leader=coords, np_coords=False)
            cell = self.model.grid[p_coords[0]][p_coords[1]][0]
            if cell.agent:
                continue
            leader_sf = sff[coords[1], coords[0]]
            partner_sf = sff[p_coords]
            # todo maybe problematic
            values.append((leader_sf + partner_sf) / 2)
            c.append(coords)
        choice = np.argmin(values)
        coords = c[choice]
        leader_cell = self.model.grid[coords[0]][coords[1]][0]
        self.next_cell = leader_cell
        leader_cell.enter(self)
        p_coords = self.partner_coords(leader=coords, np_coords=False)
        partner_cell = self.model.grid[p_coords[0]][p_coords[1]][0]
        self.partner.next_cell = partner_cell
        partner_cell.enter(self.partner)
        return leader_cell, partner_cell

    def move(self, cell):
        if not self.leader:
            if self.partner.next_cell:
                super().move(cell)
            return
        if not self.partner:
            super().move(cell)
            return
        p_cell = self.partner.next_cell
        if not p_cell:
            return
        else:
            if p_cell.winner != self.partner:
                return
            else:
                p_cell.advance()
        super().move(cell)

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
            position = ORIENTATION.EAST
        if sx == px and sy > py:
            position = ORIENTATION.SOUTH
        if sx < px and sy == py:
            position = ORIENTATION.WEST
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
            coords = leader[0], leader[1] + 1
        if self.orientation == ORIENTATION.WEST:
            coords = leader[0], leader[1] - 1
        if np_coords:
            return coords[1], coords[0]
        return coords