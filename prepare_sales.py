import csv
from html import escape
import sys
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


REQUIRED_COLUMNS = (
    "Date",
    "Order_ID",
    "Region",
    "Salesperson",
    "Product",
    "Category",
    "Quantity",
    "Unit_Price",
)
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y")
NUMBER_WORDS = {
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
}
SUMMARY_DIMENSIONS = ("Region", "Product", "Salesperson", "Category")
DIMENSION_TITLES = {
    "Region": "Sales by region",
    "Product": "Sales by product",
    "Salesperson": "Sales by salesperson",
    "Category": "Popular categories",
}


def parse_date(value):
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value, date_format).date().isoformat()
        except ValueError:
            continue
    return None


def normalize_label(value):
    value = value.strip()
    if value.isupper() or value.islower():
        return value.title()
    return value


def write_summary_graphic(path, grouped, sale_count):
    width = 1280
    height = 760
    card_width = 592
    card_height = 286
    card_positions = ((36, 132), (652, 132), (36, 440), (652, 440))
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f4f7fb"/>',
        '<text x="40" y="58" fill="#172b4d" font-family="Arial, sans-serif" font-size="30" font-weight="700">Sales performance</text>',
        f'<text x="42" y="88" fill="#52647a" font-family="Arial, sans-serif" font-size="14">Revenue and units across {sale_count} rows with usable quantity and price</text>',
    ]

    for dimension, (x, y) in zip(SUMMARY_DIMENSIONS, card_positions):
        groups = grouped[dimension]
        entries = sorted(
            groups.items(),
            key=lambda item: (-item[1]["units"], -item[1]["revenue"], item[0].casefold()),
        )
        max_revenue = max((totals["revenue"] for _, totals in entries), default=Decimal("0"))
        elements.extend(
            (
                f'<rect x="{x}" y="{y}" width="{card_width}" height="{card_height}" rx="14" fill="#ffffff" stroke="#dce4ee"/>',
                f'<text x="{x + 22}" y="{y + 36}" fill="#172b4d" font-family="Arial, sans-serif" font-size="19" font-weight="700">{escape(DIMENSION_TITLES[dimension])}</text>',
                f'<text x="{x + 22}" y="{y + 61}" fill="#718096" font-family="Arial, sans-serif" font-size="11">BAR LENGTH = REVENUE · UNITS AND SALES SHOWN AT RIGHT</text>',
            )
        )

        for index, (label, totals) in enumerate(entries):
            center_y = y + 94 + index * 29
            bar_width = float(totals["revenue"] / max_revenue * Decimal("112")) if max_revenue else 0
            elements.extend(
                (
                    f'<text x="{x + 22}" y="{center_y + 4}" fill="#334155" font-family="Arial, sans-serif" font-size="12">{escape(label)}</text>',
                    f'<rect x="{x + 168}" y="{center_y - 8}" width="112" height="12" rx="6" fill="#edf2f7"/>',
                    f'<rect x="{x + 168}" y="{center_y - 8}" width="{bar_width:.1f}" height="12" rx="6" fill="#3978d4"/>',
                    f'<text x="{x + 294}" y="{center_y + 4}" fill="#334155" font-family="Arial, sans-serif" font-size="11">{totals["units"]} units · £{totals["revenue"]:.2f} · {totals["lines"]} sales</text>',
                )
            )

    elements.append("</svg>")
    path.write_text("\n".join(elements), encoding="utf-8")


