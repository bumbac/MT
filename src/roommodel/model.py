import copy

import numpy as np
import mesa

from .goal import Goal
from .scheduler import SequentialActivation
from .file_loader import FileLoader
from .utils.room import normalize_grid
from .utils.constants import AREA_STATIC_BOOSTER, OCCUPIED_CELL, ORIENTATION
from .utils.algorithms import pair_positions
from .partner import DirectedPartnerAgent


class RoomModel(mesa.Model):
    """Room and one crowd simulation class which orchestrates all processes.

    Attributes:
        file_loader (object): Loads topology, SFF, goals from file and places agents and cells.
        dimensions (int, int): Width, height dimensions of the room.
        schedule (object): Scheduler for agents and movement in cells.
        grid (object): Rectangular grid of positions where agents and cells are located.
        gate (int, int): xy coordinates of the gate.
        room (object): np.array(height, width) floats that defines topology - walls, obstacles.
        sff (object): np.array(height, width) floats of SFF values in the room.
        of (object): np.array(height, width) floats of occupancy of cells in the room.
        cell_gate (object): Cell which is in the position of the gate.
        agent_positions (list): xy coordinates of all initial agent positions.
        leader (object): LeaderAgent object is physical leader moving and locally influencing agents.
        virtual_leader (object): VirtualLeaderAgent object is non-physical leader that updates SFF for navigation based
        on current goals.

    """
    def __init__(self, filename):
        super().__init__()
        self.file_loader = FileLoader(filename)
        self.dimensions = self.file_loader.dimensions()
        self.schedule = SequentialActivation(self)
        self.grid = mesa.space.MultiGrid(*self.dimensions, torus=False)
        self.gate = self.file_loader.get_gate()
        self.room = self.file_loader.get_room()
        self.goals = self.file_loader.get_goals(self)
        self.sff = self.file_loader.get_sff()
        self.of = self.file_loader.get_room()
        self.uid_ctr = 0
        self.n_evacuated_followers = 0
        self.n_evacuated_leaders = 0
        self.cell_gate = self.file_loader.place_cells(self)
        self.agent_positions = self.file_loader.place_agents(self)
        self.leader, self.virtual_leader = self.file_loader.get_leader()
        # update OF and update internal states of agents
        self.initialize_agents()

    def initialize_agents(self):
        """Update OF and update internal states of agents."""
        for a in self.schedule.agent_buffer():
            cell = a.cell
            if cell is None:
                continue
            cell.agent = a
            self.grid.move_agent(a, cell.pos)
            self.of[cell.pos[1], cell.pos[0]] = OCCUPIED_CELL

    def form_pairs(self):
        """Solves the pairing of DirectedAgents and replaces the objects in the schedule."""
        # occupancy grid for solitary DirectedAgents
        grid = np.zeros(shape=self.dimensions)
        for agent in self.schedule.agents:
            if agent.partner is None and agent.name.startswith("Follower"):
                grid[agent.pos] = OCCUPIED_CELL
        # solve the problem by iteratively decrementing highest vertex degrees until solution
        positions = pair_positions(grid)
        for position in positions:
            # positions of a pair
            leader_position, partner_position = position

            # find original solitary agents
            leader_cell = self.grid.grid[leader_position[0]][leader_position[1]][0]
            leader_agent = leader_cell.agent
            partner_cell = self.grid.grid[partner_position[0]][partner_position[1]][0]
            partner_agent = partner_cell.agent

            leader = DirectedPartnerAgent(leader_agent.unique_id, self)
            partner = DirectedPartnerAgent(partner_agent.unique_id, self)

            # replace agents in schedule, in grid, update internal states
            self.replace_agent(leader_agent, leader)
            self.replace_agent(partner_agent, partner)

            # find which of the 4 orientations fits their position
            for orientation in ORIENTATION:
                leader.orientation = orientation
                if leader.partner_coords() == partner_position:
                    partner.orientation = orientation
                    break

            leader.add_partner(partner)

    def replace_agent(self, agent, new_agent):
        """Replaces solitary agent with paired agent in the schedule, in the grid and update internal states."""
        agent_position = agent.pos
        agent_cell = self.grid.grid[agent_position[0]][agent_position[1]][0]
        if agent:
            self.grid.remove_agent(agent)
            self.schedule.remove_agent(agent)
        if new_agent:
            self.schedule.add(new_agent)
            agent_cell.agent = new_agent
            new_agent.cell = agent_cell
            self.grid.place_agent(new_agent, agent_position)

    def step(self):
        """Execute one model step."""
        print("-----------")
        # always pair solitary agents if found
        self.form_pairs()

        # check current goals
        if self.current_goal().reached_checkpoint():
            # update for new goal
            if self.checkpoint():
                self.sff_update(self.current_goal().area, "Leader")
        if self.running:
            self.schedule.step()

    def current_goal(self) -> Goal:
        """Goals are a stored in a stack populated by goals in file.

        Returns:
            Goal (object): Goal influences SFF.

        """
        return self.goals[0]

    def checkpoint(self):
        """Current goal is reached and assigns a new one."""
        cp = self.goals.pop(0)
        print("Checkpoint", cp, "finished.")
        print("Checkpoint", cp, "finished.")
        print("Checkpoint", cp, "finished.")
        if len(self.goals) > 0:
            return True
        else:
            print("Finished evacuation.")
            self.running = False
            return False

    def sff_update(self, interest_area, key, focus=None):
        """Sets the SFF for followers based on the interest_area.

        Args:
            interest_area (lt, rb): Left top xy coordinates and rig
            key (str): The audience of the SFF.
            focus: Color focus for cells.

        """
        self.sff[key] = self.sff_compute(interest_area, focus)
        if self.schedule.time % 2 == 0:
            color_focus = "Follower"
        else:
            color_focus = "Leader"
        if color_focus in self.sff:
            normalized_color = normalize_grid(self.sff[color_focus])
            # do not use schedule.cells because all cells need to be colored
            for row in self.grid.grid:
                for agents in row:
                    cell = agents[0]
                    np_coords = cell.coords[1], cell.coords[0]
                    # cell.update_color(self.sff["Follower"][np_coords])
                    cell.update_color(normalized_color[np_coords])

    def sff_compute(self, interest_area=None, focus=None, normalize=False):
        """Computes the SFF for interest_area.

        Args:
            interest_area (lt, rb): Left top xy coordinates and right bottom xy coordinates of goal (area).
            focus (str): Audience of the SFF.
            normalize (bool): SFF is normalized to [0, 1]

        Returns:
            np.array(height, width) of SFF values.

        """
        if not interest_area:
            raise ValueError("Missing area of interest for SFF.")
        bonus_mask = np.ones_like(self.room) * AREA_STATIC_BOOSTER
        tl_x, tl_y = interest_area[0]
        rb_x, rb_y = interest_area[1]
        bonus_mask[rb_y:tl_y+1, tl_x:rb_x+1] = 0
        # center of area
        coords = ((rb_x - tl_x)//2 + tl_x, (rb_y - tl_y)//2 + tl_y)
        static_field = copy.deepcopy(self.sff[coords])
        static_field = static_field * bonus_mask
        if normalize:
            return normalize_grid(static_field)
        return static_field

    def generate_uid(self):
        """Generates unique id for each agent."""
        self.uid_ctr += 1
        return self.uid_ctr
