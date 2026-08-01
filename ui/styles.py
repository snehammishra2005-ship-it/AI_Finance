import streamlit as st


def inject_global_css():
    """
    Global styling that gives the app a clean, minimal, ChatGPT-like look:
    an off-white rounded sidebar, a white content area, pill-shaped controls,
    soft shadows instead of hard borders, and generous whitespace.

    This is presentation only - it restyles the existing widgets and does not
    change any behaviour, callbacks, or page structure.
    """

    st.markdown(
        """
        <style>
        :root {
            --bg-main: #ffffff;
            --bg-sidebar: #f9f9f9;
            --bg-hover: #ececec;
            --bg-active: #e8e8e8;
            --text-primary: #1a1a1a;
            --text-secondary: #8a8a8a;
            --accent: #000000;
            --radius-pill: 999px;
            --radius-card: 16px;
            --shadow-soft: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
            --shadow-input: 0 2px 12px rgba(0,0,0,0.08);
        }

        html, body, [class*="css"] {
            font-family: "Söhne", -apple-system, BlinkMacSystemFont, "Segoe UI",
                Inter, Roboto, Helvetica, Arial, sans-serif;
            color: var(--text-primary);
        }

        /* ---- Surfaces ---- */
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            background: var(--bg-main);
        }
        /* Streamlit's own top header + bottom chat-input chrome, so they match
           the light content area instead of showing a dark bar. */
        [data-testid="stHeader"] {
            background: var(--bg-main);
        }
        [data-testid="stBottom"],
        [data-testid="stBottom"] > div,
        [data-testid="stBottomBlockContainer"] {
            background: var(--bg-main);
        }

        .block-container {
            max-width: 820px;
            padding-top: 4rem;
            padding-bottom: 7rem;
            margin: 0 auto;
        }

        h1 { font-size: 1.4rem; font-weight: 650; }
        h2 { font-size: 1.15rem; font-weight: 650; }
        h3 { font-size: 1rem; font-weight: 650; }

        /* ================= SIDEBAR ================= */
        section[data-testid="stSidebar"] {
            min-width: 290px;
            max-width: 290px;
            background: var(--bg-sidebar);
            border-right: none;
        }
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1.1rem;
            padding-left: 0.9rem;
            padding-right: 0.9rem;
            max-width: 100%;
        }
        /* soften Streamlit's default dividers */
        section[data-testid="stSidebar"] hr {
            margin: 0.6rem 0;
            border-color: rgba(0,0,0,0.06);
        }

        .sidebar-brand {
            font-size: 1.02rem;
            font-weight: 700;
            padding: 0.1rem 0.4rem 0.6rem 0.4rem;
            letter-spacing: -0.01em;
        }

        .sidebar-section-label {
            font-size: 0.7rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--text-secondary);
            margin: 0.9rem 0 0.3rem 0.5rem;
        }

        /* Sidebar buttons (nav + recents) -> soft rounded rows */
        section[data-testid="stSidebar"] .stButton button {
            font-size: 0.88rem;
            font-weight: 500;
            text-align: left;
            justify-content: flex-start;
            background: transparent;
            border: none;
            box-shadow: none;
            color: var(--text-primary);
            border-radius: 10px;
            padding: 0.45rem 0.7rem;
            min-height: 38px;
        }
        section[data-testid="stSidebar"] .stButton button:hover {
            background: var(--bg-hover);
            color: var(--text-primary);
        }
        /* "New chat" (primary) gets a subtle solid emphasis */
        section[data-testid="stSidebar"] .stButton button[kind="primary"],
        section[data-testid="stSidebar"] [data-testid="baseButton-primary"] {
            background: var(--bg-active);
            font-weight: 600;
        }
        section[data-testid="stSidebar"] .stButton button[kind="primary"]:hover {
            background: #e0e0e0;
        }

        /* Page nav radio -> ChatGPT-style nav rows (hide the radio dots) */
        section[data-testid="stSidebar"] div[role="radiogroup"] {
            gap: 2px;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label {
            border-radius: 10px;
            padding: 0.4rem 0.6rem;
            min-height: 38px;
            display: flex;
            align-items: center;
            cursor: pointer;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
            background: var(--bg-hover);
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
            background: var(--bg-active);
            font-weight: 600;
        }
        section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
            display: none;  /* hide the radio circle */
        }

        /* User account row pinned near the bottom */
        .sidebar-user {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            padding: 0.5rem 0.5rem;
            margin-top: 0.6rem;
            border-radius: 12px;
        }
        .sidebar-user:hover { background: var(--bg-hover); }
        .sidebar-user .avatar {
            width: 30px; height: 30px;
            border-radius: 50%;
            background: #1a1a1a;
            color: #fff;
            display: flex; align-items: center; justify-content: center;
            font-size: 0.72rem; font-weight: 700;
            flex: 0 0 auto;
        }
        .sidebar-user .who { line-height: 1.15; overflow: hidden; }
        .sidebar-user .who .name { font-size: 0.85rem; font-weight: 600; }
        .sidebar-user .who .plan { font-size: 0.72rem; color: var(--text-secondary); }

        /* ================= MAIN AREA ================= */
        /* Chat header title */
        .chat-title {
            font-size: 1.05rem;
            font-weight: 650;
            line-height: 2.6rem;
            margin: 0;
        }

        /* Model / persona selectors -> subtle pills */
        div[data-testid="stSelectbox"] label { display: none; }
        div[data-testid="stSelectbox"] > div > div {
            border-radius: var(--radius-pill);
            border: 1px solid rgba(0,0,0,0.08);
            background: #fff;
            box-shadow: var(--shadow-soft);
            font-size: 0.85rem;
            min-height: 2.4rem;
        }

        /* Welcome / greeting */
        .welcome-wrap {
            text-align: center;
            margin: 4.5rem 0 2.2rem 0;
        }
        .welcome-title {
            font-size: 2.1rem;
            font-weight: 700;
            color: #2b2b2b;
            letter-spacing: -0.02em;
        }
        .welcome-subtitle {
            font-size: 0.95rem;
            color: var(--text-secondary);
            margin-top: 0.6rem;
            line-height: 1.5;
        }

        /* Chat messages */
        [data-testid="stChatMessage"] {
            padding: 0.6rem 0;
            font-size: 1rem;
            line-height: 1.7;
            background: transparent;
        }
        [data-testid="stChatMessage"] p { font-size: 1rem; line-height: 1.7; }
        [data-testid="stChatMessage"] .stCaption { font-size: 0.75rem; }

        /* Chat input -> prominent pill with soft shadow, no hard border */
        [data-testid="stChatInput"] {
            border-radius: var(--radius-pill);
            border: 1px solid rgba(0,0,0,0.08);
            box-shadow: var(--shadow-input);
            background: #fff;
            padding: 0.15rem 0.4rem;
        }
        [data-testid="stChatInput"] textarea { font-size: 1rem; }
        [data-testid="stChatInput"]:focus-within {
            border-color: rgba(0,0,0,0.18);
        }
        /* Send button -> black circular accent */
        [data-testid="stChatInput"] button {
            border-radius: 50%;
            background: var(--accent);
            color: #fff;
        }

        /* Attach / toggles -> soft rounded card, subtle shadow, no hard border */
        [data-testid="stExpander"] {
            border-radius: var(--radius-card);
            border: none;
            box-shadow: var(--shadow-soft);
            background: #fff;
            overflow: hidden;
        }

        /* Generic buttons in the main area -> rounded, soft */
        [data-testid="stMain"] .stButton button {
            border-radius: var(--radius-pill);
            border: 1px solid rgba(0,0,0,0.08);
            box-shadow: var(--shadow-soft);
        }
        [data-testid="stMain"] .stButton button:hover {
            border-color: rgba(0,0,0,0.18);
        }

        /* Download buttons + dataframes rounded */
        [data-testid="stDownloadButton"] button { border-radius: var(--radius-pill); }
        </style>
        """,
        unsafe_allow_html=True,
    )
