from mesa import Agent
from environment.resource import ResourceType
from random import choice


def log(agent, msg):
    print(f"[Reactive {agent.unique_id}] {msg}")


class ReactiveAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.carrying = None
        self.delivered = {
            ResourceType.CRYSTAL: 0,
            ResourceType.METAL: 0,
            ResourceType.STRUCTURE: 0,
        }

    def step(self):
        if self.carrying:
            self.move_towards_base()
            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying, self.unique_id)
                self.delivered[self.carrying] += 1
                log(self, f"entregou {self.carrying.name} na base")
                self.carrying = None
            return

        if self.try_collect_resource():
            return

        self.random_move()

    def try_collect_resource(self):
        for obj in self.model.grid.get_cell_list_contents([self.pos]):
            if hasattr(obj, "resource_type"):
                r_type = obj.resource_type
                if r_type in (ResourceType.CRYSTAL, ResourceType.METAL):
                    self.model.grid.remove_agent(obj)
                    self.carrying = r_type
                    log(self, f"coletou {r_type.name} em {self.pos}")
                    return True
        return False

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
        self.model.safe_move(self, (x, y))

    def random_move(self):
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        if neighbors:
            new_pos = choice(neighbors)
            self.model.safe_move(self, new_pos)
            log(self, f"andou aleatoriamente para {new_pos}")
