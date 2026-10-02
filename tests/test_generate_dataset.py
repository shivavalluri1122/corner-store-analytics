from datetime import date

from data.synthetic.generate_dataset import (
    NUM_DAYS,
    build_stockout_windows,
    day_multiplier,
    generate_line_items,
    is_out_of_stock,
    make_malformed,
    sample_by_transaction,
)
from data.synthetic.sku_catalog import CATEGORY_ITEMS, build_sku_catalog


def test_catalog_has_expected_size():
    catalog = build_sku_catalog()
    assert len(catalog) == 150
    assert catalog["category"].nunique() == len(CATEGORY_ITEMS) == 10
    assert catalog["sku"].is_unique


def test_catalog_prices_are_positive():
    catalog = build_sku_catalog()
    assert (catalog["unit_price"] > 0).all()


def test_weekend_multiplier_higher_than_midweek():
    saturday = date(2025, 2, 8)  # not a spike day
    tuesday = date(2025, 2, 4)
    assert day_multiplier(saturday) > day_multiplier(tuesday)


def test_first_of_month_spike():
    first_of_month = date(2025, 3, 1)
    mid_regular_day = date(2025, 3, 10)
    assert day_multiplier(first_of_month) > day_multiplier(mid_regular_day)


def test_mid_month_spike():
    mid_month = date(2025, 3, 16)
    regular_day = date(2025, 3, 10)
    assert day_multiplier(mid_month) > day_multiplier(regular_day)


def test_stockout_windows_cover_five_skus():
    catalog = build_sku_catalog()
    import random

    rng = random.Random(1)
    windows = build_stockout_windows(catalog, rng)
    assert len(windows) == 5
    for start, end in windows.values():
        assert 0 <= start < end < NUM_DAYS


def test_is_out_of_stock_respects_window():
    windows = {"BEV-001": (10, 20)}
    assert is_out_of_stock("BEV-001", 15, windows)
    assert not is_out_of_stock("BEV-001", 5, windows)
    assert not is_out_of_stock("SNK-001", 15, windows)


def test_generate_line_items_has_expected_columns():
    df = generate_line_items(base_transactions_per_day=2, seed=1)
    expected = {"Date", "SKU", "Qty", "Gross Sales", "Transaction ID", "Customer Name"}
    assert expected.issubset(set(df.columns))
    assert len(df) > 0


def test_stockout_sku_has_no_sales_during_its_window():
    seed = 42
    df = generate_line_items(base_transactions_per_day=60, seed=seed)
    catalog = build_sku_catalog()
    import random

    # replicate generate_line_items' RNG consumption order: weights are
    # built before stockout windows, so we must do the same here.
    from data.synthetic.generate_dataset import build_sku_weights

    rng = random.Random(seed)
    build_sku_weights(catalog, rng)
    windows = build_stockout_windows(catalog, rng)
    sku, (start, end) = next(iter(windows.items()))
    dates = df.loc[df["SKU"] == sku, "Date"]

    from datetime import timedelta

    from data.synthetic.generate_dataset import START_DATE

    window_dates = {
        (START_DATE + timedelta(days=d)).strftime("%m/%d/%Y") for d in range(start, end + 1)
    }
    assert not set(dates).intersection(window_dates)


def test_sample_by_transaction_keeps_whole_baskets():
    df = generate_line_items(base_transactions_per_day=20, seed=7)
    sample = sample_by_transaction(df, fraction=0.5, seed=1)
    # every kept transaction id present in sample should have all its line items
    original_counts = df.groupby("Transaction ID").size()
    sample_counts = sample.groupby("Transaction ID").size()
    for txn_id, count in sample_counts.items():
        assert count == original_counts[txn_id]


def test_make_malformed_drops_required_columns_and_breaks_values():
    import pandas as pd

    df = generate_line_items(base_transactions_per_day=20, seed=7)
    malformed = make_malformed(df, seed=3)
    assert "SKU" not in malformed.columns
    assert "Net Sales" not in malformed.columns

    parsed_dates = pd.to_datetime(malformed["Date"], format="%m/%d/%Y", errors="coerce")
    assert parsed_dates.isna().any()  # at least one invalid date

    bad_qty = pd.to_numeric(malformed["Qty"], errors="coerce")
    assert bad_qty.isna().any()  # at least one invalid Qty

    bad_gross = malformed["Gross Sales"].str.match(r"^-?\$\d+\.\d{2}$")
    assert (~bad_gross).any()  # at least one invalid Gross Sales
