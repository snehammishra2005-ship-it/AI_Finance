import streamlit as st


def inject_global_css():
    """
    Global styling — "Carbon amber" dark theme: warm charcoal surfaces, a gold
    accent, pill-shaped controls, soft depth instead of hard borders, and
    generous whitespace.

    Presentation only — it restyles the existing widgets and does not change any
    behaviour, callbacks, or page structure. Palette lives in :root, so swapping
    themes is a matter of editing the variables here (+ .streamlit/config.toml).
    """

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
        :root {
            --bg-main: #17130d;
            --bg-sidebar: #1e180f;
            --bg-hover: #2a2016;
            --bg-active: #33281a;
            --surface: #221b11;
            --text-primary: #efe7db;
            --text-secondary: #a29688;
            --accent: #f59e0b;
            --accent-hover: #fbb43b;
            --on-accent: #1a1400;
            --border: rgba(255,255,255,0.09);
            --border-strong: rgba(255,255,255,0.20);
            --radius-pill: 999px;
            --radius-card: 16px;
            --shadow-soft: 0 1px 3px rgba(0,0,0,0.40);
            --shadow-input: 0 2px 14px rgba(0,0,0,0.45);
        }

        /* One clean font everywhere. Inter (loaded above) with a system
           fallback; !important so it also overrides Streamlit's own default
           font on its emotion-cache classes for a consistent look. */
        html, body, .stApp, [class*="css"], [class*="st-"],
        button, input, textarea, select,
        [data-testid="stMarkdownContainer"], [data-testid="stMarkdownContainer"] * {
            font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI",
                Roboto, Helvetica, Arial, sans-serif !important;
        }
        /* Global scale-down: Streamlit sizes text in rem off the root, so
           lowering the root font size shrinks all text proportionally. */
        html { font-size: 14px; }
        html, body { color: var(--text-primary); }

        /* Headings use Space Grotesk (display); body stays Inter. Needs
           !important + these specific selectors to beat the blanket Inter rule
           above, including markdown headings inside answers. */
        .welcome-title, .chat-title, .sidebar-brand,
        h1, h2, h3,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3 {
            font-family: "Space Grotesk", "Inter", -apple-system,
                "Segoe UI", sans-serif !important;
        }
        /* Restore Material Symbols on icon glyphs — the blanket Inter rule
           above otherwise turns Streamlit's icons into their ligature text
           (e.g. "keyboard_double_arrow_left" on the sidebar toggle). */
        [data-testid="stIconMaterial"] {
            font-family: "Material Symbols Rounded" !important;
        }

        /* ---- Surfaces ---- */
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"] {
            background: var(--bg-main);
        }
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
            padding-top: 3rem;
            padding-bottom: 1.5rem;
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
        section[data-testid="stSidebar"] hr {
            margin: 0.6rem 0;
            border-color: var(--border);
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
        section[data-testid="stSidebar"] .stButton button[kind="primary"],
        section[data-testid="stSidebar"] [data-testid="baseButton-primary"] {
            background: var(--bg-active);
            font-weight: 600;
        }
        section[data-testid="stSidebar"] .stButton button[kind="primary"]:hover {
            background: #3f3120;
        }

        /* Page nav radio -> nav rows (hide the radio dots) */
        section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 2px; }
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
            display: none;
        }

        /* Make the sidebar's content column fill the height and push the user
           account row to the very bottom. */
        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .sidebar-user) {
            display: flex;
            flex-direction: column;
            min-height: calc(100vh - 3.5rem);
        }
        section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has(.sidebar-user) {
            margin-top: auto;
        }

        /* User account row at the bottom */
        .sidebar-user {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            padding: 0.5rem 0.5rem;
            border-radius: 12px;
        }
        .sidebar-user:hover { background: var(--bg-hover); }
        .sidebar-user .avatar {
            width: 30px; height: 30px;
            border-radius: 50%;
            background: var(--accent);
            color: var(--on-accent);
            display: flex; align-items: center; justify-content: center;
            font-size: 0.72rem; font-weight: 700;
            flex: 0 0 auto;
        }
        .sidebar-user .who { line-height: 1.15; overflow: hidden; }
        .sidebar-user .who .name { font-size: 0.85rem; font-weight: 600; }
        .sidebar-user .who .plan { font-size: 0.72rem; color: var(--text-secondary); }

        /* Hide Streamlit's sidebar collapse/expand control (the
           "keyboard_double_arrow" chevrons) so the sidebar stays put. */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stExpandSidebarButton"],
        button[aria-label="Close sidebar"],
        button[aria-label="Open sidebar"],
        button[aria-label="Collapse sidebar"] {
            display: none !important;
        }

        /* Pin the profile row to the very bottom of the sidebar: make the
           sidebar's content column fill the height, then push the keyed user
           dock down with an auto top margin. */
        /* Pin the profile row to the sidebar bottom: position it absolutely
           against the sidebar section (which is exactly the visible sidebar
           height), and reserve scroll room so recents don't hide behind it. */
        section[data-testid="stSidebar"] { position: relative; }
        section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
            padding-bottom: 3rem;
        }
        .st-key-sidebar_user_dock {
            position: absolute !important;
            left: 0.9rem !important;
            right: 0.9rem !important;
            bottom: 10px !important;
            top: auto !important;
            height: auto !important;
            min-height: 0 !important;
            flex-grow: 0 !important;
            z-index: 5;
        }

        /* ================= MAIN AREA ================= */
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
            border: 1px solid var(--border);
            background: var(--surface);
            box-shadow: var(--shadow-soft);
            font-size: 0.85rem;
            min-height: 2.4rem;
        }

        /* Welcome / greeting — pushed toward vertical center on the empty
           screen (the composer sits inline just below it). */
        .welcome-wrap { text-align: center; margin: 12vh 0 2rem 0; }
        .welcome-title {
            font-size: 2.1rem;
            font-weight: 700;
            color: var(--text-primary);
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

        /* Chat input (legacy widget) -> pill */
        [data-testid="stChatInput"] {
            border-radius: var(--radius-pill);
            border: 1px solid var(--border);
            box-shadow: var(--shadow-input);
            background: var(--surface);
            padding: 0.15rem 0.4rem;
        }
        [data-testid="stChatInput"] textarea { font-size: 1rem; }
        [data-testid="stChatInput"] > div,
        [data-testid="stChatInput"] [data-baseweb="textarea"],
        [data-testid="stChatInput"] [data-baseweb="base-input"] {
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }
        [data-testid="stChatInput"]:focus-within { border-color: var(--border-strong); }
        [data-testid="stChatInput"] button {
            border-radius: 50%;
            background: var(--accent);
            color: var(--on-accent);
        }

        /* ---- Composer pill: bordered container with [+] [input] [send] ---- */
        .st-key-composer_pill {
            border-radius: var(--radius-pill) !important;
            border: 1px solid var(--border) !important;
            box-shadow: var(--shadow-input) !important;
            background: var(--surface) !important;
            padding: 0.1rem 0.6rem !important;
        }
        [data-testid="stForm"] {
            border: none !important;
            padding: 0 !important;
            background: transparent !important;
        }
        .st-key-composer_pill [data-baseweb="input"],
        .st-key-composer_pill [data-baseweb="base-input"],
        .st-key-composer_pill input {
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
        }
        /* "+" attach trigger -> round, subtle */
        [data-testid="stPopover"] button {
            border-radius: 50% !important;
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
            color: var(--text-secondary) !important;
            font-size: 1.2rem;
            min-height: 36px;
        }
        [data-testid="stPopover"] button:hover { background: var(--bg-hover) !important; }
        [data-testid="stPopover"] button [data-testid="stIconMaterial"] {
            display: none !important;
        }
        /* send button (form submit) -> gold accent circle */
        [data-testid="stFormSubmitButton"] button {
            border-radius: 50% !important;
            background: var(--accent) !important;
            color: var(--on-accent) !important;
            border: none !important;
            box-shadow: none !important;
            min-height: 34px;
        }
        [data-testid="stFormSubmitButton"] button:hover { background: var(--accent-hover) !important; }

        /* Attach / toggles -> soft rounded card */
        [data-testid="stExpander"] {
            border-radius: var(--radius-card);
            border: none;
            box-shadow: var(--shadow-soft);
            background: var(--surface);
            overflow: hidden;
        }

        /* Generic buttons in the main area -> rounded, soft */
        [data-testid="stMain"] .stButton button {
            border-radius: var(--radius-pill);
            border: 1px solid var(--border);
            box-shadow: var(--shadow-soft);
        }
        [data-testid="stMain"] .stButton button:hover { border-color: var(--border-strong); }

        [data-testid="stDownloadButton"] button { border-radius: var(--radius-pill); }
        </style>
        """,
        unsafe_allow_html=True,
    )
