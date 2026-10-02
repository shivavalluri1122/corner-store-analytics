import datetime as dt

import pandas as pd
import pytest

from app.components import charts
from pipeline import analytics
from pipeline.ingest import ingest_csv
from tests.create_kpi_check import compare as kpi_compare
from tests.create_kpi_check import independent_kpis, write_workbook


def test_get_date_bounds_matches_data(loaded_conn, small_clean_path):
    df = ingest_csv(small_clean_path)
    min_date, max_date = analytics.get_date_bounds(loaded_conn)
    assert min_date == df["date"].min().date()
    assert max_date == df["date"].max().date()


def test_compute_kpis_matches_manual_calculation(loaded_conn, small_clean_path):
    df = ingest_csv(small_clean_path)
    min_date, max_date = analytics.get_date_bounds(loaded_conn)

    kpis = analytics.compute_kpis(loaded_conn, min_date, max_date)

    assert kpis.net_sales == pytest.approx(df["net_sales"].sum())
    assert kpis.transactions == df["transaction_id"].nunique()
    assert kpis.units == df["qty"].sum()
    assert kpis.distinct_items == df["item"].nunique()
    assert kpis.avg_basket == pytest.approx(kpis.net_sales / kpis.transactions)


def test_compute_kpis_average_basket_is_zero_when_no_transactions(loaded_conn):
    min_date, _ = analytics.get_date_bounds(loaded_conn)
    before_data = min_date - dt.timedelta(days=30)

    kpis = analytics.compute_kpis(loaded_conn, before_data, before_data)

    assert kpis.net_sales == 0
    assert kpis.transactions == 0
    assert kpis.avg_basket == 0  # must not raise ZeroDivisionError
    assert kpis.units == 0
    assert kpis.distinct_items == 0


def test_date_range_filter_narrows_all_kpis(loaded_conn):
    min_date, max_date = analytics.get_date_bounds(loaded_conn)
    full_range = analytics.compute_kpis(loaded_conn, min_date, max_date)
    one_day = analytics.compute_kpis(loaded_conn, min_date, min_date)

    assert one_day.net_sales <= full_range.net_sales
    assert one_day.transactions <= full_range.transactions
    assert one_day.units <= full_range.units


def test_category_mix_percentages_sum_to_100(loaded_conn):
    min_date, max_date = analytics.get_date_bounds(loaded_conn)
    mix = analytics.category_mix(loaded_conn, min_date, max_date)

    assert len(mix) == 10  # all 10 catalog categories appear
    assert round(mix["pct_of_total"].sum(), 6) == 100.0
    # sorted descending by net_sales
    assert list(mix["net_sales"]) == sorted(mix["net_sales"], reverse=True)


def test_category_mix_empty_range_returns_empty_frame(loaded_conn):
    min_date, _ = analytics.get_date_bounds(loaded_conn)
    before_data = min_date - dt.timedelta(days=30)
    mix = analytics.category_mix(loaded_conn, before_data, before_data)
    assert mix.empty


def test_hour_weekday_grid_is_full_and_matches_transaction_count(loaded_conn):
    min_date, max_date = analytics.get_date_bounds(loaded_conn)
    heatmap = analytics.hour_weekday_transaction_counts(loaded_conn, min_date, max_date)
    kpis = analytics.compute_kpis(loaded_conn, min_date, max_date)

    assert len(heatmap) == 7 * 24  # every weekday x hour combination present
    assert set(heatmap["weekday"]) == set(analytics.WEEKDAY_ORDER)
    assert set(heatmap["hour"]) == set(range(24))
    assert heatmap["transactions"].sum() == kpis.transactions


def test_month_over_month_trend_sorted_chronologically(loaded_conn):
    min_date, max_date = analytics.get_date_bounds(loaded_conn)
    trend = analytics.month_over_month_trend(loaded_conn, min_date, max_date)

    assert list(trend["month"]) == sorted(trend["month"])
    assert trend["mom_pct_change"].iloc[0] is None or trend["mom_pct_change"].isna().iloc[0]


def test_top_n_items_by_units_respects_limit_and_order(loaded_conn):
    min_date, max_date = analytics.get_date_bounds(loaded_conn)
    top = analytics.top_n_items_by_units(loaded_conn, min_date, max_date, n=20)

    assert len(top) <= 20
    assert list(top["units"]) == sorted(top["units"], reverse=True)


def test_top_n_items_by_sales_respects_limit_and_order(loaded_conn):
    min_date, max_date = analytics.get_date_bounds(loaded_conn)
    top = analytics.top_n_items_by_sales(loaded_conn, min_date, max_date, n=20)

    assert len(top) <= 20
    assert list(top["net_sales"]) == sorted(top["net_sales"], reverse=True)


def test_no_pii_columns_in_analytics_tables(loaded_conn):
    line_items = loaded_conn.execute("SELECT * FROM line_items LIMIT 1").df()
    transactions = loaded_conn.execute("SELECT * FROM transactions LIMIT 1").df()
    for col in ("customer_name", "customer_id", "customer_reference_id", "notes", "details"):
        assert col not in line_items.columns
        assert col not in transactions.columns


# --- Independent cross-checks (raw CSV / plain pandas) and date-filter coverage ---

SUB_START, SUB_END = dt.date(2025, 4, 10), dt.date(2025, 8, 20)  # mid-year window inside the data


def _in_range(df, start, end):
    return df[(df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))]


