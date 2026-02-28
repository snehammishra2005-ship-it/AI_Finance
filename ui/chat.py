
import streamlit as st
import requests
from ui.file_upload import render_file_upload
from config.settings import BACKEND_BASE_URL

def render_chat():
    """
    Renders the main chat interface.
    Connects to Backend API for SLM responses.
    """

    st.title("📊 AI Finance Assistant")

    # Initialize chat messages
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display existing chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # File upload section
    st.divider()
    render_file_upload()
    st.divider()

    # Chat input
    user_input = st.chat_input(
        "Ask about economic conditions, government policies, or uploaded data..."
    )

    if user_input:
        # Append user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        with st.chat_message("user"):
            st.markdown(user_input)

        # Call Backend
        persona = st.session_state.get("persona", "General User")
        slm = st.session_state.get("slm", "Default SLM")
        
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    payload = {
                        "message": user_input,
                        "persona": persona,
                        "slm_model": slm
                    }
                    response = requests.post(f"{BACKEND_BASE_URL}/chat", json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        ai_response = data.get("response", "No response from backend.")
                    else:
                        ai_response = f"⚠️ Backend Error: {response.text}"
                        
                except Exception as e:
                    ai_response = f"⚠️ Connection Error: {e}"
            
            st.markdown(ai_response)

        st.session_state.messages.append({
            "role": "assistant",
            "content": ai_response
        })
