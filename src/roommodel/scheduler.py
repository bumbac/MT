import mesa

from .cell import Cell
from .utils.algorithms import scc_graph


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
        # select next_cell
        for agent in self._agents.values():
            agent.step()
        # select winner
        for cell in self._cells.values():
            cell.step()
        # confirm move
        for agent in self._agents.values():
            agent.advance()

        scc = scc_graph(self.model.graph)
        # self.untangle(scc)

        for cell in self._cells.values():
            cell.advance()

        for agent in self.removed_agents.values():
            self.remove(agent)

        self.model.graph = self.model.reset_graph()
        self.steps += 1
        self.time += 1

    def add_cell(self, cell: Cell):
        self._cells[cell.unique_id] = cell

    def remove_agent(self, agent: mesa.Agent):
        self.removed_agents[agent.unique_id] = agent


    def untangle(self, scc):
        for component in scc:
            agents = [self._agents[uid] for uid in component]
            leader = agents[0]
            if leader.head:
                leader.head.tail = None
            leader.head = None