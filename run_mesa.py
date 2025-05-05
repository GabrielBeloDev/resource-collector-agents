from mesa_simulation.model import ResourceModel
from configs.sample_config import config

model = ResourceModel(
    width=config["terrain"]["width"],
    height=config["terrain"]["height"],
    agent_configs=config["agents"],
    resources=config["resources"],
    obstacles=config["obstacles"],
    storm_turn=config["simulation"]["storm_turn"],
)

for i in range(config["simulation"]["steps"]):
    model.step()

print("\n=== RESUMO ===")
print(f"Utilidade total: {model.base.get_total_utility()}")
print(f"Passos executados: {model.schedule.time}")
