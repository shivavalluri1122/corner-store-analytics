"""CSV ingestion: read a Square-like item sales CSV and produce a cleaned
DataFrame. Order matches the Week 2 spec: normalize headers, remove PII/
free-text columns, parse date/time, convert currency columns. Bad values
are coerced to null rather than raising, so pipeline.validate can report
them clearly instead of the pipeline crashing on a messy upload.
"""

import re

import numpy as np
import pandas as pd

# PII (customer_*) and free-text (notes/details) columns: dropped immediately
# after header normalization, before validation, transform, or DuckDB loading.
COLUMNS_TO_DROP = ["customer_name", "customer_id", "customer_reference_id", "notes", "details"]
CURRENCY_COLUMNS = ["gross_sales", "discounts", "net_sales", "tax"]
CURRENCY_PATTERN = re.compile(r"^(-?)\$(\d+(?:\.\d{1,2})?)$")


def _to_snake_case(column: str) -> str:
    column = column.strip().lower()
    column = re.sub(r"[^0-9a-z]+", "_", column)
    return column.strip("_")


def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns to snake_case regardless of the exporter's casing/spacing."""
    df = df.copy()
    df.columns = [_to_snake_case(c) for c in df.columns]
    return df


def parse_datetime(df: pd.DataFrame) -> pd.DataFrame:
    """Combine date + time into transaction_ts; unparseable values become NaT."""
    df = df.copy()
    if "date" in df.columns and "time" in df.columns:
        combined = df["date"].astype(str).str.strip() + " " + df["time"].astype(str).str.strip()
        df["transaction_ts"] = pd.to_datetime(
            combined, format="%m/%d/%Y %I:%M:%S %p", errors="coerce"
        )
    elif "date" in df.columns:
        df["transaction_ts"] = pd.to_datetime(df["date"], format="%m/%d/%Y", errors="coerce")

    if "transaction_ts" in df.columns:
        df["date"] = df["transaction_ts"].dt.normalize()
    return df


def _parse_currency_value(value: object) -> float:
    if pd.isna(value):
        return np.nan
    match = CURRENCY_PATTERN.match(str(value).strip())
    if not match:
        return np.nan
    sign, amount = match.groups()
    parsed = float(amount)
    return -parsed if sign == "-" else parsed


def convert_currency(df: pd.DataFrame) -> pd.DataFrame:
    """Convert `$12.34` / `-$1.23` style strings to floats; anything that
    doesn't match a currency shape becomes null. Also coerces Qty to numeric."""
    df = df.copy()
    for col in CURRENCY_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(_parse_currency_value)
    if "qty" in df.columns:
        df["qty"] = pd.to_numeric(df["qty"], errors="coerce")
    return df


def remove_pii(df: pd.DataFrame) -> pd.DataFrame:
    """Drop customer name/id/reference and free-text notes/details columns entirely."""
    return df.drop(columns=[c for c in COLUMNS_TO_DROP if c in df.columns], errors="ignore")


def read_csv(path_or_buffer) -> pd.DataFrame:
    """Read the raw CSV with every column as a string, no surprise dtype
    inference, so downstream parsing controls every conversion explicitly."""
    return pd.read_csv(path_or_buffer, dtype=str, keep_default_na=False, na_values=[""])


def ingest_csv(path_or_buffer) -> pd.DataFrame:
    """Full ingestion: read -> normalize headers -> remove PII/free-text ->
    parse date/time -> convert currency."""
    df = read_csv(path_or_buffer)
    df = normalize_headers(df)
    df = remove_pii(df)
    df = parse_datetime(df)
    df = convert_currency(df)
    return df
