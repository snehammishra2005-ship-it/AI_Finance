import streamlit as st

from utils.history_manager import (
    save_chat_history,
    load_all_histories,
    load_chat_history
)
from ui.api import logout


# -------------------------------------------------
# Load Previous Chat Callback
# -------------------------------------------------
def load_chat_callback(file_path):
    data = load_chat_history(file_path, user_key=st.session_state.get("username"))

    st.session_state.messages = data.get("messages", [])
    st.session_state.persona = data.get("persona", "General User")
    st.session_state.slm = data.get("slm", None)
    st.session_state.page = "chat"


# -------------------------------------------------
# New Chat Callback
# -------------------------------------------------
def new_chat_callback():
    if st.session_state.get("messages"):
        save_chat_history(
            messages=st.session_state.messages,
            persona=st.session_state.get("persona"),
            slm=st.session_state.get("slm"),
            user_key=st.session_state.get("username"),
        )

    st.session_state.messages = []
    st.session_state.page = "chat"


# -------------------------------------------------
# Sidebar Renderer
# -------------------------------------------------
def render_sidebar():

    with st.sidebar:

        st.markdown(
            "<div class='sidebar-brand'>📊 AI in Finance</div>",
            unsafe_allow_html=True
        )

        st.button(
            "➕  New chat",
            use_container_width=True,
            type="primary",
            on_click=new_chat_callback
        )

        st.divider()

        # =================================================
        # PAGE NAVIGATION
        # =================================================
        nav_labels = ["💬 Chat", "📈 Analysis", "🏗️ Architecture"]
        nav_map = {
            "💬 Chat": "chat",
            "📈 Analysis": "analysis",
            "🏗️ Architecture": "architecture",
        }
        reverse_nav_map = {v: k for k, v in nav_map.items()}

        current_page = st.session_state.get("page", "chat")
        current_label = reverse_nav_map.get(current_page, nav_labels[0])

        selected_label = st.radio(
            "Navigate",
            nav_labels,
            index=nav_labels.index(current_label),
            label_visibility="collapsed"
        )

        st.session_state.page = nav_map[selected_label]

        st.divider()

        # =================================================
        # CHAT HISTORY
        # =================================================
        st.markdown(
            "<div class='sidebar-section-label'>Recents</div>",
            unsafe_allow_html=True
        )

        histories = load_all_histories(st.session_state.get("username"))

        if not histories:
            st.caption("No saved chats yet.")

        else:
            for history in histories:

                # Title = the chat's first question (falls back to timestamp).
                history_label = history.get("title") or history["timestamp"]

                st.button(
                    label=history_label,
                    key=history["file"],
                    use_container_width=True,
                    on_click=load_chat_callback,
                    args=(history["path"],)
                )

        # =================================================
        # USER ACCOUNT ROW (logged-in user + logout)
        # Keyed container so CSS can pin it to the very bottom of the sidebar.
        # =================================================
        with st.container(key="sidebar_user_dock"):
            username = st.session_state.get("username", "User")
            initials = (username[:2] or "U").upper()
            st.markdown(
                f"""
                <div class='sidebar-user'>
                    <div class='avatar'>{initials}</div>
                    <div class='who'>
                        <div class='name'>{username}</div>
                        <div class='plan'>Signed in</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Log out", use_container_width=True, key="logout_btn"):
                logout()
                st.rerun()
