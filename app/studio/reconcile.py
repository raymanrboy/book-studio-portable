"""Matching Etsy receipts with Printify / Gelato orders — the Etsy Profit Calculator's rules, one receipt at a time:

 1. a manual link set by the owner (or "none": this receipt has no print order);
 2. the receipt's number in a print order: Printify (metadata.shop_order_id or a line item's title), then Gelato
    (orderReferenceId);
 3. the shipping recipient's name: Printify, then Gelato — the order closest in time when several fit.

Both number rules come before either name rule (since 2026-09-26): a receipt whose own Gelato order carries its
number was taken by any Printify order with a similar name ("Ann Lee" is inside "Joann Leeds") — and then showed
that order's status and tracking. A live order is always preferred to a cancelled one or a Gelato draft; orders the
owner marked as a replacement reprint are never matched by themselves. One print order that several receipts find is
a bundle: its cost is split equally. What the rows then cost and earn after cancellations, refunds and reprints is
outcomes.py's.
"""
from __future__ import annotations

import bisect
import re
from datetime import datetime, timezone

from .fees import r1, r2
from .printorders import facts as order_facts, js_round, num, rates as current_rates

_STRIP = re.compile(r"[^\w\s]|_", re.UNICODE)
_SPACES = re.compile(r"\s+")
_DIGITS = re.compile(r"\d+")
MIN_NAME = 3  # a shorter shipping name finds nothing by itself


def normalize_name(name: str | None) -> str:
    if not name:
        return ""
    return _SPACES.sub(" ", _STRIP.sub("", name.lower())).strip()


def is_name_match(name_a: str | None, name_b: str | None) -> bool:
    a, b = normalize_name(name_a), normalize_name(name_b)
    if not a or not b:
        return False
    if a == b:
        return True
    words_a = [w for w in a.split(" ") if w]
    words_b = [w for w in b.split(" ") if w]
    if len(words_a) >= 2 and len(words_b) >= 2 and words_a[0] == words_b[0] and words_a[-1] == words_b[-1]:
        return True
    return len(a) >= 4 and len(b) >= 4 and (a in b or b in a)


def parse_time(value) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp() * 1000


def _distance(a: float | None, b: float | None) -> float:
    if a is None or b is None:
        return float("inf")
    return abs(a - b)


# ---------------------------------------------------------------- the cover a buyer chose

HARD = ("hardcover", "hard cover", "hardback", "тверд")
SOFT = ("softcover", "soft cover", "paperback", "м'як")


def item_format(item: dict) -> str | None:
    """"hardcover" / "softcover" as the Etsy item says it — its variations, then its SKU, then its title; None when
    it doesn't say."""
    for v in item.get("variations") or []:
        text = f"{v.get('name') or ''} {v.get('value') or ''}".lower()
        if any(k in text for k in HARD):
            return "hardcover"
        if any(k in text for k in SOFT):
            return "softcover"
    sku = (item.get("sku") or "").lower()
    if sku:
        if "hard" in sku or "-hc" in sku or sku.startswith("hc") or "_hc" in sku:
            return "hardcover"
        if "soft" in sku or "-sc" in sku or sku.startswith("sc") or "_sc" in sku or "pb" in sku:
            return "softcover"
    title = (item.get("title") or "").lower()
    if any(k in title for k in HARD):
        return "hardcover"
    if any(k in title for k in SOFT):
        return "softcover"
    return None


def cover_label(items: list) -> str:
    """«2x Hardcover + Softcover книга» — from what the buyer chose. Only the Etsy items say it (until 2026-09-26 the
    letters of a Gelato order's name were read as well: «Oscar» made a softcover)."""
    if not items:
        return "Книга"
    counts = {"hardcover": 0, "softcover": 0}
    for item in items:
        fmt = item_format(item)
        if fmt:
            counts[fmt] += int(item.get("quantity") or 1)
    parts = [f"{f'{n}x ' if n > 1 else ''}{label}" for label, n in (("Hardcover", counts["hardcover"]),
                                                                     ("Softcover", counts["softcover"])) if n]
    return f"{' + '.join(parts)} книга" if parts else items[0].get("title") or "Книга"


# ---------------------------------------------------------------- finding a receipt's print order

class _NameIndex:
    """Finds every name for which is_name_match() is true without comparing all pairs.

    Same result as scanning the whole list with is_name_match, in list order,
    but in O(len(name)^2) lookups per query instead of O(len(list)).
    """

    def __init__(self, names: list[str]):
        self.norm = [normalize_name(n) for n in names]
        self.exact: dict[str, list[int]] = {}
        self.first_last: dict[tuple[str, str], list[int]] = {}
        self.starts: list[int] = []
        pos = 0
        for i, b in enumerate(self.norm):
            self.starts.append(pos)
            pos += len(b) + 1
            if not b:
                continue
            self.exact.setdefault(b, []).append(i)
            words = [w for w in b.split(" ") if w]
            if len(words) >= 2:
                self.first_last.setdefault((words[0], words[-1]), []).append(i)
        self.blob = "\x00".join(self.norm)

    def candidates(self, name: str | None) -> list[int]:
        a = normalize_name(name)
        if not a:
            return []
        found = set(self.exact.get(a, ()))
        words = [w for w in a.split(" ") if w]
        if len(words) >= 2:
            found.update(self.first_last.get((words[0], words[-1]), ()))
        if len(a) >= 4:
            start = self.blob.find(a)
            while start >= 0:  # names that contain `a`
                i = bisect.bisect_right(self.starts, start) - 1
                if len(self.norm[i]) >= 4:
                    found.add(i)
                start = self.blob.find(a, start + 1)
            for i0 in range(len(a)):  # names that are contained in `a`
                for j in range(i0 + 4, len(a) + 1):
                    for idx in self.exact.get(a[i0:j], ()):
                        found.add(idx)
        return sorted(found)


