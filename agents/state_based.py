from random import choice
from mesa import Agent
from environment.resource import ResourceType


def log(agent, msg: str):
    print(f"[StateBased {agent.unique_id}] {msg}")


class StateBasedAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.memory: set[tuple[int, int]] = set()
        self.carrying: ResourceType | None = None
        self.waiting_for_help = False
        self.current_task = None
        self.delivered = {rt: 0 for rt in ResourceType}

    def step(self):
        self.memory.add(self.pos)
        self._receive_messages()

        if self.carrying:
            self._move_towards(self.model.base_position)
            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying, self.unique_id)
                self.delivered[self.carrying] += 1
                log(self, f"entregou {self.carrying.name} na base")
                self.carrying = None
                self.current_task = None
            return

        if self.waiting_for_help:
            self._check_for_partner()
            return

        if self.current_task:
            target = self.current_task["position"]
            self.memory.add(target)
            self._move_towards(target)
            if self.pos == target:
                self._look_and_collect()
            return

        self._look_and_collect()
        self._explore()

    def _receive_messages(self):
        if self.carrying or self.waiting_for_help:
            return

        if self.current_task and self.pos != tuple(self.current_task["position"]):
            return

        for msg in self.model.message_bus.receive(str(self.unique_id)):
            if msg["type"] == "task" and msg["action"] == "collect":
                self.current_task = {
                    "position": tuple(msg["position"]),
                    "resource_type": msg["resource_type"],
                }
                log(self, f"📥 nova task {msg['resource_type']} em {msg['position']}")

    def _send_belief(self, pos, r_type):
        self.model.report_resource(pos, r_type)
        self.model.message_bus.send(
            "BDI",
            {"type": "belief", "data": {"position": pos, "resource_type": r_type.name}},
        )

    def _check_for_partner(self):
        cellmates = self.model.grid.get_cell_list_contents([self.pos])
        has_structure = any(
            hasattr(o, "resource_type") and o.resource_type == ResourceType.STRUCTURE
            for o in cellmates
        )
        if not has_structure:
            self.waiting_for_help = False
            log(self, "STRUCTURE sumiu, cancelou espera")
            return

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
            for p in partners:
                p.carrying = ResourceType.STRUCTURE
                p.waiting_for_help = False
            log(self, f"coletou STRUCTURE com {[p.unique_id for p in partners]}")

    def _explore(self):
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        unexplored = [p for p in neighbors if p not in self.memory]
        new_pos = choice(unexplored or neighbors)
        self.model.safe_move(self, new_pos)
        log(self, f"moveu-se p/ {new_pos}")

    def _move_towards(self, dest):
        x, y = self.pos
        dx, dy = dest
        if x < dx:
            x += 1
        elif x > dx:
            x -= 1
        elif y < dy:
            y += 1
        elif y > dy:
            y -= 1
        self.model.safe_move(self, (x, y))

    def _look_and_collect(self):
        neighborhood = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=True
        )
        for pos in neighborhood:
            for obj in self.model.grid.get_cell_list_contents([pos]):
                if not hasattr(obj, "resource_type"):
                    continue
                r_type = obj.resource_type
                self._send_belief(pos, r_type)
                if pos == self.pos:
                    # coleta simples de pequenos
                    if r_type in (ResourceType.CRYSTAL, ResourceType.METAL):
                        self.model.grid.remove_agent(obj)
                        self.carrying = r_type
                        log(self, f"coletou {r_type.name} em {pos}")
                        self.current_task = None
                        return

                    # estrutura: tenta parceria, mas se não houver, coleta solo
                    if r_type == ResourceType.STRUCTURE:
                        cellmates = self.model.grid.get_cell_list_contents([pos])
                        partners = [
                            a for a in cellmates
                            if isinstance(a, StateBasedAgent)
                            and a.unique_id != self.unique_id
                            and a.waiting_for_help
                        ]
                        # se encontrou parceiro, mantém coleta cooperativa
                        if partners:
                            self._check_for_partner()
                        else:
                            # coleta solo
                            self.model.grid.remove_agent(obj)
                            self.carrying = ResourceType.STRUCTURE
                            log(self, f"coletou STRUCTURE solo em {pos}")
                        return

                else:
                    if (
                        r_type in (ResourceType.CRYSTAL, ResourceType.METAL)
                        and self.carrying is None
                        and self.current_task is None
                    ):
                        self.current_task = {
                            "position": pos,
                            "resource_type": r_type.name,
                        }
                        return
