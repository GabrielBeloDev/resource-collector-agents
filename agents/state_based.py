from mesa import Agent
from random import choice
from environment.resource import ResourceType


def log(agent, msg):
    print(f"[StateBased {agent.unique_id}] {msg}")


class StateBasedAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.visited = set()
        self.carrying = None
        self.known_agents = {}
        self.known_structures = set()
        self.waiting_for_help = False

    def step(self):
        self.visited.add(self.pos)

        if self.carrying:
            self.move_towards_base()
            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying)
                log(self, f"entregou {self.carrying.name}")
                self.carrying = None
        elif self.waiting_for_help:
            self.check_for_partner()
        else:
            self.explore_and_collect()

    def explore_and_collect(self):
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        unexplored = [p for p in neighbors if p not in self.visited]
        options = unexplored if unexplored else neighbors

        if options:
            new_pos = choice(options)
            self.model.safe_move(self, new_pos)
            log(self, f"andou para {self.pos}")
            self.check_surroundings()

    def check_surroundings(self):
        for obj in self.model.grid.get_cell_list_contents([self.pos]):
            if hasattr(obj, "resource_type"):
                if obj.resource_type in (ResourceType.CRYSTAL, ResourceType.METAL):
                    self.model.grid.remove_agent(obj)
                    self.carrying = obj.resource_type
                    log(self, f"coletou {obj.resource_type.name}")
                    break
                elif obj.resource_type == ResourceType.STRUCTURE:
                    self.known_structures.add(self.pos)
                    self.waiting_for_help = True
                    log(self, "encontrou STRUCTURE e está aguardando ajuda")
            elif isinstance(obj, Agent) and obj.unique_id != self.unique_id:
                self.known_agents[obj.unique_id] = obj.pos
                log(self, f"avistou agente {obj.unique_id} na posição {obj.pos}")

    def check_for_partner(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        partners = [
            a
            for a in cellmates
            if isinstance(a, StateBasedAgent) and a.unique_id != self.unique_id
        ]

        if partners:
            for obj in cellmates:
                if (
                    hasattr(obj, "resource_type")
                    and obj.resource_type == ResourceType.STRUCTURE
                ):
                    self.model.grid.remove_agent(obj)
                    break
            self.carrying = ResourceType.STRUCTURE
            self.waiting_for_help = False
            log(self, f"coletou STRUCTURE com ajuda de agente {partners[0].unique_id}")
        else:
            log(self, "aguardando parceiro para coletar STRUCTURE")

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
