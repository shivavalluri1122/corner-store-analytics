# Design Decisions

Short log of notable decisions and the reasoning behind them, in roughly
chronological order.

## Scope: Weeks 1-3 only
Per the project plan, this build stops at a working ingestion pipeline and
dashboard. Forecasting, segmentation, the Claude assistant, auth, payments,
and deployment are deliberately excluded, even though some of their
dependencies (`prophet`, `scikit-learn`, `anthropic`) are pre-installed for
later phases — see `requirements.txt` and `docs/spec.md`.

## Synthetic data models a real Square "Item Sales" export
The generator's raw columns (`Date`, `Time`, `Gross Sales`, `Transaction
ID`, etc.) mirror what a store owner would actually download from Square,
including currency-formatted strings and separate date/time columns. This
gives the Week 2 pipeline real messiness to clean instead of already-tidy
data. See `docs/square_schema.md`.

## No alcohol/tobacco categories
The 10 categories (Beverages, Snacks, Candy, Dairy, Bakery, Frozen Foods,
Household & Cleaning, Personal Care, Grocery & Pantry, Health & OTC) avoid
age-restricted product types to keep the synthetic catalog simple and
uncontroversial for a portfolio project.

## `small_clean.csv` is sampled from `large_clean.csv`, not generated separately
Generating both datasets from scratch risked subtle inconsistencies between
"small" and "large" seasonality patterns. Instead, `large_clean.csv` is
generated directly, then `small_clean.csv` is a reproducible, date-stratified
sample of **whole transactions** (never partial baskets) pulled from it.
This guarantees every basket stays intact and both datasets show the same
underlying patterns at different scales. See `docs/data_generation.md`.

## Validation happens after lenient parsing, not on raw strings
Per the Week 2 order (normalize headers → remove PII/free text → parse
date/time → convert currency → validate), `pipeline/ingest.py` never raises on bad
input — currency/date parsing failures become `NaN`/`NaT`. `pipeline/
validate.py` then runs a single Pandera schema over the cleaned frame,
catching missing columns, failed parses (as nulls), and out-of-range values
in one pass with `lazy=True`, producing a complete, user-facing error report
instead of crashing on the first bad row.

## Currency parsing uses an exact pattern, not blanket character-stripping
An earlier draft stripped all non-numeric characters from currency strings,
which would have "fixed" malformed values like `"$$12.00"` into a valid
number and defeated the malformed-data test fixture. The final
implementation only accepts strings matching `^-?\$\d+(\.\d{1,2})?$` and
treats everything else as null.

## PII is dropped in `pipeline/ingest.py`, before validation or storage
`Customer Name`, `Customer ID`, `Customer Reference ID`, `Notes`, and
`Details` never reach Pandera, DuckDB, or the dashboard — removal happens as
its own step immediately after header normalization, before date/time
parsing, currency conversion, validation, or transformation.

## Three DuckDB tables: `transactions`, `line_items`, `daily_item_sales`
Chosen to match natural analysis grains: `transactions` for basket-level
metrics (avg basket value, hour/weekday heatmap), `line_items` for
row-level detail, and `daily_item_sales` (date × SKU rollup) for most
dashboard charts (top-20 products, category mix, trend). See
`docs/data_dictionary.md`.

## DuckDB connection is in-memory per session
The Streamlit app loads data into an in-memory DuckDB connection stored in
`st.session_state`, rather than a persisted `.duckdb` file. Each upload is
a fresh analysis session; nothing needs to survive a server restart yet.
