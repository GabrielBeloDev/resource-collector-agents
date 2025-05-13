import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from mesa_simulation.model import ResourceModel
from environment.resource import ResourceType

VALUE_MAP = {
    ResourceType.CRYSTAL: 10,
    ResourceType.METAL: 20,
    ResourceType.STRUCTURE: 50,
}

PARAMS = dict(
    width=20,
    height=13,
    agent_configs=[
        {"type": "BDI", "position": [0, 0]},
        {"type": "GOAL_BASED", "position": [0, 0]},
        {"type": "REACTIVE", "position": [0, 0]},
        {"type": "STATE_BASED", "position": [0, 0]},
        {"type": "STATE_BASED", "position": [0, 0]},
        {"type": "COOPERATIVE", "position": [0, 0]},
    ],
    resources=[
        {"type": "CRYSTAL", "position": [2, 3]},
        {"type": "CRYSTAL", "position": [8, 10]},
        {"type": "CRYSTAL", "position": [5, 5]},
        {"type": "CRYSTAL", "position": [10, 6]},
        {"type": "METAL", "position": [4, 8]},
        {"type": "METAL", "position": [12, 2]},
        {"type": "STRUCTURE", "position": [1, 1]},
        {"type": "STRUCTURE", "position": [5, 1]},
    ],
    obstacles=[],
)

COLOR_AGENT = {
    "ReactiveAgent": "orange",
    "StateBasedAgent": "mediumpurple",
    "GoalBasedAgent": "limegreen",
    "CooperativeAgent": "red",
    "BDIAgent": "gold",
}
COLOR_RESOURCE = {
    ResourceType.CRYSTAL: "dodgerblue",
    ResourceType.METAL: "black",
    ResourceType.STRUCTURE: "black",
}
LABEL_RESOURCE = {
    ResourceType.CRYSTAL: "C",
    ResourceType.METAL: "M",
    ResourceType.STRUCTURE: "S",
}


def make_model():
    from mesa.datacollection import DataCollector

    def _utility(m):
        storage = getattr(m.base, "storage", {})
        return sum(storage.get(rt, 0) * val for rt, val in VALUE_MAP.items())

    def _count(rt):
        return lambda m: getattr(m.base, "storage", {}).get(rt, 0)

    class InstrumentedModel(ResourceModel):
        def __init__(self, **kw):
            super().__init__(**kw)
            self.datacollector = DataCollector(
                model_reporters={
                    "Utility": _utility,
                    "Cristais": _count(ResourceType.CRYSTAL),
                    "Metais": _count(ResourceType.METAL),
                    "Estruturas": _count(ResourceType.STRUCTURE),
                }
            )
            self.datacollector.collect(self)  

        def step(self):
            super().step()  
            self.datacollector.collect(self)  

    return InstrumentedModel(**PARAMS)


def grid_image(model):
    w, h = PARAMS["width"], PARAMS["height"]
    canvas = np.ones((h, w, 3))

    annotations = []
    if hasattr(model, "known_resources"):
        for (x, y), rtype in model.known_resources.items():
            color = COLOR_RESOURCE.get(rtype, "black")
            canvas[y, x] = mcolors.to_rgb(color)
            annotations.append((x, y, LABEL_RESOURCE.get(rtype, "?")))

    for ag in model.schedule.agents:
        if hasattr(ag, "resource_type"):
            x, y = ag.pos
            color = COLOR_RESOURCE.get(ag.resource_type, "black")
            canvas[y, x] = mcolors.to_rgb(color)
            annotations.append((x, y, LABEL_RESOURCE.get(ag.resource_type, "?")))

    for x, y in getattr(model, "obstacles", []):
        canvas[y, x] = 0.3
    for ag in model.schedule.agents:
        if ag.__class__.__name__ == "ObstacleAgent":
            x, y = ag.pos
            canvas[y, x] = 0.3

    for ag in model.schedule.agents:
        if hasattr(ag, "resource_type") or ag.__class__.__name__ == "ObstacleAgent":
            continue

        x, y = ag.pos
        rgb = mcolors.to_rgb(COLOR_AGENT.get(ag.__class__.__name__, "gray"))
        canvas[y, x] = rgb

        if getattr(ag, "carrying", None):
            carry = ag.carrying
            lbl = LABEL_RESOURCE.get(carry, "?")
            canvas[y, x] = mcolors.to_rgb("yellow")
            annotations.append((x, y, lbl))  

    fig, ax = plt.subplots()
    ax.imshow(canvas, origin="lower")
    ax.set_xticks([])
    ax.set_yticks([])
    for x, y, lbl in annotations:
        ax.text(x, y, lbl, ha="center", va="center", color="white", fontsize=7)
    plt.close(fig)
    return fig


