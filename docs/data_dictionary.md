# Data Dictionary — Cleaned Schema & DuckDB Tables

This describes the data **after** `pipeline/ingest.py` has normalized
headers, parsed dates/currency, and stripped PII, and after
`pipeline/transform.py` has split it into three DuckDB tables.

## PII handling
`Customer Name`, `Customer ID`, and `Customer Reference ID` are dropped
during ingestion, before any validation or storage. They never reach any
DuckDB table.

## Table: `transactions`
One row per basket (`Transaction ID`).

| Column | Type | Description |
|---|---|---|
| `transaction_id` | string (PK) | Unique basket identifier |
| `payment_id` | string | Payment identifier |
| `transaction_ts` | timestamp | Combined date + time |
| `date` | date | Calendar date, for daily rollups |
| `hour` | int | Hour of day (0-23), for the heatmap |
| `weekday` | string | Day name (Monday-Sunday), for the heatmap |
| `device_name` | string | Register/terminal |
| `location` | string | Store name |
| `num_line_items` | int | Count of line items in the basket |
| `total_qty` | int | Sum of quantities across line items |
| `total_gross_sales` | float | Sum of gross sales |
| `total_discounts` | float | Sum of discounts |
| `total_net_sales` | float | Sum of net sales |
| `total_tax` | float | Sum of tax |

## Table: `line_items`
One row per original CSV line item.

| Column | Type | Description |
|---|---|---|
| `transaction_id` | string (FK -> transactions) | Basket this item belongs to |
| `line_item_id` | string (PK) | `transaction_id` + sequence number |
| `date` | date | Calendar date |
| `transaction_ts` | timestamp | Combined date + time |
| `sku` | string | Catalog SKU |
| `item` | string | Product name |
| `category` | string | Product category |
| `qty` | int | Units sold |
| `price_point_name` | string | Square variation label |
| `gross_sales` | float | Qty × unit price |
| `discounts` | float | Discount amount (positive magnitude) |
| `net_sales` | float | Gross sales - discounts |
| `tax` | float | Tax amount |

## Table: `daily_item_sales`
One row per (date, SKU) — the rollup used by most dashboard charts.

| Column | Type | Description |
|---|---|---|
| `date` | date (PK part) | Calendar date |
| `sku` | string (PK part) | Catalog SKU |
| `item` | string | Product name |
| `category` | string | Product category |
| `units_sold` | int | Sum of qty for that SKU that day |
| `gross_sales` | float | Sum of gross sales |
| `discounts` | float | Sum of discounts |
| `net_sales` | float | Sum of net sales |
| `tax` | float | Sum of tax |
| `transactions_count` | int | Distinct transactions containing this SKU that day |

## Malformed sample (`malformed.csv`) — what's broken and why
Used to test that validation fails loudly and specifically, instead of
silently producing wrong numbers.

| Issue | What was done |
|---|---|
| Missing required columns | `SKU` and `Net Sales` columns removed entirely |
| Invalid numeric data | 5 rows have non-numeric `Qty` (e.g. `"three"`, `"N/A"`); 5 rows have non-numeric `Gross Sales` (e.g. `"twelve dollars"`, `"$$12.00"`) |
| Invalid date | 1 row has an unparseable `Date` value (e.g. `"Not a date"`, `"02/30/2025"`) |
