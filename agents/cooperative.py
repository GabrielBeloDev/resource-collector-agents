from random import choice
from mesa import Agent
from environment.resource import ResourceType


def log(a, m):
    print(f"[Coop {a.unique_id}] {m}")


class CooperativeAgent(Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.carrying = None
        self.waiting_for_help = False
        self.structures = set()
        self.target = None
        self.delivered = {rt: 0 for rt in ResourceType}

    def step(self):
        if self.carrying:
            self._move(self.model.base_position)
            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying, self.unique_id)
                self.delivered[self.carrying] += 1
                log(self, "entregou STRUCTURE na base")
                self.carrying = None
            return
        if self.waiting_for_help:
            self._check()
            return
        self._scan()
        if self.structures:
            b = self._best()
            if b:
                self.target = b
                log(self, f"ajudando em {b}")
                self._move(b)
                if self.pos == b:
                    self._check()
                return
        self._walk()

    def _scan(self):
        self.structures.clear()
        for x in range(self.model.grid.width):
            for y in range(self.model.grid.height):
                if any(
                    getattr(o, "resource_type", None) == ResourceType.STRUCTURE
                    for o in self.model.grid.get_cell_list_contents([(x, y)])
                ):
                    self.structures.add((x, y))

    def _best(self):
        best, u = None, -1
        for p in self.structures:
            d = abs(self.pos[0] - p[0]) + abs(self.pos[1] - p[1])
            w = sum(
                1
                for a in self.model.grid.get_cell_list_contents([p])
                if getattr(a, "waiting_for_help", False)
            )
            val = (1 / (d + 1)) * (1 + w) * ResourceType.STRUCTURE.value
            if val > u:
                best, u = p, val
        return best

    def _check(self):
        cell = self.model.grid.get_cell_list_contents([self.pos])
        for obj in cell:
            if getattr(obj, "resource_type", None) == ResourceType.STRUCTURE:
                self.model.grid.remove_agent(obj)
                self.carrying = ResourceType.STRUCTURE
                for a in cell:
                    if getattr(a, "waiting_for_help", False):
                        a.carrying = ResourceType.STRUCTURE
                        a.waiting_for_help = False
                self.waiting_for_help = False
                log(self, "coleta concluída em parceria")
                return
        self.waiting_for_help = True
        log(self, "aguardando parceiro")

    def _move(self, d):
        x, y = self.pos
        dx, dy = d
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
