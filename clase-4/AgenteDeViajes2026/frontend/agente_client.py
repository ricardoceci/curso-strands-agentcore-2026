"""
Invoca el agente AgenteDeViajes desplegado en AgentCore Runtime.

Tres pasos:
  1. Crear el cliente boto3 apuntando al servicio de runtime.
  2. Construir el payload JSON con el mensaje, el actor y la sesión.
  3. Llamar invoke_agent_runtime y leer la respuesta.
"""

import json
import os

import boto3
from dotenv import load_dotenv

load_dotenv()

# ── Configuración ──────────────────────────────────────────────────────────────
RUNTIME_ARN = os.environ["AGENTCORE_RUNTIME_ARN"]
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# ── Cliente boto3 ──────────────────────────────────────────────────────────────
# "bedrock-agentcore" es el servicio que ejecuta el agente desplegado.
client = boto3.client("bedrock-agentcore", region_name=AWS_REGION)


def invoke_agent(prompt: str, actor_id: str, session_id: str) -> str:
    """Envía un mensaje al agente y devuelve su respuesta como string.

    Args:
        prompt:     Mensaje del usuario.
        actor_id:   ID del empleado que hace la solicitud (p.ej. "EMP001").
        session_id: Identificador de sesión; mantiene el hilo de conversación.
    """

    # 1. Payload: exactamente lo que recibe el parámetro `payload` dentro
    #    del @app.entrypoint en main.py del agente desplegado.
    payload = {
        "prompt": prompt,
        "sessionId": session_id,   # el agente usa esto para la memoria
        "actionActor": actor_id,   # el agente lee esto como el empleado activo
    }

    # 2. Llamada al runtime.
    #    - runtimeSessionId: header que AgentCore usa para gestionar la sesión.
    #    - payload: cuerpo JSON que lee main.py en el @app.entrypoint.
    #    La respuesta llega como streaming blob en response["response"].
    response = client.invoke_agent_runtime(
        agentRuntimeArn=RUNTIME_ARN,
        runtimeSessionId=session_id,
        qualifier="DEFAULT",
        payload=json.dumps(payload).encode(),
    )

    # 3. Leer y deserializar. El agente devuelve {"result": "<texto>"}.
    raw = response["response"].read()
    result = json.loads(raw)
    return result.get("result", "")


# ── Prueba rápida desde la terminal ───────────────────────────────────────────
if __name__ == "__main__":
    respuesta = invoke_agent(
        prompt="Necesito un vuelo de Buenos Aires a Madrid para la próxima semana.",
        actor_id="EMP001",
        session_id="test-session-001",
    )
    print(respuesta)
