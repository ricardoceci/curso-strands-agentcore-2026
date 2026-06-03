# Agentes de 0 a Producción

Curso práctico de construcción de agentes de IA con **Strands Agents**. Partimos desde el agente más simple posible y vamos agregando complejidad hasta llegar a un sistema listo para producción.

---

## Clase 1 — Tu primer Agente

Introducción al framework Strands: qué es un agente, cómo se conecta a distintos modelos, y cómo se le dan herramientas para que pueda actuar en el mundo.

### Contenido

```
clase-1/
├── lab1.ipynb          # Tu primer agente (Bedrock, historial, system prompt, logs)
├── lab2.ipynb          # Cambiando de proveedor: OpenAI, Anthropic, Ollama
├── tools.ipynb         # Por qué los agentes necesitan herramientas (calculadora)
├── requirements.txt    # Dependencias del curso
└── agente/
    ├── clase1.ipynb    # Agente de viajes corporativos
    └── tools/
        ├── flights.py  # Búsqueda de vuelos con la API de Duffel
        ├── weather.py  # Pronóstico del tiempo con Open-Meteo
        └── logger.py   # Log local de búsquedas en JSONL
```

### Notebooks

| Notebook | Qué aprenden |
|----------|-------------|
| `lab1.ipynb` | Crear un agente, conversar con él, inspeccionar el historial de mensajes, modificar el system prompt y activar logs de debug |
| `lab2.ipynb` | Cambiar el proveedor de LLM sin modificar la lógica del agente (OpenAI, Anthropic directo, Ollama local) |
| `tools.ipynb` | Diferencia entre un agente sin herramientas y uno con la tool `calculator`; por qué los LLMs no pueden hacer aritmética exacta |
| `agente/clase1.ipynb` | Agente : definir tools con `@tool`, importar tools, system prompt con reglas de negocio, conversación multi-turno con encadenamiento de herramientas |

---

## Clase 2 — MCP y Memoria Persistente

Conectamos el agente a servicios externos mediante el **Model Context Protocol (MCP)** y resolvemos la falta de memoria persistente con **mem0**.

### Contenido

```
clase-2/
├── lab1.ipynb          # MCP + Memoria Persistente (cliente, prompts, mem0)
├── mcp_server.py       # Servidor MCP custom (Duffel + Open-Meteo)
└── requirements.txt    # Dependencias de la clase
```

### Notebooks

| Notebook | Qué aprenden |
|----------|-------------|
| `lab1.ipynb` | Conectar un agente a un servidor MCP por HTTP; descubrir y usar Tools, Resources y Prompts; manejar el ciclo de vida de la conexión (`with` vs `start()/stop()`); demostrar el aislamiento de memoria entre instancias; agregar memoria persistente entre sesiones con mem0 |

### Servidor MCP (`mcp_server.py`)

El servidor expone los tres primitivos de MCP sobre la API de Duffel y Open-Meteo:

| Primitivo | Nombre | Descripción |
|-----------|--------|-------------|
| Tool | `search_flights` | Busca vuelos de ida con la API de Duffel |
| Tool | `get_offer_details` | Detalle completo de una oferta por ID |
| Tool | `get_weather` | Pronóstico diario para una ciudad (Open-Meteo) |
| Resource | `airports://list` | Catálogo estático de aeropuertos con códigos IATA |
| Prompt | `planificar_viaje` | Template para planificar un viaje completo |

> Levantarlo antes de correr el notebook:
> ```bash
> cd clase-2
> python mcp_server.py --http
> ```

---

## Clase 3 — Hooks, Multi-Agente y A2A

Agregamos control y coordinación a los agentes: hooks de observabilidad y enforcement, steering para confirmación humana antes de acciones irreversibles, tres patrones multi-agente (`as_tool`, Swarm, Graph), contexto por llamada con `invocation_state`, y comunicación entre procesos con el protocolo **A2A**.

### Contenido

```
clase-3/
├── clase-3.ipynb           # Hooks, multi-agente, invocation_state, A2A
├── a2a_weather_server.py   # Agente de clima expuesto como servidor A2A
├── requirements.txt        # Dependencias de la clase
└── .env.example            # Variables de entorno requeridas
```

### Notebooks

| Notebook | Qué aprenden |
|----------|-------------|
| `clase-3.ipynb` | Hooks de observabilidad (timing por tool call) y enforcement (bloqueo por política corporativa); `LLMSteeringHandler` para pedir confirmación antes de acciones irreversibles; agente como tool con `.as_tool()`; `Swarm` para orquestación con delegación; `GraphBuilder` para pipelines secuenciales; `invocation_state` para propagar metadatos sin contaminar el historial; protocolo A2A para invocar agentes en procesos remotos |

### Servidor A2A (`a2a_weather_server.py`)

Expone el agente de clima como endpoint A2A sobre HTTP.

