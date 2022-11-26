import mesa


class SequentialActivation(mesa.time.BaseScheduler):
    def __init__(self, model: mesa.Model) -> None:
        super().__init__(model)
        self.added_cells: dict[int, mesa.Agent] = {}
        self.removed_cells: dict[int, mesa.Agent] = {}
        self.removed_agents: dict[int, mesa.Agent] = {}

    def add(self, agent: mesa.Agent) -> None:
        if agent.unique_id in self._agents:
            return
        self._agents[agent.unique_id] = agent

    def step(self) -> None:
        """Step all agents, then advance them."""
        for agent in self._agents.values():
            agent.step()

        for cell in self.removed_cells.values():
            self.remove(cell)

        for cell in self.added_cells.values():
            cell.step()
            self.add(cell)
        # the previous steps might remove some agents, but
        # this loop will go over the remaining existing agents
        for agent in self._agents.values():
            agent.advance()

        for agent in self.removed_agents.values():
            self.remove(agent)

        self.added_cells: dict[int, mesa.Agent] = {}
        self.removed_cells: dict[int, mesa.Agent] = {}
        self.removed_agents: dict[int, mesa.Agent] = {}

        self.steps += 1
        self.time += 1

    def add_cell(self, cell: mesa.Agent):
        self.added_cells[cell.unique_id] = cell

    def remove_cell(self, cell: mesa.Agent):
        self.removed_cells[cell.unique_id] = cell

    def remove_agent(self, agent: mesa.Agent):
        self.removed_agents[agent.unique_id] = agent
