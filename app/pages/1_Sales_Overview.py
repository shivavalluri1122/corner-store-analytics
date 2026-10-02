"""Sales Overview dashboard: KPIs, category mix, hour-by-weekday heatmap,
month-over-month trend, and top-20 products by units/sales.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import streamlit as st  # noqa: E402

from app.components.charts import (  # noqa: E402
    category_mix_chart,
    hour_weekday_heatmap,
    month_over_month_trend,
    top_n_by_sales,
    top_n_by_units,
)
from app.components.kpi_cards import render_kpi_cards  # noqa: E402
from pipeline import analytics  # noqa: E402

st.set_page_config(page_title="Sales Overview - Corner Store Analytics", layout="wide")
st.title("Sales Overview")

if not st.session_state.get("data_loaded"):
    st.warning("No data loaded yet. Go to the Home page to upload a CSV or load the demo store.")
    st.stop()

conn = st.session_state["conn"]
min_date, max_date = analytics.get_date_bounds(conn)

date_range = st.date_input(
    "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
if not isinstance(date_range, tuple) or len(date_range) != 2:
    st.stop()  # user is mid-selection (only one date picked so far)
start_date, end_date = date_range

kpis = analytics.compute_kpis(conn, start_date, end_date)
render_kpi_cards(kpis)

st.divider()

col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(category_mix_chart(analytics.category_mix(conn, start_date, end_date)), width="stretch")
with col2:
    st.plotly_chart(
        hour_weekday_heatmap(analytics.hour_weekday_transaction_counts(conn, start_date, end_date)),
        width="stretch",
    )

st.plotly_chart(
    month_over_month_trend(analytics.month_over_month_trend(conn, start_date, end_date)), width="stretch"
)

col3, col4 = st.columns(2)
with col3:
    st.plotly_chart(top_n_by_units(analytics.top_n_items_by_units(conn, start_date, end_date, n=20)), width="stretch")
with col4:
    st.plotly_chart(top_n_by_sales(analytics.top_n_items_by_sales(conn, start_date, end_date, n=20)), width="stretch")
