import pandas as pd

from pipeline.ingest import (
    convert_currency,
    ingest_csv,
    normalize_headers,
    parse_datetime,
    remove_pii,
)


def test_normalize_headers_converts_to_snake_case():
    df = pd.DataFrame(columns=["Transaction ID", "Gross Sales", "SKU", "Time Zone"])
    result = normalize_headers(df)
    assert list(result.columns) == ["transaction_id", "gross_sales", "sku", "time_zone"]


def test_parse_datetime_combines_date_and_time():
    df = pd.DataFrame({"date": ["01/15/2025"], "time": ["02:30:00 PM"]})
    result = parse_datetime(df)
    assert result["transaction_ts"].iloc[0] == pd.Timestamp("2025-01-15 14:30:00")
    assert result["date"].iloc[0] == pd.Timestamp("2025-01-15")


def test_parse_datetime_invalid_date_becomes_nat():
    df = pd.DataFrame({"date": ["Not a date"], "time": ["02:30:00 PM"]})
    result = parse_datetime(df)
    assert pd.isna(result["transaction_ts"].iloc[0])


def test_convert_currency_parses_valid_values():
    df = pd.DataFrame({"gross_sales": ["$12.34"], "discounts": ["-$1.23"], "qty": ["3"]})
    result = convert_currency(df)
    assert result["gross_sales"].iloc[0] == 12.34
    assert result["discounts"].iloc[0] == -1.23
    assert result["qty"].iloc[0] == 3


def test_convert_currency_invalid_values_become_null():
    df = pd.DataFrame({"gross_sales": ["twelve dollars", "$$12.00", "N/A"], "qty": ["three", "N/A", ""]})
    result = convert_currency(df)
    assert result["gross_sales"].isna().all()
    assert result["qty"].isna().all()


def test_remove_pii_drops_customer_columns():
    df = pd.DataFrame({"customer_name": ["Jane"], "customer_id": ["1"], "sku": ["BEV-001"]})
    result = remove_pii(df)
    assert "customer_name" not in result.columns
    assert "customer_id" not in result.columns
    assert "sku" in result.columns


def test_ingest_csv_end_to_end_removes_pii_and_parses_types(small_clean_path):
    df = ingest_csv(small_clean_path)
    assert "customer_name" not in df.columns
    assert "customer_id" not in df.columns
    assert "customer_reference_id" not in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df["transaction_ts"])
    assert df["gross_sales"].dtype.kind == "f"


def test_ingest_csv_removes_all_pii_and_free_text_but_keeps_analytics_fields(small_clean_path):
    raw_before = small_clean_path.read_bytes()
    raw_columns = pd.read_csv(small_clean_path, nrows=0).columns
    for col in ("Customer Name", "Customer ID", "Customer Reference ID", "Notes", "Details"):
        assert col in raw_columns  # the raw synthetic CSV carries these columns

    df = ingest_csv(small_clean_path)

    for col in ("customer_name", "customer_id", "customer_reference_id", "notes", "details"):
        assert col not in df.columns
    for col in ("transaction_id", "transaction_ts", "date", "category", "item", "sku", "qty", "net_sales"):
        assert col in df.columns
    assert small_clean_path.read_bytes() == raw_before  # raw file is never modified
