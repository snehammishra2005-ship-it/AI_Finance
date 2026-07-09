import os
import sys
import streamlit as st

# =====================================================
# PROJECT ROOT
# =====================================================
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# =====================================================
# UI IMPORTS
# =====================================================
from ui.styles import inject_global_css
from ui.sidebar import render_sidebar
from ui.chat import render_chat_header, render_chat
from ui.analysis_view import render_analysis_view
from ui.architecture import render_architecture_view

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="AI in Finance",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="expanded"
)

inject_global_css()

# =====================================================
# SESSION STATE
# =====================================================
defaults = {
    "messages": [],
    "history": [],
    "uploaded_file": None,
    "processed_text": "",
    "slm": None,
    "persona": None,
    "page": "chat",
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# =====================================================
# SIDEBAR
# =====================================================
render_sidebar()

# =====================================================
# PAGE ROUTING
# =====================================================
page = st.session_state.get("page", "chat")

if page == "chat":

    render_chat_header()

    # -------------------------------------------------
    # Welcome Screen
    # -------------------------------------------------
    if len(st.session_state.messages) == 0:

        st.markdown(
            """
            <div class="welcome-wrap">
                <div class="welcome-title">What can I help with?</div>
                <div class="welcome-subtitle">
                    Ask about financial analysis, investments, RBI policies,
                    or GDP &amp; inflation — or attach a document to get started.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # -------------------------------------------------
    # Conversation
    # -------------------------------------------------
    render_chat()

elif page == "analysis":

    render_analysis_view()

elif page == "architecture":

    render_architecture_view()