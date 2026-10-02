"""DuckDB storage layer: load the transformed tables (transactions,
line_items, daily_item_sales) into a DuckDB connection.
"""

import duckdb
import pandas as pd

from pipeline.transform import transform

TABLE_NAMES = ("transactions", "line_items", "daily_item_sales")


def get_connection(db_path: str = ":memory:") -> duckdb.DuckDBPyConnection:
    return duckdb.connect(db_path)


def load_tables(conn: duckdb.DuckDBPyConnection, tables: dict[str, pd.DataFrame]) -> None:
    """Write each DataFrame to a DuckDB table of the same name."""
    for name, df in tables.items():
        conn.register(f"_{name}_incoming", df)
        conn.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM _{name}_incoming")
        conn.unregister(f"_{name}_incoming")


def build_and_load(conn: duckdb.DuckDBPyConnection, cleaned_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Transform a cleaned line-item DataFrame and load the result into DuckDB."""
    tables = transform(cleaned_df)
    load_tables(conn, tables)
    return tables


def query_table(conn: duckdb.DuckDBPyConnection, table_name: str) -> pd.DataFrame:
    return conn.execute(f"SELECT * FROM {table_name}").df()
