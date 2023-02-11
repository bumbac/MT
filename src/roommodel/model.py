import copy

import numpy as np
import mesa

from .goal import Goal
from .scheduler import SequentialActivation
from .file_loader import FileLoader
from .utils.room import compute_static_field, normalize_grid
from .utils.constants import AREA_STATIC_BOOSTER, LEADER, FOLLOWER, DIRECTED, PAIR_DIRECTED, MAP_SYMBOLS, GATE


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
        self.n_evacuated_followers = 0
        self.n_evacuated_leaders = 0
        self.sff = {}
        self.of = self.file_loader.get_room()
        self.cell_gate = self.file_loader.place_cells(self)
        self.leader_positions = self.file_loader.place_agents(self, LEADER)
        self.follower_positions = self.file_loader.place_agents(self, FOLLOWER)
        self.directed_positions = self.file_loader.place_agents(self, DIRECTED)
        self.directed_pairs_positions = self.file_loader.place_agents(self, PAIR_DIRECTED)
        self.graph = self.reset_graph()
        for a in self.schedule.agent_buffer():
            cell = a.cell
            cell.agent = a
            self.grid.move_agent(a, cell.pos)

    def step(self):
        print("-----------")
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
        if key == color_focus:
            for row in self.grid.grid:
                for agents in row:
                    cell = agents[0]
                    np_coords = cell.coords[1], cell.coords[0]
                    cell.update_color(self.sff["Follower"][np_coords])
                    # cell.update_color(self.sff[color_focus][np_coords])

    def sff_compute(self, interest_area=None, focus=None):
        if not interest_area:
            raise ValueError("Missing area of interest for SFF.")
        copy_room = copy.deepcopy(self.room)
        bonus_mask = np.ones_like(copy_room) * AREA_STATIC_BOOSTER
        tl_x, tl_y = interest_area[0]
        rb_x, rb_y = interest_area[1]
        bonus_mask[rb_y:tl_y+1, tl_x:rb_x+1] = 0
        # center of area
        coords = ((rb_x - tl_x)//2 + tl_x, (rb_y - tl_y)//2 + tl_y)
        if focus:
            coords = focus
        np_coords = (coords[1], coords[0])
        copy_room[np_coords] = MAP_SYMBOLS[GATE]
        static_field = compute_static_field(copy_room)
        static_field = static_field * bonus_mask
        return normalize_grid(static_field)

    def generate_uid(self):
        self.uid_ctr += 1
        return self.uid_ctr
