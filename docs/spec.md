# Product Spec — Corner Store Analytics

## Problem statement
A small corner store owner exports item-level sales data from Square as a CSV
but has no way to turn it into decisions. Corner Store Analytics lets the
owner upload that CSV and get an instant, readable sales dashboard — no
spreadsheet wrangling required.

## Scope for this build (Weeks 1-3 only)

### Week 1 — Project foundation & synthetic data
- Repository scaffolding (`app/`, `pipeline/`, `models/`, `assistant/`,
  `data/synthetic/`, `docs/`, `tests/`).
- A synthetic Square-like item sales generator producing:
  - ~150 SKUs across 10 categories
  - 12 months of daily transactions
  - weekly seasonality (higher weekend demand)
  - first-of-month spike (days 1-3) and mid-month spike (days 15-17)
  - a summer lift for the Beverages category (Jun-Aug)
  - 5 SKUs with visible multi-day stockout gaps
- Three CSVs: `small_clean.csv` (~2k rows), `large_clean.csv` (~50k rows),
  `malformed.csv` (missing required columns, invalid numerics, invalid date).

### Week 2 — Ingestion pipeline
- CSV ingestion: normalize headers, parse date/time, convert currency
  strings to numeric, strip PII (customer name/id/reference).
- Pandera schema validation with a readable pass/fail report.
- Load into DuckDB as three tables: `transactions`, `line_items`,
  `daily_item_sales`.
- pytest coverage for ingestion, validation, transform, and DB load.

### Week 3 — Streamlit application
- CSV upload widget + a "Load Demo Store" button (uses `small_clean.csv`).
- Validation results shown to the user before any dashboard renders.
- Sales Overview dashboard:
  - KPI cards (revenue, units, transactions, avg basket, date range)
  - category mix
  - hour-by-weekday heatmap
  - month-over-month trend
  - top 20 products by units
  - top 20 products by sales

## Explicitly out of scope for this build
Forecasting, customer segmentation, the Claude assistant, authentication,
payment processing, and deployment. These are future-phase work; some of
their dependencies are pre-installed but unused (see `requirements.txt`).

## Primary user
A single-location corner store owner/operator with no data background.
Every dashboard element must be understandable without training.