@pytest.mark.parametrize("use_sub_range", [False, True])
def test_kpis_match_independent_raw_csv_calculation(loaded_conn, small_clean_path, use_sub_range):
    min_date, max_date = analytics.get_date_bounds(loaded_conn)
    start, end = (SUB_START, SUB_END) if use_sub_range else (min_date, max_date)

    expected = independent_kpis(small_clean_path, start, end)
    kpis = analytics.compute_kpis(loaded_conn, start, end)

    assert kpis.net_sales == pytest.approx(expected["Net Sales"], abs=0.005)
    assert kpis.transactions == expected["Transactions"]
    assert kpis.avg_basket == pytest.approx(expected["Average Basket"], abs=0.005)
    assert kpis.units == expected["Units"]
    assert kpis.distinct_items == expected["Distinct Items Sold"]


def test_date_range_is_inclusive_and_narrows_kpis(loaded_conn, small_clean_path):
    df = ingest_csv(small_clean_path)
    min_date, max_date = analytics.get_date_bounds(loaded_conn)
    full = analytics.compute_kpis(loaded_conn, min_date, max_date)
    sub = analytics.compute_kpis(loaded_conn, SUB_START, SUB_END)

    assert 0 < sub.transactions < full.transactions
    assert 0 < sub.net_sales < full.net_sales
    assert sub.units < full.units

    # a single-day range includes that whole day (both endpoints inclusive)
    one_day = df[df["date"] == pd.Timestamp(SUB_START)]
    day_kpis = analytics.compute_kpis(loaded_conn, SUB_START, SUB_START)
    assert day_kpis.transactions == one_day["transaction_id"].nunique()
    assert day_kpis.net_sales == pytest.approx(one_day["net_sales"].sum())


def test_category_mix_matches_groupby_and_respects_date_range(loaded_conn, small_clean_path):
    df = _in_range(ingest_csv(small_clean_path), SUB_START, SUB_END)
    mix = analytics.category_mix(loaded_conn, SUB_START, SUB_END)

    expected = df.groupby("category")["net_sales"].sum().sort_values(ascending=False, kind="stable")
    assert dict(zip(mix["category"], mix["net_sales"])) == pytest.approx(expected.to_dict())
    assert mix["pct_of_total"].sum() == pytest.approx(100.0)
    assert mix["pct_of_total"].iloc[0] == pytest.approx(expected.iloc[0] / expected.sum() * 100)


def test_top_20_tables_match_groupby_and_respect_date_range(loaded_conn, small_clean_path):
    df = _in_range(ingest_csv(small_clean_path), SUB_START, SUB_END)

    by_units = analytics.top_n_items_by_units(loaded_conn, SUB_START, SUB_END, n=20)
    expected_units = df.groupby("item")["qty"].sum().sort_values(ascending=False).head(20)
    assert len(by_units) == 20
    assert list(by_units["units"]) == list(expected_units)  # ties make item names ambiguous, values are exact

    by_sales = analytics.top_n_items_by_sales(loaded_conn, SUB_START, SUB_END, n=20)
    expected_sales = df.groupby("item")["net_sales"].sum().sort_values(ascending=False).head(20)
    assert len(by_sales) == 20
    assert list(by_sales["net_sales"]) == pytest.approx(list(expected_sales))


def test_monthly_trend_is_chronological_and_respects_date_range(loaded_conn, small_clean_path):
    df = ingest_csv(small_clean_path)
    min_date, max_date = analytics.get_date_bounds(loaded_conn)

    full = analytics.month_over_month_trend(loaded_conn, min_date, max_date)
    assert [m.month for m in full["month"]] == list(range(1, 13))  # calendar order, not alphabetical
    expected_mom = full["net_sales"].pct_change() * 100
    assert full["mom_pct_change"].iloc[1:].tolist() == pytest.approx(expected_mom.iloc[1:].tolist())

    sub = analytics.month_over_month_trend(loaded_conn, SUB_START, SUB_END)
    assert [m.month for m in sub["month"]] == [4, 5, 6, 7, 8]
    sub_df = _in_range(df, SUB_START, SUB_END)
    assert sub["net_sales"].sum() == pytest.approx(sub_df["net_sales"].sum())


def test_heatmap_is_monday_to_sunday_by_hour_and_respects_date_range(loaded_conn, small_clean_path):
    df = ingest_csv(small_clean_path)
    heatmap = analytics.hour_weekday_transaction_counts(loaded_conn, SUB_START, SUB_END)

    assert list(heatmap["weekday"].drop_duplicates()) == [
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    ]
    assert list(heatmap["hour"].iloc[:24]) == list(range(24))
    sub_df = _in_range(df, SUB_START, SUB_END)
    assert heatmap["transactions"].sum() == sub_df["transaction_id"].nunique()

    fig = charts.hour_weekday_heatmap(heatmap)
    assert list(fig.data[0].y) == analytics.WEEKDAY_ORDER
    assert list(fig.data[0].x) == list(range(24))


def test_kpi_check_workbook_all_pass(small_clean_path, tmp_path):
    rows = kpi_compare(small_clean_path)
    out = tmp_path / "kpi_check.xlsx"
    write_workbook(rows, small_clean_path, out)

    sheet = pd.read_excel(out, sheet_name="KPI Check")
    for column in ("KPI", "Independent Value", "Application/Query Value", "Difference", "Status"):
        assert column in sheet.columns
    assert set(sheet["KPI"]) == {"Net Sales", "Transactions", "Average Basket", "Units", "Distinct Items Sold"}
    assert (sheet["Status"] == "PASS").all()
