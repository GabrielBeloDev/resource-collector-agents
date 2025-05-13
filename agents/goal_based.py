from mesa import Agent
from environment.resource import ResourceType
from random import choice


def log(agent, msg):
    print(f"[GoalBased {agent.unique_id}] {msg}")


class GoalBasedAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.carrying = None                          
        self.known_resources: dict[tuple,int] = {}     
        self.waiting_for_help = False                 
        self.current_task = None                      
        self.delivered = {rt: 0 for rt in ResourceType}

    def step(self):
        self.receive_messages()       
        self.scan_environment()       
        self.clean_invalid_memory()   

        # Entrega se estiver carregando
        if self.carrying:
            self.move_towards(self.model.base_position)
            if self.pos == self.model.base_position:
                self.model.base.deposit(self.carrying, self.unique_id)
                self.delivered[self.carrying] += 1
                log(self, f"entregou {self.carrying.name}")
                self.carrying = None
                self.current_task = None
            return

        # Se aguardando parceiro para STRUCTURE
        if self.waiting_for_help:
            self.check_for_partner()
            return

        # Se há tarefa do BDI, a executa
        if self.current_task:
            tgt = tuple(self.current_task["position"])
            if tgt not in self.known_resources:
                log(self, f"tarefa inválida em {tgt}")
                self.current_task = None
            else:
                self.move_towards(tgt)
                if self.pos == tgt:
                    self.collect_resource()
            return

        # Caso contrário, busca o melhor recurso 
        if self.known_resources:
            tgt = self.choose_best_resource()
            self.move_towards(tgt)
            if self.pos == tgt:
                self.collect_resource()
        else:
            self.random_move()

    def receive_messages(self):
        for msg in self.model.message_bus.receive(str(self.unique_id)):
            if msg.get("type") == "task":
                self.current_task = {
                    "position": tuple(msg["position"]),
                    "resource_type": msg["resource_type"],
                }
                log(self, f"recebeu tarefa em {msg['position']}")

    def scan_environment(self):
        # reporta crenças sobre recursos na própria e vizinhas células
        positions = [self.pos] + self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        for pos in positions:
            for obj in self.model.grid.get_cell_list_contents([pos]):
                if hasattr(obj, "resource_type") and pos not in self.known_resources:
                    self.known_resources[pos] = obj.resource_type
                    log(self, f"viu {obj.resource_type.name} em {pos}")
                    self.model.message_bus.send(
                        "BDI",
                        {"type": "belief", "data": {"position": pos, "resource_type": obj.resource_type.name}},
                    )

    def clean_invalid_memory(self):
        # remove memórias cuja célula não tem mais recurso
        for pos in list(self.known_resources):
            if not any(hasattr(o, "resource_type") for o in self.model.grid.get_cell_list_contents([pos])):
                del self.known_resources[pos]

    def choose_best_resource(self):
        # escolhe recurso de maior valor/distância
        best, score = None, -1
        for pos, rt in self.known_resources.items():
            d = abs(self.pos[0] - pos[0]) + abs(self.pos[1] - pos[1])
            s = rt.value / (d + 1)
            if s > score:
                best, score = pos, s
        return best

    def collect_resource(self):
        # coleta CRYSTAL/METAL ou marca espera para STRUCTURE
        for obj in self.model.grid.get_cell_list_contents([self.pos]):
            r = getattr(obj, "resource_type", None)
            if r in (ResourceType.CRYSTAL, ResourceType.METAL):
                self.model.grid.remove_agent(obj)
                self.carrying = r
                log(self, f"coletou {r.name} em {self.pos}")
                del self.known_resources[self.pos]
                self.current_task = None
                return
            if r == ResourceType.STRUCTURE:
                self.waiting_for_help = True
                log(self, "esperando parceiro")
                return

    def check_for_partner(self):
        # coleta STRUCTURE se encontrar outro agente esperando
        cell = self.model.grid.get_cell_list_contents([self.pos])
        if not any(getattr(o, "resource_type", None) == ResourceType.STRUCTURE for o in cell):
            self.waiting_for_help = False
            return
        partners = [a for a in cell if a.unique_id != self.unique_id and getattr(a, "waiting_for_help", False)]
        for obj in cell:
            if getattr(obj, "resource_type", None) == ResourceType.STRUCTURE:
                self.model.grid.remove_agent(obj)
                self.carrying = ResourceType.STRUCTURE
                self.waiting_for_help = False
                for p in partners:
                    p.carrying = ResourceType.STRUCTURE
                    p.waiting_for_help = False
                    log(self, f"coletou com {p.unique_id}")
                return

    def move_towards(self, dst):
        # um passo manhattan
        x, y = self.pos; dx, dy = dst
        if x < dx: x += 1
        elif x > dx: x -= 1
        elif y < dy: y += 1
        elif y > dy: y -= 1
        self.model.safe_move(self, (x, y))

    def random_move(self):
        nbrs = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        if nbrs:
            p = choice(nbrs)
            self.model.safe_move(self, p)
            log(self, f"moveu para {p}")
