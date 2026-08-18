"""
Small frontend helpers for talking to the authenticated backend.

Every backend call (except the health check and the /auth/* endpoints) now
requires a bearer token. `auth_headers()` returns the Authorization header built
from the token stored in the Streamlit session after login, so the request call
sites just pass `headers=auth_headers()`.
"""

import streamlit as st


def auth_headers() -> dict:
    """Authorization header for backend requests, or {} if not logged in."""
    token = st.session_state.get("auth_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def logout() -> None:
    """Clear the session's auth + per-conversation state and return to login."""
    for key in (
        "auth_token", "username",
        "messages", "history", "session_id",
        "uploaded_file", "processed_text", "current_file_name",
    ):
        st.session_state.pop(key, None)
