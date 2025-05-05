from .terrain import Position


class Base:
    def __init__(self, position: Position):
        self.position = position
        self.storage = {"CRYSTAL": 0, "METAL": 0, "STRUCTURE": 0}

    def deposit(self, resource_type):
        if resource_type.name in self.storage:
            self.storage[resource_type.name] += 1
            total = self.get_total_utility()
            print(
                f"[BASE] Recebeu {resource_type.name}  (+{resource_type.value})  → Total={total}"
            )

    def get_total_utility(self):
        return (
            self.storage["CRYSTAL"] * 10
            + self.storage["METAL"] * 20
            + self.storage["STRUCTURE"] * 50
        )
