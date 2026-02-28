import streamlit as st
from config.slm_config import SLM_LIST
from utils.history_manager import (
    save_chat_history,
    load_all_histories,
    load_chat_history
)


def load_chat_callback(file_path):
    data = load_chat_history(file_path)
    st.session_state.messages = data["messages"]
    st.session_state.persona = data["persona"]
    st.session_state.slm = data["slm"]

def render_sidebar():
    st.sidebar.title("📊 AI in Finance")

    # -----------------------------
    # Model Selection
    # -----------------------------
    model_names = [m["name"] for m in SLM_LIST]
    
    current_slm = st.session_state.get("slm", model_names[0] if model_names else None)
    try:
        slm_index = model_names.index(current_slm) if current_slm in model_names else 0
    except ValueError:
        slm_index = 0

    selected_slm = st.sidebar.selectbox(
        "🤖 Small Language Model",
        model_names,
        index=slm_index
    )
    st.session_state.slm = selected_slm

    # -----------------------------
    # Persona Selection
    # -----------------------------
    personas = [
        "Student", "Teacher", "Engineering Student",
        "MBA Student", "Clerk", "Homemaker",
        "Retiree", "Senior Citizen"
    ]

    current_persona = st.session_state.get("persona", personas[0])
    try:
        persona_index = personas.index(current_persona) if current_persona in personas else 0
    except ValueError:
        persona_index = 0

    selected_persona = st.sidebar.selectbox(
        "👤 Persona",
        personas,
        index=persona_index
    )
    st.session_state.persona = selected_persona

    # -----------------------------
    # Chat History
    # -----------------------------
    st.sidebar.divider()
    st.sidebar.subheader("🕘 Chat History")

    histories = load_all_histories()

    if not histories:
        st.sidebar.caption("No saved chats yet.")
    else:
        for h in histories:
            st.sidebar.button(
                f"{h['timestamp']} | {h['persona']}",
                key=h["file"],
                on_click=load_chat_callback,
                args=(h["path"],)
            )

    # -----------------------------
    # New Chat (Save + Reset)
    # -----------------------------
    st.sidebar.divider()
    if st.sidebar.button("➕ New Chat"):
        if st.session_state.get("messages"):
            save_chat_history(
                messages=st.session_state.messages,
                persona=st.session_state.get("persona"),
                slm=st.session_state.get("slm")
            )
        st.session_state.messages = []