| Componente | Detalle |
|------------|---------|
| Protocolo | A2A (Agent-to-Agent) |
| Puerto | `9010` |
| Agente | `weather_agent` con la tool `get_weather` |

> Levantarlo antes de ejecutar la celda A2A del notebook:
> ```bash
> cd clase-3
> python a2a_weather_server.py
> ```

---

## Requisitos

- Python 3.11+
- Cuenta en AWS con acceso a Amazon Bedrock (para `clase-1/lab1.ipynb`)
- Claves de API según el lab (ver abajo)

### Instalar dependencias

```bash
# Clase 1
cd clase-1
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Clase 2 (desde el mismo .venv o uno nuevo)
cd clase-2
pip install -r requirements.txt

# Clase 3
cd clase-3
pip install -r requirements.txt
```

Para el agente de viajes de la Clase 1:

```bash
cd clase-1/agente
pip install -r requirements.txt
```

### Variables de entorno

Creá un archivo `.env` en cada carpeta de clase con las claves que necesites:

**`clase-1/.env`**
```env
# Para lab2.ipynb
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Para clase1.ipynb (agente de viajes)
DUFFEL_API_KEY=duffel_sandbox_...
```

**`clase-2/.env`**
```env
# Para el servidor MCP y el agente de viajes
DUFFEL_API_KEY=duffel_sandbox_...

# Para mem0 (memoria persistente) — opcional si usás la versión local
MEM0_API_KEY=m0-...
```

**`clase-3/.env`**
```env
DUFFEL_API_KEY=duffel_sandbox_...
```

> Las claves de Bedrock se toman automáticamente de las credenciales de AWS configuradas en tu entorno (`~/.aws/credentials` o variables de entorno `AWS_*`).

#### Obtener las claves

