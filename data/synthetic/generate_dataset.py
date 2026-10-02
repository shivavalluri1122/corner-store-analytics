"""Synthetic Square-like item sales CSV generator for Corner Store Analytics.

Produces three CSVs modeled on a Square "Item Sales" export (see
docs/square_schema.md for column definitions):

- small_clean.csv   ~2,000 rows, 12 months, fully valid
- large_clean.csv   ~50,000 rows, 12 months, fully valid
- malformed.csv     small sample with missing columns, bad numerics, bad date

Patterns baked into the clean datasets:
- weekly seasonality: Fri/Sat/Sun higher demand than midweek
- first-of-month spike (days 1-3), mid-month spike (days 15-17)
- summer lift (Jun-Aug) for the Beverages category
- 5 SKUs with visible multi-day stockout gaps (zero sales windows)
"""

import random
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

from data.synthetic.sku_catalog import build_sku_catalog

OUTPUT_DIR = Path(__file__).parent

START_DATE = date(2025, 1, 1)
NUM_DAYS = 365
TAX_RATE = 0.07
LOCATION = "Corner Store #1"
TIME_ZONE = "America/Chicago"
DEVICES = ["Register 1", "Register 2", "Mobile POS"]

# Monday=0 ... Sunday=6
DOW_MULTIPLIER = {0: 1.0, 1: 0.95, 2: 0.95, 3: 1.0, 4: 1.25, 5: 1.45, 6: 1.2}
FIRST_OF_MONTH_DAYS = {1, 2, 3}
FIRST_OF_MONTH_LIFT = 1.4
MID_MONTH_DAYS = {15, 16, 17}
MID_MONTH_LIFT = 1.25
SUMMER_MONTHS = {6, 7, 8}
SUMMER_BEVERAGE_LIFT = 1.6

NUM_STOCKOUT_SKUS = 5
STOCKOUT_MIN_DAYS = 7
STOCKOUT_MAX_DAYS = 21

ITEMS_PER_TXN = [1, 2, 3, 4, 5]
ITEMS_PER_TXN_WEIGHTS = [0.45, 0.28, 0.15, 0.08, 0.04]
QTY_CHOICES = [1, 2, 3]
QTY_WEIGHTS = [0.75, 0.18, 0.07]
DISCOUNT_RATE_CHANCE = 0.06
DISCOUNT_RATE = 0.10
LOYALTY_CUSTOMER_CHANCE = 0.30

RAW_COLUMNS = [
    "Date", "Time", "Time Zone", "Category", "Item", "SKU", "Qty",
    "Price Point Name", "Gross Sales", "Discounts", "Net Sales", "Tax",
    "Transaction ID", "Payment ID", "Device Name", "Notes", "Details",
    "Event Type", "Location", "Dining Option", "Customer Name",
    "Customer ID", "Customer Reference ID",
]


def day_multiplier(d: date) -> float:
    """Weekly seasonality plus first-of-month / mid-month spikes."""
    m = DOW_MULTIPLIER[d.weekday()]
    if d.day in FIRST_OF_MONTH_DAYS:
        m *= FIRST_OF_MONTH_LIFT
    elif d.day in MID_MONTH_DAYS:
        m *= MID_MONTH_LIFT
    return m


def hour_weights() -> tuple[list[int], list[float]]:
    """Store open 7am-9:59pm, busier at lunch and early evening."""
    hours = list(range(7, 22))
    weights = []
    for h in hours:
        if 16 <= h <= 19:
            w = 3.5
        elif 11 <= h <= 13:
            w = 3.0
        elif 7 <= h <= 9:
            w = 1.8
        else:
            w = 1.0
        weights.append(w)
    return hours, weights


