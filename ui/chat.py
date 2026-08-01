import streamlit as st
import requests
import os
import json

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

    # Slim top bar: just the model + persona pickers on the left (the brand
    # lives in the sidebar), so the header isn't cramped.
    model_col, persona_col, _spacer = st.columns([3, 3, 4])

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
            if message.get("web_note"):
                st.caption(f"ℹ️ {message['web_note']}")
            if message.get("caption"):
                st.caption(message["caption"])

    # =================================================
    # COMPOSER DOCK  —  [ + attach ] [ input ] [ send ]  + toggles below
    # On the welcome screen the dock sits inline under the centered greeting;
    # once a conversation exists it's pinned to the bottom of the viewport
    # (ChatGPT-style) so messages scroll above it.
    # =================================================
    has_messages = bool(st.session_state.messages)

    if has_messages:
        st.markdown(
            "<style>.st-key-composer_dock{position:sticky;bottom:0;z-index:20;"
            "background:var(--bg-main);padding-top:10px;padding-bottom:2px;}</style>",
            unsafe_allow_html=True,
        )

    with st.container(key="composer_dock"):

        with st.container(border=True, key="composer_pill"):
            plus_col, form_col = st.columns([0.09, 1], vertical_alignment="center")

            with plus_col:
                # "+" opens the attach-a-document panel (kept out of the form,
                # since Streamlit forms can't hold a file uploader).
                with st.popover("＋", use_container_width=True):
                    render_file_upload()

            with form_col:
                with st.form("composer", clear_on_submit=True, border=False):
                    input_col, send_col = st.columns([1, 0.08], vertical_alignment="center")
                    with input_col:
                        user_input = st.text_input(
                            "message",
                            placeholder="Ask about finance, inflation, investments, "
                                        "uploaded reports, or policies...",
                            label_visibility="collapsed",
                        )
                    with send_col:
                        submitted = st.form_submit_button("↑", use_container_width=True)

        # ---- Tools: toggles BELOW the input ----
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
                     "sources it used beneath the answer. Turn this on together "
                     "with the document option to blend your uploaded documents "
                     "with live web results in one cited answer."
            )

        st.session_state.use_rag = use_rag
        st.session_state.use_web = use_web

    # =================================================
    # HANDLE USER MESSAGE
    # =================================================
    if submitted and user_input and user_input.strip():

        user_input = user_input.strip()
        st.session_state.messages.append({"role": "user", "content": user_input})

        persona = st.session_state.get("persona", "General User")
        slm = st.session_state.get("slm", "Llama 3.1 8B Instant (Groq)")

        # Determine mode (both toggles = blend web + documents)
        if use_web and use_rag:
            mode = "blend"
        elif use_web:
            mode = "web"
        elif use_rag:
            mode = "rag"
        else:
            mode = "chat"

        spinner_text = {
            "web": "Searching the web...",
            "blend": "Searching your documents + the web...",
            "rag": "Searching your documents...",
            "chat": f"Thinking with {slm}...",
        }[mode]

        sources = []
        web_note = None

        with st.spinner(spinner_text):
            try:
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
                    # Prior turns (everything before the message just added) so
                    # the assistant has conversation memory. Cap to the last
                    # few to bound tokens; send role + content only.
                    history = [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages[:-1]
                    ][-8:]

                    response = requests.post(
                        url=f"{BACKEND_BASE_URL}/chat",
                        json={
                            "message": user_input,
                            "persona": persona,
                            "slm_model": slm,
                            "web_search": (mode in ("web", "blend")),
                            "use_documents": (mode == "blend"),
                            "session_id": st.session_state.get("session_id", "default"),
                            "history": history,
                        },
                        timeout=180
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

        caption = {
            "rag": "📚 Answered from your uploaded documents",
            "web": f"🌐 Web search · {active_model}",
            "blend": f"🌐📚 Web + documents · {active_model}",
            "chat": f"🤖 Model Used: {active_model}",
        }[mode]

        st.session_state.messages.append({
            "role": "assistant",
            "content": ai_response,
            "sources": sources,
            "web_note": web_note,
            "caption": caption,
        })

        # Re-render so the new turn shows above the composer (correct order)
        # and the input clears.
        st.rerun()