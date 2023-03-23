import mesa
import numpy as np

from .utils.portrayal import create_color
from .utils.constants import KS, KO, KD, GAMMA, OCCUPIED_CELL
from .agent import Agent


class LeaderAgent(Agent):
    """Physical solitary leader agent with no orientation. Influences agents in neighbourhood.

    Does not update SFF.

    """
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.color = create_color(self)
        self.name = "Leader: " + str(self.unique_id)
        self.nominal_movement_duration = self.model.leader_movement_duration
        self.movement_duration = self.nominal_movement_duration

    def step(self):
        """Stochastically selects next step based on SFF of current goal."""
        self.reset()
        sff = self.model.sff["Leader"]
        self.select_cell(sff)

    def middle_crowd(self):
        """Position of the middle of the crowd between Virtual leader and most distant agent from him.

        Returns:
            (int, (int, int)): Manhattan distance and xy coordinates of the middle of the crowd.

        """
        distances = []
        virtual_leader_pos = self.model.virtual_leader.pos
        for agent in self.model.schedule.agents:
            # incorrect measure
            d = self.dist(virtual_leader_pos, agent.pos)
            distances.append((d, agent.pos))
        distances = sorted(distances, key=lambda x: x[0], reverse=True)
        median = len(distances) // 2
        return distances[median]

    def most_distant(self):
        """Position of the most distant agent from Virtual leader.

        Most distant agent is on the tail and it can be used as a reference
        to the length of the queue by comparing it to the position
        of virtual leader.

        The value is used to control the speed of Leader and Virtual leader.

        Returns:
            (int, (int, int)): Manhattan distance and xy coordinates of most distant agent.

        """
        distances = []
        occupancy_grid = self.model.of
        virtual_leader_pos = self.model.virtual_leader.pos
        for y, x in np.argwhere(occupancy_grid == OCCUPIED_CELL):
            if (x, y) == self.pos:
                continue
            distances.append((self.dist(virtual_leader_pos, (x, y)), (x, y)))
        distances = sorted(distances, key=lambda dist_pos: dist_pos[0], reverse=True)
        if len(distances) > 0:
            return distances[0]
        else:
            return 0, self.pos

    def adapt_speed(self):
        """Based on the distance to followers (de)accelerate.

        When agent is at the front, he tries to maintain the length
        of the queue to be around num_of_follower / 2.
        When agent is at the back he tries to be very close to the last
        agent.
        """
        self.nominal_movement_duration = 0
        d, pos = self.most_distant()
        if self.model.leader_front_location_switch:
            # at the front
            # length of queue of pairs is approximately half of number of agents
            if d < (len(self.model.schedule.agents) // 2):
                # the queue is short, keep normal speed
                d = 1
            else:
                # the queue is too long, move slower
                d = 2
        else:
            # at the back of the queue
            if d > 5:
                # the most distant agent is too far, increase speed
                d = 0
            else:
                # keep normal speed
                d = 1
        self.movement_duration = round(self.nominal_movement_duration * d)


class VirtualLeader(LeaderAgent):
    """Virtual solitary leader agent with no orientation. Sets the SFF for other agents.

    Updates SFF.

    """
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.name = "Virtual " + self.name
        self.k = {KS: 10,
                  KO: 0,
                  KD: 0,
                  GAMMA: 0}

    def step(self):
        """Stochastically selects next cell based on SFF of current goal.

        Does not physically move on the grid, is not visible and does not occupy any cell.

        """
        self.reset()
        cells = self.model.grid.get_neighborhood(self.pos, include_center=True, moore=True)
        sff = self.model.sff["Virtual leader"]
        attraction = self.attraction(sff, cells)
        coords = self.deterministic_choice(attraction)
        cell = self.model.grid[coords[0]][coords[1]][0]
        self.next_cell = cell
        self.adapt_speed()
        self.tau = max(self.model.schedule.time, self.tau) + self.movement_cost()
        self.pos = cell.pos

    def advance(self):
        """Updates SFF with his position as goal."""
        # self.model.sff_update([self.pos, self.pos], "Follower")

    def adapt_speed(self):
        """Based on the distance to followers (de)accelerate.

        When agent is at the front, he tries to maintain the length
        of the queue to be around num_of_follower / 2.
        When agent is at the back he tries to be very close to the last
        agent.
        """
        d, pos = self.most_distant()

        if d < (len(self.model.schedule.agents) // 2):
            # keep normal speed
            d = 1
        else:
            # half the normal speed = twice the movement duration
            d = 2
        self.movement_duration = round(self.nominal_movement_duration * d)
