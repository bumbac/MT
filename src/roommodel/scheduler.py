import mesa

from .cell import Cell


class SequentialActivation(mesa.time.BaseScheduler):
    """Scheduler with adaptive time spand and sequential activation of agents.

    Attributes:
        _agents (dict): unique_id(key), Agent(value) which is updated every step.
        _cells (dict): unique_id(key), Cell(value) which is updated every step if occupied.
        removed_agents (dict): unique_id(key), Agent(value) for preserving agents after evacuation.
        steps (int): Model step increments by 1.
        time (int): Timestep clock increments by 2 per model step. Used to schedule agents and control speed.

    """
    def __init__(self, model: mesa.Model) -> None:
        super().__init__(model)
        self._cells: dict[int, Cell] = {}
        self.removed_agents: dict[int, mesa.Agent] = {}

    def add(self, agent: mesa.Agent) -> None:
        """Add agent to the schedule."""
        if agent.unique_id in self._agents:
            return
        self._agents[agent.unique_id] = agent

    def step(self) -> None:
        """Check all agents if they can enter the timestep and activate them. Activate occupied cells."""
        self._cells = {}
        # Only agents with time in the timestep window are activated.
        running_agents = {}
        for agent in self._agents.values():
            if agent.allow_entrance():
                running_agents[agent.unique_id] = agent

        # reset states, select next_cell
        for agent in running_agents.values():
            agent.step()
        # select winner, solve conflicts
        for cell in self._cells.values():
            cell.step()
        # confirm move, adapt speed
        for agent in self._agents.values():
            agent.advance()
        # move agents, update states
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

    def get_cells(self):
        return self._cells

    @property
    def cells(self):
        return list(self._cells.values())

