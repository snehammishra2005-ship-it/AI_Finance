import streamlit as st
import pandas as pd
import os


def render_analysis_view():
    """
    Renders the analysis output section.
    Reads CSV files generated during SLM evaluation
    and allows users to view and download them.
    """

    st.subheader("📈 SLM Analysis Output")

    analysis_dir = "data/analysis_outputs"

    # Ensure directory exists
    if not os.path.exists(analysis_dir):
        st.info("No analysis outputs available yet.")
        return

    # List CSV files
    csv_files = [f for f in os.listdir(analysis_dir) if f.endswith(".csv")]

    if not csv_files:
        st.info("No analysis CSV files found.")
        return

    # Select CSV file
    selected_csv = st.selectbox(
        "Select Analysis File",
        csv_files
    )

    csv_path = os.path.join(analysis_dir, selected_csv)

    try:
        df = pd.read_csv(csv_path)

        st.markdown("### 📄 Analysis Preview")
        st.dataframe(df, use_container_width=True)

        # Download option
        with open(csv_path, "rb") as f:
            st.download_button(
                label="⬇️ Download Analysis CSV",
                data=f,
                file_name=selected_csv,
                mime="text/csv"
            )

    except Exception as e:
        st.error("Failed to load analysis file.")
        st.exception(e)
