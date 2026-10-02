"""Upload / demo-load widget: runs the Week 2 pipeline (ingest -> validate ->
transform -> DuckDB) and shows the validation result before any dashboard
data is made available.
"""

from pathlib import Path

import streamlit as st

from pipeline.db import build_and_load, get_connection
from pipeline.ingest import ingest_csv
from pipeline.validate import validate_line_items

DEMO_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "synthetic" / "small_clean.csv"


def _process(file_or_path) -> None:
    df = ingest_csv(file_or_path)
    result = validate_line_items(df)
    st.session_state["validation_result"] = result

    if not result.is_valid:
        st.session_state["data_loaded"] = False
        return

    conn = get_connection()
    tables = build_and_load(conn, df)
    st.session_state["conn"] = conn
    st.session_state["tables"] = tables
    st.session_state["data_loaded"] = True


def render_upload_section() -> None:
    st.subheader("1. Load your sales data")

    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded_file = st.file_uploader("Upload a Square item sales CSV", type=["csv"])
    with col2:
        st.write("")
        st.write("")
        load_demo = st.button("Load Demo Store", width="stretch")

    if uploaded_file is not None:
        _process(uploaded_file)
    elif load_demo:
        _process(DEMO_DATA_PATH)

    result = st.session_state.get("validation_result")
    if result is None:
        return

    if result.is_valid:
        st.success(f"Validation passed - {result.row_count:,} rows loaded.")
    else:
        st.error(f"Validation failed - {result.error_count} issue(s) found in {result.row_count:,} rows.")
        st.dataframe(result.errors, width="stretch")
