# Resource Collector Agents 🚀🌍

Simulação de agentes inteligentes explorando um planeta hostil para coletar recursos e construir uma base, utilizando o framework [Mesa](https://github.com/projectmesa/mesa) para modelagem baseada em agentes.

## 🧠 Sobre o Projeto

Cinco tipos de agentes autônomos pousaram em um planeta desconhecido. A missão deles é:

- Explorar o terreno irregular
- Coletar recursos valiosos e retornar à base ao estar carregando um recurso
- Trabalhar em equipe (quando necessário)

Eles tomam decisões com diferentes níveis de complexidade, indo de ações puramente reativas até planejamento com delegação de tarefas e compartilhamento de crenças.

## 🚀 Estratégias de Agentes

| Estratégia do Agente | Descrição resumida |
|:---------------------|:-------------------|
| Reativo              | Age com base apenas na percepção atual do ambiente. |
| Baseado em Estado    | Mantém memória curta de eventos passados para decidir a próxima ação. |
| Baseado em Objetivos | Seleciona ações que maximizam o progresso rumo a um objetivo definido. |
| Cooperativo          | Identifica recursos, espera parceiros para pegar estruturas. |
| BDI                  | Gerencia crenças, desejos e intenções, coordenando os demais.

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
- Visualização modular com painéis customizados (info, stats, legenda)
- HTML + JS (via Mesa Server)
## 📁 Estrutura do Projeto

```text
resource-collector-agents/
├── agents/             # Cinco agentes (Reactive, State, Goal, Coop, BDI)
├── communication/      # MessageBus para troca de mensagens
├── environment/        # Terrain, tipos de recursos e base
├── mesa_simulation/    # Modelos de simulação e visualização interativa
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

#### Acesse: http://localhost:8521 no seu navegador.


## 🛠️ Customização via params

Edite os arquivos em server.py para mudar o grid, agentes ou recursos:

```bash
params = {
    "width": 20,
    "height": 13,
    "agent_configs": [...],
    "resources": [...],
    "obstacles": [],
}
```
- Edite a lista de agentes, recursos (com tipo e posição) ou obstáculos diretamente.

### 🧪 Logs e Diagnóstico

Cada agente imprime logs detalhados no terminal. Os logs incluem:
- Percepções (avistou, recebeu tarefa)
- Ações (coletou, entregou, delegou)
- Colaborações (aguarda parceiro, coletou em equipe com [...])
- Movimentações (explorou, moveu para)

### 🔬 Extensões Futuras
- Visualização em tempo real com `mesa.visualization`
- Otimização por heurísticas ou aprendizado
- Configurações via linha de comando (CLI)
- Pathfinding com A*
- Treinamento de agentes com Aprendizado por Reforço

### 👨‍🏫 Créditos
Este projeto integra a disciplina de Inteligência Artificial – Ciência da Computação, UFMA (2025.1).  
Alunos: Gabriel Belo Pereira dos Reis, João Felipe, Gabriel Bastos.
