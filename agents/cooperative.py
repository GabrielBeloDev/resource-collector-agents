from mesa import Agent
from environment.resource import ResourceType
from random import choice


def log(agent, msg):
    print(f"[Coop {agent.unique_id}] {msg}")


class CooperativeAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        for pos in neighbors:
            cellmates = self.model.grid.get_cell_list_contents([pos])
            for obj in cellmates:
                if (
                    hasattr(obj, "resource_type")
                    and obj.resource_type == ResourceType.STRUCTURE
                ):
                    if self.has_ally_near(pos):
                        self.model.grid.remove_agent(obj)
                        self.model.base.deposit(ResourceType.STRUCTURE)
                        self.model.safe_move(self, pos)
                        log(self, f"coletou STRUCTURE em {pos} (cooperação)")
                        return

        new_pos = choice(neighbors)
        self.model.safe_move(self, new_pos)
        log(self, f"moveu para {self.pos}")

    def has_ally_near(self, pos):
        allies = [
            a
            for a in self.model.grid.get_cell_list_contents([pos])
            if isinstance(a, Agent) and a != self
        ]
        return len(allies) >= 1

    def random_move(self):
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        if neighbors:
            self.model.safe_move(self, choice(neighbors))
