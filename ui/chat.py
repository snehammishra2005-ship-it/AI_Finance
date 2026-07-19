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

    model_names = [m["name"] for m in SLM_LIST] or ["Llama 3.1 8B Instant (Groq)"]
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
# SOURCES (Perplexity-style list under an answer)
# -------------------------------------------------
def render_sources(sources):
    """Render the list of web sources the model used for an answer."""
    if not sources:
        return

    with st.expander(f"🌐 {len(sources)} sources"):
        for s in sources:
            title = s.get("title") or s.get("url", "")
            url = s.get("url", "")
            domain = s.get("domain", "")
            snippet = s.get("snippet", "")

            st.markdown(f"**[{s.get('n')}] [{title}]({url})**")

            meta = f"`{domain}`" if domain else ""
            if snippet:
                meta = f"{meta} — {snippet}" if meta else snippet
            if meta:
                st.caption(meta)


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
            render_sources(message.get("sources"))

    # =================================================
    # FILE UPLOAD SECTION
    # =================================================
    with st.expander("📎 Attach a document"):
        render_file_upload()

    toggle_col1, toggle_col2 = st.columns(2)

    with toggle_col1:
        use_rag = st.checkbox(
            "📚 Answer using my uploaded documents",
            value=st.session_state.get("use_rag", False),
            help="When enabled, answers are grounded in documents you've uploaded "
                 "instead of a general chat response."
        )

    with toggle_col2:
        use_web = st.checkbox(
            "🌐 Search the web",
            value=st.session_state.get("use_web", False),
            help="When enabled, the assistant searches the web and lists the "
                 "sources it used beneath the answer. Takes priority over the "
                 "document option if both are on."
        )

    st.session_state.use_rag = use_rag
    st.session_state.use_web = use_web

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
            "Llama 3.1 8B Instant (Groq)"
        )

        # ---------------------------------------------
        # Determine mode (web search takes priority over docs)
        # ---------------------------------------------
        if use_web:
            mode = "web"
        elif use_rag:
            mode = "rag"
        else:
            mode = "chat"

        # ---------------------------------------------
        # Assistant Response
        # ---------------------------------------------
        with st.chat_message("assistant"):

            spinner_text = {
                "web": "Searching the web...",
                "rag": "Searching your documents...",
                "chat": f"Thinking with {slm}...",
            }[mode]

            sources = []
            web_note = None

            with st.spinner(spinner_text):

                try:
                    request_start = time.time()

                    # -------- Request per mode --------
                    if mode == "rag":
                        response = requests.post(
                            url=f"{BACKEND_BASE_URL}/rag/ask",
                            json={
                                "question": user_input,
                                "session_id": st.session_state.get("session_id", "default")
                            },
                            timeout=120
                        )
                    else:
                        response = requests.post(
                            url=f"{BACKEND_BASE_URL}/chat",
                            json={
                                "message": user_input,
                                "persona": persona,
                                "slm_model": slm,
                                "web_search": (mode == "web"),
                            },
                            timeout=120
                        )

                    # -------- Success --------
                    if response.status_code == 200:

                        data = response.json()

                        if mode == "rag":
                            ai_response = data.get("answer", "No answer returned from backend.")
                            active_model = "Document RAG (Groq)"
                        else:
                            ai_response = data.get("response", "No response returned from backend.")
                            active_model = data.get("model", slm)
                            sources = data.get("sources", []) or []
                            web_note = data.get("web_note")

                        response_time = round(time.time() - request_start, 2)

                        save_test_report(
                            model_name=active_model,
                            persona=persona if mode != "rag" else "N/A (RAG)",
                            prompt=user_input,
                            response=ai_response,
                            response_time=response_time,
                            status="SUCCESS"
                        )

                    # -------- Backend error --------
                    else:
                        try:
                            detail = response.json().get("detail", response.text)
                        except Exception:
                            detail = response.text
                        ai_response = (
                            f"⚠️ The model could not answer "
                            f"({response.status_code}):\n\n{detail}"
                        )
                        active_model = slm

                except requests.exceptions.Timeout:
                    ai_response = (
                        "⚠️ Request timed out.\n\n"
                        "The selected model may be taking too long to respond."
                    )
                    active_model = slm

                except requests.exceptions.ConnectionError:
                    ai_response = (
                        "⚠️ Could not connect to backend.\n\n"
                        "Make sure FastAPI server is running."
                    )
                    active_model = slm

                except Exception as e:
                    ai_response = f"⚠️ Unexpected Error:\n\n{str(e)}"
                    active_model = slm

            # -------- Display --------
            st.markdown(ai_response)

            render_sources(sources)

            if web_note:
                st.caption(f"ℹ️ {web_note}")

            if mode == "rag":
                st.caption("📚 Answered from your uploaded documents")
            elif mode == "web":
                st.caption(f"🌐 Web search · {active_model}")
            else:
                st.caption(f"🤖 Model Used: {active_model}")

        # =================================================
        # SAVE ASSISTANT MESSAGE (with sources so they persist)
        # =================================================
        assistant_message = {
            "role": "assistant",
            "content": ai_response,
            "sources": sources,
        }

        st.session_state.messages.append(assistant_message)