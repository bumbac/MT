import mesa
import numpy as np

from .directed import DirectedAgent
from .utils.constants import ORIENTATION, MANEUVERS, KO
from .utils.portrayal import create_color


class DirectedPartnerAgent(DirectedAgent):
    def __init__(self, uid: int, model: mesa.Model):
        super().__init__(uid, model)
        self.name = "Follower Pair: " + self.name
        self.leader = True
        self.k[KO] = 0.1

    def step(self) -> None:
        self.leader = self.update_leader()
        if not self.leader:
            return
        if not self.partner:
            super().step()
            return
        self.reset()
        self.partner.reset()
        sff = self.model.sff["Follower"]
        return self.select_cell(sff)

    def move(self):
        # if self.finished_move:
        #     return None
        if self.partner is None:
            # move as single agent
            return super().move()

        if not self.partner.confirm_move:
            # partner agent did not win
            self.confirm_move = False
            if self.next_cell:
                self.next_cell.winner = None
            self.next_cell = None
            return None

        self.moved = True
        if not self.partner.moved:
            # attempt to move partner
            self.partner.next_cell.advance()
        if self.partner.moved:
            # if attempt was successful
            # or partner attempts to move me
            # definitive move
            return super().move()
        else:
            # one of the two can't move
            self.confirm_move = False
            self.moved = False
            if self.next_cell:
                self.next_cell.winner = None
            self.next_cell = None
            return None

    def select_cell(self, sff):
        if not self.partner:
            raise ValueError("Calculating partner position with no partner.")
        maneuvers = self.offset_maneuvers()
        cells = [[], []]
        for leader, partner in maneuvers:
            cells[0].append(leader[0])
            cells[1].append(partner[0])
        leader_attraction = self.attraction(sff, cells[0])
        partner_attraction = self.partner.attraction(sff, cells[1])
        attraction = {}
        for leader, partner in maneuvers:
            coords, _ = leader
            p_coords, _ = partner
            if leader_attraction[coords] == 0 or partner_attraction[p_coords] == 0:
                attraction[(leader, partner)] = 0
            else:
                attraction[(leader, partner)] = leader_attraction[coords] + partner_attraction[p_coords]

        normalize = sum(attraction.values())
        for key in attraction:
            attraction[key] /= normalize
        leader, partner = self.stochastic_choice(attraction)
        coords, orientation = leader
        p_coords, p_orientation = partner
        leader_cell = self.model.grid.grid[coords[0]][coords[1]][0]
        self.next_cell = leader_cell
        self.next_orientation = orientation
        leader_cell.enter(self)
        partner_cell = self.model.grid.grid[p_coords[0]][p_coords[1]][0]
        self.partner.next_cell = partner_cell
        self.partner.next_orientation = p_orientation
        partner_cell.enter(self.partner)
        print(self.pos, leader_cell.pos, self.next_orientation, self.model.schedule.epochs)
        print(self.partner.pos, partner_cell.pos, self.partner.next_orientation)
        return leader_cell, partner_cell

    def dist(self, start, goal):
        return np.abs(start[0] - goal[0]) + np.abs(start[1] - goal[1])

    def maneuver_out_of_bounds(self, maneuver):
        width, height = self.model.dimensions
        x, y = maneuver
        if 0 <= x < width and 0 <= y < height:
            return False
        return True

    def offset_maneuvers(self):
        leader_pos = self.pos
        maneuvers = []
        for move in MANEUVERS[self.orientation]:
            leader_offset, leader_orientation = move[0]
            partner_offset, partner_orientation = move[1]

            leader_move = leader_pos[0] + leader_offset[0], leader_pos[1] + leader_offset[1]
            partner_move = leader_pos[0] + partner_offset[0], leader_pos[1] + partner_offset[1]
            if self.maneuver_out_of_bounds(leader_move) or self.maneuver_out_of_bounds(partner_move):
                continue
            offset_move = (leader_move, leader_orientation), (partner_move, partner_orientation)

            maneuvers.append(offset_move)
        return maneuvers

    def update_leader(self):
        if not self.partner:
            return True
        if self.partner.pos == self.partner_coords():
            self.partner.leader = False
            return True
        if self.pos == self.partner.partner_coords():
            self.partner.leader = True
            return False
        raise ValueError("Leader error, partner is incompatible.")

    def add_partner(self, partner):
        if self.partner:
            raise ValueError("Partner already assigned.")
        if not partner:
            raise ValueError("Assigned partner is None.")
        distance = self.dist(self.pos, partner.pos)
        if distance > 1:
            raise ValueError("Partner is too far to assign.")

        self.partner = partner
        partner.partner = self
        self.leader = self.update_leader()
        self.partner.leader = self.partner.update_leader()
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

    def partner_coords(self, leader=None):
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
        return coords
