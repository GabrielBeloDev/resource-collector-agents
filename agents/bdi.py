from math import dist
from random import choice
from mesa import Agent
from environment.resource import ResourceType


VALUE = {
    ResourceType.CRYSTAL: 10,
    ResourceType.METAL: 20,
    ResourceType.STRUCTURE: 50,
}


def log(agent, msg):
    print(f"[BDI {agent.unique_id}] {msg}")


class BDIAgent(Agent):
    def __init__(self, uid, model, bus):
        super().__init__(uid, model)
        self.bus = bus
        self.beliefs: dict[tuple[int,int], ResourceType] = {}  
        self.dispatched: set[tuple[int,int]] = set()          
        self.delivered = {rt: 0 for rt in ResourceType}       

    def step(self):
        self._update_beliefs()    
        self._receive_beliefs()   
        self._delegate_tasks()    

    def _update_beliefs(self):
        # adiciona ao dicionário todas as posições que o modelo conhece
        self.beliefs.update(self.model.known_resources)

    def _receive_beliefs(self):
        # processa mensagens tipo "belief" vindas dos agentes
        for msg in self.bus.receive("BDI"):
            if msg["type"] == "belief":
                pos = tuple(msg["data"]["position"])
                rt = ResourceType[msg["data"]["resource_type"]]
                self.beliefs[pos] = rt
                self.model.report_resource(pos, rt)

    def _delegate_tasks(self):
        # filtra recursos ainda não delegados
        pending = {p: r for p, r in self.beliefs.items() if p not in self.dispatched}
        if not pending:
            return
        # evita delegar múltiplas STRUCTURE simultaneamente
        if any(self.beliefs[p] == ResourceType.STRUCTURE for p in self.dispatched):
            return
        # escolhe recurso de maior valor e menor distância à base
        best_pos, best_rt = min(
            pending.items(),
            key=lambda kv: (-VALUE[kv[1]], dist(self.model.base_position, kv[0]))
        )
        # envia tarefa de coleta para todos (broadcast)
        self.bus.send(
            "broadcast",
            {"type": "task", "action": "collect",
             "position": best_pos, "resource_type": best_rt.name},
        )
        self.dispatched.add(best_pos)
        log(self, f"delegou {best_rt.name} em {best_pos}")
