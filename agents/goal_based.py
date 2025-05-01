from environment.terrain import Position


class GoalBasedAgent:
    def __init__(self, agent_id, position: Position):
        self.agent_id = agent_id
        self.position = position

    def perceive(self, environment):
        return environment.get_all_known_resources()

    def plan(self, known_resources):
        return min(
            known_resources, key=lambda r: r.distance_to(self.position), default=None
        )

    def act(self, environment):
        resource = self.plan(self.perceive(environment))
        if resource:
            self.position = environment.move_towards(self.position, resource.position)
            if self.position == resource.position:
                environment.collect_resource(self.position)
