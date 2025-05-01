from environment.terrain import Position


class ReactiveAgent:
    def __init__(self, agent_id, position: Position):
        self.agent_id = agent_id
        self.position = position

    def perceive(self, environment):
        return environment.get_cell(self.position)

    def act(self, environment):
        self.position = environment.get_random_adjacent_position(self.position)
        if environment.has_small_resource(self.position):
            environment.collect_resource(self.position)
