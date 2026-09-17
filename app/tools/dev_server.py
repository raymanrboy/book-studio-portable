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


def _printify(rid: int, status: str, tracking: str = "") -> dict:
    """A made-up Printify order (slim, as saved at sync) carrying the receipt number."""
    return {"id": f"{rid:024x}", "app_order_id": str(rid)[-6:], "total_price": 1995, "total_shipping": 500,
            "total_tax": 0, "created_at": time.strftime("%Y-%m-%d %H:%M:%S+00:00", time.gmtime()), "status": status,
            "metadata": {"shop_order_id": str(rid)}, "address_to": {}, "line_items": [],
            "shipments": [{"carrier": "usps", "number": tracking, "url": ""}] if tracking else []}


def _gelato(rid: int, status: str, carrier: str = "", tracking: str = "") -> dict:
    """A made-up Gelato order (slim, tracking already read) carrying the receipt number."""
    return {"id": f"00000000-0000-4000-8000-{rid:012d}", "orderReferenceId": f"{rid}-sample", "firstName": "",
            "lastName": "", "totalInclVat": "21.50", "currency": "EUR", "fulfillmentStatus": status,
            "financialStatus": "draft" if status == "draft" else "paid",
            "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
            "orderType": "draft" if status == "draft" else "order",
            "shipments": [{"carrier": carrier, "number": tracking, "url": ""}] if tracking else []}


def seed(data: Path) -> None:
    from studio import core, profit  # imported after BOOK_STUDIO_DATA is set

    hard, soft = "Hardcover 8&quot; x 8&quot;", "Softcover 8&quot; x 8&quot;"
    receipts = [
        _receipt(4100000101, "Jane Doe", "US", "Springfield", "IL", hard, "Emma"),
        _receipt(4100000102, "Maria Example", "CA", "Toronto", "ON", soft, "Noah", days_ago=1),
        _receipt(4100000103, "Alex Sample", "GB", "Leeds", "", "Softcover 5.5&quot; x 5.5&quot;", "Olivia", days_ago=2),
        _receipt(4100000104, "Sam Test", "US", "Austin", "TX", hard, "Liam", shipped=True, days_ago=9),
        _receipt(4100000105, "Chris Demo", "US", "Denver", "CO", hard, "Ava", days_ago=4),
        _receipt(4100000106, "Pat Example", "US", "Salem", "OR", hard, "Mia", days_ago=1),
        _receipt(4100000107, "Lee Sample", "US", "Dayton", "OH", hard, "Leo", days_ago=3),
    ]
    printify_orders = [
        _printify(4100000104, "fulfilled", "9400100000000000000001"),
        _printify(4100000105, "fulfilled", "9400100000000000000002"),   # sent: waits for the mark on Etsy
        _printify(4100000106, "in-production"),
        _printify(4100000107, "has-issues"),
    ]
    gelato_orders = [
        _gelato(4100000102, "in_transit", "Canada Post Tracked Packet", "7023210000000003"),  # sent
        _gelato(4100000103, "draft"),
    ]
    snapshot = {"receipts": [profit.normalize_receipt(r) for r in receipts], "printify": printify_orders,
                "gelato": gelato_orders, "shopName": "Sample shop", "syncedAt": core.now_iso(), "warnings": []}
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
