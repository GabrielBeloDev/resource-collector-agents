from mesa_simulation.model import ResourceModel
from configs.sample_config import config

model = ResourceModel(
    width=config["terrain"]["width"],
    height=config["terrain"]["height"],
    num_agents=len(config["agents"]),
    resources=config["resources"],
)

for i in range(config["simulation"]["steps"]):
    model.step()

print("Total utility:", model.base.get_total_utility())
