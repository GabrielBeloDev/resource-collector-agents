from mesa import Agent
from environment.resource import ResourceType


def log(agent, msg):
    print(f"[BDI {agent.unique_id}] {msg}")


class BDIAgent(Agent):
    def __init__(self, unique_id, model, message_bus):
        super().__init__(unique_id, model)
        self.message_bus = message_bus
        self.beliefs: dict[tuple[int, int], ResourceType] = {}
        self.assigned_tasks: set[tuple[int, int]] = set()

    def step(self):
        recebeu_alguma_coisa = False

        for msg in self.message_bus.receive(str(self.unique_id)):
            if msg["type"] == "belief":
                pos = tuple(msg["data"]["position"])
                r_type = ResourceType[msg["data"]["resource_type"]]
                self.beliefs[pos] = r_type
                recebeu_alguma_coisa = True
                log(self, f"🧠 crença atualizada: {r_type.name} em {pos}")

        if recebeu_alguma_coisa:
            log(self, f"📥 total de crenças armazenadas: {len(self.beliefs)}")

        to_remove = []
        for pos, r_type in self.beliefs.items():
            cellmates = self.model.grid.get_cell_list_contents([pos])
            if not any(
                hasattr(obj, "resource_type") and obj.resource_type == r_type
                for obj in cellmates
            ):
                to_remove.append(pos)

        for pos in to_remove:
            log(
                self,
                f"❌ recurso {self.beliefs[pos].name} desapareceu de {pos}, removendo",
            )
            del self.beliefs[pos]
            self.assigned_tasks.discard(pos)

        if not self.beliefs:
            log(self, "📊 painel de recursos: vazio")
            return

        def utilidade(item):
            pos, r_type = item
            dist = self.manhattan_distance(pos)
            agentes_livres = [
                a
                for a in self.model.schedule.agents
                if a.unique_id != self.unique_id
                and getattr(a, "carrying", None) is None
            ]
            return (r_type.value / (dist + 1)) * (1 + len(agentes_livres))

        recursos_disponiveis = [
            item for item in self.beliefs.items() if item[0] not in self.assigned_tasks
        ]

        if not recursos_disponiveis:
            log(self, "🕵️‍♂️ todos os recursos já foram atribuídos")
            return

        best_pos, best_type = max(recursos_disponiveis, key=utilidade)

        agentes_livres = [
            a
            for a in self.model.schedule.agents
            if a.unique_id != self.unique_id and getattr(a, "carrying", None) is None
        ]

        if not agentes_livres:
            log(self, "🙅‍♂️ nenhum agente livre para executar tarefa")
            return

        nearest = min(
            agentes_livres,
            key=lambda a: self.manhattan_distance_between(a.pos, best_pos),
        )

        task_msg = {
            "type": "task",
            "action": "collect",
            "position": best_pos,
            "resource_type": best_type.name,
        }
        self.message_bus.send(str(nearest.unique_id), task_msg)
        self.assigned_tasks.add(best_pos)

        log(
            self,
            f"📩 tarefa enviada → agente {nearest.unique_id} vai coletar {best_type.name} em {best_pos}",
        )
        log(
            self,
            f"📦 tarefas em andamento: {len(self.assigned_tasks)} | crenças ativas: {len(self.beliefs)}",
        )

    def manhattan_distance(self, pos):
        bx, by = self.model.base_position
        return abs(bx - pos[0]) + abs(by - pos[1])

    def manhattan_distance_between(self, pos1, pos2):
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
