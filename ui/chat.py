import streamlit as st
import requests
import os
import csv
import json
import time
from datetime import datetime

from config.settings import BACKEND_BASE_URL
from config.slm_config import SLM_LIST
from utils.persona_manager import get_persona_names
from ui.file_upload import render_file_upload


# -------------------------------------------------
# CHAT HEADER (title + model/persona pickers)
# -------------------------------------------------
def render_chat_header():
    """
    Slim header above the chat, similar to ChatGPT's model switcher:
    app title on the left, compact Model / Persona pickers on the right.
    """

    model_names = [m["name"] for m in SLM_LIST] or ["Local Fallback"]
    personas = get_persona_names() or ["General User"]

    current_slm = st.session_state.get("slm") or model_names[0]
    if current_slm not in model_names:
        current_slm = model_names[0]

    current_persona = st.session_state.get("persona") or personas[0]
    if current_persona not in personas:
        current_persona = personas[0]

    title_col, model_col, persona_col = st.columns([3, 2, 2])

    with title_col:
        st.markdown(
            "<p class='chat-title'>📊 AI Finance Assistant</p>",
            unsafe_allow_html=True
        )

    with model_col:
        selected_slm = st.selectbox(
            "Model",
            model_names,
            index=model_names.index(current_slm),
            label_visibility="collapsed"
        )

    with persona_col:
        selected_persona = st.selectbox(
            "Persona",
            personas,
            index=personas.index(current_persona),
            label_visibility="collapsed"
        )

    st.session_state.slm = selected_slm
    st.session_state.persona = selected_persona

    os.makedirs("data/runtime", exist_ok=True)
    with open("data/runtime/current_model.json", "w") as f:
        json.dump({"selected_model": selected_slm}, f)

    st.divider()


# -------------------------------------------------
# SAVE TEST REPORT
# -------------------------------------------------
def save_test_report(
    model_name,
    persona,
    prompt,
    response,
    response_time,
    status="SUCCESS"
):

    report_folder = "data/test_reports"

    os.makedirs(report_folder, exist_ok=True)

    existing_reports = [
        f for f in os.listdir(report_folder)
        if f.endswith(".csv")
    ]

    serial_number = len(existing_reports) + 1

    safe_model_name = (
        model_name
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace(".", "")
    )

    date_str = datetime.now().strftime("%Y-%m-%d")

    filename = (
        f"test_{serial_number}_"
        f"{safe_model_name}_"
        f"{date_str}_report.csv"
    )

    filepath = os.path.join(
        report_folder,
        filename
    )

    report_data = {
        "serial_number": serial_number,
        "model_name": model_name,
        "persona": persona,
        "prompt": prompt,
        "response_time_seconds": response_time,
        "status": status,
        "response_preview": str(response)[:150],
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }

    with open(
        filepath,
        mode="w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=report_data.keys()
        )

        writer.writeheader()

        writer.writerow(report_data)


