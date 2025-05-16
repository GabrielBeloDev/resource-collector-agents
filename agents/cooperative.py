from random import choice
from mesa import Agent
from environment.resource import ResourceType


DISPLAY = {
    ResourceType.CRYSTAL: 10,
    ResourceType.METAL: 20,
    ResourceType.STRUCTURE: 50,
}

_KEY = 37


def _hidden(rt):
    v = DISPLAY[rt]
    return ((v ^ _KEY) + v) * 1.5


def log(a, m):
    t = a.model.schedule.time
    print(f"[Coop {a.unique_id:02} | t={t:03}] {m}")


class CooperativeAgent(Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.carrying = None
        self.waiting_for_help = False
        self.sights: dict[tuple[int, int], ResourceType] = {}
        self.target = None
        self.delivered = {rt: 0 for rt in ResourceType}

    def step(self):
        if self.carrying:
            self._go_to_base()
            return
        if self._collect_here():
            return
        if self.waiting_for_help:
            self._check_partnership()
            return
        self._scan()
        if self.sights:
            dest, rt = self._best()
            self.target = dest
            log(self, f"alvo {rt.name} em {dest}")
            self._move(dest)
            if self.pos == dest:
                if rt == ResourceType.STRUCTURE:
                    self._check_partnership()
                else:
                    self._collect_here()
            return
        self._walk()

    def _collect_here(self):
        for obj in self.model.grid.get_cell_list_contents([self.pos]):
            rt = getattr(obj, "resource_type", None)
            if rt in (ResourceType.CRYSTAL, ResourceType.METAL):
                self.model.grid.remove_agent(obj)
                self.carrying = rt
                self.model.consume_resource_info(self.pos)
                log(self, f"coletou {rt.name}")
                return True
        return False

    def _scan(self):
        self.sights.clear()
        for x in range(self.model.grid.width):
            for y in range(self.model.grid.height):
                for obj in self.model.grid.get_cell_list_contents([(x, y)]):
                    rt = getattr(obj, "resource_type", None)
                    if rt is None:
                        continue
                    self.sights[(x, y)] = rt

    def _check_partnership(self):
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
            return
        partners = [
            a for a in cell if getattr(a, "waiting_for_help", False) and a != self
        ]
        if partners:
            self.model.grid.remove_agent(struct)
            self.carrying = ResourceType.STRUCTURE
            self.waiting_for_help = False
            for p in partners:
                p.carrying = ResourceType.STRUCTURE
                p.waiting_for_help = False
                if hasattr(p, "_start_return"):
                    p._start_return(ResourceType.STRUCTURE)
            self.model.consume_resource_info(self.pos)
            ids = [p.unique_id for p in partners]
            log(self, f"coletou STRUCTURE em equipe com {ids}")
        else:
            self.waiting_for_help = True
            log(self, "chegou primeiro, aguardando parceiro")

    def _go_to_base(self):
        self._move(self.model.base_position)
        if self.pos == self.model.base_position:
            self.model.base.deposit(self.carrying, self.unique_id)
            self.delivered[self.carrying] += 1
            log(
                self,
                f"entregou {self.carrying.name} (total={self.delivered[self.carrying]})",
            )
            self.carrying = None

    def _move(self, dest):
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

    def _walk(self):
        nbrs = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        if nbrs:
            p = choice(nbrs)
            self.model.safe_move(self, p)
            log(self, f"andou para {p}")

    def _best(self):
        best_p, best_rt, best_v = None, None, -1
        for p, rt in self.sights.items():
            d = abs(self.pos[0] - p[0]) + abs(self.pos[1] - p[1])
            base_val = _hidden(rt)
            if rt == ResourceType.STRUCTURE:
                w = sum(
                    1
                    for a in self.model.grid.get_cell_list_contents([p])
                    if getattr(a, "waiting_for_help", False)
                )
                val = (1 / (d + 1)) * (1 + w) * base_val
            else:
                val = (1 / (d + 1)) * base_val
            if val > best_v:
                best_p, best_rt, best_v = p, rt, val
        return best_p, best_rt
