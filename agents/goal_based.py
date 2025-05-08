from mesa import Agent
from environment.resource import ResourceType
from random import choice


def log(agent, msg):
    print(f"[GoalBased {agent.unique_id}] {msg}")


class GoalBasedAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.carrying = None
        self.target = None
        self.name = "Goal-Based"
        self.delivered = {
            ResourceType.CRYSTAL: 0,
            ResourceType.METAL: 0,
            ResourceType.STRUCTURE: 0,
        }

    def step(self):
        if self.carrying:
            self.move_towards(self.model.base_position)
            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying, self.unique_id)
                self.delivered[self.carrying] += 1
                log(self, f"entregou {self.carrying.name} na base")
                self.carrying = None
                self.target = None
            return

        if self.target:
            self.move_towards(self.target)
            if self.pos == self.target:
                self.collect_resource()
            return

        self.look_for_resources()
        if not self.target:
            self.random_move()

    def look_for_resources(self):
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=True
        )
        for pos in neighbors:
            cellmates = self.model.grid.get_cell_list_contents([pos])
            for obj in cellmates:
                if (
                    hasattr(obj, "resource_type")
                    and obj.resource_type != ResourceType.STRUCTURE
                ):
                    self.target = pos
                    log(self, f"viu {obj.resource_type.name} em {pos}")
                    return

    def collect_resource(self):
        for obj in self.model.grid.get_cell_list_contents([self.pos]):
            if (
                hasattr(obj, "resource_type")
                and obj.resource_type != ResourceType.STRUCTURE
            ):
                self.carrying = obj.resource_type
                self.model.grid.remove_agent(obj)
                log(self, f"coletou {self.carrying.name} em {self.pos}")
                return

    def move_towards(self, destination):
        x, y = self.pos
        dx, dy = destination
        if x < dx:
            x += 1
        elif x > dx:
            x -= 1
        elif y < dy:
            y += 1
        elif y > dy:
            y -= 1
        self.model.safe_move(self, (x, y))

    def random_move(self):
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        if neighbors:
            new_pos = choice(neighbors)
            self.model.safe_move(self, new_pos)
            log(self, f"moveu para {new_pos}")
