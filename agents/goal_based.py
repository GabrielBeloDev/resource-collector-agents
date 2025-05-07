from mesa import Agent
from environment.resource import ResourceType
from random import choice


def log(agent, msg):
    print(f"[GoalBased {agent.unique_id}] {msg}")


class GoalBasedAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.carrying = None
        self.known_resources = {}
        self.waiting_for_help = False

    def step(self):
        if self.carrying:
            self.move_towards(self.model.base_position)
            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying)
                log(self, f"🎯 entregou {self.carrying.name} na base")
                self.carrying = None
            return

        self.update_knowledge()
        self.clean_known_resources()

        if self.waiting_for_help:
            self.check_for_partner()
            return

        if self.known_resources:
            target = self.get_best_resource()
            log(
                self,
                f"📌 indo para recurso em {target} ({self.known_resources[target].name})",
            )
            self.move_towards(target)

            if self.pos == target:
                self.collect_resource()
        else:
            self.random_move()

    def update_knowledge(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        for obj in cellmates:
            if hasattr(obj, "resource_type"):
                self.known_resources[self.pos] = obj.resource_type
                log(
                    self,
                    f"🧠 memorizou {obj.resource_type.name} na própria célula {self.pos}",
                )

        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        for pos in neighbors:
            for obj in self.model.grid.get_cell_list_contents([pos]):
                if hasattr(obj, "resource_type"):
                    if pos not in self.known_resources:
                        self.known_resources[pos] = obj.resource_type
                        log(
                            self,
                            f"🧠 viu e memorizou {obj.resource_type.name} em {pos}",
                        )

    def clean_known_resources(self):
        to_delete = []
        for pos in self.known_resources:
            cellmates = self.model.grid.get_cell_list_contents([pos])
            if not any(hasattr(obj, "resource_type") for obj in cellmates):
                to_delete.append(pos)
                log(self, f"🗑️ removeu recurso de {pos} da memória")

        for pos in to_delete:
            del self.known_resources[pos]

    def get_best_resource(self):
        best = None
        best_score = -1
        for pos, r_type in self.known_resources.items():
            dist = self.manhattan_distance(pos)
            if dist == 0:
                return pos
            score = r_type.value / dist
            if score > best_score:
                best = pos
                best_score = score
        return best

    def collect_resource(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        for obj in cellmates:
            if hasattr(obj, "resource_type"):
                if obj.resource_type in (ResourceType.CRYSTAL, ResourceType.METAL):
                    self.model.grid.remove_agent(obj)
                    self.carrying = obj.resource_type
                    del self.known_resources[self.pos]
                    log(self, f"🎒 coletou {obj.resource_type.name} em {self.pos}")
                    return
                elif obj.resource_type == ResourceType.STRUCTURE:
                    partners = [
                        a
                        for a in cellmates
                        if isinstance(a, Agent)
                        and a.unique_id != self.unique_id
                        and getattr(a, "waiting_for_help", False)
                    ]
                    if partners:
                        self.model.grid.remove_agent(obj)
                        self.carrying = ResourceType.STRUCTURE
                        self.waiting_for_help = False
                        for partner in partners:
                            partner.carrying = ResourceType.STRUCTURE
                            partner.waiting_for_help = False
                            log(
                                partner,
                                f"🤝 coletou STRUCTURE com ajuda de {self.__class__.__name__} {self.unique_id}",
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
                    return

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
                    self.carrying = ResourceType.STRUCTURE
                    self.waiting_for_help = False
                    log(
                        self,
                        f"🧱 coletou STRUCTURE com ajuda de agente {partners[0].unique_id}",
                    )
                    break
        else:
            log(self, "⏳ aguardando parceiro para pegar STRUCTURE")

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
