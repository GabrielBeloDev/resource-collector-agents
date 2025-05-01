import yaml
from environment.terrain import Position
from environment.resource import Resource, ResourceType
from simulation.simulator import Simulator
from agents.reactive import ReactiveAgent
from agents.state_based import StateBasedAgent
from agents.goal_based import GoalBasedAgent
from agents.cooperative import CooperativeAgent
from evaluation.metrics import EvaluationMetrics


def load_config(path: str):
    with open(path, "r") as file:
        return yaml.safe_load(file)


def create_agent(agent_type: str, agent_id: int, position: Position):
    if agent_type == "REACTIVE":
        return ReactiveAgent(agent_id, position)
    elif agent_type == "STATE_BASED":
        return StateBasedAgent(agent_id, position)
    elif agent_type == "GOAL_BASED":
        return GoalBasedAgent(agent_id, position)
    elif agent_type == "COOPERATIVE":
        return CooperativeAgent(agent_id, position)
    else:
        raise ValueError(f"Unknown agent type: {agent_type}")


def main():
    config = load_config("configs/sample_config.yaml")
    terrain_cfg = config["terrain"]
    sim_cfg = config["simulation"]

    sim = Simulator(terrain_cfg["width"], terrain_cfg["height"], sim_cfg["steps"])
    metrics = EvaluationMetrics()

    for res in config["resources"]:
        r_type = ResourceType[res["type"]]
        pos = Position(*res["position"])
        sim.add_resource(Resource(r_type, pos))

    for idx, ag in enumerate(config["agents"]):
        pos = Position(*ag["position"])
        agent = create_agent(ag["type"], idx, pos)
        sim.add_agent(agent)

    sim.run()

    metrics.set_steps(sim.steps)
    metrics.update(sim.base.get_total_utility())

    print("=== Simulation Summary ===")
    print(metrics.summary())


if __name__ == "__main__":
    main()
