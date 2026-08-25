"""
Small frontend helpers for talking to the authenticated backend.

Every backend call (except the health check and the /auth/* endpoints) now
requires a bearer token. `auth_headers()` returns the Authorization header built
from the token stored in the Streamlit session after login, so the request call
sites just pass `headers=auth_headers()`.
"""

import requests
import streamlit as st

from config.settings import BACKEND_BASE_URL


def auth_headers() -> dict:
    """Authorization header for backend requests, or {} if not logged in."""
    token = st.session_state.get("auth_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


# -------------------------------------------------
# Chat history (backend, database-backed, per-user)
# -------------------------------------------------
def list_histories() -> list:
    """The logged-in user's saved chats (metadata), newest first. Returns [] on
    any error so the sidebar degrades gracefully."""
    try:
        r = requests.get(f"{BACKEND_BASE_URL}/history", headers=auth_headers(), timeout=15)
        if r.status_code == 200:
            return r.json().get("histories", [])
    except requests.exceptions.RequestException:
        pass
    return []


def save_history(messages, persona, slm) -> None:
    """Persist the current conversation to the user's history (best-effort)."""
    try:
        requests.post(
            f"{BACKEND_BASE_URL}/history",
            json={"messages": messages, "persona": persona, "slm": slm},
            headers=auth_headers(),
            timeout=15,
        )
    except requests.exceptions.RequestException:
        pass


def load_history(history_id) -> dict:
    """Load one of the user's saved chats by id. Returns {} on error."""
    try:
        r = requests.get(
            f"{BACKEND_BASE_URL}/history/{history_id}", headers=auth_headers(), timeout=15
        )
        if r.status_code == 200:
            return r.json()
    except requests.exceptions.RequestException:
        pass
    return {}


def logout() -> None:
    """Clear the session's auth + per-conversation state and return to login."""
    for key in (
        "auth_token", "username",
        "messages", "history", "session_id",
        "uploaded_file", "processed_text", "current_file_name",
    ):
        st.session_state.pop(key, None)
