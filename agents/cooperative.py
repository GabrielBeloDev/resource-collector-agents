from mesa import Agent
from environment.resource import ResourceType
from random import choice


def log(agent, msg):
    print(f"[Cooperative {agent.unique_id}] {msg}")


class CooperativeAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.carrying = None
        self.waiting_for_help = False

    def step(self):
        if self.carrying:
            self.move_towards_base()
            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying)
                log(self, f"🎯 entregou {self.carrying.name} na base")
                self.carrying = None
            return

        if self.waiting_for_help:
            self.check_for_partner()
            return

        structure_pos = self.find_best_structure_to_help()
        if structure_pos:
            log(self, f"📍 indo ajudar com STRUCTURE em {structure_pos}")
            self.move_towards(structure_pos)
            if self.pos == structure_pos:
                self.check_for_partner()
            return

        self.random_move()

    def find_best_structure_to_help(self):
        best_pos = None
        best_score = -1
        width, height = self.model.grid.width, self.model.grid.height

        for x in range(width):
            for y in range(height):
                pos = (x, y)
                cellmates = self.model.grid.get_cell_list_contents([pos])
                has_structure = any(
                    hasattr(obj, "resource_type")
                    and obj.resource_type == ResourceType.STRUCTURE
                    for obj in cellmates
                )
                has_waiting_agent = any(
                    isinstance(obj, Agent)
                    and obj.unique_id != self.unique_id
                    and getattr(obj, "waiting_for_help", False)
                    for obj in cellmates
                )
                if has_structure and has_waiting_agent:
                    distance = self.manhattan_distance(pos)
                    score = 1 / distance if distance > 0 else 1.5
                    if score > best_score:
                        best_score = score
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
            for partner in partners:
                partner.carrying = ResourceType.STRUCTURE
                partner.waiting_for_help = False
                log(
                    partner,
                    f"🤝 coletou STRUCTURE com ajuda de CooperativeAgent {self.unique_id}",
                )
            log(
                self,
                f"🧱 coletou STRUCTURE com ajuda de {partners[0].__class__.__name__} {partners[0].unique_id}",
            )
        else:
            log(self, "⏳ chegou na STRUCTURE, mas ainda está esperando ajuda")
            self.waiting_for_help = True

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
            log(self, f"🤷‍♂️ andou aleatoriamente para {self.pos}")
