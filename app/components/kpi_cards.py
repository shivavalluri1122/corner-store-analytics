"""KPI card row for the Sales Overview dashboard."""

import streamlit as st

from pipeline.analytics import KPIResult


def render_kpi_cards(kpis: KPIResult) -> None:
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Net Sales", f"${kpis.net_sales:,.2f}")
    col2.metric("Transactions", f"{kpis.transactions:,}")
    col3.metric("Average Basket", f"${kpis.avg_basket:,.2f}")
    col4.metric("Units", f"{kpis.units:,}")
    col5.metric("Distinct Items Sold", f"{kpis.distinct_items:,}")
