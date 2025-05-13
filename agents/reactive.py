from random import choice
from mesa import Agent
from environment.resource import ResourceType


def log(a, m):
    print(f"[Reactive {a.unique_id}] {m}")


class ReactiveAgent(Agent):
    def __init__(self, uid, model):
        super().__init__(uid, model)
        self.carrying = None
        self.delivered = {rt: 0 for rt in ResourceType}

    def step(self):
        if self.carrying:
            self._to_base()
            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying, self.unique_id)
                self.delivered[self.carrying] += 1
                log(self, f"🚚 entregou {self.carrying.name}")
                self.carrying = None
            return
        if self._collect():
            return
        self._walk()

    def _collect(self):
        for obj in self.model.grid.get_cell_list_contents([self.pos]):
            if hasattr(obj, "resource_type"):
                r = obj.resource_type
                if r in (ResourceType.CRYSTAL, ResourceType.METAL):
                    self.model.grid.remove_agent(obj)
                    self.carrying = r
                    log(self, f"💎 pegou {r.name}")
                    return True
        return False

    def _to_base(self):
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

    def _walk(self):
        nbrs = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        if nbrs:
            p = choice(nbrs)
            self.model.safe_move(self, p)
            log(self, f"andou para {p}")
