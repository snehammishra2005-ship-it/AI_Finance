import streamlit as st
import requests

from config.settings import BACKEND_BASE_URL


def render_research_view():
    """
    Deep Research page: asks the backend to combine live web search with the
    user's uploaded documents into a single cited report.
    """

    st.markdown("## 🔬 Deep Research")
    st.caption(
        "Researches your question across the live web and your uploaded "
        "documents, then synthesizes a cited report."
    )

    st.divider()

    question = st.text_area(
        "Research question",
        placeholder="e.g. How have rising interest rates affected Indian banking stocks this year?",
        height=100,
    )

    run = st.button("🔍 Run Deep Research", type="primary")

    if not run:
        return

    if not question or not question.strip():
        st.warning("Please enter a research question.")
        return

    persona = st.session_state.get("persona", "General User")
    session_id = st.session_state.get("session_id", "default")

    with st.spinner("Searching the web, reading your documents, and synthesizing..."):
        try:
            response = requests.post(
                f"{BACKEND_BASE_URL}/research",
                json={
                    "question": question,
                    "session_id": session_id,
                    "persona": persona,
                },
                timeout=180,
            )
        except requests.exceptions.Timeout:
            st.error("⚠️ Research timed out after 180s. Try a narrower question.")
            return
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Could not connect to backend. Make sure the FastAPI server is running.")
            return
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            return

    if response.status_code != 200:
        st.error(f"Research failed ({response.status_code}): {response.text}")
        return

    data = response.json()

    # ------- Report -------
    st.markdown("### 📄 Research Report")
    st.markdown(data.get("report", "_No report returned._"))

    # ------- Web sources -------
    web_sources = data.get("web_sources", [])
    if web_sources:
        st.markdown("### 🌐 Web Sources")
        for i, src in enumerate(web_sources, 1):
            title = src.get("title") or src.get("url", "Untitled")
            url = src.get("url", "")
            st.markdown(f"**[W{i}]** [{title}]({url})")

    # ------- Transparency notes -------
    notes = data.get("notes", [])
    if notes:
        with st.expander("ℹ️ About this answer's sources"):
            for note in notes:
                st.markdown(f"- {note}")

    # ------- Source summary line -------
    used_web = data.get("web_configured")
    used_docs = data.get("used_docs")
    summary_bits = []
    summary_bits.append("🌐 web" if used_web else "web not used")
    summary_bits.append("📚 your documents" if used_docs else "no documents used")
    st.caption("Sources: " + " · ".join(summary_bits))
