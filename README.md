# Resource Collector Agents 🚀🌍

Simulação de agentes inteligentes explorando um planeta hostil para coletar recursos e construir uma base, utilizando o framework [Mesa](https://github.com/projectmesa/mesa) para modelagem baseada em agentes.

## 🧠 Sobre o Projeto

Uma equipe de agentes autônomos pousou em um planeta desconhecido. Eles precisam coletar recursos espalhados por um terreno 2D irregular, superar obstáculos naturais e entregar esses recursos em uma base central antes de uma tempestade de radiação.

## 🚀 Estratégias de Agentes

| Estratégia do Agente | Descrição resumida |
|:---------------------|:-------------------|
| Reativo              | Responde unicamente ao estado atual do ambiente, sem memória. |
| Baseado em Estado    | Mantém memória curta de eventos passados para decidir a próxima ação. |
| Baseado em Objetivos | Seleciona ações que maximizam o progresso rumo a um objetivo definido. |
| Cooperativo          | Troca mensagens com outros agentes e divide tarefas para ganhar eficiência. |
| BDI                  | Age segundo o modelo Crenças-Desejos-Intenções, equilibrando metas e percepções.

## 🎮 Como funciona

| Ícone | Objeto | Cor no canvas |
|-------|--------|---------------|
| ⬜ | **Base** | branco, contorno preto |
| 🔵 | Cristal (10 pts) | blue |
| ⚪ | Metal (20 pts) | silver |
| ⚫ | Estrutura (50 pts) | black |
| 🟠 | Agente Reativo | orange |
| 🟣 | Agente Estado | mediumpurple |
| 🟢 | Agente Objetivo | limegreen |
| 🔴 | Agente Cooperativo | red |
| 🟡 | Agente BDI | gold |

Clique **Reset** e depois **Start** no navegador para ver os agentes contornando obstáculos, coletando recursos e depositando na base.

## ⚙️ Tecnologias

- Python 3.10+
- [Mesa](https://mesa.readthedocs.io/) — framework de simulação multiagente
- Estrutura modular e extensível
## 📁 Estrutura do Projeto

```text
resource-collector-agents/
├── agents/             # Cinco agentes (Reactive, State, Goal, Coop, BDI)
├── communication/      # MessageBus
├── configs/            # sample_config.yaml / .py
├── environment/        # Terrain, ResourceType, Base
├── mesa_simulation/    # ResourceModel + BaseAgent/ObstacleAgent
├── run_mesa.py         # Execução headless (terminal)
├── server.py           # Visualização web (http://localhost:8521)
└── README.md
```

## 📦 Instalação

#### 1. Clone o repositório:
```bash
git clone https://github.com/GabrielBeloDev/resource-collector-agents.git
```
```bash
cd resource-collector-agents
```

####  2. Crie um ambiente virtual (opcional, mas recomendado):
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
```

#### 3. Instale as dependências:
```bash
pip install mesa==2.1.1"
```

#### 4. Execução da Simulação
```bash
🔹 Modo Web (com Mesa):
python3 server.py 
```



## 🔸 Configuração:

Edite os arquivos em configs/sample_config.yaml ou sample_config.py para mudar o grid, agentes ou recursos:

- terrain.width / height

- resources: tipo e posição

- agents: tipo e posição

- obstacles: lista de tuplas (x, y)

- simulation.storm_turn: passo em que a tempestade encerra a coleta


### 🔬 Extensões Futuras
- Visualização em tempo real com `mesa.visualization`
- Otimização por heurísticas ou aprendizado
- Configurações via linha de comando (CLI)

### 👨‍🏫 Créditos
Este projeto integra a disciplina de Inteligência Artificial – Ciência da Computação, UFMA (2025.1).  
Alunos: Gabriel Belo Pereira dos Reis, João Felipe, Gabriel Bastos.
