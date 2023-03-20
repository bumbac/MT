import os
import time
import copy
import numpy as np
import pickle
import mesa

from .cell import Cell
from .leader import LeaderAgent, VirtualLeader
from .directed import DirectedAgent
from .goal import GateGoal, AreaGoal, LocationGoal, GuardGoal
from .utils.constants import MAP_SYMBOLS, OBSTACLE, LEADER, FOLLOWER, DIRECTED, PAIR_DIRECTED, EXIT_GOAL_SYMBOL,\
    AREA_GOAL_SYMBOL, LOCATION_GOAL_SYMBOL, GUARD_GOAL_SYMBOL, ORIENTATION, GATE, EMPTY
from .utils.room import compute_static_field
from .utils.portrayal import agent_portrayal


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
        self.pos = {
            LEADER: [],
            DIRECTED: []
        }
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
        self.leader = None
        self.virtual_leader = None

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

    def get_leader(self):
        return self.leader, self.virtual_leader

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
            if goal_symbol == LOCATION_GOAL_SYMBOL:
                lt = g[1]
                target = g[3]
                wait_time = g[2]
                goals_list.append(LocationGoal(model, *lt, wait_time, target))
            if goal_symbol == GUARD_GOAL_SYMBOL:
                lt = g[1]
                target = g[3]
                wait_time = g[2]
                goals_list.append(GuardGoal(model, *lt, wait_time, target))
        return goals_list

    def get_canvas(self, resolution):
        CELL_SIZE = 30
        canvas_width = CELL_SIZE*self.width
        canvas_height = CELL_SIZE*self.height
        return mesa.visualization.CanvasGrid(agent_portrayal, self.width, self.height, canvas_width, canvas_height)

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
        for x in range(self.width):
            for _y in range(self.height):
                y = self.height - _y - 1
                point = lines[y][x]
                if point in MAP_SYMBOLS.keys():
                    self.room[_y, x] = MAP_SYMBOLS[point]
                    continue
                if point in self.pos.keys():
                    self.pos[point].append((x, _y))
        self.load_goals(lines[height+1:])

    def load_goals(self, lines):
        for goal_line in lines:
            tokens = goal_line.split()
            goal_symbol = tokens[0]
            target = tokens[-1]
            lt = (int(tokens[1]), int(tokens[2]))
            if goal_symbol == EXIT_GOAL_SYMBOL:
                gate_goal = [EXIT_GOAL_SYMBOL, [lt], target]
                self.gate = lt
                self.goals.append(gate_goal)
            if goal_symbol == AREA_GOAL_SYMBOL:
                rb = (int(tokens[3]), int(tokens[4]))
                area_goal = [AREA_GOAL_SYMBOL, [lt, rb], target]
                self.goals.append(area_goal)
            if goal_symbol == LOCATION_GOAL_SYMBOL:
                wait_time = tokens[3]
                leader_position = tokens[4]
                location_goal = [LOCATION_GOAL_SYMBOL, [lt], wait_time, leader_position, target]
                self.goals.append(location_goal)
            if goal_symbol == GUARD_GOAL_SYMBOL:
                wait_time = tokens[3]
                leader_position = tokens[4]
                location_goal = [GUARD_GOAL_SYMBOL, [lt], wait_time,leader_position, target]
                self.goals.append(location_goal)

    def place_agents(self, model):
        agent_positions = {LEADER: [],
                           DIRECTED: []}
        # leader
        for coords in self.pos[LEADER]:
            x, y = coords
            self.leader = LeaderAgent(model.generate_uid(), model)
            self.virtual_leader = VirtualLeader(model.generate_uid(), model)

            model.grid.place_agent(self.leader, coords)
            self.virtual_leader.pos = coords
            model.schedule.add(self.virtual_leader)
            model.schedule.add(self.leader)
            self.leader.cell = model.grid[x][y][0]
            self.virtual_leader.cell = None
            self.leader.next_cell = self.leader.cell
            self.virtual_leader.next_cell = None
            model.sff_update(model.current_goal().area, "Leader")
            model.sff_update([coords, coords], "Follower")
            agent_positions[LEADER].append(coords)

        for coords in self.pos[DIRECTED]:
            x, y = coords
            leader = DirectedAgent(model.generate_uid(), model)
            model.grid.place_agent(leader, coords)
            model.schedule.add(leader)
            leader.cell = model.grid[x][y][0]
            leader.next_cell = leader.cell
            agent_positions[DIRECTED].append(coords)

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
        self.sff["Gate"] = self.sff[self.gate]
        print("SFF calculated in:", time.time() - start, "seconds.")
        with open(data_file, "wb") as f:
            pickle.dump(self.sff, f)
        map_hash = self.deterministic_hash(self.room)
        with open(self.filename) as f:
            lines = f.readlines()
        lines[self.height] = str(map_hash)+"\n"
        with open(self.filename, "w") as f:
            f.writelines(lines)
