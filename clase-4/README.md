# Clase 4 — AgenteDeViajes con AgentCore Runtime, Memory y Gateway

Este ejemplo muestra un agente de viajes corporativo desplegado sobre **Amazon Bedrock AgentCore**.
El agente usa **Strands** como framework, tiene **memoria de largo plazo** (preferencias del empleado)
y se conecta a una herramienta externa de clima a través de un **AgentCore Gateway** que apunta a una
Lambda desplegada con CDK.

## Estructura del proyecto

```
clase-4/
├── AgenteDeViajes2026/          # Proyecto AgentCore principal
│   ├── agentcore/               # Configuración de infraestructura (agentcore.json)
│   ├── app/AgenteCurso2026/     # Código del agente (main.py, tools/, Dockerfile)
│   └── frontend/                # Interfaz Streamlit
└── cdk-weather-lambda/          # Lambda de clima (CDK)
    ├── lambda/handler.py        # Handler de la Lambda
    └── tool_schema.json         # Esquema MCP de la herramienta get_weather
```

## Orden de despliegue

### 1. Desplegar la Lambda de clima con CDK

Desde la carpeta `cdk-weather-lambda/`:

```bash
cd clase-4/cdk-weather-lambda

pip install -r requirements.txt

cdk bootstrap   # solo la primera vez por cuenta/región
cdk deploy
```

El output del deploy muestra el ARN de la Lambda. Guárdalo para el paso siguiente:

```
Outputs:
WeatherLambdaStack.WeatherLambdaArn = arn:aws:lambda:us-east-1:123456789012:function:agentcore-weather-tool
```

### 2. Crear la memoria del agente

Desde la carpeta `AgenteDeViajes2026/`:

```bash
cd clase-4/AgenteDeViajes2026

agentcore add memory
```

El CLI te pedirá un nombre (usa `MemoriaDelAgente`) y la estrategia de memoria. El ID generado
aparecerá en `agentcore/agentcore.json` bajo `memories[].name`.

### 3. Crear el Gateway

```bash
agentcore add gateway --name weather-gateway --authorizer-type NONE --runtimes AgenteCurso2026
```

### 4. Registrar la Lambda como target del Gateway

Reemplaza `<YOUR_LAMBDA_ARN>` con el ARN obtenido en el paso 1:

```bash
agentcore add gateway-target \
  --name TargetLambda \
  --type lambda-function-arn \
  --lambda-arn <YOUR_LAMBDA_ARN> \
  --tool-schema-file ../../cdk-weather-lambda/tool_schema.json \
  --gateway weather-gateway
```

Después de este paso, `agentcore/agentcore.json` tendrá el gateway y su target configurados.

### 5. Desplegar el agente en AgentCore Runtime

```bash
agentcore deploy
```

El CLI construye la imagen del agente, la sube a ECR y levanta el Runtime.
Al terminar muestra el ARN del Runtime; cópialo al archivo `.env` del frontend.

### 6. Probar localmente (opcional)

```bash
agentcore dev
```

Levanta el agente en modo local apuntando a los mismos recursos de AWS (memoria y gateway).

### 7. Arrancar el frontend

Desde la carpeta `AgenteDeViajes2026/frontend/`:

```bash
cd clase-4/AgenteDeViajes2026/frontend

# Copia el ejemplo y pon el ARN del Runtime del paso 5
cp .env.example .env

pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Variables de entorno

| Archivo | Variable | Descripción |
|---|---|---|
| `app/AgenteCurso2026/.env` | `DUFFEL_API_KEY` | API key de Duffel para vuelos |
| `frontend/.env` | `AGENTCORE_RUNTIME_ARN` | ARN del Runtime desplegado en el paso 5 |

## Cómo funciona

```
Usuario (Streamlit)
      │  prompt + session_id + actor_id
      ▼
AgentCore Runtime  (AgenteDeViajes2026/AgenteCurso2026)
      │
      ├── Strands Agent
      │     ├── search_flights / book_flight / get_employee_policy  (tools locales)
      │     ├── current_time                                        (strands_tools)
      │     └── get_weather  ──► AgentCore Gateway (weather-gateway)
      │                                │
      │                                └──► Lambda agentcore-weather-tool
      │                                          │
      │                                          └──► Open-Meteo API (gratuita)
      │
      └── AgentCoreMemorySessionManager
            └── Memoria USER_PREFERENCE  (preferencias por actor_id)
```

El agente recuerda las preferencias de cada empleado entre sesiones gracias al
`AgentCoreMemorySessionManager`. El namespace `/users/{actorId}/preferences` almacena
datos como asiento preferido, clase de vuelo o destinos frecuentes.
