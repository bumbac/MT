import mesa
import numpy as np

from .utils.portrayal import create_color
from .utils.constants import SFF_OBSTACLE, KS, KO, KD, GAMMA, OCCUPIED_CELL, EMPTY_CELL
from .utils.algorithms import dist


class Agent(mesa.Agent):
    """Base (abstract) class for physical agent moving on grid.

    Attributes:
        name (str): Human readable name of agent with characterization.
        color (str): HTML Hex code of color.
        head (Agent): Bounded agent to the front.
        tail (Agent): Bounded agent to the back.
        cell (Cell): Cell which is occupied by this agent.
        next_cell (Cell): Cell which agent want to enter in the next step.
        confirm_move (bool): Indicator of confirmed move in the next step.
        moved (bool): Indicator of successful move.
        partner (Agent): Partner agent in case of DirectedPartnerAgent, for other types is None.
        tau (int): Timestep after move.
        movement_duration (int): Duration of a normal move.
        k (dict): Parameters which affect attraction calculation.
    """

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
        self.partner = None
        self.tau = 0
        self.nominal_movement_duration = self.model.agent_movement_duration
        self.movement_duration = int(self.nominal_movement_duration)
        self.penalization_orientation = self.model.penalization_orientation
        self.penalization_cross_obstacle = 0.5
        self.k = {KS: self.model.ks,
                  KO: self.model.ko,
                  KD: self.model.kd,
                  GAMMA: 0.1}

    def __repr__(self):
        return self.name + " " + str(self.pos)

    def debug(self):
        self.model.logger.debug(str(self.unique_id)+str(self.k[KS])+str(self.k[KO])+"MD:"+str(self.movement_duration)
                                +"\tP:"+str(self.penalization_orientation))

    def dist(self, goal, start=None):
        if start is None:
            start = self.pos
        sff = self.model.sff[goal]
        return sff[start[1], start[0]]

    def path_dist(self, goal, start=None):
        """Path distance from start to goal. If start is None, use agent pos.

        Args:
            start Tuple[int,int]: xy coordinates of start position.
            goal Tuple[int,int]: xy coordinates of goal position.

        """
        if start is None:
            start = self.pos
        sff = self.model.sff["Gate"]
        d = sff[start[1], start[0]] - sff[goal[1], goal[0]]
        return abs(d)

    def leader_dist(self, start=None):
        if start is None:
            start = self.pos
        sff = self.model.sff[self.model.leader.pos]
        return sff[start[1], start[0]]

    def reset(self):
        """Reset state variables of the agent."""
        # self.debug()
        self.head = None
        self.tail = None
        self.confirm_move = False
        self.next_cell = None
        self.moved = False

    def select_cell(self, sff):
        """Stochastically select cell to enter in the next step based on SFF.

        Agent enters the competition for the cell.

        Args:
            sff np.array(height, width):  Array of float static field values.

        """
        cells = self.model.grid.get_neighborhood(self.pos, moore=True, include_center=True)
        attraction = self.attraction(sff, cells)
        coords = self.stochastic_choice(attraction)
        cell = self.model.grid[coords[0]][coords[1]][0]
        self.next_cell = cell
        cell.enter(self)
        return cell

    def attraction(self, sff, cells):
        """Calculate attraction of each position in cells based on sff etc.

        Args:
            sff (object):  np.array(height, width) of float static field values.
            cells (list): xy coordinates for next moves.

        Returns:
            dict: xy coordinates(key) and attraction(value).

        """
        ks = self.k[KS]
        ko = self.k[KO]
        kd = self.k[KD]
        discipline = 1

        # discipline calculation based on distance to leader
        distance_to_leader = self.leader_dist()
        if self.name.startswith("Follower") and distance_to_leader > 0:
            discipline += 1 / distance_to_leader
        # mixing P_s and P_o based od ko sensitivity
        P_s = {'top': {}, 'bottom_sum': 0}
        attraction_static = {}
        P_o = {'top': {}, 'bottom_sum': 0}
        attraction_static_occupancy = {}
        # results
        attraction_final = {}

        offset_sff_neighbourhood = np.full(shape=(5, 5), fill_value=float("inf"))
        for pos in cells:
            offset_cell = pos[1] - self.pos[1] + 2, pos[0] - self.pos[0] + 2
            offset_sff_neighbourhood[offset_cell] = sff[pos[1], pos[0]]
        offset_sff_neighbourhood -= offset_sff_neighbourhood[2,2]
        for pos in cells:
            offset_cell = pos[1] - self.pos[1] + 2, pos[0] - self.pos[0] + 2
            S = offset_sff_neighbourhood[offset_cell]
            ks = self.k[KS] * discipline
            # self.model.logger.debug(str(discipline)+str(distance_to_leader)+str(S)+str(ks)+str(self.k[KS]))
            # O is 0 or 1
            Occupy = 0
            if self.model.of[pos[1], pos[0]] == OCCUPIED_CELL:
                Occupy = 1
            # D is 0 or 1
            D = int(self.is_diagonal(pos))
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
        """Pick xy coordinates stochastically based on probability in attraction.

        Args:
            attraction (dict): xy coordinates(key): attraction(value)

        Returns:
            (int, int): xy coordinates

        """
        coords = list(attraction.keys())
        probabilities = list(attraction.values())
        norm = sum(probabilities)
        if norm == 0 or norm == np.inf or norm == -np.inf or np.isnan(norm):
            if self.partner:
                return (self.pos, self.orientation), (self.partner.pos, self.orientation)
            else:
                return self.pos
        probabilities = probabilities / norm
        idx = np.random.choice(len(coords), p=probabilities)

        return coords[idx]

    def deterministic_choice(self, attraction):
        coords = list(attraction.keys())
        probabilities = list(attraction.values())
        norm = sum(probabilities)
        if norm == 0 or norm == np.inf or norm == -np.inf or np.isnan(norm):
            return self.pos
        choices = [(coords[i], probabilities[i]) for i in range(len(attraction))]
        choices = sorted(choices, key=lambda x: x[1], reverse=True)
        top_coords, top_prob = choices[0]
        return top_coords

    def advance(self):
        """Test if agent will move to next cell in the next step and update states.

        If agent cant move, he propagates to bounded agents behind that he will not
        move from his cell.
        Agent adapts speed based on surroundings

        """
        if self.next_cell is not None:
            if self.next_cell.winner == self:
                self.confirm_move = True
                self.adapt_speed()
            else:
                self.bubbledown()
        else:
            self.bubbledown()

    def bubbledown(self):
        """Reset states because of unsuccessful move in the next step.

        Propagate the same to bounded agents behind.

        """
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
        """Move agent to next cell and updates states, move bounded agents behind.

        Agent updates timestep with duration of the move.

        """
        cell = self.next_cell
        self.tau = max(self.model.schedule.time, self.tau) + self.movement_cost()
        self.model.grid.move_agent(self, cell.pos)
        self.model.of[cell.pos[1], cell.pos[0]] = OCCUPIED_CELL
        # prev cell
        prev_cell = self.cell
        self.cell.leave()
        self.model.of[self.cell.pos[1], self.cell.pos[0]] = EMPTY_CELL
        # current cell
        self.cell = cell
        self.next_cell = None
        self.cell.agent = self
        self.cell.winner = None
        if self.tail is not None:
            self.tail.head = None
            self.tail.move()
            self.tail = None
        # evacuation is in the moment of entrance so it is different from self.cell.leave()
        self.cell.evacuate()
        return prev_cell

    def movement_cost(self):
        """Duration or cost of the movement in timesteps.

        Returns:
            int: Duration in timesteps.

        """
        distance = 0
        if self.next_cell:
            distance = dist(self.pos, self.next_cell.pos)
        if distance == 0:
            return 0
        # diagonal movements have same value as normal values
        if distance < 3:
            return self.movement_duration
        # special maneuvers have double duration compared to normal
        if distance == 3:
            return 2 * self.movement_duration

    def adapt_speed(self):
        """Based on the surroundings and state (de)accelerate agent.

        Agents with empty cell in front and close to the leader
        increase speed.

        """
        d = self.leader_dist()
        self.movement_duration = self.nominal_movement_duration
        if self.next_cell is not None and d > 0:
            if self.next_cell.agent is None:
                self.movement_duration = round(self.nominal_movement_duration - self.movement_duration * 1/d)

    def allow_entrance(self):
        """Indicator of agent allowed to move in timestep.

        Schedule runs in 2 ticks per update. Agents with tau lower
        than timestep are allowed to move.

        Returns:
            bool: Agent can move in the next timestep.

        """
        if self.tau <= self.model.schedule.time:
            if self.partner is not None:
                if self.partner.tau > self.model.schedule.time:
                    return False
            return True
        else:
            return False

    def cross_obstacle(self, pos):
        """Indicator of crossing obstacle.

        Args:
            pos (int,int): xy coordinates of position to check.

        Returns:
            bool: Agent crosses obstacle.

        """
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
        """Indicator of diagonal movement. Can be outside Moore neighbourhood.

        Args:
            pos (int,int): xy coordinates of position to check.
            agent_pos (int,int): xy coordinates of starting position. If none, self.pos is used.

        Returns:
              bool: Movement to pos is diagonal.

        """
        if agent_pos is None:
            agent_pos = self.pos
        return (agent_pos[0] != pos[0]) and (agent_pos[1] != pos[1])

    def update_color(self, value):
        """ Assign HTML Hex color code for agent.

        Args:
            value (Float): Float or other type which affects color e.g. the SFF of cell.

        """
        self.color = create_color(self)
