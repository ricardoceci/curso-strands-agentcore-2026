"""
Interfaz Streamlit para AgenteDeViajes (AgentCore Runtime).

Arranca con:
    streamlit run streamlit_app.py
"""

import uuid

import streamlit as st

from agente_client import invoke_agent

# ── Empleados disponibles (mismos que en tools/employee.py) ───────────────────
EMPLOYEES = {
    "EMP001": "Ana García",
    "EMP002": "Carlos López",
    "EMP003": "María Fernández",
    "EMP004": "Roberto Silva",
}

# ── Estado de sesión (persiste entre reruns de Streamlit) ─────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "actor_id" not in st.session_state:
    st.session_state.actor_id = "EMP001"

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configuración")

    actor_id = st.selectbox(
        "Empleado (actor_id)",
        options=list(EMPLOYEES.keys()),
        format_func=lambda k: f"{k} — {EMPLOYEES[k]}",
        index=list(EMPLOYEES.keys()).index(st.session_state.actor_id),
    )

    # Al cambiar de empleado se crea una sesión nueva y se limpia el chat
    if actor_id != st.session_state.actor_id:
        st.session_state.actor_id = actor_id
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("session_id (generado automáticamente)")
    st.code(st.session_state.session_id, language=None)

    if st.button("🔄 Nueva sesión"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()

# ── Página principal ───────────────────────────────────────────────────────────
st.title("✈️ AgenteDeViajes")
st.caption(
    f"Hablando como **{st.session_state.actor_id}** "
    f"— {EMPLOYEES[st.session_state.actor_id]}"
)

# Historial de mensajes
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input del usuario
if user_input := st.chat_input("¿En qué puedo ayudarte con tu viaje?"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Consultando al agente..."):
            try:
                answer = invoke_agent(
                    prompt=user_input,
                    actor_id=st.session_state.actor_id,
                    session_id=st.session_state.session_id,
                )
            except Exception as exc:
                answer = f"❌ Error al invocar el agente: {exc}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
