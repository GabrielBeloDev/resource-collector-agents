from math import dist
from random import choice
from mesa import Agent
from environment.resource import ResourceType

VALUE = {ResourceType.CRYSTAL: 10, ResourceType.METAL: 20, ResourceType.STRUCTURE: 50}


def log(a, m):
    s = a.model.schedule.time
    print(f"[GoalBased {a.unique_id:02} | t={s:03}] {m}")


class GoalBasedAgent(Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.carrying = None
        self.waiting_for_help = False
        self.current_task = None
        self.known = {}
        self.path = []
        self.delivered = {rt: 0 for rt in ResourceType}
        model.message_bus.register(str(uid))

    def step(self):
        self._sync_beliefs()
        self._receive_tasks()
        if self.carrying and self.pos == self.model.base_position:
            self._deliver()
        if self.carrying is None:
            if self.waiting_for_help:
                self._check_for_partner()
            else:
                self._look_and_collect()
        if not self.path:
            self._deliberate()
        if self.path:
            self._move_along_path()

    def _receive_tasks(self):
        # Lê mensagens de tarefa em canais dedicados
        for chan in (str(self.unique_id), "broadcast_GOAL"):
            for msg in self.model.message_bus.receive(chan):
                if msg.get("type") == "task" and msg.get("action") == "collect":
                    self.current_task = {
                        "position": tuple(msg["position"]),
                        "resource_type": msg["resource_type"],
                    }
                    self.path.clear()
                    log(self, f"📥 task {msg['resource_type']} em {msg['position']}")

    def _sync_beliefs(self):
        # Sincroniza mapa interno com informações do modelo e vizinhança
        self.known.update(self.model.known_resources)
        for p in list(self.known):
            if not any(hasattr(o, "resource_type") for o in self.model.grid.get_cell_list_contents([p])):
                self.known.pop(p, None)
                self.model.consume_resource_info(p)
        for p in self.model.grid.get_neighborhood(self.pos, moore=False, include_center=True):
            for obj in self.model.grid.get_cell_list_contents([p]):
                if not hasattr(obj, "resource_type"):
                    continue
                rt = obj.resource_type
                if p not in self.known:
                    log(self, f"👀 viu {rt.name} em {p}")
                self.known[p] = rt
                self.model.message_bus.send(
                    "BDI",
                    {"type": "belief", "data": {"position": p, "resource_type": rt.name}},
                )

    def _deliberate(self):
        # Decide próximo destino com base em tarefa ou utilidade
        if self.current_task and tuple(self.current_task["position"]) in self.known:
            g = tuple(self.current_task["position"])
            self.path = self._plan_path(self.pos, g)
            log(self, f"🎯 alvo TASK em {g}")
            return
        if not self.known:
            self._random_explore()
            return
        best_pos, best_rt = min(
            self.known.items(), key=lambda kv: (-VALUE[kv[1]], dist(self.pos, kv[0]))
        )
        self.path = self._plan_path(self.pos, best_pos)
        log(self, f"🎯 alvo {best_rt.name} em {best_pos}")

    def _look_and_collect(self):
        # Coleta recursos ao redor imediatamente ou aguarda parceiro para STRUCTURE
        cell = self.model.grid.get_cell_list_contents([self.pos])
        for obj in cell:
            rt = getattr(obj, "resource_type", None)
            if rt is None:
                continue
            if rt in (ResourceType.CRYSTAL, ResourceType.METAL):
                self.model.grid.remove_agent(obj)
                self._start_return(rt)
                return
            if rt == ResourceType.STRUCTURE:
                self.waiting_for_help = True
                log(self, "🏗 chegou na STRUCTURE • WAIT")
                return

    def _check_for_partner(self):
        # Verifica e executa coleta cooperativa de STRUCTURE
        cell = self.model.grid.get_cell_list_contents([self.pos])
        if not any(getattr(o, "resource_type", None) == ResourceType.STRUCTURE for o in cell):
            self.waiting_for_help = False
            log(self, "⚠️ STRUCTURE sumiu")
            return
        partners = [
            a for a in cell
            if isinstance(a, GoalBasedAgent) and a.waiting_for_help and a.unique_id != self.unique_id
        ]
        if partners:
            for obj in cell:
                if getattr(obj, "resource_type", None) == ResourceType.STRUCTURE:
                    self.model.grid.remove_agent(obj)
                    break
            self.carrying = ResourceType.STRUCTURE
            self.waiting_for_help = False
            for p in partners:
                p.carrying = ResourceType.STRUCTURE
                p.waiting_for_help = False
            self.model.consume_resource_info(self.pos)
            log(self, f"🤝 cooperou com {[p.unique_id for p in partners]}")

    def _plan_path(self, s, g):
        # Gera caminho Manhattan direto de s até g
        x, y = s
        gx, gy = g
        path = []
        while (x, y) != (gx, gy):
            if x < gx:
                x += 1
            elif x > gx:
                x -= 1
            elif y < gy:
                y += 1
            elif y > gy:
                y -= 1
            path.append((x, y))
        return path

    def _random_explore(self):
        nbrs = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        if nbrs:
            t = choice(nbrs)
            self.path = [t]
            log(self, f"🔄 explorou → {t}")

    def _move_along_path(self):
        nxt = self.path.pop(0)
        self.model.safe_move(self, nxt)
        log(self, f"🚶 moveu-se para {nxt}")

    def _start_return(self, rt):
        self.carrying = rt
        self.known.pop(self.pos, None)
        self.model.consume_resource_info(self.pos)
        log(self, f"📦 coletou {rt.name}")
        self.path = self._plan_path(self.pos, self.model.base_position)

    def _deliver(self):
        self.model.base.deposit(self.carrying, self.unique_id)
        self.delivered[self.carrying] += 1
        log(self, f"🚚 entregou {self.carrying.name} | total={self.delivered}")
        self.carrying = None
        self.current_task = None
        self.path.clear()
