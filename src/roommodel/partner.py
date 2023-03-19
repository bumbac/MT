import mesa
import numpy as np

from .directed import DirectedAgent
from .utils.constants import ORIENTATION, MANEUVERS, KO, KS
from .utils.portrayal import create_color
from .utils.algorithms import dist


class DirectedPartnerAgent(DirectedAgent):
    """Paired agent with orientation. Can be solitary when partner evacuates.

    Attributes:
        leader (bool): Indicator of agent being in charge of all processes.
    """
    def __init__(self, uid, model, ):
        super().__init__(uid, model)
        self.name = "Follower Pair: " + self.name
        self.leader = True

    def step(self):
        """Leader stochastically selects next step for both agents. Updates leadership based on position in pair,
         partner does nothing."""
        self.leader = self.update_leader()
        if not self.leader:
            return
        if not self.partner:
            super().step()
            return
        self.reset()
        self.partner.reset()
        sff = self.model.sff["Follower"]
        self.select_cell(sff)

    def select_cell(self, sff):
        """Stochastically select maneuver for both agents in pair to execute.

        Solitary agent selects cell using DirectedAgent method.

        Args:
            sff np.array(height, width):  Array of float static field values.

        """
        if not self.partner:
            return super().select_cell(sff)
        # cells are empty because attraction method inserts positions from maneuvers
        cells = [[], []]
        attraction = self.attraction(sff, cells)
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
        return leader_cell, partner_cell

    def attraction(self, sff, cells):
        """Calculate attraction of each maneuvers with penalisation.

        Solitary agent uses DirectedAgent method.

        Args:
            sff (object):  np.array(height, width) of float static field values.
            cells (list): Empty list, positions will be inserted from maneuvers.

        Returns:
            dict: (leader:((int, int), ORIENTATION), partner)(key) and attraction(value).

        """
        if self.partner is None:
            return super().attraction(sff, cells)
        # Calculate real coordinates from maneuver offset
        maneuvers = self.offset_maneuvers()
        for leader, partner in maneuvers:
            cells[0].append(leader[0])
            cells[1].append(partner[0])
        # discipline is already included
        leader_attraction = super(DirectedPartnerAgent, self).attraction(sff, cells[0])
        partner_attraction = super(DirectedPartnerAgent, self.partner).attraction(sff, cells[1])
        attraction = {}
        for leader, partner in maneuvers:
            coords, _ = leader
            p_coords, _ = partner
            penalization = 0
            # cross obstacle penalization
            if self.cross_obstacle(leader[0]) \
                    or self.partner.cross_obstacle(partner[0]):
                penalization = self.penalization_cross_obstacle
            # if any agent has zero attraction that movement is forbidden
            if leader_attraction[coords] == 0 or partner_attraction[p_coords] == 0:
                attraction[(leader, partner)] = 0
            else:
                attraction[(leader, partner)] = (1-penalization) * (leader_attraction[coords] + partner_attraction[p_coords])

        # calculating correct orientation in next move
        top_maneuver = (float("-inf"), None)
        for key in attraction:
            if attraction[key] > top_maneuver[0]:
                top_maneuver = (attraction[key], key)
        _, top_key = top_maneuver
        top_orientation = top_key[0][1]
        # orientation penalisation
        penalization = {}
        for key in attraction:
            _, next_orientation = key[0]
            if next_orientation == top_orientation:
                penalization[key] = 0
            else:
                distance_to_leader = min(self.path_dist(self.pos, self.model.leader.pos),
                                         self.partner.path_dist(self.partner.pos, self.model.leader.pos))
                if distance_to_leader > 0:
                    penalization[key] = (1 - (1/distance_to_leader)**2) * self.penalization_orientation
        # apply penalization to each maneuver
        for key in penalization:
            attraction[key] = attraction[key] * (1 - penalization[key])
        # normalize to make probability
        normalize = sum(attraction.values())
        for key in attraction:
                attraction[key] /= normalize
        return attraction

    def maneuver_out_of_bounds(self, maneuver):
        """Indicator of maneuver resulting in position outside dimensions of the room.

        Args:
            maneuver (int, int): xy coordinates of the position.

        Returns:
            bool: Maneuver is out of dimensions of the room.

        """
        width, height = self.model.dimensions
        x, y = maneuver
        if 0 <= x < width and 0 <= y < height:
            return False
        return True

    def offset_maneuvers(self):
        """Calculates real coordinates of maneuver from maneuver offset of leader and partner.

        Returns:
            list: (leader_xy, leader_orientation), (partner_xy, partner_orientation)

        """
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
        """Update leadership in the pair based on the positions and orientation."""
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
        """Add a partner to form directed agent pair. Updates states, leadership, orientation.

        Args:
            partner (object): DirectedPartnerAgent to be paired with.

        """
        if self.partner:
            raise ValueError("Partner already assigned.")
        if not partner:
            raise ValueError("Assigned partner is None.")
        distance = dist(self.pos, partner.pos)
        if distance > 1:
            raise ValueError("Partner is too far to assign.")

        self.partner = partner
        partner.partner = self
        self.leader = self.update_leader()
        self.partner.leader = self.partner.update_leader()
        self.name = "Follower Pair: " + str(self.unique_id) + " " + str(partner.unique_id)
        partner.name = "Follower Pair: " + str(partner.unique_id) + " " + str(self.unique_id)
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

    def remove_partner(self):
        """Split the pair and update states and leadership. Used in evacuation."""
        if not self.partner:
            raise ValueError("No partner to remove.")
        self.partner = None
        self.leader = True
        self.name = "Follower Pair: " + str(self.unique_id)
        self.color = create_color(self)

    def partner_coords(self, leader=None):
        """Calculate position of partner of this agent perspective and orientation as a leader.

        Args:
            leader (int, int): xy coordinates of the leader.

        Returns:
            (int, int): xy coordinates of supposed partner.

        """
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
