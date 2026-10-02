"""Dashboard analytics: reusable DuckDB-backed calculations for the Sales
Overview page. All aggregation logic lives here (not in Streamlit) so every
KPI/chart is computed exactly once, from the same tables, with the same
date-range filter applied consistently.

Reads from the `line_items` and `transactions` DuckDB tables produced by
pipeline.transform - neither table carries PII (see docs/data_dictionary.md).
"""

import datetime as dt
from dataclasses import dataclass

import duckdb
import pandas as pd

WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

DateLike = dt.date | pd.Timestamp


@dataclass
class KPIResult:
    net_sales: float
    transactions: int
    avg_basket: float
    units: int
    distinct_items: int


def _date_range_params(start_date: DateLike, end_date: DateLike) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Inclusive [start_date, end_date] -> [start_ts, end_ts_exclusive) for SQL."""
    start_ts = pd.Timestamp(start_date).normalize()
    end_ts_exclusive = pd.Timestamp(end_date).normalize() + pd.Timedelta(days=1)
    return start_ts, end_ts_exclusive


def get_date_bounds(conn: duckdb.DuckDBPyConnection) -> tuple[dt.date, dt.date]:
    """Min/max available date in line_items, used to default the date-range filter."""
    result = conn.execute("SELECT MIN(date) AS min_date, MAX(date) AS max_date FROM line_items").df()
    min_date = result.loc[0, "min_date"]
    max_date = result.loc[0, "max_date"]
    if pd.isna(min_date) or pd.isna(max_date):
        today = dt.date.today()
        return today, today
    return pd.Timestamp(min_date).date(), pd.Timestamp(max_date).date()


def compute_kpis(conn: duckdb.DuckDBPyConnection, start_date: DateLike, end_date: DateLike) -> KPIResult:
    """The five headline KPIs: Net Sales, Transactions, Average Basket, Units,
    Distinct Items Sold. Average Basket is Net Sales / Transactions, 0 if no
    transactions in range."""
    start_ts, end_ts_exclusive = _date_range_params(start_date, end_date)
    row = conn.execute(
        """
        WITH agg AS (
            SELECT
                COALESCE(SUM(net_sales), 0) AS net_sales,
                COUNT(DISTINCT transaction_id) AS transactions,
                COALESCE(SUM(qty), 0) AS units,
                COUNT(DISTINCT item) AS distinct_items
            FROM line_items
            WHERE date >= ? AND date < ?
        )
        SELECT
            net_sales,
            transactions,
            CASE WHEN transactions = 0 THEN 0 ELSE net_sales / transactions END AS avg_basket,
            units,
            distinct_items
        FROM agg
        """,
        [start_ts, end_ts_exclusive],
    ).df().iloc[0]
    return KPIResult(
        net_sales=float(row["net_sales"]),
        transactions=int(row["transactions"]),
        avg_basket=float(row["avg_basket"]),
        units=int(row["units"]),
        distinct_items=int(row["distinct_items"]),
    )


def category_mix(conn: duckdb.DuckDBPyConnection, start_date: DateLike, end_date: DateLike) -> pd.DataFrame:
    """Net sales and % of total net sales per category, sorted descending."""
    start_ts, end_ts_exclusive = _date_range_params(start_date, end_date)
    return conn.execute(
        """
        SELECT
            category,
            SUM(net_sales) AS net_sales,
            SUM(net_sales) * 100.0 / NULLIF(SUM(SUM(net_sales)) OVER (), 0) AS pct_of_total
        FROM line_items
        WHERE date >= ? AND date < ?
        GROUP BY category
        ORDER BY net_sales DESC, category
        """,
        [start_ts, end_ts_exclusive],
    ).df()


def hour_weekday_transaction_counts(
    conn: duckdb.DuckDBPyConnection, start_date: DateLike, end_date: DateLike
) -> pd.DataFrame:
    """Transaction count for every (weekday, hour) combination - a full,
    zero-filled 7x24 grid (Monday-Sunday, hours 0-23), regardless of gaps
    in the underlying data."""
    start_ts, end_ts_exclusive = _date_range_params(start_date, end_date)
    return conn.execute(
        """
        WITH hours AS (
            SELECT UNNEST(generate_series(0, 23)) AS hour
        ),
        weekdays AS (
            SELECT * FROM (VALUES
                (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'),
                (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')
            ) AS wd(idx, weekday)
        ),
        grid AS (
            SELECT weekdays.idx, weekdays.weekday, hours.hour
            FROM weekdays CROSS JOIN hours
        ),
        counts AS (
            SELECT weekday, hour, COUNT(*) AS transactions
            FROM transactions
            WHERE date >= ? AND date < ?
            GROUP BY weekday, hour
        )
        SELECT grid.weekday, grid.hour, COALESCE(counts.transactions, 0) AS transactions
        FROM grid
        LEFT JOIN counts ON grid.weekday = counts.weekday AND grid.hour = counts.hour
        ORDER BY grid.idx, grid.hour
        """,
        [start_ts, end_ts_exclusive],
    ).df()


def month_over_month_trend(
    conn: duckdb.DuckDBPyConnection, start_date: DateLike, end_date: DateLike
) -> pd.DataFrame:
    """Net sales by calendar month, chronologically sorted, with
    month-over-month % change (null for the first month or when the prior
    month had $0 in net sales)."""
    start_ts, end_ts_exclusive = _date_range_params(start_date, end_date)
    return conn.execute(
        """
        WITH monthly AS (
            SELECT date_trunc('month', date) AS month, SUM(net_sales) AS net_sales
            FROM line_items
            WHERE date >= ? AND date < ?
            GROUP BY 1
        )
        SELECT
            month,
            net_sales,
            CASE
                WHEN LAG(net_sales) OVER (ORDER BY month) IS NULL THEN NULL
                WHEN LAG(net_sales) OVER (ORDER BY month) = 0 THEN NULL
                ELSE (net_sales - LAG(net_sales) OVER (ORDER BY month)) * 100.0
                     / LAG(net_sales) OVER (ORDER BY month)
            END AS mom_pct_change
        FROM monthly
        ORDER BY month
        """,
        [start_ts, end_ts_exclusive],
    ).df()


def top_n_items_by_units(
    conn: duckdb.DuckDBPyConnection, start_date: DateLike, end_date: DateLike, n: int = 20
) -> pd.DataFrame:
    start_ts, end_ts_exclusive = _date_range_params(start_date, end_date)
    return conn.execute(
        """
        SELECT item, SUM(qty) AS units
        FROM line_items
        WHERE date >= ? AND date < ?
        GROUP BY item
        ORDER BY units DESC, item
        LIMIT ?
        """,
        [start_ts, end_ts_exclusive, n],
    ).df()


def top_n_items_by_sales(
    conn: duckdb.DuckDBPyConnection, start_date: DateLike, end_date: DateLike, n: int = 20
) -> pd.DataFrame:
    start_ts, end_ts_exclusive = _date_range_params(start_date, end_date)
    return conn.execute(
        """
        SELECT item, SUM(net_sales) AS net_sales
        FROM line_items
        WHERE date >= ? AND date < ?
        GROUP BY item
        ORDER BY net_sales DESC, item
        LIMIT ?
        """,
        [start_ts, end_ts_exclusive, n],
    ).df()
