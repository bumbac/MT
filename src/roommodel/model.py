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
        self.graph = self.reset_graph()
        for a in self.schedule.agent_buffer():
            cell = a.cell
            if cell is None:
                continue
            cell.agent = a
            self.grid.move_agent(a, cell.pos)

    def form_pairs(self):
        grid = np.zeros(shape=self.dimensions)
        for agent in self.schedule.get_agents().values():
            if agent.partner is None and agent.name.startswith("Follower"):
                grid[agent.pos] = OCCUPIED_CELL
        positions = pair_positions(grid)
        for position in positions:
            leader_position, partner_position = position

            leader_cell = self.grid.grid[leader_position[0]][leader_position[1]][0]
            leader_agent = leader_cell.agent
            self.replace_agent(leader_agent)
            partner_cell = self.grid.grid[partner_position[0]][partner_position[1]][0]
            partner_agent = partner_cell.agent
            self.replace_agent(partner_agent)

            leader = DirectedPartnerAgent(leader_agent.unique_id, self)
            leader_cell.agent = leader
            leader.cell = leader_cell
            partner = DirectedPartnerAgent(partner_agent.unique_id, self)
            partner_cell.agent = partner
            partner.cell = partner_cell

            self.schedule.add(leader)
            self.schedule.add(partner)
            self.grid.place_agent(leader, leader_position)
            self.grid.place_agent(partner, partner_position)

            for orientation in ORIENTATION:
                leader.orientation = orientation
                if leader.partner_coords() == partner_position:
                    partner.orientation = orientation
                    break

            leader.add_partner(partner)

    def replace_agent(self, agent):
        if agent:
            self.grid.remove_agent(agent)
            self.schedule.remove_agent(agent)

    def step(self):
        print("-----------")
        self.form_pairs()

        if self.current_goal().reached_checkpoint():
            if self.checkpoint():
                self.sff_update(self.current_goal().area, "Leader")
        if self.running:
            self.schedule.step()

    def current_goal(self) -> Goal:
        return self.goals[0]

    def reset_graph(self):
        return [set(), {}]

    def checkpoint(self):
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
        self.sff[key] = self.sff_compute(interest_area, focus)
        if self.schedule.time % 2 == 0:
            color_focus = "Follower"
        else:
            color_focus = "Leader"
        if color_focus in self.sff:
            normalized_color = normalize_grid(self.sff[color_focus])
            for row in self.grid.grid:
                for agents in row:
                    cell = agents[0]
                    np_coords = cell.coords[1], cell.coords[0]
                    # cell.update_color(self.sff["Follower"][np_coords])
                    cell.update_color(normalized_color[np_coords])

    def sff_compute(self, interest_area=None, focus=None, normalize=False):
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
        self.uid_ctr += 1
        return self.uid_ctr
