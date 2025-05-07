from mesa import Agent
from environment.resource import ResourceType


def log(agent, msg):
    print(f"[BDI {agent.unique_id}] {msg}")


class BDIAgent(Agent):
    def __init__(self, unique_id, model, message_bus):
        super().__init__(unique_id, model)
        self.message_bus = message_bus
        self.beliefs: dict[tuple[int, int], ResourceType] = {}

    def step(self):
        for msg in self.message_bus.receive(str(self.unique_id)):
            if msg["type"] == "belief":
                pos = tuple(msg["data"]["position"])
                r_type = ResourceType[msg["data"]["resource_type"]]
                self.beliefs[pos] = r_type
                log(self, f"🧠 crença atualizada: {r_type.name} em {pos}")

        panel = ", ".join(f"{rtype.name}@{pos}" for pos, rtype in self.beliefs.items())
        log(self, f"📊 painel de recursos: {panel or 'vazio'}")

        if self.beliefs:
            best_pos, best_type = max(
                self.beliefs.items(),
                key=lambda item: item[1].value / self.manhattan_distance(item[0]),
            )
            free_agents = [
                a
                for a in self.model.schedule.agents
                if getattr(a, "carrying", None) is None
                and a.unique_id != self.unique_id
            ]
            if free_agents:
                nearest = min(
                    free_agents,
                    key=lambda a: abs(a.pos[0] - best_pos[0])
                    + abs(a.pos[1] - best_pos[1]),
                )
                instr = {
                    "type": "task",
                    "action": "collect",
                    "position": best_pos,
                    "resource_type": best_type.name,
                }
                self.message_bus.send(str(nearest.unique_id), instr)
                log(
                    self,
                    f"📩 instruiu {nearest.__class__.__name__} {nearest.unique_id} a coletar {best_type.name} em {best_pos}",
                )

    def manhattan_distance(self, pos: tuple[int, int]) -> int:
        bx, by = self.model.base_position
        return abs(bx - pos[0]) + abs(by - pos[1])
