# Sales data cleanup and reporting

This project reviews and cleans `messy_sales.csv`, then produces sales summaries and a chart. It uses only the Python standard library; no package installation is required. Run commands from the project folder with Python 3:

```powershell
python review_sales.py
python prepare_sales.py
```

## Files

- `messy_sales.csv` — source data. The scripts read this file and do not modify it.
- `review_sales.py` — reports missing values, inconsistent formatting, invalid values, likely corrections, and duplicate order IDs. Red marks data that cannot be determined from the row; yellow marks cleanup or suggestions. A suggestion is not necessarily correct and should be checked.
- `prepare_sales.py` — creates the cleaned data, summary, and chart. It overwrites those generated files when run.
- `cleaned_sales.csv` — cleaned rows, retaining unresolved blanks for later correction.
- `sales_summary.csv` — totals grouped by region, product, salesperson, and category.
- `sales_summary.svg` — graphic version of the summary, with four panels and revenue bars. Open it in a web browser or an SVG-compatible viewer.
- `main.py` — the original example script that prints the current date and time; it is independent of the sales workflow.

## Cleaning rules

The preparation script trims surrounding spaces, standardizes dates to `YYYY-MM-DD` where recognized, normalizes inconsistent all-lowercase or all-uppercase labels, and formats valid prices to two decimal places. It converts number words from `one` through `ten` to digits. A missing category is filled only if the product has exactly one known category elsewhere in the source.

Exact duplicate rows (identical across all required columns after trimming) are removed. Other missing fields are left blank; the script does not guess missing dates, order IDs, quantities, or salespeople. A blank salesperson appears as `Unspecified` in the summary.

## How the summary is calculated

Each eligible row contributes its quantity to units sold and `quantity × unit price` to revenue. Summary rows are sorted by units sold, then revenue, descending. Sales lines counts eligible source rows, not unique order IDs.

Rows with missing or invalid quantity or price, non-positive quantities, or negative prices are omitted from numerical totals. Other missing fields, such as date or order ID, do not prevent a row from contributing if its quantity and price are usable. In the SVG, each chart's revenue bars are scaled relative to the largest revenue in that chart; the printed values are the figures from the CSV summary.

## Current source data notes

For the supplied CSV, the preparation script removes one exact duplicate, infers one category, converts `three` to `3`, and retains one row with a missing quantity. That row is excluded from totals. The row with a missing salesperson is included under `Unspecified`; rows with missing date or order ID are still included because their quantity and price are available.

The missing quantity and salesperson, date, and order ID remain unresolved in `cleaned_sales.csv`. Check `review_sales.py`'s report before using the data for decisions; in particular, inferred and converted values are based on patterns in the file, not external confirmation.
