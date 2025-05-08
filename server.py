from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, TextElement
from mesa.datacollection import DataCollector

from mesa_simulation.model import ResourceModel
from environment.resource import ResourceType

VALUE_MAP = {
    ResourceType.CRYSTAL: 1,
    ResourceType.METAL: 3,
    ResourceType.STRUCTURE: 10,
}


def _utility(model):
    storage = getattr(model.base, "storage", {})
    return sum(storage.get(rt, 0) * val for rt, val in VALUE_MAP.items())


def _count(resource):
    return lambda m: getattr(m.base, "storage", {}).get(resource, 0)


class InstrumentedModel(ResourceModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.datacollector = DataCollector(
            model_reporters={
                "Utility": _utility,
                "Cristais": _count(ResourceType.CRYSTAL),
                "Metais": _count(ResourceType.METAL),
                "Estruturas": _count(ResourceType.STRUCTURE),
            }
        )

    def step(self):
        self.datacollector.collect(self)
        super().step()


class InfoPanel(TextElement):
    def render(self, model):
        step = model.schedule.steps
        util = _utility(model)
        c = _count(ResourceType.CRYSTAL)(model)
        m_ = _count(ResourceType.METAL)(model)
        s = _count(ResourceType.STRUCTURE)(model)
        return f"Passo: {step}"


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
        label_map = {
            ResourceType.CRYSTAL: "C",
            ResourceType.METAL: "M",
            ResourceType.STRUCTURE: "S",
        }
        return {
            "Shape": "circle",
            "Color": color_map[agent.resource_type],
            "Filled": "true",
            "Layer": 0,
            "r": 0.4,
            "text": label_map[agent.resource_type],
            "text_color": "white",
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
        "text": str(agent.unique_id),
        "text_color": "black",
    }


params = {
    "width": 20,
    "height": 15,
    "agent_configs": [
        {"type": "BDI", "position": [0, 0]},
        # {"type": "STATE_BASED", "position": [0, 0]},
        # {"type": "GOAL_BASED", "position": [0, 0]},
        {"type": "REACTIVE", "position": [0, 0]},
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
        {"type": "CRYSTAL", "position": [2, 1]},
        {"type": "CRYSTAL", "position": [4, 3]},
        {"type": "CRYSTAL", "position": [2, 2]},
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


info = InfoPanel()

server = ModularServer(
    InstrumentedModel,
    [grid, info],
    "Resource‑Collector Agents (v3)",
    params,
)

server.port = 8521

if __name__ == "__main__":
    server.launch()
