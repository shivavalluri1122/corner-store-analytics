"""Transform a cleaned, validated line-item DataFrame into the three tables
described in docs/data_dictionary.md: transactions, line_items, and
daily_item_sales.
"""

import pandas as pd


def build_line_items(df: pd.DataFrame) -> pd.DataFrame:
    """Grain = one row per original CSV line item."""
    df = df.copy()
    df["qty"] = df["qty"].astype(int)
    df["discounts"] = df["discounts"].fillna(0.0) if "discounts" in df.columns else 0.0
    df["line_item_id"] = (
        df["transaction_id"] + "-" + (df.groupby("transaction_id").cumcount() + 1).astype(str)
    )

    ordered_columns = [
        "line_item_id", "transaction_id", "date", "transaction_ts", "sku", "item",
        "category", "qty", "price_point_name", "gross_sales", "discounts", "net_sales", "tax",
    ]
    columns = [c for c in ordered_columns if c in df.columns]
    return df[columns].reset_index(drop=True)


def build_transactions(line_items: pd.DataFrame, raw: pd.DataFrame) -> pd.DataFrame:
    """Grain = one row per basket (transaction_id)."""
    transactions = line_items.groupby("transaction_id").agg(
        transaction_ts=("transaction_ts", "first"),
        date=("date", "first"),
        num_line_items=("line_item_id", "count"),
        total_qty=("qty", "sum"),
        total_gross_sales=("gross_sales", "sum"),
        total_discounts=("discounts", "sum"),
        total_net_sales=("net_sales", "sum"),
        total_tax=("tax", "sum"),
    ).reset_index()

    header_columns = [c for c in ["payment_id", "device_name", "location"] if c in raw.columns]
    if header_columns:
        headers = raw.groupby("transaction_id")[header_columns].first().reset_index()
        transactions = transactions.merge(headers, on="transaction_id", how="left")

    transactions["hour"] = transactions["transaction_ts"].dt.hour
    transactions["weekday"] = transactions["transaction_ts"].dt.day_name()
    return transactions


def build_daily_item_sales(line_items: pd.DataFrame) -> pd.DataFrame:
    """Grain = one row per (date, sku) - the rollup most dashboard charts use."""
    return line_items.groupby(["date", "sku"]).agg(
        item=("item", "first"),
        category=("category", "first"),
        units_sold=("qty", "sum"),
        gross_sales=("gross_sales", "sum"),
        discounts=("discounts", "sum"),
        net_sales=("net_sales", "sum"),
        tax=("tax", "sum"),
        transactions_count=("transaction_id", "nunique"),
    ).reset_index()


def transform(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Build all three tables from a cleaned, validated line-item DataFrame."""
    line_items = build_line_items(df)
    transactions = build_transactions(line_items, df)
    daily_item_sales = build_daily_item_sales(line_items)
    return {
        "transactions": transactions,
        "line_items": line_items,
        "daily_item_sales": daily_item_sales,
    }
