"""Home page: upload a Square item sales CSV or load the demo store."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from app.components.upload_widget import render_upload_section  # noqa: E402

st.set_page_config(page_title="Corner Store Analytics", layout="wide")

st.title("Corner Store Analytics")
st.write(
    "Upload your Square item sales CSV, or load a demo store, to see instant "
    "sales analytics. Customer information is stripped before any analysis "
    "runs, and nothing is stored beyond this session."
)

render_upload_section()

if st.session_state.get("data_loaded"):
    st.info("Data loaded. Open **Sales Overview** in the sidebar to see the dashboard.")
