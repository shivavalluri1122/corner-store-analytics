from pipeline.db import build_and_load, get_connection, query_table
from pipeline.ingest import ingest_csv


def test_build_and_load_creates_all_tables(small_clean_path):
    df = ingest_csv(small_clean_path)
    conn = get_connection()
    tables = build_and_load(conn, df)

    for name in ("transactions", "line_items", "daily_item_sales"):
        stored = query_table(conn, name)
        assert len(stored) == len(tables[name])


def test_duckdb_round_trip_preserves_row_count(small_clean_path):
    df = ingest_csv(small_clean_path)
    conn = get_connection()
    tables = build_and_load(conn, df)

    stored_line_items = query_table(conn, "line_items")
    assert len(stored_line_items) == len(df)


def test_duckdb_can_run_sql_aggregation(small_clean_path):
    df = ingest_csv(small_clean_path)
    conn = get_connection()
    build_and_load(conn, df)

    result = conn.execute(
        "SELECT category, SUM(units_sold) AS units FROM daily_item_sales GROUP BY category"
    ).df()
    assert len(result) > 0
    assert "units" in result.columns
