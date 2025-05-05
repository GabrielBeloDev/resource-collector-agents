from mesa import Agent
from random import choice
from environment.resource import ResourceType


def log(agent, msg):
    print(f"[Reactive {agent.unique_id}] {msg}")


class ReactiveAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        new_position = choice(neighbors)
        self.model.safe_move(self, new_position)
        log(self, f"moveu para {self.pos}")

        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        for obj in cellmates:
            if (
                hasattr(obj, "resource_type")
                and obj.resource_type == ResourceType.CRYSTAL
            ):
                self.model.grid.remove_agent(obj)
                self.model.base.deposit(obj.resource_type)
                log(self, "coletou CRYSTAL")
                break
