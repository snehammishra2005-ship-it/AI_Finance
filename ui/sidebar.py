import streamlit as st

from utils.history_manager import (
    save_chat_history,
    load_all_histories,
    load_chat_history
)


# -------------------------------------------------
# Load Previous Chat Callback
# -------------------------------------------------
def load_chat_callback(file_path):
    data = load_chat_history(file_path)

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
            slm=st.session_state.get("slm")
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
            "<div class='sidebar-section-label'>Chats</div>",
            unsafe_allow_html=True
        )

        histories = load_all_histories()

        if not histories:
            st.caption("No saved chats yet.")

        else:
            for history in histories:

                history_label = (
                    f"{history['timestamp']} · {history['persona']}"
                )

                st.button(
                    label=history_label,
                    key=history["file"],
                    use_container_width=True,
                    on_click=load_chat_callback,
                    args=(history["path"],)
                )