def _receipt_ids_in(text: str, rid_set: set[str], lengths: set[int]) -> set[str]:
    """Receipt ids that occur as substrings of text (ids are digits, so only digit runs can hold them)."""
    out: set[str] = set()
    for run in _DIGITS.findall(text or ""):
        for size in lengths:
            for k in range(len(run) - size + 1):
                piece = run[k:k + size]
                if piece in rid_set:
                    out.add(piece)
    return out


def _numbers_named(provider: str, order: dict, rid_set: set[str], lengths: set[int]) -> set[str]:
    """The receipts a print order names by number: Printify's shop_order_id and its line items' titles, Gelato's
    orderReferenceId («4100000001 - Emma»)."""
    if provider == "gelato":
        return _receipt_ids_in(str(order.get("orderReferenceId") or ""), rid_set, lengths)
    hits: set[str] = set()
    shop_order_id = (order.get("metadata") or {}).get("shop_order_id")
    if shop_order_id and str(shop_order_id) in rid_set:
        hits.add(str(shop_order_id))
    for li in order.get("line_items") or []:
        hits |= _receipt_ids_in(f"{(li.get('metadata') or {}).get('title') or ''} {li.get('title') or ''}",
                                rid_set, lengths)
    return hits


DAY_MS = 86_400_000
NAME_WINDOW_BEFORE = 1 * DAY_MS   # a print order made a day before its receipt still fits (clocks, time zones)
NAME_WINDOW_AFTER = 30 * DAY_MS   # ...and one made up to 30 days after it


def _in_window(order_time: float | None, receipt_time: float | None) -> bool:
    """A name alone is weak evidence: a repeat buyer's old print order must not be taken by her new receipt (2026-10-08).
    Unknown times don't exclude anything."""
    if order_time is None or receipt_time is None:
        return True
    return -NAME_WINDOW_BEFORE <= order_time - receipt_time <= NAME_WINDOW_AFTER


class _Printer:
    """One printer's orders as matching reads them: by the receipt number they name (the first order that names it,
    a live one before a cancelled one or a draft) and by the recipient's name."""

    def __init__(self, provider: str, orders: list[dict], rates: dict, reserved, rid_set: set[str]):
        self.orders = [order_facts(provider, o, rates) for o in orders]
        self.by_id = {f["id"]: f for f in self.orders}
        free = [f["key"] not in reserved for f in self.orders]
        lengths = {len(r) for r in rid_set}
        self.by_number: dict[str, dict] = {}
        for i in sorted(range(len(self.orders)), key=lambda i: bool(self.orders[i]["dead"])):
            if free[i]:
                for rid in _numbers_named(provider, self.orders[i]["order"], rid_set, lengths):
                    self.by_number.setdefault(rid, self.orders[i])
        self.names = _NameIndex([f["name"] for f in self.orders])
        self.times = [parse_time(f["created"]) for f in self.orders]
        self.free = free

    def by_name(self, name: str, created) -> dict | None:
        if len(name.strip()) < MIN_NAME:
            return None
        t = parse_time(created)
        found = [i for i in self.names.candidates(name) if self.free[i] and _in_window(self.times[i], t)]
        if not found:
            return None
        return self.orders[min(found, key=lambda i: (bool(self.orders[i]["dead"]), _distance(self.times[i], t)))]


def _find(eo: dict, rid: str, link: dict | None, printers: dict) -> tuple[dict | None, str]:
    """The receipt's print order and how it was found ("manual" / "auto"); (None, "none") for a receipt the owner
    said has none, (None, "unmatched") when nothing fits."""
    if link:
        if link.get("provider") == "none":
            return None, "none"
        printer = printers.get(link.get("provider"))
        manual = printer.by_id.get(str(link.get("orderId") or "")) if printer else None
        if manual:
            return manual, "manual"
    p, g = printers["printify"], printers["gelato"]
    name, created = eo.get("customer_shipping_name") or "", eo.get("created_at")
    found = p.by_number.get(rid) or g.by_number.get(rid) or p.by_name(name, created) or g.by_name(name, created)
    return (found, "auto") if found else (None, "unmatched")