def main():
    directory = Path(__file__).resolve().parent
    source = directory / "messy_sales.csv"
    cleaned_path = directory / "cleaned_sales.csv"
    summary_path = directory / "sales_summary.csv"
    graphic_path = directory / "sales_summary.svg"

    if not source.exists():
        print(f"Could not find sales file: {source}", file=sys.stderr)
        return 1

    with source.open(newline="", encoding="utf-8-sig") as sales_file:
        reader = csv.DictReader(sales_file)
        if reader.fieldnames is None:
            print("The sales file is empty or has no header.", file=sys.stderr)
            return 1
        missing_columns = [column for column in REQUIRED_COLUMNS if column not in reader.fieldnames]
        if missing_columns:
            print(f"Missing required columns: {', '.join(missing_columns)}", file=sys.stderr)
            return 1
        rows = list(reader)

    category_by_product = defaultdict(set)
    for row in rows:
        product = (row.get("Product") or "").strip().casefold()
        category = (row.get("Category") or "").strip()
        if product and category:
            category_by_product[product].add(category.title())

    cleaned_rows = []
    seen_rows = set()
    duplicate_count = 0
    inferred_categories = 0
    converted_quantities = 0
    missing_quantities = 0

    for row in rows:
        original = tuple((row.get(column) or "").strip() for column in REQUIRED_COLUMNS)
        if original in seen_rows:
            duplicate_count += 1
            continue
        seen_rows.add(original)

        cleaned = dict(zip(REQUIRED_COLUMNS, original))
        if cleaned["Date"]:
            parsed_date = parse_date(cleaned["Date"])
            if parsed_date:
                cleaned["Date"] = parsed_date

        for field in ("Region", "Salesperson", "Product", "Category"):
            cleaned[field] = normalize_label(cleaned[field])

        if not cleaned["Category"] and cleaned["Product"]:
            candidates = category_by_product[cleaned["Product"].casefold()]
            if len(candidates) == 1:
                cleaned["Category"] = next(iter(candidates))
                inferred_categories += 1

        quantity = cleaned["Quantity"].casefold()
        if quantity in NUMBER_WORDS:
            cleaned["Quantity"] = NUMBER_WORDS[quantity]
            converted_quantities += 1
        elif not quantity:
            missing_quantities += 1

        price = cleaned["Unit_Price"].replace("£", "").replace(",", "").strip()
        try:
            cleaned["Unit_Price"] = f"{Decimal(price):.2f}" if price else ""
        except InvalidOperation:
            cleaned["Unit_Price"] = price

        cleaned_rows.append(cleaned)

    complete_sales = []
    for row in cleaned_rows:
        try:
            quantity = int(row["Quantity"])
            price = Decimal(row["Unit_Price"])
            if quantity > 0 and price >= 0:
                complete_sales.append((row, quantity, price))
        except (ValueError, InvalidOperation):
            continue

    with cleaned_path.open("w", newline="", encoding="utf-8-sig") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(cleaned_rows)

    grouped = {}
    for dimension in SUMMARY_DIMENSIONS:
        groups = defaultdict(lambda: {"units": 0, "revenue": Decimal("0"), "lines": 0})
        for row, quantity, price in complete_sales:
            label = row[dimension] or "Unspecified"
            groups[label]["units"] += quantity
            groups[label]["revenue"] += quantity * price
            groups[label]["lines"] += 1
        grouped[dimension] = groups

    with summary_path.open("w", newline="", encoding="utf-8-sig") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(("Breakdown", "Name", "Units_Sold", "Revenue_GBP", "Sales_Lines"))
        for dimension, groups in grouped.items():
            for label, totals in sorted(
                groups.items(),
                key=lambda item: (-item[1]["units"], -item[1]["revenue"], item[0].casefold()),
            ):
                writer.writerow(
                    (
                        dimension,
                        label,
                        totals["units"],
                        f"{totals['revenue']:.2f}",
                        totals["lines"],
                    )
                )

    write_summary_graphic(graphic_path, grouped, len(complete_sales))

    print(f"Created {cleaned_path.name} with {len(cleaned_rows)} rows.")
    print(
        f"Created {summary_path.name} with regional, product, salesperson, and category totals "
        f"from {len(complete_sales)} rows with usable quantity and price."
    )
    print(f"Created {graphic_path.name} with charts for regions, products, salespeople, and categories.")
    if duplicate_count:
        print(f"Removed {duplicate_count} exact duplicate row(s).")
    if inferred_categories:
        print(f"Inferred {inferred_categories} missing category value(s) from consistent product mappings.")
    if converted_quantities:
        print(f"Converted {converted_quantities} quantity word(s) to numbers.")
    if missing_quantities:
        print(
            f"Retained {missing_quantities} row(s) with missing quantity in the cleaned file; "
            "these are excluded from numeric summaries."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
