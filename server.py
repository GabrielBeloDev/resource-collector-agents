from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, ChartModule
from mesa import Model, Agent
from mesa_simulation.model import ResourceModel
from environment.resource import ResourceType


def agent_portrayal(agent):
    if agent.__class__.__name__ == "BaseAgent":
        return {
            "Shape": "rect",
            "w": 1,
            "h": 1,
            "Color": "white",
            "Filled": "true",
            "Layer": 0,
            "stroke_color": "black",
        }

    if agent.__class__.__name__ == "ObstacleAgent":
        return {
            "Shape": "rect",
            "w": 1,
            "h": 1,
            "Color": "#555",
            "Filled": "true",
            "Layer": 0,
        }

    if hasattr(agent, "resource_type"):
        color_map = {
            ResourceType.CRYSTAL: "dodgerblue",
            ResourceType.METAL: "silver",
            ResourceType.STRUCTURE: "black",
        }
        return {
            "Shape": "circle",
            "Color": color_map[agent.resource_type],
            "Filled": "true",
            "Layer": 0,
            "r": 0.4,
        }

    class_color = {
        "ReactiveAgent": "orange",
        "StateBasedAgent": "mediumpurple",
        "GoalBasedAgent": "limegreen",
        "CooperativeAgent": "red",
        "BDIAgent": "gold",
    }
    return {
        "Shape": "rect",
        "w": 0.8,
        "h": 0.8,
        "Color": class_color.get(agent.__class__.__name__, "gray"),
        "Filled": "true",
        "Layer": 1,
    }


params = {
    "width": 20,
    "height": 15,
    "agent_configs": [
        {"type": "BDI", "position": [0, 0]},
        {"type": "STATE_BASED", "position": [0, 0]},
        {"type": "GOAL_BASED", "position": [0, 0]},
    ],
    "resources": [
        {"type": "CRYSTAL", "position": [2, 3]},
        {"type": "CRYSTAL", "position": [8, 10]},
        {"type": "CRYSTAL", "position": [5, 5]},
        {"type": "CRYSTAL", "position": [10, 6]},
        {"type": "CRYSTAL", "position": [3, 12]},
        {"type": "CRYSTAL", "position": [17, 4]},
        {"type": "METAL", "position": [4, 8]},
        {"type": "METAL", "position": [12, 2]},
        {"type": "STRUCTURE", "position": [1, 1]},
    ],
    "obstacles": [],
}

cell_px = 40
grid = CanvasGrid(
    agent_portrayal,
    params["width"],
    params["height"],
    cell_px * params["width"],
    cell_px * params["height"],
)


chart = ChartModule(
    [{"Label": "Utility", "Color": "black"}],
    data_collector_name=None,
)

server = ModularServer(
    ResourceModel,
    [grid],
    "Resource‑Collector Agents",
    params,
)
server.port = 8521
server.launch()