def match(etsy_orders: list, printify_orders: list, gelato_orders: list, links: dict, rates: dict | None = None,
          reserved: frozenset | set = frozenset(), sent: dict | None = None) -> list:
    """One row per receipt: its Etsy money and the print order found for it, with the cost and profit the Profit
    Calculator shows (the whole order's cost, split between the receipts of a bundle). `sent` — the print orders
    this program sent for each receipt (profit.load_sends()): the row lists them as `sent_orders`, for the money
    step to count the ones besides the matched one."""
    rates = current_rates() if rates is None else rates
    rid_set = {str(eo["receipt_id"]) for eo in etsy_orders}
    printers = {provider: _Printer(provider, orders, rates, reserved, rid_set)
                for provider, orders in (("printify", printify_orders), ("gelato", gelato_orders))}
    found = {}
    users: dict[str, list[str]] = {}
    for eo in etsy_orders:
        rid = str(eo["receipt_id"])
        f, how = _find(eo, rid, links.get(rid), printers)
        found[rid] = (f, how)
        if f:
            users.setdefault(f["key"], []).append(rid)
    rows = []
    for eo in etsy_orders:
        rid = str(eo["receipt_id"])
        f, how = found[rid]
        row = _row(eo, rid, how)
        if f:
            row.update(_order_part(f, how, len(users[f["key"]]), row["etsy_net"]))
        row["sent_orders"] = [(str(r.get("provider")), str(r.get("orderId"))) for r in (sent or {}).get(rid) or []]
        row["cover_label"] = cover_label(row["items"])
        rows.append(row)
    return rows


def _row(eo: dict, rid: str, how: str) -> dict:
    return {
        "id": rid,
        "etsy_receipt_id": rid,
        "customer_name": eo.get("customer_shipping_name") or "",
        "created_at": eo.get("created_at"),
        "status": eo.get("status"),
        "is_shipped": eo.get("is_shipped"),
        "etsy_gross": eo.get("etsy_gross"),
        "etsy_fees": eo.get("etsy_fees"),
        "etsy_net": eo.get("etsy_net") or 0.0,
        "fee_breakdown": eo.get("fee_breakdown"),
        "items": eo.get("items") or [],
        "shipping_address": eo.get("shipping_address") or {},
        "link_blocked": how == "none",
        "match_type": "unmatched" if how in ("none", "unmatched") else how,
        "pod_provider": None,
        "pod_total_cost": 0,
        "printify_production_cost": 0,
        "printify_shipping_cost": 0,
        "printify_total_cost": 0,
        "profit": None,
        "profit_margin": None,
        "is_bundle": False,
        "bundle_count": None,
    }


def _order_part(f: dict, how: str, bundle: int, net: float) -> dict:
    """The matched order's part of a row, split between the receipts of a bundle."""
    cost = None if f["cost"] is None else r2(f["cost"] / bundle)
    profit = None if cost is None else r2(net - cost)
    part = {
        "match_type": how,
        "pod_provider": f["provider"],
        "pod_total_cost": cost or 0,
        "printify_total_cost": cost or 0,
        "profit": profit,
        "profit_margin": (r1(profit / net * 100) if net > 0 else 0) if profit is not None else None,
        "is_bundle": bundle > 1,
        "bundle_count": bundle if bundle > 1 else None,
    }
    if f["provider"] == "printify":
        part.update({"printify_order_id": f["id"], "app_order_id": f["id"][-6:].upper(),
                     "matched_printify_recipient": f["name"],
                     "printify_production_cost": r2(f["prod"] / bundle),
                     "printify_shipping_cost": r2(f["ship"] / bundle)})
    else:
        part.update({"gelato_order_id": f["id"], "gelato_order_reference": f["order"].get("orderReferenceId"),
                     "matched_gelato_recipient": f["name"], "gelato_cost": r2(f["raw_cost"] / bundle),
                     "gelato_currency": f["currency"], "gelato_status": f["status"],
                     "cost_unknown": f["cost"] is None})
    return part


def printify_only_rows(printify_orders: list) -> list:
    """Printify orders shown on their own while Etsy is not connected (no profit)."""
    rows = []
    for p in printify_orders:
        addr = p.get("address_to") or {}
        name = _SPACES.sub(" ", f"{addr.get('first_name') or ''} {addr.get('last_name') or ''}").strip() or "Без імені"
        prod_c = sum(num(li.get("cost")) * (num(li.get("quantity")) or 1) for li in (p.get("line_items") or []))
        ship_c, tax_c = num(p.get("total_shipping")), num(p.get("total_tax"))
        rows.append({
            "id": str(p.get("id")),
            "customer_name": name,
            "created_at": p.get("created_at"),
            "match_type": "printify_only",
            "pod_provider": "printify",
            "printify_order_id": str(p.get("id")),
            "app_order_id": p.get("app_order_id") or str(p.get("id")),
            "printify_production_cost": js_round(prod_c) / 100,
            "printify_shipping_cost": js_round(ship_c) / 100,
            "printify_total_cost": js_round(prod_c + ship_c + tax_c) / 100,
            "pod_total_cost": js_round(prod_c + ship_c + tax_c) / 100,
            "items": [],
            "profit": None,
            "profit_margin": None,
            "cover_label": "Книга",
        })
    return rows
