from mesa import Agent


def log(agent, msg):
    print(f"[{agent.__class__.__name__} {agent.unique_id}] {msg}")


class GoalBasedAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        resources = []
        width, height = self.model.grid.width, self.model.grid.height
        for x in range(width):
            for y in range(height):
                cellmates = self.model.grid.get_cell_list_contents([(x, y)])
                for obj in cellmates:
                    if hasattr(obj, "resource_type"):
                        resources.append(((x, y), obj.resource_type))

        if not resources:
            return

        resources.sort(key=lambda r: self.manhattan_distance(r[0]))
        target_pos = resources[0][0]

        self.model.safe_move(self, target_pos)
        if self.pos != target_pos:
            log(self, f"moveu para {self.pos}")

        cellmates = self.model.grid.get_cell_list_contents([self.pos])

        for obj in cellmates:
            if hasattr(obj, "resource_type"):
                self.model.grid.remove_agent(obj)
                self.model.base.deposit(obj.resource_type)
                log(self, f"coletou {obj.resource_type.name} em {self.pos}")
                break

    def manhattan_distance(self, pos):
        return abs(self.pos[0] - pos[0]) + abs(self.pos[1] - pos[1])
