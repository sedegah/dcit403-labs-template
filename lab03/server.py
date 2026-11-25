import csv
from datetime import date, datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "pharmacy_stock.csv"
SALES = HERE / "data" / "sales.csv"
FIELDS = ["item", "strength", "form", "quantity", "unit_price_ghs", "expiry_date"]

mcp = FastMCP("pharmacy-stock")


def load_rows():
    with DATA.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def save_rows(rows):
    with DATA.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def public_row(row):
    return {
        "item": row["item"],
        "strength": row["strength"],
        "form": row["form"],
        "quantity": int(row["quantity"]),
        "unit_price_ghs": float(row["unit_price_ghs"]),
        "expiry_date": row["expiry_date"],
    }


def days_left(row):
    return (date.fromisoformat(row["expiry_date"]) - date.today()).days


def compact(value):
    return "".join(str(value).lower().split())


def record_sale_row(row, qty):
    total = qty * float(row["unit_price_ghs"])
    exists = SALES.exists()
    with SALES.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "timestamp",
                "item",
                "strength",
                "form",
                "qty",
                "unit_price_ghs",
                "total_ghs",
                "stock_left",
            ],
        )
        if not exists:
            writer.writeheader()
        writer.writerow(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "item": row["item"],
                "strength": row["strength"],
                "form": row["form"],
                "qty": qty,
                "unit_price_ghs": f"{float(row['unit_price_ghs']):.2f}",
                "total_ghs": f"{total:.2f}",
                "stock_left": row["quantity"],
            }
        )


@mcp.tool()
def check_stock(item: str, strength: str = "") -> list[dict]:
    """Look up a medicine in the pharmacy stock. Use full generic names: Amoxil is
    amoxicillin, ORS is oral rehydration salts. Returns matching rows with form,
    quantity, unit_price_ghs, expiry_date and days_left. If nothing matches, try
    search_items with a shorter keyword before saying the item is not stocked."""
    needle = compact(item)
    strength_key = compact(strength)
    rows = []
    for row in load_rows():
        if needle in compact(row["item"]) and (
            not strength_key or strength_key == compact(row["strength"])
        ):
            rows.append({**public_row(row), "days_left": days_left(row)})
    return rows


@mcp.tool()
def search_items(query: str) -> list[dict]:
    """Search the stock list by a keyword in the item name, strength or form.
    Use it when the exact medicine name is unknown, or for questions such as
    which syrups, tablets or inhalers are available."""
    tokens = [compact(part) for part in query.split() if part.strip()]
    rows = []
    for row in load_rows():
        haystack = compact(row["item"]) + compact(row["strength"]) + compact(row["form"])
        if tokens and all(token in haystack for token in tokens):
            rows.append({**public_row(row), "days_left": days_left(row)})
    return rows


@mcp.tool()
def list_expiring(days: int = 60) -> list[dict]:
    """List items that expire within the next days, including items that have
    already expired, soonest first. Each row includes days_left; a negative
    value means the batch is expired and must not be sold."""
    limit = max(0, int(days))
    rows = []
    for row in load_rows():
        left = days_left(row)
        if left <= limit:
            rows.append({**public_row(row), "days_left": left})
    return sorted(rows, key=lambda row: row["days_left"])


@mcp.tool()
def record_sale(item: str, strength: str, qty: int) -> dict:
    """Record a sale and reduce stock in the stock file. Only use when the user
    clearly says an item was sold. item is the medicine name, strength is the
    exact strength such as 500mg, and qty is the number of packs sold. The sale
    is refused for a non-positive quantity, an unknown item, an ambiguous item,
    an expired batch, or a quantity greater than the stock on hand."""
    if qty <= 0:
        return {
            "ok": False,
            "message": f"Sale refused: quantity must be at least 1 (got {qty}).",
        }

    needle = compact(item)
    strength_key = compact(strength)
    rows = load_rows()
    matches = [
        row
        for row in rows
        if needle in compact(row["item"])
        and (not strength_key or strength_key == compact(row["strength"]))
    ]

    if not matches:
        return {
            "ok": False,
            "message": f"Sale refused: no stock found for {item} {strength}.".strip(),
        }

    if len(matches) > 1:
        options = ", ".join(
            f"{row['item']} {row['strength']} ({row['form']})" for row in matches
        )
        return {
            "ok": False,
            "message": f"Sale refused: more than one product matches: {options}. Be more specific.",
        }

    row = matches[0]
    left = days_left(row)
    if left < 0:
        return {
            "ok": False,
            "message": f"Sale refused: {row['item']} {row['strength']} expired on {row['expiry_date']}.",
        }

    available = int(row["quantity"])
    if qty > available:
        return {
            "ok": False,
            "message": (
                f"Sale refused: only {available} packs of {row['item']} "
                f"{row['strength']} in stock; cannot sell {qty}."
            ),
        }

    row["quantity"] = str(available - qty)
    save_rows(rows)
    record_sale_row(row, qty)
    total = qty * float(row["unit_price_ghs"])
    return {
        "ok": True,
        "message": (
            f"Sold {qty} x {row['item']} {row['strength']} for GHS {total:.2f}. "
            f"Stock left: {row['quantity']}."
        ),
        "item": row["item"],
        "strength": row["strength"],
        "form": row["form"],
        "sold": qty,
        "unit_price_ghs": float(row["unit_price_ghs"]),
        "total_ghs": round(total, 2),
        "stock_left": int(row["quantity"]),
    }


@mcp.resource("stock://all")
def all_stock() -> str:
    """Read-only CSV snapshot of every stock row."""
    return DATA.read_text(encoding="utf-8")


if __name__ == "__main__":
    mcp.run()
