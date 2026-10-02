from pipeline.ingest import ingest_csv
from pipeline.transform import transform


def test_transform_produces_three_tables(small_clean_path):
    df = ingest_csv(small_clean_path)
    tables = transform(df)
    assert set(tables) == {"transactions", "line_items", "daily_item_sales"}
    assert len(tables["line_items"]) == len(df)


def test_transactions_totals_match_line_item_sums(small_clean_path):
    df = ingest_csv(small_clean_path)
    tables = transform(df)
    line_items = tables["line_items"]
    transactions = tables["transactions"]

    expected_gross = line_items.groupby("transaction_id")["gross_sales"].sum()
    actual_gross = transactions.set_index("transaction_id")["total_gross_sales"]
    assert (expected_gross.round(2) == actual_gross.round(2)).all()


def test_daily_item_sales_units_match_line_items(small_clean_path):
    df = ingest_csv(small_clean_path)
    tables = transform(df)
    line_items = tables["line_items"]
    daily = tables["daily_item_sales"]

    expected_units = line_items.groupby(["date", "sku"])["qty"].sum().sum()
    assert daily["units_sold"].sum() == expected_units


def test_no_transaction_has_more_line_items_than_its_daily_total(small_clean_path):
    df = ingest_csv(small_clean_path)
    tables = transform(df)
    assert (tables["transactions"]["num_line_items"] > 0).all()
