from mesa import Agent
from random import choice
from environment.resource import ResourceType


def log(agent, msg):
    print(f"[Reactive {agent.unique_id}] {msg}")


class ReactiveAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.carrying = None

    def step(self):
        if self.carrying:
            self.move_towards_base()

            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying)
                log(self, f"entregou {self.carrying.name} na base")
                self.carrying = None
        else:
            neighbors = self.model.grid.get_neighborhood(
                self.pos, moore=False, include_center=False
            )
            new_pos = choice(neighbors)
            self.model.safe_move(self, new_pos)
            log(self, f"andou para {self.pos}")

            for obj in self.model.grid.get_cell_list_contents([self.pos]):
                if (
                    hasattr(obj, "resource_type")
                    and obj.resource_type == ResourceType.CRYSTAL
                ):
                    self.model.grid.remove_agent(obj)
                    self.carrying = obj.resource_type
                    log(self, f"coletou {obj.resource_type.name}")
                    break

    def move_towards_base(self):
        x, y = self.pos
        bx, by = self.model.base_position

        if x < bx:
            x += 1
        elif x > bx:
            x -= 1
        elif y < by:
            y += 1
        elif y > by:
            y -= 1

        new_pos = (x, y)
        self.model.safe_move(self, new_pos)
