from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from environment.resource import ResourceType
from environment.base import Base
from random import choice


class ResourceAgent(Agent):
    def __init__(self, unique_id, model, resource_type):
        super().__init__(unique_id, model)
        self.resource_type = resource_type


class ExplorerAgent(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.carrying = None

    def step(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.pos, moore=False, include_center=False
        )
        new_position = choice(possible_steps)
        self.model.grid.move_agent(self, new_position)

        cellmates = self.model.grid.get_cell_list_contents([new_position])
        for obj in cellmates:
            if isinstance(obj, ResourceAgent) and self.carrying is None:
                self.carrying = obj.resource_type
                self.model.grid.remove_agent(obj)
                break

        if self.pos == self.model.base_position and self.carrying:
            self.model.base.deposit(self.carrying)
            self.carrying = None


class ResourceModel(Model):
    def __init__(self, width, height, num_agents, resources):
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = RandomActivation(self)
        self.base_position = (0, 0)
        self.base = Base(position=None)

        for i in range(num_agents):
            agent = ExplorerAgent(i, self)
            self.schedule.add(agent)
            self.grid.place_agent(agent, (i % width, i % height))

        uid = num_agents
        for r in resources:
            resource_type = ResourceType[r["type"]]
            pos = tuple(r["position"])
            r_agent = ResourceAgent(uid, self, resource_type)
            self.grid.place_agent(r_agent, pos)
            uid += 1

    def step(self):
        self.schedule.step()
