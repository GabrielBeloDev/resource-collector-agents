from .terrain import Position


class Base:
    def __init__(self, model, position: Position):
        self.model = model
        self.position = position
        self.storage = {"CRYSTAL": 0, "METAL": 0, "STRUCTURE": 0}

    def deposit(self, resource_type, agent_id=None):
        if resource_type.name in self.storage:
            self.model.total_resources -= 1
            print(f"🔻 Recursos restantes: {self.model.total_resources}")
            self.storage[resource_type.name] += 1
            total = self.get_total_utility()
            print(
                f"[BASE] Recebeu {resource_type.name}  (+{resource_type.value})  → Total={total}"
            )

            if agent_id is not None:
                log = self.model.agents_log.get(agent_id)
                if log is not None:
                    log[resource_type] += 1

    def get_total_utility(self):
        return (
            self.storage["CRYSTAL"] * 10
            + self.storage["METAL"] * 20
            + self.storage["STRUCTURE"] * 50
        )
