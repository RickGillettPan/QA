import csv
import sys
from collections import defaultdict
from datetime import datetime
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
NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
                "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def color(text, code):
    if sys.stdout.isatty():
        return f"{code}{text}{RESET}"
    return text


def parse_date(value):
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(value.strip(), date_format).date()
        except ValueError:
            pass
    return None


def main():
    source = Path(__file__).with_name("messy_sales.csv")
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

    if not rows:
        print("The sales file contains no sales rows.")
        return 0

    categories_by_product = defaultdict(set)
    for row in rows:
        product = row["Product"].strip().casefold()
        category = row["Category"].strip()
        if product and category:
            categories_by_product[product].add(category.title())

    issues = []
    order_rows = defaultdict(list)
    for line_number, row in enumerate(rows, start=2):
        row_issues = []
        values = {key: (value or "").strip() for key, value in row.items()}

        for field in REQUIRED_COLUMNS:
            if not values[field]:
                if field == "Category":
                    candidates = categories_by_product[values["Product"].casefold()]
                    if len(candidates) == 1:
                        row_issues.append(
                            ("suggestion", f"Category is missing; Product suggests {next(iter(candidates))}.")
                        )
                    else:
                        row_issues.append(("unresolved", "Category is missing and cannot be inferred."))
                else:
                    row_issues.append(("unresolved", f"{field} is missing and cannot be recovered from this row."))

        if values["Date"]:
            parsed_date = parse_date(values["Date"])
            if parsed_date is None:
                row_issues.append(("unresolved", f"Date {values['Date']!r} is not in a recognized date format."))
            elif values["Date"] != parsed_date.isoformat():
                row_issues.append(("cleanup", "Date uses a different format; it can be standardized to YYYY-MM-DD."))

        for field in ("Region", "Salesperson", "Product", "Category"):
            value = row[field] or ""
            stripped_value = value.strip()
            if value and value != stripped_value:
                row_issues.append(("cleanup", f"{field} has extra spaces."))
            if stripped_value and (stripped_value.islower() or stripped_value.isupper()):
                row_issues.append(("cleanup", f"{field} uses inconsistent capitalization."))

        quantity = values["Quantity"]
        if quantity:
            if quantity.isdigit():
                if int(quantity) <= 0:
                    row_issues.append(("unresolved", f"Quantity {quantity!r} must be greater than zero."))
            elif quantity.casefold() in NUMBER_WORDS:
                row_issues.append(
                    ("suggestion", f"Quantity {quantity!r} likely means {NUMBER_WORDS[quantity.casefold()]} (confirm before changing).")
                )
            else:
                row_issues.append(("unresolved", f"Quantity {quantity!r} is not a valid whole number."))

        price = values["Unit_Price"]
        if price:
            normalized_price = price.replace("£", "").replace(",", "").strip()
            try:
                if float(normalized_price) < 0:
                    row_issues.append(("unresolved", f"Unit_Price {price!r} cannot be negative."))
                elif normalized_price != price:
                    row_issues.append(("cleanup", f"Unit_Price {price!r} can be standardized to {normalized_price}."))
            except ValueError:
                row_issues.append(("unresolved", f"Unit_Price {price!r} is not a valid number."))

        if values["Order_ID"]:
            order_rows[values["Order_ID"]].append((line_number, row))
        if row_issues:
            issues.append((line_number, row.get("Order_ID", "").strip(), row_issues))

    duplicates = []
    for order_id, occurrences in order_rows.items():
        if len(occurrences) > 1:
            first_line, first_row = occurrences[0]
            for line_number, row in occurrences[1:]:
                if row == first_row:
                    detail = f"Exact duplicate of row {first_line}."
                else:
                    detail = f"Order ID also appears on row {first_line}; verify whether these are separate sales."
                duplicates.append((line_number, order_id, detail))

    unresolved_count = sum(
        1 for _, _, row_issues in issues for kind, _ in row_issues if kind == "unresolved"
    ) + len(duplicates)
    print(f"Sales data review: {source.name} ({len(rows)} rows)")
    if not issues and not duplicates:
        print("No data-quality issues found.")
        return 0

    for line_number, order_id, row_issues in issues:
        label = f"Row {line_number}"
        if order_id:
            label += f" ({order_id})"
        print(f"\n{label}")
        for kind, message in row_issues:
            if kind == "unresolved":
                print(f"  {color('CANNOT DETERMINE', RED)}: {message}")
            elif kind == "suggestion":
                print(f"  {color('SUGGESTION', YELLOW)}: {message}")
            else:
                print(f"  {color('CLEANUP', YELLOW)}: {message}")

    for line_number, order_id, detail in duplicates:
        print(f"\n{color('Row ' + str(line_number) + ' (' + order_id + ')', RED)}")
        print(f"  {color('CHECK', RED)}: {detail}")

    print(f"\nFound {len(issues)} rows with field issues and {len(duplicates)} duplicate-order checks.")
    print(f"{unresolved_count} unresolved item(s) are highlighted in red; suggestions need confirmation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
