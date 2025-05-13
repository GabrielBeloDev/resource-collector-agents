from mesa import Agent
from environment.resource import ResourceType
from random import choice


def log(agent, msg):
    print(f"[Reactive {agent.unique_id}] {msg}")


class ReactiveAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        # Recurso atualmente carregado (None se vazio)
        self.carrying = None
        # Contador de entregas por tipo de recurso
        self.delivered = {
            ResourceType.CRYSTAL: 0,
            ResourceType.METAL: 0,
            ResourceType.STRUCTURE: 0,
        }

    def step(self):
        # Se estiver carregando, volta à base para entregar
        if self.carrying:
            self.move_towards_base()
            # Ao chegar na base, deposita e zera carrying
            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying, self.unique_id)
                self.delivered[self.carrying] += 1
                log(self, f"entregou {self.carrying.name} na base")
                self.carrying = None
            return

        # Tenta coletar recurso na célula atual
        if self.try_collect_resource():
            return

        # Se não coletou nada, movimenta-se aleatoriamente
        self.random_move()

    def try_collect_resource(self):
        # Varre todos os agentes/objetos na própria célula
        for obj in self.model.grid.get_cell_list_contents([self.pos]):
            if hasattr(obj, "resource_type"):
                r_type = obj.resource_type
                # Coleta somente CRYSTAL ou METAL
                if r_type in (ResourceType.CRYSTAL, ResourceType.METAL):
                    self.model.grid.remove_agent(obj)
                    self.carrying = r_type
                    log(self, f"coletou {r_type.name} em {self.pos}")
                    return True
        return False

    def move_towards_base(self):
        # Move um passo em direção à base (distância Manhattan)
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

    def random_move(self):
        # Busca vizinhos ortogonais disponíveis
        neighbors = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        if neighbors:
            new_pos = choice(neighbors)
            self.model.safe_move(self, new_pos)
            log(self, f"andou aleatoriamente para {new_pos}")
