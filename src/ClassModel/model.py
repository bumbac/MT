import copy

import numpy as np
import mesa

from .leader import LeaderAgent
from .follower import FollowerAgent
from .cell import Cell

from .utils.room import create_grid, compute_static_field, normalize_grid
from .utils.constants import AREA_STATIC_BOOSTER


class RoomModel(mesa.Model):
    def __init__(self, width, height, gate):
        super().__init__()
        self.schedule = mesa.time.BaseScheduler(self)
        self.grid = mesa.space.MultiGrid(width, height, torus=False)
        self.dimensions = (width, height)
        self.gate = gate
        self.room = create_grid(width, height)
        self.uid_ctr = 0
        self.goals = [[(5, 3), (8, 6)], [self.gate]]
        self.leader_positions = [(11, 3)]
        self.follower_positions = [(12, 3), (12, 2), (12, 4), (13, 3), (13, 2), (13, 4)]
        self.n_followers = len(self.follower_positions)
        self.sff = None
        self.sff = self.sff_compute(interest_area=self.goals[0])
        self.follower_sff = None
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
            cell = self.grid[x][y][0]
            cell.enter(a)
            cell.step()
            self.schedule.add(a)
            self.follower_sff_update([coords])
        # followers
        for coords in self.follower_positions:
            x, y = coords
            a = FollowerAgent(self.generate_uid(), self)
            self.grid.place_agent(a, coords)
            cell = self.grid[x][y][0]
            cell.enter(a)
            cell.step()
            self.schedule.add(a)
        for x in range(width):
            for y in range(height):
                cell = self.grid[x][y][0]
                self.schedule.add(cell)

    def followers_in_area(self, area):
        cnt = 0
        tl_x, tl_y = area[0]
        rb_x, rb_y = area[1]
        for x in range(tl_x, rb_x+1):
            for y in range(tl_y, rb_y+1):
                cell = self.grid[x][y][0]
                agent = cell.get_agent()
                if agent is None:
                    continue
                if agent.name.startswith("Follower"):
                    cnt += 1
        return cnt

    def reached_checkpoint(self):
        cg = self.current_goal()
        if len(cg) > 1:
            n_followers = self.followers_in_area(cg)
            return n_followers == self.n_followers
        else:
            return self.n_followers == len(self.follower_positions)

    def evacuate(self):
        if not self.cell_gate.empty:
            agent = self.cell_gate.evacuate()
            if agent.name.startswith("Follower"):
                self.n_followers -= 1
            self.schedule.remove(agent)

    def step(self):
        self.evacuate()
        if self.reached_checkpoint():
            if self.checkpoint():
                self.sff_update(self.current_goal())

        if self.running:
            self.schedule.step()

    def current_goal(self):
        return self.goals[0]

    def checkpoint(self):
        if len(self.goals) > 1:
            cp = self.goals.pop(0)
            print("Checkpoint", cp, "finished.")
            return True
        else:
            cp = self.goals.pop(0)
            print("Checkpoint", cp, "finished.")
            print("Finished evacuation.")
            self.running = False
            return False

    def generate_uid(self):
        self.uid_ctr += 1
        return self.uid_ctr

    def sff_update(self, interest_area):
        self.sff = self.sff_compute(interest_area)

    def sff_compute(self, interest_area=None):
        if not interest_area:
            raise ValueError("Missing area of interest for SFF.")
        copy_room = copy.deepcopy(self.room)
        bonus_mask = np.ones_like(copy_room)
        static_field = None
        # only gate or leader
        if len(interest_area) == 1:
            coords = interest_area[0]
            np_coords = (coords[1], coords[0])
            bonus_mask[np_coords] = 0
            copy_room[np_coords] = 100
            static_field = compute_static_field(copy_room)
        # AREA
        else:
            bonus_mask = bonus_mask * AREA_STATIC_BOOSTER
            tl_x, tl_y = interest_area[0]
            rb_x, rb_y = interest_area[1]
            bonus_mask[tl_y:rb_y, tl_x:rb_x] = 0
            # center of area
            coords = ((rb_x - tl_x)//2 + tl_x, (rb_y - tl_y)//2 + tl_y)
            np_coords = (coords[1], coords[0])
            copy_room[np_coords] = 100
            static_field = compute_static_field(copy_room)
        static_field = static_field + bonus_mask
        return normalize_grid(static_field)

    def follower_sff_update(self, interest_area):
        self.follower_sff = self.sff_compute(interest_area=interest_area)

    @staticmethod
    def in_checkpoint(coords, checkpoint):
        x, y = coords
        tl_x, tl_y = checkpoint[0]
        rb_x, rb_y = checkpoint[1]
        if tl_x <= x <= rb_x and tl_y <= y <= rb_y:
            return True
        else:
            return False