| Clave | Dónde obtenerla |
|-------|----------------|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `ANTHROPIC_API_KEY` | [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) |
| `DUFFEL_API_KEY` | [app.duffel.com](https://app.duffel.com) → Settings → API tokens (sandbox) |
| `MEM0_API_KEY` | [app.mem0.ai](https://app.mem0.ai) → Settings → API Keys |

#### Ollama (local)

```bash
# Instalar Ollama: https://ollama.com/download
ollama pull qwen3:4b
```

---

## Stack tecnológico

| Componente | Tecnología |
|-----------|-----------|
| Framework de agentes | [Strands Agents](https://strandsagents.com) |
| Modelos en la nube | Amazon Bedrock, OpenAI, Anthropic |
| Modelo local | Ollama + Qwen3 4B |
| Protocolo de herramientas | [MCP](https://modelcontextprotocol.io) (Model Context Protocol) |
| Comunicación entre agentes | A2A (Agent-to-Agent protocol) |
| Memoria persistente | [mem0](https://mem0.ai) |
| API de vuelos | [Duffel](https://duffel.com) (sandbox) |
| API de clima | [Open-Meteo](https://open-meteo.com) (sin autenticación) |
| Notebooks | Jupyter / VS Code |

---

## Conceptos clave de la Clase 1

### Agent

```python
from strands import Agent

agente = Agent()                          # Bedrock por default
agente("Hola, ¿quién sos?")              # Primer turno
agente("¿Y cuál es tu especialidad?")    # Segundo turno (con historial)
```

Strands mantiene el historial automáticamente en `agente.messages`. Cada llamada incluye el contexto completo de la conversación.

### Tool

```python
from strands import tool

@tool
def get_temperature(city: str) -> str:
    """Get the current temperature of a city."""
    return f"The current temperature in {city} is 25°C."

agente = Agent(tools=[get_temperature])
agente("¿Cuánto hace en Lima?")  # El agente llama a la tool automáticamente
```

El decorador `@tool` genera el schema JSON a partir del nombre, docstring y type hints de la función.

### Cambiar de modelo

```python
from strands.models.openai import OpenAIModel

model = OpenAIModel(model_id="gpt-4o-mini", client_args={"api_key": OPENAI_API_KEY})
agente = Agent(model=model)
```

La interfaz del agente es idéntica independientemente del proveedor.

---

---

## Conceptos clave de la Clase 2

### MCPClient — conectarse a un servidor externo

```python
from mcp.client.streamable_http import streamable_http_client
from strands.tools.mcp import MCPClient

# Opción A: bloque `with` — para un uso puntual en una sola celda
mcp_client = MCPClient(lambda: streamable_http_client("http://localhost:8002/mcp"))
with mcp_client:
    tools = mcp_client.list_tools_sync()
    agente = Agent(tools=[tools])
    agente("Buscame vuelos de EZE a MIA para el 31 de mayo")

# Opción B: start()/stop() — para mantener la conexión entre celdas del notebook
mcp_client.start()
# ... múltiples celdas usando mcp_client ...
mcp_client.stop()
```

### Los tres primitivos de MCP

```python
with mcp_client:
    # Tools — herramientas ejecutables
    tools = mcp_client.list_tools_sync()

    # Resources — datos estáticos como contexto
    resource = mcp_client.read_resource_sync("airports://list")

    # Prompts — templates de instrucciones con parámetros
    result = mcp_client.get_prompt_sync("planificar_viaje", {
        "origen": "Buenos Aires",
        "destino": "Miami",
        "fecha_ida": "2026-06-15"
    })
    prompt_text = result.messages[0].content.text
```

### mem0 — memoria persistente entre sesiones

```python
from strands_tools import mem0_memory
from strands import Agent

# El system prompt le dice al agente cuándo guardar y cuándo recuperar memoria.
SYSTEM_PROMPT = """
Al inicio de cada conversacion, usa mem0_memory con action='retrieve'.
Cuando el usuario comparta una preferencia, usa mem0_memory con action='store'.
"""

agente = Agent(tools=[*mcp_tools, mem0_memory], system_prompt=SYSTEM_PROMPT)

# Primera sesión: el agente guarda las preferencias en la base de datos vectorial.
agente("Soy usuario_123. Siempre prefiero asiento de pasillo y soy vegetariano.")

# Segunda sesión (nueva instancia): el agente recupera las preferencias automáticamente.
agente_nuevo = Agent(tools=[*mcp_tools, mem0_memory], system_prompt=SYSTEM_PROMPT)
agente_nuevo("Soy usuario_123. ¿Qué preferencias tengo?")  # Las conoce sin que se las digan
```

La diferencia clave:

| | `messages[]` | mem0 |
|---|---|---|
| **Duración** | Una sesión | Permanente |
| **Recuperación** | Todo el historial | Búsqueda semántica |
| **Compartido entre instancias** | ❌ No | ✅ Sí (por `user_id`) |

---

---

## Conceptos clave de la Clase 3

### Hooks

```python
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import BeforeToolCallEvent, AfterToolCallEvent

class ObservabilityHook(HookProvider):
    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeToolCallEvent, self.before)
        registry.add_callback(AfterToolCallEvent, self.after)

    def before(self, event: BeforeToolCallEvent) -> None:
        print(f">>> tool.start | {event.tool_use['name']}")

    def after(self, event: AfterToolCallEvent) -> None:
        print(f">>> tool.end   | {event.tool_use['name']}")

agent = Agent(tools=[...], hooks=[ObservabilityHook()])
```

Para cancelar una tool antes de que se ejecute:

```python
def gate(self, event: BeforeToolCallEvent) -> None:
    if event.tool_use['name'] == "search_flights":
        dest = event.tool_use.get('input', {}).get("destination", "")
        if dest in RESTRICTED:
            event.cancel_tool = "Destino restringido por política corporativa."
```

### Steering — confirmación humana

```python
from strands.vended_plugins.steering.handlers.llm.llm_handler import LLMSteeringHandler

confirm = LLMSteeringHandler(
    system_prompt="Antes de ejecutar book_flight, pedí confirmación explícita al usuario."
)
agent = Agent(tools=[...], plugins=[confirm])
```

### Multi-agente

```python
# Agente como tool
weather_agent = Agent(name="weather_agent", tools=[get_weather], ...)
travel_agent = Agent(
    tools=[search_flights,
           weather_agent.as_tool(name="weather_agent", description="...")],
)

# Swarm — orquestación con delegación
from strands.multiagent import Swarm
swarm = Swarm([orchestrator, agent_a, agent_b])
swarm("...")

# Graph — pipeline secuencial con orden fijo
from strands.multiagent import GraphBuilder
builder = GraphBuilder()
builder.add_node(agent_a, "step_a")
builder.add_node(agent_b, "step_b")
builder.add_edge("step_a", "step_b")
graph = builder.build()
graph("...")
```

### `invocation_state`

```python
agent = Agent(tools=[...], hooks=[ContextLogHook()])
agent(
    "Buscame vuelos...",
    invocation_state={"employee_id": "emp_001", "budget_usd": 2500}
)
# En los hooks: event.invocation_state.get("employee_id")
```

### A2A — comunicación entre procesos

```python
# Servidor (a2a_weather_server.py)
from strands.multiagent.a2a import A2AServer
server = A2AServer(agent=weather_agent, host="127.0.0.1", port=9010, enable_a2a_compliant_streaming=True)
server.serve()

# Cliente
from strands.agent.a2a_agent import A2AAgent
remote = A2AAgent(endpoint="http://localhost:9010", name="weather_agent")
result = remote("¿Qué tiempo hace en Miami hoy?")
```

---

## Roadmap del curso

| Clase | Tema |
|-------|------|
| **Clase 1** | Introducción a Strands, tools básicas, agente de viajes |
| **Clase 2** | MCP (Tools, Resources, Prompts), memoria persistente con mem0 |
| **Clase 3** | Hooks, steering, multi-agente (as_tool / Swarm / Graph), invocation_state, A2A |

