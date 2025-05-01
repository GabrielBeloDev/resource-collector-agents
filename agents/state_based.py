from environment.terrain import Position


class StateBasedAgent:
    def __init__(self, agent_id, position: Position):
        self.agent_id = agent_id
        self.position = position
        self.visited = set()

    def perceive(self, environment):
        return environment.get_surroundings(self.position)

    def act(self, environment):
        self.visited.add(self.position)
        new_position = environment.get_least_visited_adjacent(
            self.position, self.visited
        )
        self.position = new_position
        if environment.has_small_resource(self.position):
            environment.collect_resource(self.position)
