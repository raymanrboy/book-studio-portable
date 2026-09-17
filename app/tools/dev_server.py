"""Book Studio server for looking at the interface during development — never on the real data.

  python app/tools/dev_server.py            empty program on http://127.0.0.1:47890/
  python app/tools/dev_server.py --sample   plus made-up orders and one library book to click through

The data folder is %TEMP%\\bsdev (or BOOK_STUDIO_DATA when it is set): no keys there, so nothing
reaches Etsy, Printify or Gelato. Stop it with Ctrl+C (or preview_stop).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
PORT = 47890


def _receipt(rid: int, name: str, country: str, city: str, state: str, cover: str, child: str,
             shipped: bool = False, days_ago: int = 0) -> dict:
    """A made-up Etsy receipt in the shape the Etsy API returns (see profit.normalize_receipt)."""
    money = lambda cents: {"amount": cents, "divisor": 100, "currency_code": "USD"}  # noqa: E731
    return {
        "receipt_id": rid, "name": name, "first_line": "12 Example St", "second_line": "", "city": city,
        "state": state, "zip": "10001", "country_iso": country, "status": "Completed" if shipped else "Paid",
        "is_shipped": shipped, "is_paid": True, "create_timestamp": int(time.time()) - days_ago * 86400,
        "message_from_buyer": "Could you ship before the baptism? Thank you!" if rid % 2 else "",
        "grandtotal": money(4990), "total_price": money(3990), "subtotal": money(3990),
        "total_shipping_cost": money(1000), "total_tax_cost": money(0), "discount_amt": money(0),
        "transactions": [{
            "transaction_id": rid * 10, "title": "Personalized Baptism Storybook for Kids", "quantity": 1,
            "price": money(3990), "sku": "", "listing_id": 4100000900,
            "variations": [
                {"formatted_name": "Cover Type &amp; Size", "formatted_value": cover},
                {"formatted_name": "Child's Name", "formatted_value": child},
                {"formatted_name": "Dedication", "formatted_value": "DEFAULT"},
                {"formatted_name": "From whom", "formatted_value": "Grandma &amp; Grandpa"},
            ],
        }],
    }


def seed(data: Path) -> None:
    from studio import core, profit  # imported after BOOK_STUDIO_DATA is set

    receipts = [
        _receipt(4100000101, "Jane Doe", "US", "Springfield", "IL", "Hardcover 8&quot; x 8&quot;", "Emma"),
        _receipt(4100000102, "Maria Example", "CA", "Toronto", "ON", "Softcover 8&quot; x 8&quot;", "Noah", days_ago=1),
        _receipt(4100000103, "Alex Sample", "GB", "Leeds", "", "Softcover 5.5&quot; x 5.5&quot;", "Olivia", days_ago=2),
        _receipt(4100000104, "Sam Test", "US", "Austin", "TX", "Hardcover 8&quot; x 8&quot;", "Liam",
                 shipped=True, days_ago=9),
    ]
    snapshot = {"receipts": [profit.normalize_receipt(r) for r in receipts], "printify": [], "gelato": [],
                "shopName": "Sample shop", "syncedAt": core.now_iso(), "warnings": []}
    core.write_json(profit.SNAPSHOT, snapshot, backup=False)
    book_id = "0" * 31 + "1"
    folder = data / "library" / "books" / book_id
    if not (folder / "book.json").exists():
        from studio import library
        book = {"id": book_id, "schema": 1, "rev": 0, "createdAt": core.now_iso(),
                "title": "Personalized Baptism Storybook (sample)",
                "listing": {"id": "4100000900", "title": "Personalized Baptism Storybook for Kids", "state": "active"},
                "canvaUrl": "https://www.canva.com/design/sample", "notes": "", "archived": False,
                "cover": None, "thumbnail": None, "slots": library._empty_slots(),
                "text": {k: "" for k in library.TEXT_KEYS}}
        book["text"]["page1"] = "Dear {Name},\n\nWishing you a lifetime filled with love.\n\nWith love,\n{Gifter}"
        folder.mkdir(parents=True, exist_ok=True)
        library.save(book)
    print(f"Sample data: {len(receipts)} orders, 1 book", flush=True)


def main(argv: list[str]) -> int:
    data = Path(os.environ.get("BOOK_STUDIO_DATA") or Path(tempfile.gettempdir()) / "bsdev").resolve()
    if data == (APP / "data").resolve():
        print("Refusing to run on the real data folder.", file=sys.stderr)
        return 1
    os.environ["BOOK_STUDIO_DATA"] = str(data)
    sys.path.insert(0, str(APP))
    if "--sample" in argv:
        data.mkdir(parents=True, exist_ok=True)
        seed(data)
    from studio.main import main as run
    return run(["--no-window", "--port", str(PORT)])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
