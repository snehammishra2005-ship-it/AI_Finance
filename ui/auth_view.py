"""
Login / create-account screen.

Shown by ui/app.py before the rest of the app when there's no valid session.
On success it stores the bearer token + username in st.session_state and reruns,
at which point app.py lets the user through.
"""

import requests
import streamlit as st

from config.settings import BACKEND_BASE_URL


def _post(path: str, username: str, password: str):
    return requests.post(
        f"{BACKEND_BASE_URL}{path}",
        json={"username": username, "password": password},
        timeout=30,
    )


def _handle(resp) -> bool:
    """Store the token on success and return True; otherwise show the backend's
    error message and return False."""
    if resp.status_code == 200:
        data = resp.json()
        st.session_state.auth_token = data["token"]
        st.session_state.username = data["username"]
        return True
    try:
        detail = resp.json().get("detail", resp.text)
    except Exception:
        detail = resp.text
    st.error(detail or f"Request failed ({resp.status_code}).")
    return False


def render_auth() -> None:
    st.markdown(
        """
        <div style="text-align:center; margin-top:8vh; margin-bottom:24px;">
            <div style="font-size:2rem; font-weight:700;">📊 AI in Finance</div>
            <div style="opacity:0.7; margin-top:6px;">
                Log in or create an account to continue.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 1.4, 1])
    with mid:
        tab_login, tab_register = st.tabs(["Log in", "Create account"])

        # ---- Log in ----
        with tab_login:
            with st.form("login_form", clear_on_submit=False):
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Log in", use_container_width=True, type="primary")
            if submitted:
                try:
                    if _handle(_post("/auth/login", username, password)):
                        st.rerun()
                except requests.exceptions.ConnectionError:
                    st.error("Could not reach the backend. Make sure it's running.")
                except Exception as e:
                    st.error(f"Unexpected error: {e}")

        # ---- Create account ----
        with tab_register:
            with st.form("register_form", clear_on_submit=False):
                new_username = st.text_input(
                    "Username", key="reg_username",
                    help="3-32 characters: letters, numbers, or . _ -",
                )
                new_password = st.text_input(
                    "Password", type="password", key="reg_password",
                    help="At least 8 characters.",
                )
                confirm = st.text_input("Confirm password", type="password", key="reg_confirm")
                registered = st.form_submit_button("Create account", use_container_width=True, type="primary")
            if registered:
                if new_password != confirm:
                    st.error("Passwords don't match.")
                else:
                    try:
                        if _handle(_post("/auth/register", new_username, new_password)):
                            st.rerun()
                    except requests.exceptions.ConnectionError:
                        st.error("Could not reach the backend. Make sure it's running.")
                    except Exception as e:
                        st.error(f"Unexpected error: {e}")
