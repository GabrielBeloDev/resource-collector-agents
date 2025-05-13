from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation

from environment.base import Base
from environment.resource import ResourceType
from environment.terrain import safe_move as _safe_move
from communication.messaging import MessageBus

from agents.reactive import ReactiveAgent
from agents.state_based import StateBasedAgent
from agents.goal_based import GoalBasedAgent
from agents.cooperative import CooperativeAgent
from agents.bdi import BDIAgent


class BaseAgent(Agent):
    pass


class ObstacleAgent(Agent):
    pass


class ResourceAgent(Agent):
    def __init__(self, uid, model, rtype: ResourceType):
        super().__init__(uid, model)
        self.resource_type = rtype


class ResourceModel(Model):
    def __init__(self, width, height, agent_configs, resources, obstacles):
        super().__init__()
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        self.base_position = (0, 0)
        self.base = Base(self, position=None)
        self.message_bus = MessageBus()
        self.next_uid = 0
        self.max_steps = 1500
        self.running = True
        self.total_resources = len(resources)
        self.known_resources: dict[tuple[int, int], ResourceType] = {}
        self.grid.place_agent(BaseAgent(self.next_uid, self), self.base_position)
        self.next_uid += 1

        for cfg in agent_configs:
            pos = tuple(cfg["position"])
            agent = self._create_agent(cfg["type"])
            self.schedule.add(agent)
            self.grid.place_agent(agent, pos)

        self.agents_log = {
            a.unique_id: {rt: 0 for rt in ResourceType}
            for a in self.schedule.agents
            if hasattr(a, "delivered")
        }

        for r in resources:
            pos = tuple(r["position"])
            self.grid.place_agent(
                ResourceAgent(self.next_uid, self, ResourceType[r["type"]]), pos
            )
            self.next_uid += 1

    def safe_move(self, agent, pos):
        _safe_move(self.grid, agent, pos, set())

    def report_resource(self, pos, rtype):
        if pos not in self.known_resources:
            self.known_resources[pos] = rtype

    def consume_resource_info(self, pos):
        self.known_resources.pop(pos, None)

    def _create_agent(self, kind: str):
        """
        Cria o agente do tipo solicitado, atribui‑lhe um nome legível
        (para aparecer no grid/legenda) e já faz o registro no MessageBus.
        """
        # gera o UID
        uid = self.next_uid
        self.next_uid += 1

        # mapeia o rótulo curto que queremos exibir
        pretty = {
            "BDI": "BDI",
            "GOAL_BASED": "Goal",
            "STATE_BASED": "State",
            "REACTIVE": "Reac",
            "COOPERATIVE": "Coop",
        }.get(kind, kind)

        # cada agente publica em seu próprio canal (até o BDI, se quiser)
        self.message_bus.register(str(uid))

        # cria o agente propriamente dito
        match kind:
            case "BDI":
                agent = BDIAgent(uid, self, self.message_bus)
            case "GOAL_BASED":
                agent = GoalBasedAgent(uid, self)
            case "STATE_BASED":
                agent = StateBasedAgent(uid, self)
            case "REACTIVE":
                agent = ReactiveAgent(uid, self)
            case "COOPERATIVE":
                agent = CooperativeAgent(uid, self)
            case _:
                raise ValueError(f"Tipo desconhecido: {kind}")

        # adiciona o nome para uso nos painéis / grid
        agent.name = f"{pretty}-{uid:02}"

        return agent

    def step(self):
        print(f"\n─── PASSO {self.schedule.time:03} ───")
        if self.schedule.time >= self.max_steps:
            print("Tempestade de radiação! Encerrando a coleta.")
            self.running = False
            return
        self.schedule.step()
