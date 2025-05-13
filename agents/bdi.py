from math import dist
from mesa import Agent
from environment.resource import ResourceType

VALUE = {ResourceType.CRYSTAL: 10, ResourceType.METAL: 20, ResourceType.STRUCTURE: 50}


def log(a, msg):
    step = a.model.schedule.time
    print(f"[BDI {a.unique_id:02} | t={step:03}] {msg}")


class BDIAgent(Agent):
    """
    • Mantém crenças de posição → tipo do recurso.
    • Só delega uma STRUCTURE por vez *por time*.
    """

    def __init__(self, uid, model, bus):
        super().__init__(uid, model)
        self.bus = bus
        self.beliefs: dict[tuple[int, int], ResourceType] = {}
        self.dispatched_GOAL: set[tuple[int, int]] = set()
        self.dispatched_STATE: set[tuple[int, int]] = set()

        # canal próprio
        self.bus.register("BDI")

    # ------------------------------------------------------------ #
    def step(self):
        self._merge_model_beliefs()
        self._receive_beliefs()
        self._delegate("GOAL")
        self._delegate("STATE")

    # ------------------------------------------------------------ #
    #  crenças                                                     #
    # ------------------------------------------------------------ #
    def _merge_model_beliefs(self):
        self.beliefs.update(self.model.known_resources)

    def _receive_beliefs(self):
        for msg in self.bus.receive("BDI"):
            if msg.get("type") == "belief":
                pos = tuple(msg["data"]["position"])
                rt = ResourceType[msg["data"]["resource_type"]]
                self.beliefs[pos] = rt
                self.model.report_resource(pos, rt)

    # ------------------------------------------------------------ #
    #  deliberação / delegação                                     #
    # ------------------------------------------------------------ #
    def _delegate(self, team: str):
        """team='GOAL' ou 'STATE'  → canal broadcast_<team>"""
        disp_set = self.dispatched_GOAL if team == "GOAL" else self.dispatched_STATE

        # recursos ainda não despachados para esse time
        pending = {p: rt for p, rt in self.beliefs.items() if p not in disp_set}
        if not pending:
            return

        # se já há STRUCTURE pendente nesse time, esperar
        if any(self.beliefs[p] == ResourceType.STRUCTURE for p in disp_set):
            return

        best_pos, best_rt = min(
            pending.items(),
            key=lambda kv: (-VALUE[kv[1]], dist(self.model.base_position, kv[0])),
        )

        self.bus.send(
            f"broadcast_{team}",
            {
                "type": "task",
                "action": "collect",
                "position": best_pos,
                "resource_type": best_rt.name,
            },
        )
        disp_set.add(best_pos)
        log(self, f"delegou {best_rt.name} ({team}) em {best_pos}")