# -------------------------------------------------
# Chat Renderer
# -------------------------------------------------
def render_chat():
    """
    Renders the main chat interface.
    Connects to FastAPI backend for AI responses.
    """



    # =================================================
    # SESSION STATE INITIALIZATION
    # =================================================
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # =================================================
    # DISPLAY CHAT HISTORY
    # =================================================
    for message in st.session_state.messages:

        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # =================================================
    # FILE UPLOAD SECTION
    # =================================================
    with st.expander("📎 Attach a document"):
        render_file_upload()

    use_rag = st.checkbox(
        "📚 Answer using my uploaded documents",
        value=st.session_state.get("use_rag", False),
        help="When enabled, answers are grounded in documents you've uploaded "
             "instead of a general chat response."
    )
    st.session_state.use_rag = use_rag

    # =================================================
    # CHAT INPUT
    # =================================================
    user_input = st.chat_input(
        "Ask about finance, inflation, investments, uploaded reports, or policies..."
    )

    # =================================================
    # HANDLE USER MESSAGE
    # =================================================
    if user_input:

        # ---------------------------------------------
        # Store user message
        # ---------------------------------------------
        user_message = {
            "role": "user",
            "content": user_input
        }

        st.session_state.messages.append(user_message)

        with st.chat_message("user"):
            st.markdown(user_input)

        # ---------------------------------------------
        # Read selected settings
        # ---------------------------------------------
        persona = st.session_state.get(
            "persona",
            "General User"
        )

        slm = st.session_state.get(
            "slm",
            "TinyLlama (Local Fallback)"
        )

        # ---------------------------------------------
        # Assistant Response
        # ---------------------------------------------
        with st.chat_message("assistant"):

            spinner_text = (
                "Searching your documents..." if use_rag
                else f"Thinking with {slm}..."
            )

            with st.spinner(spinner_text):

                try:
                    # =========================================
                    # START TIMER
                    # =========================================
                    request_start = time.time()

                    # =========================================
                    # API Request (RAG vs normal chat)
                    # =========================================
                    if use_rag:
                        response = requests.post(
                            url=f"{BACKEND_BASE_URL}/rag/ask",
                            json={
                                "question": user_input,
                                "session_id": st.session_state.get("session_id", "default")
                            },
                            timeout=120
                        )
                    else:
                        payload = {
                            "message": user_input,
                            "persona": persona,
                            "slm_model": slm
                        }

                        response = requests.post(
                            url=f"{BACKEND_BASE_URL}/chat",
                            json=payload,
                            timeout=120
                        )

                    # =========================================
                    # HANDLE SUCCESS
                    # =========================================
                    if response.status_code == 200:

                        data = response.json()

                        if use_rag:
                            ai_response = data.get(
                                "answer",
                                "No answer returned from backend."
                            )
                            active_model = "Document RAG (Groq)"
                        else:
                            ai_response = data.get(
                                "response",
                                "No response returned from backend."
                            )
                            active_model = data.get(
                                "model",
                                slm
                            )

                        # =====================================
                        # RESPONSE TIME
                        # =====================================
                        response_time = round(
                            time.time() - request_start,
                            2
                        )

                        # =====================================
                        # AUTO SAVE REPORT
                        # =====================================
                        save_test_report(
                            model_name=active_model,
                            persona=persona if not use_rag else "N/A (RAG)",
                            prompt=user_input,
                            response=ai_response,
                            response_time=response_time,
                            status="SUCCESS"
                        )

                    # =========================================
                    # HANDLE BACKEND ERROR
                    # =========================================
                    else:

                        ai_response = (
                            f"⚠️ Backend Error "
                            f"({response.status_code}):\n\n"
                            f"{response.text}"
                        )

                        active_model = "Document RAG (Groq)" if use_rag else slm

                # =============================================
                # HANDLE TIMEOUT
                # =============================================
                except requests.exceptions.Timeout:

                    ai_response = (
                        "⚠️ Request timed out.\n\n"
                        "The selected model may be taking too long to respond."
                    )

                    active_model = "Document RAG (Groq)" if use_rag else slm

                # =============================================
                # HANDLE CONNECTION ERROR
                # =============================================
                except requests.exceptions.ConnectionError:

                    ai_response = (
                        "⚠️ Could not connect to backend.\n\n"
                        "Make sure FastAPI server is running."
                    )

                    active_model = "Document RAG (Groq)" if use_rag else slm

                # =============================================
                # HANDLE UNEXPECTED ERROR
                # =============================================
                except Exception as e:

                    ai_response = f"⚠️ Unexpected Error:\n\n{str(e)}"

                    active_model = "Document RAG (Groq)" if use_rag else slm

            # =============================================
            # DISPLAY RESPONSE
            # =============================================
            st.markdown(ai_response)

            if use_rag:
                st.caption("📚 Answered from your uploaded documents")
            else:
                st.caption(f"🤖 Model Used: {active_model}")

        # =================================================
        # SAVE ASSISTANT MESSAGE
        # =================================================
        assistant_message = {
            "role": "assistant",
            "content": ai_response
        }

        st.session_state.messages.append(assistant_message)