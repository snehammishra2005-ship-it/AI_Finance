import os
import sys
import time
import subprocess
import uuid
import requests
import streamlit as st

# =====================================================
# PROJECT ROOT
# =====================================================
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.settings import BACKEND_HOST, BACKEND_PORT, BACKEND_BASE_URL, DATA_DIR

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

# =====================================================
# BACKEND LIFECYCLE
# =====================================================
# `streamlit run ui/app.py` is the single entry point for the project: it
# also boots the FastAPI backend as a child process so the user never has
# to start two things separately. Skipped when BACKEND_HOST points at a
# non-local host (e.g. Docker Compose's separate "backend" service), since
# in that case something else is responsible for running it - we just wait
# for it to become reachable.
_BACKEND_LOCK_FILE = DATA_DIR / ".backend.lock"
_IS_LOCAL_BACKEND = BACKEND_HOST in ("127.0.0.1", "localhost")


def _backend_is_up() -> bool:
    try:
        requests.get(BACKEND_BASE_URL + "/", timeout=1)
        return True
    except requests.exceptions.RequestException:
        return False


def _wait_for_backend(timeout_seconds: int) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if _backend_is_up():
            return True
        time.sleep(0.5)
    return False


def ensure_backend_running(timeout_seconds: int = 30) -> bool:
    """
    Makes sure the FastAPI backend is reachable, starting it locally if
    needed. Guarded by an on-disk lock so multiple browser tabs/sessions
    don't each spawn their own copy of the backend.
    """
    if _backend_is_up():
        return True

    if not _IS_LOCAL_BACKEND:
        # A separate service (e.g. Docker) owns the backend lifecycle.
        return _wait_for_backend(timeout_seconds)

    try:
        fd = os.open(_BACKEND_LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        # Another session is already starting the backend - just wait.
        return _wait_for_backend(timeout_seconds)

    try:
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app",
             "--host", BACKEND_HOST, "--port", str(BACKEND_PORT)],
            cwd=PROJECT_ROOT,
        )
        return _wait_for_backend(timeout_seconds)
    finally:
        try:
            os.remove(_BACKEND_LOCK_FILE)
        except OSError:
            pass


if "backend_ready" not in st.session_state:
    with st.spinner("Starting backend service..."):
        st.session_state.backend_ready = ensure_backend_running()

if not st.session_state.backend_ready:
    st.error(
        "Backend service didn't start in time. Check the terminal running "
        "Streamlit for errors, then reload this page."
    )
    st.stop()

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
    # Scopes RAG-uploaded documents to this browser session only, so one
    # user's uploads never surface in another session's RAG answers.
    "session_id": str(uuid.uuid4()),
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