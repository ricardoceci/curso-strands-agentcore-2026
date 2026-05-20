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

## Requisitos

- Python 3.11+
- Cuenta en AWS con acceso a Amazon Bedrock (para `lab1.ipynb`)
- Claves de API según el lab (ver abajo)

### Instalar dependencias

```bash
cd clase-1
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Para el agente de viajes:

```bash
cd clase-1/agente
pip install -r requirements.txt
```

### Variables de entorno

Creá un archivo `.env` en `clase-1/` (y otro en `clase-1/agente/`) con las claves que necesites:

```env
# Para lab2.ipynb
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Para clase1.ipynb (agente de viajes)
DUFFEL_API_KEY=duffel_sandbox_...
```

> Las claves de Bedrock se toman automáticamente de las credenciales de AWS configuradas en tu entorno (`~/.aws/credentials` o variables de entorno `AWS_*`).

#### Obtener las claves

| Clave | Dónde obtenerla |
|-------|----------------|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `ANTHROPIC_API_KEY` | [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) |
| `DUFFEL_API_KEY` | [app.duffel.com](https://app.duffel.com) → Settings → API tokens (sandbox) |

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

## Roadmap del curso

| Clase | Tema |
|-------|------|
| **Clase 1** | Introducción a Strands, tools básicas, agente de viajes |
|
