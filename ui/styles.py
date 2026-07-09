import streamlit as st


def inject_global_css():
    """
    Global layout/typography styling to give the app a ChatGPT-like feel:
    narrow centered chat column, compact sidebar, comfortable message
    spacing and font sizing. Intentionally leaves colors untouched.
    """

    st.markdown(
        """
        <style>
        html, body, [class*="css"] {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                Roboto, Helvetica, Arial, sans-serif;
        }

        /* ---- Centered, ChatGPT-width main column ---- */
        .block-container {
            max-width: 820px;
            padding-top: 4.5rem;
            padding-bottom: 7rem;
            margin: 0 auto;
        }

        h1 { font-size: 1.4rem; font-weight: 600; }
        h2 { font-size: 1.15rem; font-weight: 600; }
        h3 { font-size: 1rem; font-weight: 600; }

        /* ---- Chat header row (title + model/persona pickers) ---- */
        .chat-title {
            font-size: 1.05rem;
            font-weight: 600;
            line-height: 2.4rem;
            margin: 0;
        }

        /* ---- Welcome screen ---- */
        .welcome-wrap {
            text-align: center;
            margin: 3.5rem 0 2.5rem 0;
        }
        .welcome-title {
            font-size: 1.7rem;
            font-weight: 600;
        }
        .welcome-subtitle {
            font-size: 0.95rem;
            opacity: 0.65;
            margin-top: 0.5rem;
            line-height: 1.5;
        }

        /* ---- Chat messages ---- */
        [data-testid="stChatMessage"] {
            padding: 0.6rem 0;
            font-size: 1rem;
            line-height: 1.65;
        }
        [data-testid="stChatMessage"] p {
            font-size: 1rem;
            line-height: 1.65;
        }
        [data-testid="stChatMessage"] .stCaption {
            font-size: 0.75rem;
        }

        /* ---- Chat input ---- */
        [data-testid="stChatInput"] textarea {
            font-size: 1rem;
        }
        [data-testid="stChatInput"] {
            border-radius: 1.25rem;
        }

        /* ---- Sidebar ---- */
        section[data-testid="stSidebar"] {
            min-width: 265px;
            max-width: 265px;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1rem;
            max-width: 100%;
        }
        section[data-testid="stSidebar"] button {
            font-size: 0.85rem;
            border-radius: 0.6rem;
        }
        .sidebar-brand {
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.75rem;
        }
        .sidebar-section-label {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            opacity: 0.6;
            margin: 0.5rem 0 0.35rem 0;
        }

        /* ---- Compact selectboxes used in the chat header ---- */
        div[data-testid="stSelectbox"] label {
            display: none;
        }
        div[data-testid="stSelectbox"] > div {
            font-size: 0.85rem;
            min-height: 2.4rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
