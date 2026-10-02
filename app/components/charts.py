"""Reusable Plotly chart builders for the Sales Overview dashboard.

These functions only shape/present data for display (pivoting into a
matrix, sort order for bars, empty-state handling). All aggregation lives
in pipeline.analytics - charts never re-derive a KPI or grouping.
"""

import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure

from pipeline.analytics import WEEKDAY_ORDER


def _empty_figure(title: str) -> Figure:
    fig = Figure()
    fig.update_layout(
        title=title,
        xaxis={"visible": False},
        yaxis={"visible": False},
        annotations=[{"text": "No data for the selected range", "showarrow": False, "font": {"size": 16}}],
    )
    return fig


def category_mix_chart(mix: pd.DataFrame) -> Figure:
    """mix: columns category, net_sales, pct_of_total (from pipeline.analytics.category_mix)."""
    if mix.empty:
        return _empty_figure("Category Mix (Net Sales)")
    ordered = mix.sort_values("net_sales", ascending=True)
    fig = px.bar(
        ordered,
        x="net_sales",
        y="category",
        orientation="h",
        custom_data=["pct_of_total"],
        title="Category Mix (Net Sales)",
    )
    fig.update_traces(hovertemplate="%{y}: $%{x:,.2f} (%{customdata[0]:.1f}% of total)<extra></extra>")
    fig.update_layout(yaxis_title="", xaxis_title="Net Sales ($)")
    return fig


def hour_weekday_heatmap(heatmap_data: pd.DataFrame) -> Figure:
    """heatmap_data: columns weekday, hour, transactions - a full 7x24 grid
    (from pipeline.analytics.hour_weekday_transaction_counts)."""
    if heatmap_data.empty:
        return _empty_figure("Transactions by Hour & Weekday")
    pivot = heatmap_data.pivot_table(index="weekday", columns="hour", values="transactions", fill_value=0)
    pivot = pivot.reindex(index=WEEKDAY_ORDER, columns=range(24), fill_value=0)
    fig = px.imshow(
        pivot,
        labels=dict(x="Hour of Day", y="Day of Week", color="Transactions"),
        aspect="auto",
        title="Transactions by Hour & Weekday",
    )
    return fig


def month_over_month_trend(trend: pd.DataFrame) -> Figure:
    """trend: columns month, net_sales, mom_pct_change (from
    pipeline.analytics.month_over_month_trend)."""
    if trend.empty:
        return _empty_figure("Month-over-Month Net Sales")
    fig = px.line(
        trend,
        x="month",
        y="net_sales",
        markers=True,
        custom_data=["mom_pct_change"],
        title="Month-over-Month Net Sales",
    )
    fig.update_traces(
        hovertemplate="%{x|%b %Y}: $%{y:,.2f}<br>MoM change: %{customdata[0]:.1f}%<extra></extra>"
    )
    fig.update_layout(xaxis_title="Month", yaxis_title="Net Sales ($)")
    return fig


def top_n_by_units(top: pd.DataFrame) -> Figure:
    """top: columns item, units (from pipeline.analytics.top_n_items_by_units)."""
    if top.empty:
        return _empty_figure("Top Products by Units")
    fig = px.bar(top, x="units", y="item", orientation="h", title=f"Top {len(top)} Products by Units")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, yaxis_title="", xaxis_title="Units Sold")
    return fig


def top_n_by_sales(top: pd.DataFrame) -> Figure:
    """top: columns item, net_sales (from pipeline.analytics.top_n_items_by_sales)."""
    if top.empty:
        return _empty_figure("Top Products by Sales")
    fig = px.bar(top, x="net_sales", y="item", orientation="h", title=f"Top {len(top)} Products by Sales")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, yaxis_title="", xaxis_title="Net Sales ($)")
    return fig
