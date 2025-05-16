from random import choice
from mesa import Agent
from environment.resource import ResourceType


def log(agent, msg: str) -> None:
    step = agent.model.schedule.time
    print(f"[StateBased {agent.unique_id:02} | t={step:03}] {msg}")


class StateBasedAgent(Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.memory: set[tuple[int, int]] = set()
        self.visit: dict[tuple[int, int], int] = {}
        self.carrying: ResourceType | None = None
        self.waiting_for_help: bool = False
        self.current_task: dict | None = None
        self.delivered = {rt: 0 for rt in ResourceType}

    def step(self) -> None:
        self.memory.add(self.pos)
        self.visit[self.pos] = self.visit.get(self.pos, 0) + 1
        self._receive_tasks()
        if self.carrying:
            self._return_to_base()
            return
        if self.waiting_for_help:
            self._check_partners()
            return
        if self.current_task:
            self._execute_task()
            return
        self._look_around()
        self._explore()

    def _receive_tasks(self) -> None:
        if (
            self.carrying
            or self.waiting_for_help
            or (self.current_task and self.pos != tuple(self.current_task["position"]))
        ):
            return
        for msg in self.model.message_bus.receive(str(self.unique_id)):
            if msg.get("type") == "task" and msg.get("action") == "collect":
                self.current_task = {
                    "position": tuple(msg["position"]),
                    "resource_type": msg["resource_type"],
                }
                log(self, f"recebeu tarefa em {msg['position']}")

    def _belief(self, p, r) -> None:
        self.model.report_resource(p, r)
        self.model.message_bus.send(
            "BDI", {"type": "belief", "data": {"position": p, "resource_type": r.name}}
        )

    def _check_partners(self) -> None:
        cell = self.model.grid.get_cell_list_contents([self.pos])
        struct = next(
            (
                o
                for o in cell
                if getattr(o, "resource_type", None) == ResourceType.STRUCTURE
            ),
            None,
        )
        if not struct:
            self.waiting_for_help = False
            log(self, "STRUCTURE desapareceu, cancelou espera")
            return
        partners = [
            a
            for a in cell
            if isinstance(a, StateBasedAgent) and a.waiting_for_help and a != self
        ]
        if not partners:
            return
        self.model.grid.remove_agent(struct)
        self.carrying = ResourceType.STRUCTURE
        self.waiting_for_help = False
        for p in partners:
            p.carrying = ResourceType.STRUCTURE
            p.waiting_for_help = False
        ids = [p.unique_id for p in partners]
        log(self, f"coletou STRUCTURE em equipe com {ids}")

    def _execute_task(self):
        dest = self.current_task["position"]
        self.memory.add(dest)
        self._move_towards(dest)
        if self.pos == dest:
            self._look_around()
            if self.carrying is None and not self.waiting_for_help:
                log(self, f"tarefa falhou, recurso não encontrado em {dest}")
                self.current_task = None

    def _look_around(self) -> None:
        nb = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=True
        )
        for p in nb:
            for obj in self.model.grid.get_cell_list_contents([p]):
                if not hasattr(obj, "resource_type"):
                    continue
                rt = obj.resource_type
                self._belief(p, rt)
                if p == self.pos:
                    if rt in (ResourceType.CRYSTAL, ResourceType.METAL):
                        self.model.grid.remove_agent(obj)
                        self.carrying = rt
                        log(self, f"coletou {rt.name}")
                        self.current_task = None
                        return
                    if rt == ResourceType.STRUCTURE:
                        self.waiting_for_help = True
                        log(self, "chegou à STRUCTURE e aguarda parceiro")
                        return
                else:
                    if (
                        rt in (ResourceType.CRYSTAL, ResourceType.METAL)
                        and not self.carrying
                        and not self.current_task
                    ):
                        self.current_task = {"position": p, "resource_type": rt.name}
                        log(self, f"definiu alvo em {p}")
                        return

    def _return_to_base(self):
        self._move_towards(self.model.base_position)
        if self.pos == self.model.base_position:
            self.model.base.deposit(self.carrying, self.unique_id)
            self.delivered[self.carrying] += 1
            log(
                self,
                f"entregou {self.carrying.name} (total={self.delivered[self.carrying]})",
            )
            self.carrying = None
            self.current_task = None

    def _move_towards(self, dest: tuple[int, int]) -> None:
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
        log(self, f"moveu para {(x, y)}")

    def _explore(self) -> None:
        nbrs = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        unseen = [p for p in nbrs if p not in self.memory]
        tgt = choice(unseen) if unseen else choice(nbrs)
        self.model.safe_move(self, tgt)
        log(self, f"explorou para {tgt}")
