import numpy as np
import mesa


class Goal:
    def __init__(self, model: mesa.model):
        self.model = model
        self.area = None
        self.target = None
        self.corner = 0

    def reached_checkpoint(self) -> bool:
        pass

    def update(self):
        pass

    def __repr__(self):
        return self.__class__.__name__ + " " + str(self.area) + " " + self.target

    def all_evacuated(self):
        return len(self.model.schedule.agents) == 1

    def sff_update(self):
        """Sets the SFF for all agent types.

        Args:
            interest_area (lt, rb): Left top xy coordinates and rig
            key (str): The audience of the SFF.
            focus: Color focus for cells.

        """
        virtual_leader_pos = self.model.virtual_leader.pos
        self.model.sff["Follower"] = self.model.sff[virtual_leader_pos]
        virtual_leader_goal = self.center_of_area()
        self.model.sff["Virtual leader"] = self.model.sff[virtual_leader_goal]

        if self.model.leader_front_location_switch:
            self.model.sff["Leader"] = self.model.sff["Follower"]
        else:
            distance, pos = self.model.leader.most_distant()
            if distance == 0:
                self.model.sff["Leader"] = self.model.sff["Follower"]
            else:
                self.model.sff["Leader"] = self.model.sff[pos]

    def center_of_area(self):
        tl, rb = self.area
        tl_x, tl_y = tl
        rb_x, rb_y = rb
        if tl == rb:
            return tl
        return (rb_x - tl_x) // 2 + tl_x, (rb_y - tl_y) // 2 + tl_y

    @staticmethod
    def in_checkpoint(self, coords):
        x, y = coords
        tl_x, tl_y = self.area[0]
        rb_x, rb_y = self.area[1]
        if tl_x <= x <= rb_x and tl_y <= y <= rb_y:
            return True
        else:
            return False

    def coords_in_checkpoint(self):
        tl_x, tl_y = self.area[0]
        rb_x, rb_y = self.area[1]
        coords = []
        for x in range(tl_x, rb_x + 1):
            for y in range(rb_y, tl_y + 1):
                coords.append((x, y))
        return coords

    def agents_in_area(self):
        cnt = 0
        for x, y in self.coords_in_checkpoint():
            cell = self.model.grid[x][y][0]
            agent = cell.get_agent()
            if agent is None:
                continue
            cnt += 1
        return cnt


class GateGoal(Goal):
    def __init__(self, model: mesa.model, gate: (int, int), target="Follower"):
        super().__init__(model)
        self.area = [gate, gate]
        self.target = target

    def reached_checkpoint(self) -> bool:
        if self.all_evacuated():
            return True
        self.sff_update()
        self.model.split_pairs()


class LocationGoal(Goal):
    def __init__(self, model: mesa.model, location: (int, int), wait_time=10, leader_position="Back", target="Follower"):
        super().__init__(model)
        self.area = [location, location]
        self.target = target
        self.clock = 0
        self.time_of_entrance = 0
        self.wait_time = int(wait_time)
        self.leader_front_location_switch = True if leader_position == "Front" else False

    def reached_checkpoint(self) -> bool:
        if self.all_evacuated():
            return True
        self.sff_update()

        self.clock += 1
        self.model.leader_front_location_switch = self.leader_front_location_switch
        # initiate time_counter
        if self.agents_in_area() > self.time_of_entrance == 0:
            self.time_of_entrance = self.clock

        # if goal is time oriented use it
        if self.wait_time > 0:
            return self.clock - self.wait_time > self.time_of_entrance > 0
        elif self.time_of_entrance > 0:
            agents = self.model.schedule.agents
            n_agents = len(agents)
            radius_time_increase = self.clock - self.time_of_entrance
            radius = n_agents // 2 + radius_time_increase
            # are all agents in the radius?
            for agent in agents:
                d = agent.path_dist(agent.pos, self.center_of_area())
                if d > radius:
                    return False
            return True
        return False


class GuardGoal(Goal):
    def __init__(self, model: mesa.model, location: (int, int), wait_time=10, leader_position="Back", target="Follower"):
        super().__init__(model)
        self.area = [location, location]
        self.target = target
        self.clock = 0
        self.time_of_entrance = 0
        self.wait_time = int(wait_time)
        self.leader_front_location_switch = True if leader_position == "Front" else False

    def sff_update(self):
        virtual_leader_pos = self.model.virtual_leader.pos
        self.model.sff["Follower"] = self.model.sff[virtual_leader_pos]
        virtual_leader_goal = self.model.gate
        self.model.sff["Virtual leader"] = self.model.sff[virtual_leader_goal]
        leader_goal = self.center_of_area()
        self.model.sff["Leader"] = self.model.sff[leader_goal]

    def reached_checkpoint(self) -> bool:
        if self.all_evacuated():
            return True
        self.sff_update()
        self.clock += 1
        self.model.leader_front_location_switch = self.leader_front_location_switch
        guard_pos = self.model.leader.pos
        # Leader arrived to the checkpoint
        if guard_pos in self.coords_in_checkpoint() and self.time_of_entrance == 0:
            self.time_of_entrance = self.clock

        if self.wait_time > 0:
            return self.clock - self.wait_time > self.time_of_entrance > 0
        elif self.time_of_entrance > 0:
            agents = self.model.schedule.agents
            gate_pos = self.model.gate
            guard_distance = agents[0].path_dist(guard_pos, gate_pos)
            for agent in agents:
                d = agent.path_dist(agent.pos, gate_pos)
                if d > guard_distance:
                    return False
            return True
        return False


class AreaGoal(Goal):
    def __init__(self, model: mesa.model, area: [(int, int), (int, int)], target="Follower"):
        super().__init__(model)
        self.area = area
        self.target = target
        self.edges = self.create_edges()

    def reached_checkpoint(self) -> bool:
        if self.all_evacuated():
            return True
        self.sff_update()
        n_agents = self.agents_in_area()
        return n_agents > 5

    def create_edges(self):
        tl, rb = self.area
        tl_x, tl_y = tl
        rb_x, rb_y = rb
        edges = [self.center_of_area(),
                 (tl_x, tl_y), (tl_x, rb_y), (rb_x, rb_y), (rb_x, tl_y)]
        return edges

    def update(self):
        self.corner = self.model.schedule.time % 5
        self.model.sff_update(self.area, key="Leader", focus=self.edges[self.corner])
