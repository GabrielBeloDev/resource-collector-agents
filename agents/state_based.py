from mesa import Agent
from environment.resource import ResourceType
from random import choice


def log(agent, msg):
    print(f"[StateBased {agent.unique_id}] {msg}")


class StateBasedAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.memory = set()
        self.carrying = None
        self.waiting_for_help = False
        self.current_task = None  # ← tarefa do BDI

    def step(self):
        self.memory.add(self.pos)
        self.receive_messages()

        if self.carrying:
            self.move_towards(self.model.base_position)
            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying)
                log(self, f"🎯 entregou {self.carrying.name} na base")
                self.carrying = None
                self.current_task = None
            return

        if self.waiting_for_help:
            self.check_for_partner()
            return

        # Se recebeu tarefa do BDI
        if self.current_task:
            target = self.current_task["position"]
            if target not in self.memory:
                self.memory.add(target)  # marca como visto
            self.move_towards(target)
            if self.pos == target:
                self.look_and_collect()
            return

        # Comportamento normal
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        for mate in cellmates:
            if (
                isinstance(mate, Agent)
                and mate.unique_id != self.unique_id
                and getattr(mate, "waiting_for_help", False)
            ):
                for obj in cellmates:
                    if (
                        hasattr(obj, "resource_type")
                        and obj.resource_type == ResourceType.STRUCTURE
                    ):
                        self.model.grid.remove_agent(obj)
                        self.carrying = ResourceType.STRUCTURE
                        self.waiting_for_help = False
                        mate.carrying = ResourceType.STRUCTURE
                        mate.waiting_for_help = False
                        log(
                            self,
                            f"🤝 ajudou {mate.unique_id} a coletar STRUCTURE em {self.pos}",
                        )
                        return

        self.look_and_collect()
        self.explore()

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

    def look_and_collect(self):
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=True
        )
        for pos in neighbors:
            cellmates = self.model.grid.get_cell_list_contents([pos])
            for obj in cellmates:
                if not hasattr(obj, "resource_type"):
                    continue

                r_type = obj.resource_type

                # Envia percepção ao BDI
                if hasattr(self.model, "message_bus"):
                    self.model.message_bus.send(
                        "BDI",
                        {
                            "type": "belief",
                            "data": {
                                "position": pos,
                                "resource_type": r_type.name,
                            },
                        },
                    )

                if r_type in (ResourceType.CRYSTAL, ResourceType.METAL):
                    self.model.grid.remove_agent(obj)
                    self.carrying = r_type
                    log(self, f"🎒 coletou {r_type.name} em {pos}")
                    self.current_task = None
                    return

                elif r_type == ResourceType.STRUCTURE:
                    self.move_towards(pos)
                    self.waiting_for_help = True
                    log(self, f"⏳ esperando ajuda em {pos} para coletar STRUCTURE")
                    return

    def check_for_partner(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        has_structure = any(
            hasattr(obj, "resource_type")
            and obj.resource_type == ResourceType.STRUCTURE
            for obj in cellmates
        )
        if not has_structure:
            self.waiting_for_help = False
            log(self, f"❌ cancelou espera: STRUCTURE não está mais em {self.pos}")
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
                self.current_task = None
                for partner in partners:
                    partner.carrying = ResourceType.STRUCTURE
                    partner.waiting_for_help = False
                    log(self, f"🤝 coletou STRUCTURE com ajuda de {partner.unique_id}")
                return

    def explore(self):
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        unexplored = [pos for pos in neighbors if pos not in self.memory]

        if unexplored:
            new_pos = choice(unexplored)
        else:
            new_pos = choice(neighbors)

        self.model.safe_move(self, new_pos)
        log(self, f"🧭 moveu-se para {new_pos}")

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
