from mesa import Agent
from environment.resource import ResourceType
from random import choice


def log(agent, msg):
    print(f"[Coop {agent.unique_id}] {msg}")


class CooperativeAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.carrying = None
        self.waiting_for_help = False
        self.known_structures = set()
        self.target = None

    def step(self):
        if self.carrying:
            self.move_towards(self.model.base_position)
            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying)
                log(self, f"entregou STRUCTURE na base")
                self.carrying = None
            return

        if self.waiting_for_help:
            self.check_for_partner()
            return

        self.scan_for_structures()

        if self.known_structures:
            best = self.choose_best_structure()
            if best:
                self.target = best
                log(self, f"decidiu ajudar em {best}")
                self.move_towards(best)
                if self.pos == best:
                    self.check_for_partner()
                return

        self.random_move()

    def scan_for_structures(self):
        self.known_structures.clear()
        for x in range(self.model.grid.width):
            for y in range(self.model.grid.height):
                pos = (x, y)
                cellmates = self.model.grid.get_cell_list_contents([pos])
                if any(
                    hasattr(obj, "resource_type")
                    and obj.resource_type == ResourceType.STRUCTURE
                    for obj in cellmates
                ):
                    self.known_structures.add(pos)

    def choose_best_structure(self):
        best_pos = None
        best_util = -1
        for pos in self.known_structures:
            dist = self.manhattan_distance(pos)
            waiting = sum(
                1
                for a in self.model.grid.get_cell_list_contents([pos])
                if isinstance(a, Agent) and getattr(a, "waiting_for_help", False)
            )
            util = (1 / (dist + 1)) * (1 + waiting) * ResourceType.STRUCTURE.value
            if util > best_util:
                best_util = util
                best_pos = pos
        return best_pos

    def check_for_partner(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        partners = [
            a
            for a in cellmates
            if isinstance(a, Agent)
            and a.unique_id != self.unique_id
            and getattr(a, "waiting_for_help", False)
        ]
        for obj in cellmates:
            if (
                hasattr(obj, "resource_type")
                and obj.resource_type == ResourceType.STRUCTURE
            ):
                self.model.grid.remove_agent(obj)
                self.carrying = ResourceType.STRUCTURE
                for partner in partners:
                    partner.carrying = ResourceType.STRUCTURE
                    partner.waiting_for_help = False
                self.waiting_for_help = False
                log(
                    self,
                    f"ajudou a coletar STRUCTURE com {partners[0].unique_id if partners else '?'}",
                )
                return

        self.waiting_for_help = True
        log(self, f"chegou na STRUCTURE, aguardando parceiro")

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

    def manhattan_distance(self, pos):
        return abs(self.pos[0] - pos[0]) + abs(self.pos[1] - pos[1])

    def random_move(self):
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        if neighbors:
            new_pos = choice(neighbors)
            self.model.safe_move(self, new_pos)
            log(self, f"andou aleatoriamente para {new_pos}")
