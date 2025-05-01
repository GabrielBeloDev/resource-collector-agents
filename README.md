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

## ⚙️ Tecnologias

- Python 3.10+
- [Mesa](https://mesa.readthedocs.io/) — framework de simulação multiagente
- YAML — para configuração de cenários
- Estrutura modular e extensível
## 📁 Estrutura do Projeto

```text
resource-collector-agents/
├── agents/                # Implementação dos diferentes tipos de agentes
├── communication/         # Sistema de mensagens entre agentes
├── configs/               # Arquivos de configuração (YAML e .py)
├── environment/           # Modelagem do terreno, base e recursos
├── evaluation/            # Métricas e avaliação de desempenho
├── mesa_simulation/       # Integração com o framework Mesa
├── simulation/            # Simulação base sem Mesa
├── main.py                # Execução tradicional (sem Mesa)
├── run_mesa.py            # Execução com Mesa
└── README.md              # Este arquivo
```

## 📦 Instalação

#### 1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/resource-collector-agents.git
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
pip install -U "mesa[rec]"
```

#### 4. Execução da Simulação
```bash
🔹 Modo tradicional (sem Mesa):
python3 main.py
```
```bash
🔸 Modo com Mesa:
python3 run_mesa.py
```


## 🔸 Configuração:

Edite os arquivos em configs/sample_config.yaml ou sample_config.py para mudar o grid, agentes ou recursos.

### 📊 Métricas de Avaliação

| Métrica                         | Valor* |
|---------------------------------|:------:|
| Recursos coletados              |   —    |
| Utilidade entregue à base       |   —    |
| Passos executados               |   —    |

### 🔬 Extensões Futuras
- Visualização em tempo real com `mesa.visualization`
- Estratégias BDI com troca de crenças
- Otimização por heurísticas ou aprendizado
- Configurações via linha de comando (CLI)

### 👨‍🏫 Créditos
Este projeto integra a disciplina de Inteligência Artificial – Ciência da Computação, UFMA (2025.1).  
Alunos: Gabriel Belo Pereira dos Reis, João Felipe, Gabriel Bastos, Isaque Santos