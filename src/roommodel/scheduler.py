import mesa

from .cell import Cell


class SequentialActivation(mesa.time.BaseScheduler):
    def __init__(self, model: mesa.Model) -> None:
        super().__init__(model)
        self._cells: dict[int, Cell] = {}
        self.removed_agents: dict[int, mesa.Agent] = {}
        self.epochs = 0

    def add(self, agent: mesa.Agent) -> None:
        if agent.unique_id in self._agents:
            return
        self._agents[agent.unique_id] = agent

    def step(self) -> None:
        """Step all agents, then advance them."""
        self.epochs += 1
        self._cells = {}
        self.removed_agents = {}
        running_agents = {}
        print("-----", self.time, "-----")
        for agent in self._agents.values():
            if agent.allow_entrance():
                running_agents[agent.unique_id] = agent

        # select next_cell
        for agent in running_agents.values():
            agent.step()
        # select winner
        for cell in self._cells.values():
            cell.step()
        # confirm move
        for agent in self._agents.values():
            agent.advance()
        # move agents
        for cell in self._cells.values():
            cell.advance()

        self.steps += 1
        self.time += 2

    def add_cell(self, cell: Cell):
        self._cells[cell.unique_id] = cell

    def remove_agent(self, agent: mesa.Agent):
        self.removed_agents[agent.unique_id] = agent
        del self._agents[agent.unique_id]

    def get_agents(self):
        return self._agents
