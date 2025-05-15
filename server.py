from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid, TextElement
from mesa.datacollection import DataCollector

from mesa_simulation.model import ResourceModel
from environment.resource import ResourceType


VALUE_MAP = {
    ResourceType.CRYSTAL: 10,
    ResourceType.METAL: 20,
    ResourceType.STRUCTURE: 50,
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


class LegendPanel(TextElement):
    def render(self, model):
        lines = ["<b>📘 Legenda</b><br><br><u>Agentes:</u><br>"]
        seen = set()
        for ag in model.schedule.agents:
            t = type(ag).__name__
            if t in seen:
                continue
            seen.add(t)
            color = {
                "BDIAgent": "gold",
                "GoalBasedAgent": "limegreen",
                "StateBasedAgent": "mediumpurple",
                "ReactiveAgent": "orange",
                "CooperativeAgent": "red",
            }[t]
            sample_name = getattr(ag, "name", t)
            lines.append(
                f'<span style="color:{color};">■</span> {sample_name.split("-")[0]}'
            )
        lines.append("<br><u>Recursos:</u>")
        lines.append('<span style="color:dodgerblue;">●</span> CRYSTAL')
        lines.append('<span style="color:silver;">●</span> METAL')
        lines.append('<span style="color:black;">●</span> STRUCTURE')
        return "<br>".join(lines)


class InfoPanel(TextElement):
    def render(self, model):
        return f"<b>Passo:</b> {model.schedule.steps}"


class AgentStatsPanel(TextElement):
    def render(self, model):
        # print(model.schedule.agents)
        output = "<b>Coletas por Agente:</b><br><pre>"
        total = {rt: 0 for rt in ResourceType}
        total_score = 0

        for agent in model.schedule.agents:
            if not hasattr(agent, "delivered"):
                continue

            delivered = agent.delivered
            score = sum(delivered[r] * VALUE_MAP[r] for r in ResourceType)
            output += f"Agente {agent.unique_id}: "
            output += " | ".join(f"{r.name[0]}: {delivered[r]}" for r in ResourceType)
            output += f" | Pontuação: {score}\n"

            for r in ResourceType:
                total[r] += delivered[r]
            total_score += score

        output += "\nTOTAL: " + " | ".join(
            f"{r.name[0]}: {total[r]}" for r in ResourceType
        )
        output += f" | Pontuação Total: {total_score}</pre>"
        return output


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
            "r": 0.4,
            "Color": color_map[agent.resource_type],
            "Filled": "true",
            "Layer": 0,
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
        "text": getattr(agent, "name", str(agent.unique_id)),
        "text_color": "black",
    }


params = {
    "width": 20,
    "height": 13,
    "agent_configs": [
        {"type": "BDI", "position": [0, 0]},
        {"type": "REACTIVE", "position": [0, 0]},
        {"type": "STATE_BASED", "position": [0, 0]},
        {"type": "GOAL_BASED", "position": [0, 0]},
        {"type": "COOPERATIVE", "position": [0, 0]},
    ],
    "resources": [
        {"type": "CRYSTAL", "position": [2, 3]},
        {"type": "STRUCTURE", "position": [4, 1]},
        {"type": "STRUCTURE", "position": [8, 2]},
        {"type": "STRUCTURE", "position": [12, 3]},
        {"type": "STRUCTURE", "position": [14, 4]},
        {"type": "CRYSTAL", "position": [8, 10]},
        {"type": "CRYSTAL", "position": [3, 12]},
        {"type": "CRYSTAL", "position": [17, 4]},
        {"type": "METAL", "position": [19, 2]},
        {"type": "METAL", "position": [19, 6]},
        {"type": "METAL", "position": [4, 8]},
        {"type": "METAL", "position": [12, 2]},
        {"type": "STRUCTURE", "position": [1, 1]},
        {"type": "CRYSTAL", "position": [2, 1]},
        {"type": "CRYSTAL", "position": [4, 3]},
        {"type": "CRYSTAL", "position": [2, 2]},
        {"type": "METAL", "position": [11, 4]},
        {"type": "STRUCTURE", "position": [5, 4]},
        {"type": "CRYSTAL", "position": [10, 1]},
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
legend = LegendPanel()
stats = AgentStatsPanel()

server = ModularServer(
    InstrumentedModel,
    [grid, info, legend, stats],
    "Resource-Collector Agents (v3)",
    params,
)
server.port = 8521

if __name__ == "__main__":
    server.launch()