def agent_stats_df(model):
    rows = []
    for ag in model.schedule.agents:
        if not hasattr(ag, "delivered"):
            continue
        rows.append(
            dict(
                Agente=f"{ag.__class__.__name__} {ag.unique_id}",
                C=ag.delivered[ResourceType.CRYSTAL],
                M=ag.delivered[ResourceType.METAL],
                S=ag.delivered[ResourceType.STRUCTURE],
                Pontuação=sum(ag.delivered[r] * VALUE_MAP[r] for r in ResourceType),
            )
        )
    return pd.DataFrame(rows).sort_values("Pontuação", ascending=False)


st.set_page_config(layout="wide", page_title="Resource‑Collector Agents")

if "model" not in st.session_state:
    st.session_state.model = make_model()

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### 🎮 Controles")
    if st.button("Avançar 1 passo ▶️"):
        st.session_state.model.step()

    if st.button("Avançar 10 passos ⏩"):
        for _ in range(10):
            st.session_state.model.step()

    if st.button("Resetar 🔄"):
        st.session_state.model = make_model()

    st.markdown(f"**Passo atual:** {st.session_state.model.schedule.steps}")

    st.markdown("---")
    st.markdown("#### 📘 Legenda")
    st.markdown(
        """
    <style>.dot{height:12px;width:12px;border-radius:50%;display:inline-block;margin-right:4px}</style>
    <b>Recursos:</b><br>
    <span class='dot' style='background:dodgerblue'></span>Crystal (C)<br>
    <span class='dot' style='background:silver'></span>Metal (M)<br>
    <span class='dot' style='background:black'></span>Structure (S)<br><br>
    <b>Agentes:</b><br>
    <span class='dot' style='background:gold'></span>BDI<br>
    <span class='dot' style='background:limegreen'></span>Goal‑Based<br>
    <span class='dot' style='background:mediumpurple'></span>State‑Based<br>
    <span class='dot' style='background:orange'></span>Reactive<br>
    <span class='dot' style='background:red'></span>Cooperative<br>
    """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown("### 🗺️ Grid de Recursos e Agentes")
    st.pyplot(grid_image(st.session_state.model), clear_figure=True)

    st.markdown("### 📊 Métricas de desempenho")
    df_model = st.session_state.model.datacollector.get_model_vars_dataframe()

    if hasattr(st.session_state.model, "known_resources"):
        df_model["Restantes"] = [
            len(st.session_state.model.known_resources)  
            for _ in range(len(df_model))
        ]

    if df_model.shape[0] > 1:
        cols_to_plot = ["Utility", "Cristais", "Metais", "Estruturas"]
        if "Restantes" in df_model.columns:
            cols_to_plot.append("Restantes")

        st.line_chart(df_model[cols_to_plot], use_container_width=True)
    else:
        st.info("Rode alguns passos para ver o gráfico 😉")

    st.markdown("### 🏅 Coletas por agente")
    st.dataframe(
        agent_stats_df(st.session_state.model),
        use_container_width=True,
        height=300,
    )
