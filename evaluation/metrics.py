class EvaluationMetrics:
    def __init__(self):
        self.total_utility = 0
        self.steps_taken = 0
        self.resources_collected = 0

    def update(self, utility_gained: int):
        self.total_utility += utility_gained
        self.resources_collected += 1

    def set_steps(self, steps: int):
        self.steps_taken = steps

    def summary(self):
        return {
            "Total Utility": self.total_utility,
            "Steps Taken": self.steps_taken,
            "Resources Collected": self.resources_collected,
        }
