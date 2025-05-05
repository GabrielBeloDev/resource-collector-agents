from mesa import Agent
from environment.resource import ResourceType


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

    def perceive(self):
        for obj in self.model.grid.get_cell_list_contents([self.pos]):
            if hasattr(obj, "resource_type"):
                self.beliefs[self.pos] = obj.resource_type
                self.broadcast_belief(self.pos, obj.resource_type)

        for msg in self.message_bus.receive(str(self.unique_id)):
            if msg["type"] == "belief":
                pos = tuple(msg["data"]["position"])
                r_type = ResourceType[msg["data"]["resource_type"]]
                self.beliefs[pos] = r_type

    def broadcast_belief(self, pos, r_type):
        for i in range(10):
            if i != self.unique_id:
                self.message_bus.send(
                    str(i),
                    {
                        "type": "belief",
                        "data": {"position": pos, "resource_type": r_type.name},
                    },
                )

    def deliberate(self):
        resources = [(p, t) for p, t in self.beliefs.items() if t in self.desires]
        if resources:
            resources.sort(key=lambda r: (-r[1].value, self.distance_to(r[0])))
            self.intentions = [resources[0][0]]

    def step(self):
        self.perceive()
        self.deliberate()

        if self.intentions:
            target = self.intentions[0]
            self.model.safe_move(self, target)
            for obj in self.model.grid.get_cell_list_contents([self.pos]):
                if hasattr(obj, "resource_type"):
                    self.model.grid.remove_agent(obj)
                    self.model.base.deposit(obj.resource_type)
                    self.intentions.pop(0)
                    break

    def distance_to(self, pos):
        return abs(self.pos[0] - pos[0]) + abs(self.pos[1] - pos[1])
