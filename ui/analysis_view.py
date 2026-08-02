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

        _render_score_chart(df)

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


# The score columns the scoring engine writes (0.0-1.0). Charted as a bar
# comparison so the four quality dimensions are readable at a glance instead
# of only as a table row.
_SCORE_COLUMNS = [
    "Verification Score",
    "Validation Score",
    "Explainability Score",
    "Persona Suitability",
    "System Score",
]


def _render_score_chart(df: pd.DataFrame) -> None:
    """Draw a bar chart of the 0-1 quality scores for each analyzed file.

    Skipped quietly when the CSV has no numeric scores (e.g. a row where
    scoring failed and the values are blank), so the view never errors.
    """
    present = [c for c in _SCORE_COLUMNS if c in df.columns]
    if not present:
        return

    chart_df = df.copy()
    for col in present:
        chart_df[col] = pd.to_numeric(chart_df[col], errors="coerce")

    # Index by file name if available so the chart legend is meaningful.
    label_col = "File Name" if "File Name" in chart_df.columns else None
    scores = chart_df[present]
    if label_col:
        scores = scores.set_axis(chart_df[label_col], axis=0)

    # Drop rows that are entirely NaN (scoring failed → nothing to plot).
    scores = scores.dropna(how="all")
    if scores.empty:
        st.caption("No numeric scores to chart for this file yet.")
        return

    st.markdown("### 📊 Score Breakdown")
    # Transpose so each dimension is a bar group; keeps it readable for a
    # single-file report (the common case) and multi-file ones alike.
    st.bar_chart(scores.T)
