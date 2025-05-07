from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from environment.base import Base
from environment.resource import ResourceType
from communication.messaging import MessageBus
from agents.reactive import ReactiveAgent
from agents.state_based import StateBasedAgent
from agents.goal_based import GoalBasedAgent
from agents.cooperative import CooperativeAgent
from agents.bdi import BDIAgent
from environment.terrain import safe_move as _safe_move


class BaseAgent(Agent):
    pass


class ObstacleAgent(Agent):
    pass


class ResourceAgent(Agent):
    def __init__(self, unique_id, model, resource_type):
        super().__init__(unique_id, model)
        self.resource_type = resource_type


class ResourceModel(Model):
    def __init__(self, width, height, agent_configs, resources, obstacles):
        super().__init__()
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        self.base_position = (0, 0)
        self.base = Base(position=None)
        self.message_bus = MessageBus()
        self.next_uid = 0

        self.grid.place_agent(BaseAgent(self.next_uid, self), self.base_position)
        self.next_uid += 1

        for ag in agent_configs:
            pos = tuple(ag["position"])
            a = self.create_agent(ag["type"])
            self.schedule.add(a)
            self.grid.place_agent(a, pos)

        for r in resources:
            pos = tuple(r["position"])
            ra = ResourceAgent(self.next_uid, self, ResourceType[r["type"]])
            self.grid.place_agent(ra, pos)
            self.next_uid += 1

    def safe_move(self, agent, pos):
        _safe_move(self.grid, agent, pos, set())

    def create_agent(self, agent_type):
        uid = self.next_uid
        self.next_uid += 1
        if agent_type == "REACTIVE":
            return ReactiveAgent(uid, self)
        if agent_type == "STATE_BASED":
            return StateBasedAgent(uid, self)
        if agent_type == "GOAL_BASED":
            return GoalBasedAgent(uid, self)
        if agent_type == "COOPERATIVE":
            return CooperativeAgent(uid, self)
        if agent_type == "BDI":
            return BDIAgent(uid, self, self.message_bus)
        raise ValueError(f"Tipo desconhecido: {agent_type}")

    def step(self):
        print(f"\n─── PASSO {self.schedule.time:03} ───")
        self.schedule.step()
