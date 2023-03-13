import mesa
import numpy as np


from .agent import Agent
from .utils.portrayal import rgb_to_hex


class Cell(Agent):
    """Grid cell class in which agents move.

    Attributes:
        name (str): Human readable name with coords.
        coords (int, int): xy coordinates in the grid.
        agent (object): Agent occupying this cell.
        winner (object): Agent which can enter this cell in the next step.
        q (list): List of agents that want to enter this cell.

    """
    def __init__(self, uid: int, model: mesa.Model, coords: (int, int)):
        super().__init__(uid, model)
        self.name = "Cell: " + self.name
        self.coords = coords
        self.agent = None
        self.winner = None
        self.q = []

    def step(self):
        """Cell selects winner from q and updates its bounds to head and tail."""
        if len(self.q) > 0:
            self.winner = np.random.permutation(self.q)[0]
            self.q = []
            if self.agent is not None:
                # do not create cycle with the same agent
                if self.winner != self.agent:
                    self.winner.head = self.agent
                    self.agent.tail = self.winner

    def advance(self):
        """Break bonds cycle or find head and execute move. Move is chained."""
        if self.winner is not None:
            head = self.bubbleup()
            if head.next_cell:
                if head.next_cell.winner is head:
                    head.move()

    def bubbleup(self):
        """Iterate bonds to the front until unbounded agent or cycle is found - break cycle."""
        head = self.winner
        origin = self.winner
        while head.head is not None:
            head = head.head
            # found cycle, back at beginning
            if head is origin:
                # split the cycle
                origin.head.tail = None
                origin.head = None
        return head

    def update_color(self, value):
        """Updates the color to present SFF value.

        Args:
            value: float, SFF value

        """
        color = [0, 0, 0]
        if 0 <= value <= 1:
            color = [0, 255, int(255*value)]
        self.color = rgb_to_hex(*color)

    def leave(self):
        self.agent = None

    def enter(self, agent):
        """When any agent enters this cell include the cell in the schedule."""
        self.q.append(agent)
        self.model.schedule.add_cell(self)

    def get_agent(self):
        return self.agent

    def evacuate(self):
        """Remove agent from schedule, update statistics, unpair if necessary."""
        if self != self.model.cell_gate:
            return
        if not self.agent:
            raise ValueError("Empty evacuation.")
        # statistics, todo
        if self.agent.name.startswith("Follower"):
            self.model.n_evacuated_followers += 1
        else:
            self.model.n_evacuated_leaders += 1

        # unpair if necessary
        if self.agent.partner:
            self.agent.partner.remove_partner()

        self.model.grid.remove_agent(self.agent)
        self.model.schedule.remove_agent(self.agent)
        # evacuation is in the moment of entrance so it is different from self.cell.leave()
        self.agent = None
