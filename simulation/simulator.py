from environment.terrain import Terrain, Position
from environment.resource import ResourceMap, Resource, ResourceType
from environment.base import Base
from agents.reactive import ReactiveAgent
from agents.state_based import StateBasedAgent
from agents.goal_based import GoalBasedAgent
from agents.cooperative import CooperativeAgent
from typing import List


class Simulator:
    def __init__(self, width: int, height: int, steps: int):
        self.terrain = Terrain(width, height)
        self.resources = ResourceMap()
        self.base = Base(Position(0, 0))
        self.agents: List = []
        self.steps = steps
        self.current_step = 0

    def add_agent(self, agent):
        self.agents.append(agent)

    def add_resource(self, resource: Resource):
        self.resources.add_resource(resource)

    def step(self):
        for agent in self.agents:
            agent.act(self)
        self.current_step += 1

    def run(self):
        while self.current_step < self.steps:
            self.step()

    def get_cell(self, position: Position):
        return self.resources.get_resource(position)

    def has_small_resource(self, position: Position):
        return self.resources.has_small_resource(position)

    def collect_resource(self, position: Position):
        value = self.resources.collect_resource(position)
        if value > 0:
            self.base.deposit(ResourceType(value))
