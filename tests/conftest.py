"""Shared pytest fixtures: paths to the synthetic dataset CSVs, plus a
ready-loaded DuckDB connection for analytics tests.
"""

from pathlib import Path

import duckdb
import pytest

from pipeline.db import build_and_load, get_connection
from pipeline.ingest import ingest_csv

DATA_DIR = Path(__file__).parent.parent / "data" / "synthetic"


@pytest.fixture
def small_clean_path() -> Path:
    return DATA_DIR / "small_clean.csv"


@pytest.fixture
def large_clean_path() -> Path:
    return DATA_DIR / "large_clean.csv"


@pytest.fixture
def loaded_conn(small_clean_path: Path) -> duckdb.DuckDBPyConnection:
    """DuckDB connection pre-loaded with small_clean.csv's transactions/line_items/daily_item_sales."""
    df = ingest_csv(small_clean_path)
    conn = get_connection()
    build_and_load(conn, df)
    return conn


@pytest.fixture
def malformed_path() -> Path:
    return DATA_DIR / "malformed.csv"
