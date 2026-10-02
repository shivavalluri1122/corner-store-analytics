# Corner Store Analytics

Upload a Square item-level sales CSV and get an instant, readable sales
dashboard — built for a small corner store owner with no data background.

This repository currently implements **Weeks 1-3** of the project:

1. **Project foundation & synthetic data** — a deterministic generator that
   produces realistic Square-like item sales CSVs (clean and malformed).
2. **Ingestion pipeline** — CSV cleaning, Pandera validation, and DuckDB
   storage (`transactions`, `line_items`, `daily_item_sales`).
3. **Streamlit dashboard** — upload/demo-load, validation feedback, and a
   Sales Overview page (KPIs, category mix, hour-by-weekday heatmap,
   month-over-month trend, top 20 products by units/sales).

Forecasting, customer segmentation, the Claude assistant, authentication,
payment processing, and deployment are **out of scope** for this phase —
see `docs/spec.md`.

## Architecture

```
app/            Streamlit UI (Home page, Sales Overview page, components)
pipeline/       CSV ingestion, Pandera validation, table transforms, DuckDB
models/         Pandera schema definitions (data contracts)
assistant/      Placeholder for a future Claude assistant (not built yet)
data/synthetic/ Dataset generator + generated CSVs
docs/           Product spec, schema docs, generation rules, data dictionary
tests/          pytest suite + a standalone KPI sanity-check script
```

## Getting started

Requires Python 3.10+. Run all commands from the repository root.

```powershell
# 1. create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate

# 2. install dependencies
pip install -r requirements.txt

# 3. (re)generate the synthetic datasets (large_clean.csv, small_clean.csv, malformed.csv)
python -m data.synthetic.generate_dataset

# 4. run the test suite
python -m pytest -q

# 5. run the app
python -m streamlit run app/Home.py
```

`requirements.txt` also installs `prophet`, `scikit-learn`, and `anthropic`;
these are reserved for later weeks and are not used yet.

Then, in the app, either upload your own Square item sales CSV or click
**Load Demo Store** to use the bundled `small_clean.csv` dataset.

## Documentation

- [docs/spec.md](docs/spec.md) — product spec and scope
- [docs/square_schema.md](docs/square_schema.md) — raw CSV column definitions
- [docs/data_generation.md](docs/data_generation.md) — synthetic data rules
- [docs/data_dictionary.md](docs/data_dictionary.md) — cleaned schema & DuckDB tables
- [docs/interviews.md](docs/interviews.md) — stakeholder interviews (placeholder; none conducted yet)
- [DECISIONS.md](DECISIONS.md) — key design decisions and rationale

## Testing

```powershell
python -m pytest -q
python tests/create_kpi_check.py
```

`tests/create_kpi_check.py` independently recomputes the five dashboard KPIs
(Net Sales, Transactions, Average Basket, Units, Distinct Items Sold) from the
raw CSV, compares them with the application's DuckDB/analytics values for the
full date range and a sub-range, writes `tests/kpi_check.xlsx`
(PASS/FAIL per KPI, plus a Methodology sheet), and prints synthetic-data
pattern checks. It exits non-zero if any KPI mismatches.

## Future scope (not built yet)

Forecasting (Prophet), customer segmentation, a Claude-powered assistant
(`assistant/` is a placeholder), authentication, payment processing, and
deployment.
