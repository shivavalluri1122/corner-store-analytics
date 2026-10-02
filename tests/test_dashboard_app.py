"""Streamlit AppTest smoke tests: Load Demo Store -> Sales Overview, and the
date range actually flows through to the rendered KPI cards."""

import datetime as dt
from pathlib import Path

from streamlit.testing.v1 import AppTest

from pipeline import analytics

APP_DIR = Path(__file__).parent.parent / "app"


def _kpi_values(at: AppTest) -> dict[str, str]:
    return {m.label: m.value for m in at.metric}


def test_load_demo_store_then_sales_overview_renders_kpis_for_selected_range(small_clean_path):
    home = AppTest.from_file(str(APP_DIR / "Home.py"), default_timeout=60).run()
    assert not home.exception
    home.button[0].click().run()
    assert not home.exception
    assert home.session_state["data_loaded"] is True

    page = AppTest.from_file(str(APP_DIR / "pages" / "1_Sales_Overview.py"), default_timeout=60)
    page.session_state["data_loaded"] = True
    page.session_state["conn"] = home.session_state["conn"]
    page.run()
    assert not page.exception

    conn = home.session_state["conn"]
    min_date, max_date = analytics.get_date_bounds(conn)
    full = analytics.compute_kpis(conn, min_date, max_date)
    assert _kpi_values(page)["Transactions"] == f"{full.transactions:,}"
    assert _kpi_values(page)["Net Sales"] == f"${full.net_sales:,.2f}"

    start, end = dt.date(2025, 4, 10), dt.date(2025, 8, 20)
    page.date_input[0].set_value((start, end)).run()
    assert not page.exception
    sub = analytics.compute_kpis(conn, start, end)
    values = _kpi_values(page)
    assert values["Net Sales"] == f"${sub.net_sales:,.2f}"
    assert values["Transactions"] == f"{sub.transactions:,}"
    assert values["Average Basket"] == f"${sub.avg_basket:,.2f}"
    assert values["Units"] == f"{sub.units:,}"
    assert values["Distinct Items Sold"] == f"{sub.distinct_items:,}"
    assert sub.transactions < full.transactions
