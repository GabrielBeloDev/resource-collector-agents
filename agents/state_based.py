from mesa import Agent
from random import choice


def log(agent, msg):
    print(f"[State {agent.unique_id}] {msg}")


class StateBasedAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.visited = set()

    def step(self):
        self.visited.add(self.pos)

        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        unvisited = [n for n in neighbors if n not in self.visited]
        new_pos = choice(unvisited) if unvisited else choice(neighbors)

        self.model.safe_move(self, new_pos)
        log(self, f"moveu para {self.pos}")

        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        for obj in cellmates:
            if hasattr(obj, "resource_type") and obj.resource_type.name == "CRYSTAL":
                self.model.grid.remove_agent(obj)
                self.model.base.deposit(obj.resource_type)
                log(self, "coletou CRYSTAL")
                break
