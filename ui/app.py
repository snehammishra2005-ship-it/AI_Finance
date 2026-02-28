import os
import sys
import streamlit as st

# -------------------------------------------------
# Ensure PROJECT ROOT is in Python path
# (Required for config/, utils/, backend/ imports)
# -------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# -------------------------------------------------
# UI imports
# -------------------------------------------------
from ui.sidebar import render_sidebar
from ui.chat import render_chat
from ui.analysis_view import render_analysis_view

# -------------------------------------------------
# Page configuration
# -------------------------------------------------
st.set_page_config(
    page_title="AI in Finance",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------
# Session state initialization
# -------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "history" not in st.session_state:
    st.session_state.history = []

if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

if "slm" not in st.session_state:
    st.session_state.slm = None

if "persona" not in st.session_state:
    st.session_state.persona = None

# -------------------------------------------------
# Render Sidebar
# -------------------------------------------------
render_sidebar()

# -------------------------------------------------
# Main Page Tabs
# -------------------------------------------------
tab_chat, tab_analysis = st.tabs(["💬 Chat", "📈 Analysis"])

with tab_chat:
    render_chat()

with tab_analysis:
    render_analysis_view()
