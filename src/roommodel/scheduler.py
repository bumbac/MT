import mesa

from .cell import Cell


class SequentialActivation(mesa.time.BaseScheduler):
    def __init__(self, model: mesa.Model) -> None:
        super().__init__(model)
        self._cells: dict[int, Cell] = {}
        self.removed_agents: dict[int, mesa.Agent] = {}

    def add(self, agent: mesa.Agent) -> None:
        if agent.unique_id in self._agents:
            return
        self._agents[agent.unique_id] = agent

    def step(self) -> None:
        """Step all agents, then advance them."""
        self._cells = {}
        self.removed_agents = {}

        for agent in self._agents.values():
            agent.step()

        for cell in self._cells.values():
            cell.step()

        for agent in self._agents.values():
            agent.advance()

        for cell in self._cells.values():
            cell.advance()

        for agent in self.removed_agents.values():
            self.remove(agent)

        self.steps += 1
        self.time += 1

    def add_cell(self, cell: Cell):
        self._cells[cell.unique_id] = cell

    def remove_agent(self, agent: mesa.Agent):
        self.removed_agents[agent.unique_id] = agent