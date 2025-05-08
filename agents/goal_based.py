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
        self.current_task = None

    def step(self):
        self.receive_messages()
        self.scan_environment()
        self.clean_invalid_memory()

        if self.carrying:
            self.move_towards(self.model.base_position)
            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying)
                log(self, f"entregou {self.carrying.name} na base")
                self.carrying = None
                self.current_task = None
            return

        if self.waiting_for_help:
            self.check_for_partner()
            return

        if self.current_task:
            target = self.current_task["position"]
            if target not in self.known_resources:
                log(self, f"tarefa ignorada: recurso não está mais em {target}")
                self.current_task = None
            else:
                self.move_towards(target)
                if self.pos == target:
                    self.collect_resource()
            return

        if self.known_resources:
            target = self.choose_best_resource()
            self.move_towards(target)
            if self.pos == target:
                self.collect_resource()
        else:
            self.random_move()

    def receive_messages(self):
        if hasattr(self.model, "message_bus"):
            for msg in self.model.message_bus.receive(str(self.unique_id)):
                if msg["type"] == "task" and msg["action"] == "collect":
                    self.current_task = {
                        "position": tuple(msg["position"]),
                        "resource_type": msg["resource_type"],
                    }
                    log(
                        self,
                        f"📥 recebeu tarefa de coletar {msg['resource_type']} em {msg['position']}",
                    )

    def scan_environment(self):
        for obj in self.model.grid.get_cell_list_contents([self.pos]):
            if hasattr(obj, "resource_type"):
                self.known_resources[self.pos] = obj.resource_type
                if hasattr(self.model, "message_bus"):
                    self.model.message_bus.send(
                        "BDI",
                        {
                            "type": "belief",
                            "data": {
                                "position": self.pos,
                                "resource_type": obj.resource_type.name,
                            },
                        },
                    )

        for pos in self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        ):
            for obj in self.model.grid.get_cell_list_contents([pos]):
                if hasattr(obj, "resource_type") and pos not in self.known_resources:
                    self.known_resources[pos] = obj.resource_type
                    log(self, f"viu {obj.resource_type.name} em {pos}")
                    if hasattr(self.model, "message_bus"):
                        self.model.message_bus.send(
                            "BDI",
                            {
                                "type": "belief",
                                "data": {
                                    "position": pos,
                                    "resource_type": obj.resource_type.name,
                                },
                            },
                        )

    def clean_invalid_memory(self):
        for pos in list(self.known_resources):
            if not any(
                hasattr(obj, "resource_type")
                for obj in self.model.grid.get_cell_list_contents([pos])
            ):
                del self.known_resources[pos]

    def choose_best_resource(self):
        best = None
        best_score = -1
        for pos, r_type in self.known_resources.items():
            dist = self.manhattan_distance(pos)
            score = r_type.value / (dist + 1)
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
                    log(self, f"coletou {obj.resource_type.name} em {self.pos}")
                    del self.known_resources[self.pos]
                    self.current_task = None
                    return
                elif obj.resource_type == ResourceType.STRUCTURE:
                    self.waiting_for_help = True
                    log(self, "esperando parceiro para coletar STRUCTURE")

    def check_for_partner(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        has_structure = any(
            hasattr(obj, "resource_type")
            and obj.resource_type == ResourceType.STRUCTURE
            for obj in cellmates
        )
        if not has_structure:
            self.waiting_for_help = False
            return

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
                self.waiting_for_help = False
                for partner in partners:
                    partner.carrying = ResourceType.STRUCTURE
                    partner.waiting_for_help = False
                    log(self, f"coletou STRUCTURE com ajuda de {partner.unique_id}")
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

    def manhattan_distance(self, pos):
        return abs(self.pos[0] - pos[0]) + abs(self.pos[1] - pos[1])

    def random_move(self):
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        if neighbors:
            new_pos = choice(neighbors)
            self.model.safe_move(self, new_pos)
            log(self, f"moveu aleatoriamente para {new_pos}")
