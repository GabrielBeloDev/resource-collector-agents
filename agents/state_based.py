from random import choice
from mesa import Agent
from environment.resource import ResourceType


def log(a, m):
    print(f"[StateBased {a.unique_id:02}] {m}")


class StateBasedAgent(Agent):
    def __init__(self, uid, model):
        # Inicializa estado interno e estatísticas do agente
        super().__init__(uid, model)
        self.memory: set[tuple[int, int]] = set()
        self.visit: dict[tuple[int, int], int] = {}
        self.carrying: ResourceType | None = None
        self.waiting_for_help: bool = False
        self.current_task: dict | None = None
        self.delivered = {rt: 0 for rt in ResourceType}

    def step(self) -> None:
        # Fluxo principal: processa entrega, cooperação ou explora/coleta
        self.memory.add(self.pos)
        self.visit[self.pos] = self.visit.get(self.pos, 0) + 1

        self._receive()
        if self.carrying:
            self._move(self.model.base_position)
            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying, self.unique_id)
                self.delivered[self.carrying] += 1
                log(self, f"entregou {self.carrying.name}")
                self.carrying = None
                self.current_task = None
            return

        if self.waiting_for_help:
            self._check()
            return

        if self.current_task:
            tgt = self.current_task["position"]
            self.memory.add(tgt)
            self._move_towards(tgt)
            if self.pos == tgt:
                self._look()
                if self.carrying is None and not self.waiting_for_help:
                    log(self, f"tarefa inválida em {tgt}")
                    self.current_task = None
            return

        self._look()
        self._explore()

    def _receive(self) -> None:
        # Lê mensagens de tarefa do BDI
        if self.carrying or self.waiting_for_help:
            return
        if self.current_task and self.pos != tuple(self.current_task["position"]):
            return
        for msg in self.model.message_bus.receive(str(self.unique_id)):
            if msg.get("type") == "task" and msg.get("action") == "collect":
                self.current_task = {
                    "position": tuple(msg["position"]),
                    "resource_type": msg["resource_type"],
                }
                log(self, f"recebeu tarefa em {msg['position']}")

    def _belief(self, p, r) -> None:
        # Envia informação de recurso avistado ao BDI
        self.model.report_resource(p, r)
        self.model.message_bus.send(
            "BDI",
            {"type": "belief", "data": {"position": p, "resource_type": r.name}},
        )

    def _check(self) -> None:
        # Coordena coleta em STRUCTURE com outro agente ou solo
        cell = self.model.grid.get_cell_list_contents([self.pos])
        if not any(getattr(o, "resource_type", None) == ResourceType.STRUCTURE for o in cell):
            self.waiting_for_help = False
            log(self, "STRUCTURE sumiu")
            return
        partners = [
            a for a in cell
            if isinstance(a, StateBasedAgent) and a.waiting_for_help and a.unique_id != self.unique_id
        ]
        for obj in cell:
            if getattr(obj, "resource_type", None) == ResourceType.STRUCTURE:
                self.model.grid.remove_agent(obj)
                break
        self.carrying = ResourceType.STRUCTURE
        self.waiting_for_help = False
        for p in partners:
            p.carrying = ResourceType.STRUCTURE
            p.waiting_for_help = False
        log(self, "coletou STRUCTURE" + (f" com {[p.unique_id for p in partners]}" if partners else " sozinho"))

    def _explore(self) -> None:
        # Move para vizinho menos visitado para cobrir o grid
        nbrs = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        unseen = [p for p in nbrs if p not in self.memory]
        tgt = choice(unseen) if unseen else choice(nbrs)
        self.model.safe_move(self, tgt)
        log(self, f"explorou → {tgt}")

    def _move_towards(self, dest: tuple[int, int]) -> None:
        # Dá um passo em direção Manhattan ao destino
        x, y = self.pos
        dx, dy = dest
        if x < dx: x += 1
        elif x > dx: x -= 1
        elif y < dy: y += 1
        elif y > dy: y -= 1
        self.model.safe_move(self, (x, y))
        log(self, f"movendo-se para {(x, y)}")

    _move = _move_towards  # retorno à base usa mesma lógica

    def _look(self) -> None:
        # Examina célula atual e adjacentes para coletar ou agendar tarefa
        nb = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=True)
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
                        log(self, "esperando ajuda")
                        return
                else:
                    if rt in (ResourceType.CRYSTAL, ResourceType.METAL) and not self.carrying and not self.current_task:
                        self.current_task = {"position": p, "resource_type": rt.name}
                        log(self, f"alvo em {p}")
                        return
