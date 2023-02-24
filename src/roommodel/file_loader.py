import os
import time
import copy
import numpy as np
import pickle

from .cell import Cell
from .follower import FollowerAgent
from .leader import LeaderAgent
from .directed import DirectedAgent
from .partner import DirectedPartnerAgent
from .goal import GateGoal, AreaGoal
from .utils.constants import MAP_SYMBOLS, OBSTACLE, LEADER, FOLLOWER, DIRECTED, PAIR_DIRECTED, EXIT_GOAL_SYMBOL,\
    AREA_GOAL_SYMBOL, ORIENTATION, GATE, EMPTY
from .utils.room import compute_static_field, normalize_grid


class FileLoader:
    def __init__(self, filename):
        if not os.path.isfile(filename):
            raise FileNotFoundError("Map file not found.")
        self.filename = filename
        self.width = 0
        self.height = 0
        self.gate = 0
        self.room = None
        self.goals = []
        self.map_hash = None
        self.load_topology()
        self.sff = {}
        self.hash_control_active = True
        self.load_sff()
        self.directed_generator = None
        self.leader_generator = None
        self.follower_generator = None
        self.pairs_directed_generator = None
        self.goal_generator = None
        self.sff_generator = None

    def dimensions(self) -> (int, int):
        return self.width, self.height

    def get_room(self):
        return self.room

    def get_gate(self):
        return self.gate

    def get_sff(self):
        if len(self.sff) == 0:
            raise ValueError("Calculated SFF is empty.")
        return self.sff

    def load_topology(self):
        if self.filename is None:
            raise FileNotFoundError("Filename for map loading cannot be None.")
        if not os.path.isfile(self.filename):
            raise FileExistsError("File", self.filename, " for map loading not found.")
        with open(self.filename) as f:
            lines = f.readlines()
            if len(lines) == 0:
                raise ValueError("Map file is empty.")
            lines = [line.rstrip() for line in lines]
            self.width = len(lines[0])
            height = 0
            while height < len(lines) and lines[height][-1] == OBSTACLE:
                height += 1
            self.height = height
            self.room = np.zeros(shape=(self.height, self.width))
            self.pos = {
                LEADER: [],
                FOLLOWER: [],
                DIRECTED: [],
                PAIR_DIRECTED: []
            }
            for x in range(self.width):
                for _y in range(self.height):
                    y = self.height - _y - 1
                    point = lines[y][x]
                    if point in MAP_SYMBOLS.keys():
                        self.room[_y, x] = MAP_SYMBOLS[point]
                        continue
                    if point in self.pos.keys():
                        self.pos[point].append((x, _y))
            for goal_line in lines[height+1:]:
                tokens = goal_line.split()
                goal_symbol = tokens[0]
                target = tokens[-1]
                lt = (int(tokens[1]), int(tokens[2]))
                rb = lt
                if len(tokens) > 4:
                    rb = (int(tokens[3]), int(tokens[4]))
                if goal_symbol == EXIT_GOAL_SYMBOL:
                    gate_goal = [EXIT_GOAL_SYMBOL, [lt], target]
                    self.gate = lt
                    self.goals.append(gate_goal)
                if goal_symbol == AREA_GOAL_SYMBOL:
                    area_goal = [AREA_GOAL_SYMBOL, [lt, rb], target]
                    self.goals.append(area_goal)

    def get_goals(self, model):
        goals_list = []
        for g in self.goals:
            goal_symbol = g[0]
            if goal_symbol == EXIT_GOAL_SYMBOL:
                lt = g[1]
                target = g[2]
                goals_list.append(GateGoal(model, *lt, target))
            if goal_symbol == AREA_GOAL_SYMBOL:
                lt = g[1][0]
                rb = g[1][1]
                target = g[2]
                goals_list.append(AreaGoal(model, [lt, rb], target))
        return goals_list

    def place_agents(self, model):
        agent_positions = {LEADER: [],
                           DIRECTED: [],
                           PAIR_DIRECTED: []}
        # leader
        for coords in self.pos[LEADER]:
            x, y = coords
            a = LeaderAgent(model.generate_uid(), model)
            model.grid.place_agent(a, coords)
            model.schedule.add(a)
            a.cell = model.grid[x][y][0]
            a.next_cell = a.cell
            model.sff_update(model.current_goal().area, "Leader")
            model.sff_update([coords, coords], "Follower")
            agent_positions[LEADER].append(coords)

        for coords in self.pos[DIRECTED]:
            x, y = coords
            a = DirectedAgent(model.generate_uid(), model)
            model.grid.place_agent(a, coords)
            model.schedule.add(a)
            a.cell = model.grid[x][y][0]
            a.next_cell = a.cell
            agent_positions[DIRECTED].append(coords)

        if len(self.pos[PAIR_DIRECTED]) == 0:
            return agent_positions

        # calculate orientation of paired agents
        directed_agent = DirectedPartnerAgent(0, model)
        directed_agent.pos = self.pos[PAIR_DIRECTED][1]
        if len(self.pos[LEADER]) > 0:
            leader_pos = self.pos[LEADER][0]
            directed_agent.orientation = directed_agent.calculate_orientation(leader_pos)
            # todo
            directed_agent.orientation = ORIENTATION.EAST
                #directed_agent.orientation.twist(directed_agent.pos, leader_pos)
        else:
            raise ValueError("Leader needs to be placed first to calculate orientation of directed agents.")

        grid = np.zeros_like(self.room)
        no_agent_present = 0
        agent_present = 1
        for coords in self.pos[PAIR_DIRECTED]:
            np_coords = coords[1], coords[0]
            grid[np_coords] = 1
        partner_id = 100
        for idx, flag in np.ndenumerate(grid):
            if flag == no_agent_present:
                continue
            if flag > agent_present:
                continue
            coords = idx[1], idx[0]
            partner_coords = directed_agent.partner_coords(leader=coords)
            agent_positions[PAIR_DIRECTED].append((coords, partner_coords))
            if grid[partner_coords[1], partner_coords[0]] == agent_present:
                grid[idx] = partner_id
                grid[partner_coords[1], partner_coords[0]] = partner_id
                partner_id += 100
                leader = DirectedPartnerAgent(model.generate_uid(), model)
                partner = DirectedPartnerAgent(model.generate_uid(), model)
                model.grid.place_agent(leader, coords)
                model.grid.place_agent(partner, partner_coords)
                model.schedule.add(leader)
                model.schedule.add(partner)
                leader.cell = leader.next_cell = model.grid[coords[0]][coords[1]][0]
                partner.cell = partner.next_cell = model.grid[partner_coords[0]][partner_coords[1]][0]
                leader.orientation = ORIENTATION.EAST
                leader.add_partner(partner)
        return agent_positions

    def place_cells(self, model):
        for x in range(self.width):
            for y in range(self.height):
                coords = (x, y)
                cell = Cell(model.generate_uid(), model, coords)
                model.grid.place_agent(cell, coords)
        return model.grid[self.gate[0]][self.gate[1]][0]

    def load_sff(self):
        if self.filename is None:
            raise FileNotFoundError("Filename for map loading cannot be None.")
        if not os.path.isfile(self.filename):
            raise FileExistsError("File", self.filename, "for map loading not found.")
        topology_folder = os.path.dirname(self.filename)
        maps_folder = os.path.dirname(topology_folder)
        filename_without_type = self.filename.split(os.sep)[-1][:- len(".txt")]
        data_file = maps_folder + "/data/" + filename_without_type + ".data"
        if not os.path.isfile(data_file):
            self.process_sff(data_file)
        with open(self.filename) as f:
            lines = f.readlines()
            if len(lines) == 0:
                raise ValueError("Map file is empty.")
            lines = [line.rstrip() for line in lines]
            map_hash = self.deterministic_hash(self.room)
            hash_line = int(lines[self.height])
        if map_hash != hash_line and self.hash_control_active:
            self.process_sff(data_file)
        with open(data_file, "rb") as f:
            self.sff = pickle.load(f)

    def deterministic_hash(self, grid):
        bytes_value = grid.data.tobytes()
        tokens = []
        idx = 0
        stride = 256
        while idx < len(bytes_value):
            tokens.append(bytes_value[idx: idx + stride])
            idx += stride
        hash_value = sum([int.from_bytes(token, byteorder="big") for token in tokens])
        return hash_value

    def process_sff(self, data_file):
        print("Calculating SFF for", self.filename)
        start = time.time()
        room = copy.deepcopy(self.room)
        gate = self.gate
        room[gate[1], gate[0]] = MAP_SYMBOLS[EMPTY]
        self.sff = {}
        cnt = 0
        for x in range(self.width):
            for y in range(self.height):
                cnt += 1
                if cnt % 32 == 1:
                    print(cnt, "/", self.width*self.height)
                if room[y, x] == MAP_SYMBOLS[OBSTACLE]:
                    continue
                room[y, x] = MAP_SYMBOLS[GATE]
                self.sff[(x, y)] = compute_static_field(room, normalize=False)
                room[y, x] = MAP_SYMBOLS[EMPTY]
        print("SFF calculated in:", time.time() - start, "seconds.")
        with open(data_file, "wb") as f:
            pickle.dump(self.sff, f)
        map_hash = self.deterministic_hash(self.room)
        with open(self.filename) as f:
            lines = f.readlines()
        lines[self.height] = str(map_hash)+"\n"
        with open(self.filename, "w") as f:
            f.writelines(lines)
