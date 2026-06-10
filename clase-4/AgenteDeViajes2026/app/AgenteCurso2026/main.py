import os

from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from tools import search_flights, book_flight, get_employee_policy
from strands_tools import current_time

from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager


from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamable_http_client


MEMORY_ID = os.environ["AGENTCORE_MEMORY_ID"]
GATEWAY_URL = os.environ["AGENTCORE_GATEWAY_URL"]

app = BedrockAgentCoreApp()

mcp_client = MCPClient(lambda: streamable_http_client(GATEWAY_URL))

@app.entrypoint
def invoke(payload: dict) -> dict:
    """Entry point for AgentCore Runtime."""
    session_id = payload.get("sessionId") or payload.get("session_id") or "default"
    actor = payload.get("actionActor") or "default-user"
    agentcore_memory_config = AgentCoreMemoryConfig(
        memory_id=MEMORY_ID,
        session_id=session_id,
        actor_id=actor,
        # Sin retrieval_config el session manager no busca memorias de largo plazo.
        retrieval_config={
            "/users/{actorId}/preferences": RetrievalConfig(top_k=10)
        })
    with AgentCoreMemorySessionManager(agentcore_memory_config,region_name="us-east-1") as session_manager:
       with mcp_client:
            mcp_tools = mcp_client.list_tools_sync()
            SYSTEM_PROMPT = """Eres un agente de viajes corporativo llamado "ViajesCorp" especializado en ayudar a los empleados de una empresa a planificar sus viajes de negocios, si el usuario tiene prefrencias guardadas usalas sin preguntar."""
            agent = Agent(system_prompt=SYSTEM_PROMPT,tools=[search_flights, book_flight, get_employee_policy, current_time,mcp_tools],session_manager=session_manager)
            response = agent(payload["prompt"])
            return {"result": str(response)}