def build_stockout_windows(catalog: pd.DataFrame, rng: random.Random) -> dict[str, tuple[int, int]]:
    """Pick 5 SKUs and assign each a contiguous zero-sales day-index window."""
    stockout_skus = rng.sample(list(catalog["sku"]), NUM_STOCKOUT_SKUS)
    windows = {}
    for sku in stockout_skus:
        length = rng.randint(STOCKOUT_MIN_DAYS, STOCKOUT_MAX_DAYS)
        start_day = rng.randint(20, NUM_DAYS - length - 20)
        windows[sku] = (start_day, start_day + length)
    return windows


def is_out_of_stock(sku: str, day_index: int, windows: dict[str, tuple[int, int]]) -> bool:
    window = windows.get(sku)
    return window is not None and window[0] <= day_index <= window[1]


def build_sku_weights(catalog: pd.DataFrame, rng: random.Random) -> dict[str, float]:
    """Deterministic per-SKU popularity weight (log-normal) so some items sell more."""
    return {sku: rng.lognormvariate(0, 0.6) for sku in catalog["sku"]}


def generate_line_items(base_transactions_per_day: float, seed: int) -> pd.DataFrame:
    """Generate raw Square-like line item rows for the full 12-month window."""
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    faker = Faker()
    Faker.seed(seed)

    catalog = build_sku_catalog()
    sku_weights = build_sku_weights(catalog, rng)
    stockout_windows = build_stockout_windows(catalog, rng)
    hours, h_weights = hour_weights()

    catalog_by_sku = catalog.set_index("sku").to_dict(orient="index")

    rows: list[dict] = []
    txn_counter = 0

    for day_index in range(NUM_DAYS):
        current_date = START_DATE + timedelta(days=day_index)
        expected_txns = base_transactions_per_day * day_multiplier(current_date)
        num_txns = np_rng.poisson(max(expected_txns, 0.1))

        # available SKUs for this day (excluding anything mid-stockout window)
        available_skus = [
            sku for sku in catalog["sku"] if not is_out_of_stock(sku, day_index, stockout_windows)
        ]
        weights = []
        for sku in available_skus:
            w = sku_weights[sku]
            if current_date.month in SUMMER_MONTHS and catalog_by_sku[sku]["category"] == "Beverages":
                w *= SUMMER_BEVERAGE_LIFT
            weights.append(w)

        for _ in range(num_txns):
            txn_counter += 1
            transaction_id = f"SQ{current_date.strftime('%Y%m%d')}{txn_counter:06d}"
            payment_id = f"PMT{current_date.strftime('%Y%m%d')}{txn_counter:06d}"

            hour = rng.choices(hours, weights=h_weights, k=1)[0]
            minute = rng.randint(0, 59)
            second = rng.randint(0, 59)
            txn_time = datetime(
                current_date.year, current_date.month, current_date.day, hour, minute, second
            )

            has_loyalty_customer = rng.random() < LOYALTY_CUSTOMER_CHANCE
            if has_loyalty_customer:
                customer_name = faker.name()
                customer_id = f"CUST{rng.randint(100000, 999999)}"
                customer_ref = faker.uuid4()
            else:
                customer_name = ""
                customer_id = ""
                customer_ref = ""

            num_items = rng.choices(ITEMS_PER_TXN, weights=ITEMS_PER_TXN_WEIGHTS, k=1)[0]
            num_items = min(num_items, len(available_skus))
            chosen_skus = rng.choices(available_skus, weights=weights, k=num_items) if available_skus else []

            for sku in chosen_skus:
                info = catalog_by_sku[sku]
                qty = rng.choices(QTY_CHOICES, weights=QTY_WEIGHTS, k=1)[0]
                unit_price = info["unit_price"]
                gross = round(unit_price * qty, 2)
                discount = round(gross * DISCOUNT_RATE, 2) if rng.random() < DISCOUNT_RATE_CHANCE else 0.0
                net = round(gross - discount, 2)
                tax = round(net * TAX_RATE, 2)

                rows.append(
                    {
                        "Date": current_date.strftime("%m/%d/%Y"),
                        "Time": txn_time.strftime("%I:%M:%S %p"),
                        "Time Zone": TIME_ZONE,
                        "Category": info["category"],
                        "Item": info["item"],
                        "SKU": sku,
                        "Qty": qty,
                        "Price Point Name": "Regular",
                        "Gross Sales": f"${gross:.2f}",
                        "Discounts": f"-${discount:.2f}" if discount else "$0.00",
                        "Net Sales": f"${net:.2f}",
                        "Tax": f"${tax:.2f}",
                        "Transaction ID": transaction_id,
                        "Payment ID": payment_id,
                        "Device Name": rng.choice(DEVICES),
                        "Notes": "",
                        "Details": "",
                        "Event Type": "Payment",
                        "Location": LOCATION,
                        "Dining Option": "",
                        "Customer Name": customer_name,
                        "Customer ID": customer_id,
                        "Customer Reference ID": customer_ref,
                    }
                )

    return pd.DataFrame(rows, columns=RAW_COLUMNS)


