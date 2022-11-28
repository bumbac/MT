import copy

import numpy as np
import mesa

from .leader import LeaderAgent
from .follower import FollowerAgent
from .directed import DirectedAgent
from .partner import DirectedPartnerAgent
from .cell import Cell
from .goal import Goal
from .scheduler import SequentialActivation
from .file_loader import FileLoader
from .utils.room import compute_static_field, normalize_grid
from .utils.constants import AREA_STATIC_BOOSTER


class RoomModel(mesa.Model):
    def __init__(self, filename):
        super().__init__()
        self.file_loader = FileLoader(filename)
        width, height = self.file_loader.dimensions()
        self.schedule = SequentialActivation(self)
        self.grid = mesa.space.MultiGrid(width, height, torus=False)
        self.dimensions = (width, height)
        self.gate = self.file_loader.get_gate()
        self.room = self.file_loader.get_room()
        self.uid_ctr = 0
        self.goals = self.file_loader.get_goals(self)
        self.leader_positions = self.file_loader.pos["L"]
            #[(11, 3)]
        self.follower_positions = self.file_loader.pos["F"]
            #[]#(12, 3), (12, 2), (13, 3)]#, (12, 4), (13, 2), (13, 4)]
        self.directed_positions = self.file_loader.pos["D"]
            #[]#(12, 3), (12, 2)]#, (13, 3), (13, 2)]
        self.directed_pairs_positions = self.file_loader.pos["P"]
            #[(13, 3), (13, 2)]#]#(12, 3), (12, 2), (13, 3), (13, 2)]
        self.n_evacuated_followers = 0
        self.n_evacuated_leaders = 0
        self.sff = {}
        self.cell_gate = None

        # cells
        for x in range(width):
            for y in range(height):
                coords = (x, y)
                cell = Cell(self.generate_uid(), self, coords)
                self.grid.place_agent(cell, coords)
        self.cell_gate = self.grid[self.gate[0]][self.gate[1]][0]

        # leader
        for coords in self.leader_positions:
            x, y = coords
            a = LeaderAgent(self.generate_uid(), self)
            self.grid.place_agent(a, coords)
            self.schedule.add(a)
            a.cell = self.grid[x][y][0]
            a.next_cell = a.cell
            self.sff_update([coords, coords], "Follower")
            self.sff_update(self.current_goal().area, "Leader")

        # followers
        for coords in self.follower_positions:
            x, y = coords
            a = FollowerAgent(self.generate_uid(), self)
            self.grid.place_agent(a, coords)
            self.schedule.add(a)
            a.cell = self.grid[x][y][0]
            a.next_cell = a.cell

        # directed
        for coords in self.directed_positions:
            x, y = coords
            a = DirectedAgent(self.generate_uid(), self)
            self.grid.place_agent(a, coords)
            self.schedule.add(a)
            a.cell = self.grid[x][y][0]
            a.next_cell = a.cell

        # pairs
        for i, coords in enumerate(self.directed_pairs_positions[::2]):
            x, y = coords
            px, py = self.directed_pairs_positions[i * 2 + 1]
            leader = DirectedPartnerAgent(self.generate_uid(), self)
            partner = DirectedPartnerAgent(self.generate_uid(), self)
            self.grid.place_agent(leader, coords)
            self.grid.place_agent(partner, (px, py))
            self.schedule.add(leader)
            self.schedule.add(partner)
            leader.cell = leader.next_cell = self.grid[x][y][0]
            partner.cell = partner.next_cell = self.grid[px][py][0]
            leader.add_partner(partner)

        for a in self.schedule.agent_buffer():
            cell = a.cell
            self.schedule.add_cell(cell)
            cell.enter(a)
            cell.step()
            a.next_cell = cell
            cell.advance()
            self.schedule.removed_cells: dict[int, mesa.Agent] = {}

    def step(self):
        print("-----------")
        if self.current_goal().reached_checkpoint():
            if self.checkpoint():
                self.sff_update(self.current_goal().area, "Leader")
        if self.running:
            self.schedule.step()

    def current_goal(self) -> Goal:
        return self.goals[0]

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
        # color_focus = "Follower"
        color_focus = "Leader"
        if key == color_focus:
            for row in self.grid.grid:
                for agents in row:
                    cell = agents[0]
                    np_coords = cell.coords[1], cell.coords[0]
                    cell.update_color(self.sff[color_focus][np_coords])

    def sff_compute(self, interest_area=None, focus=None):
        if not interest_area:
            raise ValueError("Missing area of interest for SFF.")
        copy_room = copy.deepcopy(self.room)
        bonus_mask = np.ones_like(copy_room) * AREA_STATIC_BOOSTER
        tl_x, tl_y = interest_area[0]
        rb_x, rb_y = interest_area[1]
        bonus_mask[tl_y:rb_y+1, tl_x:rb_x+1] = 0
        # center of area
        coords = ((rb_x - tl_x)//2 + tl_x, (rb_y - tl_y)//2 + tl_y)
        if focus:
            coords = focus
        np_coords = (coords[1], coords[0])
        copy_room[np_coords] = 100
        static_field = compute_static_field(copy_room)
        static_field = static_field + bonus_mask
        return normalize_grid(static_field)

    def generate_uid(self):
        self.uid_ctr += 1
        return self.uid_ctr
