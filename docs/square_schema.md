# Square Item Sales CSV Schema (raw / as-uploaded)

The synthetic generator and the ingestion pipeline both target the column
layout of a Square **Item Sales** export. This is the "raw" schema — exactly
what a store owner would download from Square and upload to the app.

| Column | Type (as exported) | Notes |
|---|---|---|
| `Date` | string, `MM/DD/YYYY` | Transaction date |
| `Time` | string, `hh:mm:ss AM/PM` | Transaction time, local |
| `Time Zone` | string | IANA-ish label, constant per store |
| `Category` | string | One of 10 catalog categories |
| `Item` | string | Product name |
| `SKU` | string | Catalog SKU code, e.g. `BEV-001` |
| `Qty` | integer | Units sold in this line item |
| `Price Point Name` | string | Square variation label (always "Regular" here) |
| `Gross Sales` | currency string, e.g. `$12.34` | Qty × unit price |
| `Discounts` | currency string, e.g. `-$1.23` or `$0.00` | Line-item discount |
| `Net Sales` | currency string | Gross Sales + Discounts |
| `Tax` | currency string | Net Sales × tax rate |
| `Transaction ID` | string | Shared by every line item in one basket |
| `Payment ID` | string | One per transaction |
| `Device Name` | string | Register/terminal name |
| `Notes` | string | Free text, usually empty |
| `Details` | string | Free text, usually empty |
| `Event Type` | string | Always "Payment" in this dataset |
| `Location` | string | Store name |
| `Dining Option` | string | Not applicable to a retail corner store, always empty |
| `Customer Name` | string, **PII** | Empty for walk-in/non-loyalty transactions |
| `Customer ID` | string, **PII** | Empty for walk-in/non-loyalty transactions |
| `Customer Reference ID` | string, **PII** | Empty for walk-in/non-loyalty transactions |

## Required vs optional columns

**Required** (validation fails if missing or malformed): `Date`, `Time`,
`Category`, `Item`, `SKU`, `Qty`, `Gross Sales`, `Net Sales`, `Tax`,
`Transaction ID`.

**Optional / best-effort**: everything else, including all three customer
(PII) columns, which are dropped by the pipeline regardless of whether
they're present.

## Known "messiness" the pipeline must handle
- Currency columns are strings with a `$` prefix and sometimes a leading
  `-` for discounts — not numeric on read.
- `Date` + `Time` are separate string columns that must be combined and
  parsed into a real timestamp.
- Column headers may have inconsistent casing/spacing across exports — the
  pipeline normalizes to `snake_case` before doing anything else.
