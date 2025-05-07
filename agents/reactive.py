from mesa import Agent
from environment.resource import ResourceType
from random import choice


def log(agent, msg):
    print(f"[Reactive {agent.unique_id}] {msg}")


class ReactiveAgent(Agent):
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

        collected = self.try_collect_here()
        if collected:
            return

        target = self.find_structure_to_help()
        if target:
            log(self, f"📍 indo ajudar com STRUCTURE em {target}")
            self.move_towards(target)
            if self.pos == target:
                self.check_for_partner()
            return

        self.random_move()

    def try_collect_here(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        for obj in cellmates:
            if hasattr(obj, "resource_type"):
                r_type = obj.resource_type
                if r_type in (ResourceType.CRYSTAL, ResourceType.METAL):
                    self.model.grid.remove_agent(obj)
                    self.carrying = r_type
                    log(self, f"🎒 coletou {r_type.name} em {self.pos}")
                    return True
                elif r_type == ResourceType.STRUCTURE:
                    partners = [
                        a
                        for a in cellmates
                        if isinstance(a, Agent) and a.unique_id != self.unique_id
                    ]
                    if partners:
                        self.model.grid.remove_agent(obj)
                        self.carrying = ResourceType.STRUCTURE
                        for p in partners:
                            p.carrying = ResourceType.STRUCTURE
                            p.waiting_for_help = False
                            log(
                                p,
                                f"🤝 coletou STRUCTURE com ReactiveAgent {self.unique_id}",
                            )
                        log(
                            self,
                            f"🧱 coletou STRUCTURE com ajuda de {partners[0].__class__.__name__} {partners[0].unique_id}",
                        )
                    else:
                        log(
                            self,
                            "⏳ encontrou STRUCTURE mas está sozinho, esperando ajuda",
                        )
                        self.waiting_for_help = True
                    return True
        return False

    def find_structure_to_help(self):
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
                agents_there = len([a for a in cellmates if isinstance(a, Agent)])

                if has_structure:
                    distance = self.manhattan_distance(pos)
                    score = (
                        (1 / distance) * (1 / (1 + agents_there))
                        if distance > 0
                        else 1.5
                    )
                    if score > best_score:
                        best_score = score
                        best_pos = pos

        return best_pos if best_score > 0.05 else None

    def check_for_partner(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        partners = [
            a
            for a in cellmates
            if isinstance(a, Agent) and a.unique_id != self.unique_id
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
            for p in partners:
                p.carrying = ResourceType.STRUCTURE
                p.waiting_for_help = False
                log(p, f"🤝 coletou STRUCTURE com ReactiveAgent {self.unique_id}")
            log(
                self,
                f"🧱 coletou STRUCTURE com ajuda de {partners[0].__class__.__name__} {partners[0].unique_id}",
            )
        else:
            log(self, "⏳ aguardando parceiro para coletar STRUCTURE")

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
