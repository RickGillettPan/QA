# Sales data cleanup and reporting

This project contains small Python examples for sales-data cleanup and a simulated search. It uses only the Python standard library; no package installation is required. Run commands from the project folder with Python 3.

## Sales data workflow

Review and prepare the sales data with:

```powershell
python review_sales.py
python prepare_sales.py
```

`review_sales.py` reads `messy_sales.csv` and reports missing values, inconsistent formatting, invalid values, likely corrections, and duplicate order IDs. Red marks data that cannot be determined from the row; yellow marks cleanup or suggestions. A suggestion is not necessarily correct and should be checked.

`prepare_sales.py` reads the source CSV, cleans values it can safely standardize, and writes `cleaned_sales.csv`, `sales_summary.csv`, and `sales_summary.svg`. Its cleaning rules, summary calculations, and limitations are described below. Running it again overwrites those generated files.

## Search simulator

Run the terminal demo with:

```powershell
python search_simulator.py
```

The script displays a welcome banner, asks for a topic, shows a short simulated progress bar, and prints three example suggestions plus a summary. The results are generated from the entered text; **the script does not search the internet or retrieve real information**. It uses ANSI colors when run in an interactive terminal and plain text when output is redirected. Press Ctrl+C to cancel the prompt.

The code is intentionally kept small and uses only built-in Python modules:

- `main()` runs the welcome, prompt, progress, results, and summary in order.
- `paint()` adds terminal color when supported.
- `banner()` and `show_result()` format the display.
- `show_progress()` provides a brief visual delay; it does not indicate a real network request.

## Project files

- `messy_sales.csv` — source data. The scripts read this file and do not modify it.
- `review_sales.py` — checks sales data quality and reports issues.
- `prepare_sales.py` — creates cleaned sales data, summary CSV, and SVG chart.
- `cleaned_sales.csv` — cleaned rows, retaining unresolved blanks for later correction.
- `sales_summary.csv` — totals grouped by region, product, salesperson, and category.
- `sales_summary.svg` — graphic version of the summary, with four panels and revenue bars. Open it in a web browser or an SVG-compatible viewer.
- `search_simulator.py` — interactive terminal example that displays simulated search results.
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
