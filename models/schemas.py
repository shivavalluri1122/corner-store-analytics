"""Pandera schema: the single data contract used to validate ingested sales
data (after header normalization, date/currency parsing, and PII removal,
per the Week 2 pipeline order). Values that failed lenient parsing show up
here as nulls, so this schema is what turns "silently wrong" into a clear,
user-facing pass/fail report.
"""

from pandera.pandas import Check, Column, DataFrameSchema

# Validates the cleaned line-item DataFrame produced by pipeline.ingest.
CLEAN_LINE_ITEM_SCHEMA = DataFrameSchema(
    {
        "transaction_id": Column(str, nullable=False),
        "transaction_ts": Column("datetime64[ns]", nullable=False),
        "date": Column("datetime64[ns]", nullable=False),
        "category": Column(str, nullable=False),
        "item": Column(str, nullable=False),
        "sku": Column(str, nullable=False),
        "qty": Column(float, Check.greater_than(0), nullable=False, coerce=True),
        "gross_sales": Column(float, Check.greater_than_or_equal_to(0), nullable=False, coerce=True),
        "net_sales": Column(float, Check.greater_than_or_equal_to(0), nullable=False, coerce=True),
        "tax": Column(float, Check.greater_than_or_equal_to(0), nullable=False, coerce=True),
    },
    strict=False,  # extra columns (device_name, location, ...) are allowed
    coerce=False,
)
