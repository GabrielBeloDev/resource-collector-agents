from environment.terrain import Position


class CooperativeAgent:
    def __init__(self, agent_id, position: Position):
        self.agent_id = agent_id
        self.position = position
        self.coop_target = None

    def perceive(self, environment):
        return environment.get_large_resource_requests()

    def decide_cooperation(self, requests):
        if requests:
            self.coop_target = min(requests, key=lambda r: r["distance"])
            return True
        return False

    def act(self, environment):
        if self.coop_target:
            self.position = environment.move_towards(
                self.position, self.coop_target["position"]
            )
            if self.position == self.coop_target["position"]:
                environment.coop_collect_resource(
                    self.coop_target["position"], self.agent_id
                )
