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

    def __repr__(self):
        return self.__class__.__name__ + " " + str(self.area) + " " + self.target

    def update(self):
        pass

    @staticmethod
    def in_checkpoint(coords, checkpoint):
        x, y = coords
        tl_x, tl_y = checkpoint[0]
        rb_x, rb_y = checkpoint[1]
        if tl_x <= x <= rb_x and tl_y <= y <= rb_y:
            return True
        else:
            return False


class AreaGoal(Goal):
    def __init__(self, model: mesa.model, area: [(int, int), (int, int)], target="Follower"):
        super().__init__(model)
        self.area = area
        self.n_positions = self.positions_in_area()
        self.target = target
        self.edges = self.create_edges()

    def agents_in_area(self, agent_type="Follower"):
        cnt = 0
        tl_x, tl_y = self.area[0]
        rb_x, rb_y = self.area[1]
        for x in range(tl_x, rb_x + 1):
            for y in range(tl_y, rb_y + 1):
                cell = self.model.grid[x][y][0]
                agent = cell.get_agent()
                if agent is None:
                    continue
                if agent.name.startswith(agent_type):
                    cnt += 1
        return cnt

    def positions_in_area(self):
        interest_area = self.area
        tl_x, tl_y = interest_area[0]
        rb_x, rb_y = interest_area[1]
        a = rb_x - tl_x + 1
        b = tl_y - rb_y + 1
        return a*b

    def reached_checkpoint(self) -> bool:
        n_agents = 0
        n_goal = 0
        if self.target == "Follower" or self.target == "All":
            n_agents += self.agents_in_area("Follower")
            n_goal += len(self.model.follower_positions)
        if self.target == "Leader" or self.target == "All":
            n_agents += self.agents_in_area("Leader")
            n_goal += len(self.model.leader_positions)
        pos = self.edges[self.corner]
        cell = self.model.grid[pos[0]][pos[1]][0]
        if cell.get_agent():
            self.update()
        return n_agents == n_goal or n_agents == self.n_positions

    def create_edges(self):
        interest_area = self.area
        tl_x, tl_y = interest_area[0]
        rb_x, rb_y = interest_area[1]
        edges = [((rb_x - tl_x) // 2 + tl_x, (rb_y - tl_y) // 2 + tl_y),
                 (tl_x, tl_y), (tl_x, rb_y), (rb_x, rb_y), (rb_x, tl_y)]
        return edges

    def update(self):
        self.corner = self.model.schedule.time % 5
        self.model.sff_update(self.area, key="Leader", focus=self.edges[self.corner])


class GateGoal(Goal):
    def __init__(self, model: mesa.model, gate: (int, int), target="Follower"):
        super().__init__(model)
        self.area = [gate, gate]
        self.target = target

    def reached_checkpoint(self) -> bool:
        n_agents = 0
        n_goal = 0
        if self.target == "Follower" or self.target == "All":
            n_agents += self.model.n_evacuated_followers
            n_goal += len(self.model.follower_positions)
            n_goal += len(self.model.directed_positions)
            n_goal += len(self.model.directed_pairs_positions)
        if self.target == "Leader" or self.target == "All":
            n_agents += self.model.n_evacuated_leaders
            n_goal += len(self.model.leader_positions)
        return n_agents == n_goal