def sample_by_transaction(df: pd.DataFrame, fraction: float, seed: int) -> pd.DataFrame:
    """Sample whole transactions (not individual line items) stratified by date,
    so daily seasonality patterns stay visible in the smaller dataset."""
    rng = np.random.default_rng(seed)
    keep_txn_ids: list[str] = []
    for _, group in df.groupby("Date"):
        txn_ids = group["Transaction ID"].unique()
        n_keep = max(1, int(round(len(txn_ids) * fraction)))
        chosen = rng.choice(txn_ids, size=min(n_keep, len(txn_ids)), replace=False)
        keep_txn_ids.extend(chosen.tolist())
    sampled = df[df["Transaction ID"].isin(keep_txn_ids)].reset_index(drop=True)
    return sampled


def make_malformed(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Take a small slice of clean data and corrupt it: missing required columns,
    invalid numeric data, and an invalid date."""
    rng = random.Random(seed)
    sample = df.head(200).copy().reset_index(drop=True)

    # missing required columns: drop SKU and Net Sales entirely
    sample = sample.drop(columns=["SKU", "Net Sales"])
    sample["Qty"] = sample["Qty"].astype(object)

    # invalid numeric data: corrupt Qty and Gross Sales in a few rows
    bad_qty_idx = rng.sample(range(len(sample)), 5)
    for i, idx in enumerate(bad_qty_idx):
        sample.loc[idx, "Qty"] = rng.choice(["three", "N/A", "-", "two dozen", ""])

    bad_gross_idx = rng.sample(range(len(sample)), 5)
    for idx in bad_gross_idx:
        sample.loc[idx, "Gross Sales"] = rng.choice(["N/A", "twelve dollars", "--", "$$12.00"])

    # invalid date: one row with an unparseable date
    bad_date_idx = rng.choice(range(len(sample)))
    sample.loc[bad_date_idx, "Date"] = rng.choice(["13/45/2025", "Not a date", "02/30/2025"])

    return sample


def main() -> None:
    seed = 42

    large = generate_line_items(base_transactions_per_day=60, seed=seed)
    large_path = OUTPUT_DIR / "large_clean.csv"
    large.to_csv(large_path, index=False)
    print(f"large_clean.csv: {len(large):,} rows -> {large_path}")

    target_small_fraction = 2000 / len(large)
    small = sample_by_transaction(large, fraction=target_small_fraction, seed=seed + 1)
    small_path = OUTPUT_DIR / "small_clean.csv"
    small.to_csv(small_path, index=False)
    print(f"small_clean.csv: {len(small):,} rows -> {small_path}")

    malformed = make_malformed(small, seed=seed + 2)
    malformed_path = OUTPUT_DIR / "malformed.csv"
    malformed.to_csv(malformed_path, index=False)
    print(f"malformed.csv: {len(malformed):,} rows -> {malformed_path}")


if __name__ == "__main__":
    main()
