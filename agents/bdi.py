from mesa import Agent
from environment.resource import ResourceType


def log(agent, msg):
    print(f"[BDI {agent.unique_id}] {msg}")


class BDIAgent(Agent):
    def __init__(self, uid, model, message_bus):
        super().__init__(uid, model)
        self.message_bus = message_bus
        self.beliefs = {}
        self.intentions = []
        self.desires = [
            ResourceType.STRUCTURE,
            ResourceType.METAL,
            ResourceType.CRYSTAL,
        ]

    def step(self):
        self.perceive()
        self.deliberate()
        self.act()

    def perceive(self):
        for msg in self.message_bus.receive(str(self.unique_id)):
            if msg["type"] == "belief":
                pos = tuple(msg["data"]["position"])
                r_type = ResourceType[msg["data"]["resource_type"]]
                self.beliefs[pos] = r_type
                log(self, f"crença atualizada: {r_type.name} em {pos}")

        to_remove = []
        for pos, r_type in self.beliefs.items():
            cellmates = self.model.grid.get_cell_list_contents([pos])
            if not any(
                hasattr(obj, "resource_type") and obj.resource_type == r_type
                for obj in cellmates
            ):
                to_remove.append(pos)

        for pos in to_remove:
            del self.beliefs[pos]
            log(self, f"recurso {r_type.name} desapareceu de {pos}, removendo")

    def deliberate(self):
        self.intentions.clear()
        for pos, r_type in self.beliefs.items():
            if r_type in self.desires:
                self.intentions.append({"position": pos, "resource_type": r_type})

    def act(self):
        log(self, f"painel de recursos: {'vazio' if not self.intentions else ''}")
        for intention in self.intentions:
            for agent in self.model.schedule.agents:
                if (
                    isinstance(agent, Agent)
                    and agent.unique_id != self.unique_id
                    and hasattr(agent, "current_task")
                    and agent.current_task is None
                ):
                    self.message_bus.send(
                        str(agent.unique_id),
                        {
                            "type": "task",
                            "action": "collect",
                            "position": intention["position"],
                            "resource_type": intention["resource_type"].name,
                        },
                    )
