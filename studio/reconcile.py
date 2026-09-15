"""Matching Etsy receipts with Printify / Gelato orders and allocating cost.

Same rules as Etsy Profit Calculator:
 1. manual links set by the operator;
 2. Printify: receipt number in metadata.shop_order_id or in a line-item title;
 3. Printify: shipping-recipient name (closest order in time when several);
 4. Gelato: receipt number in orderReferenceId, then recipient name;
 5. one provider order shared by several receipts = bundle, cost split equally.

Additions: cancelled provider orders and Gelato drafts are only used when no live order
fits, and orders the operator marked as a replacement reprint are never auto-matched.
"""
from __future__ import annotations

import bisect
import math
import re
from datetime import datetime, timezone

from .fees import r1, r2

_STRIP = re.compile(r"[^\w\s]|_", re.UNICODE)
_SPACES = re.compile(r"\s+")


def _js_round(value: float) -> float:
    """JavaScript Math.round for plain numbers."""
    return math.floor(value + 0.5)


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


def gelato_cost_to_usd(cost: float, currency: str | None, eur_rate: float) -> float:
    if not cost:
        return 0.0
    cur = (currency or "USD").upper()
    if cur == "EUR":
        return r2(cost * eur_rate)
    return cost


def _num(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return 0.0


def _full_name(first: str | None, last: str | None) -> str:
    return f"{first or ''} {last or ''}".strip()


def cover_label(items: list, gelato_reference: str | None = None) -> str:
    """Hardcover / Softcover label from Etsy variations, SKU or title."""
    if not items:
        return "Книга"
    details: list[tuple[str, int]] = []
    for item in items:
        fmt = "unknown"
        for v in item.get("variations") or []:
            combined = f"{v.get('name') or ''} {v.get('value') or ''}".lower()
            if any(k in combined for k in ("hardcover", "hard cover", "hardback", "тверд")):
                fmt = "hardcover"
                break
            if any(k in combined for k in ("softcover", "soft cover", "paperback", "м'як")):
                fmt = "softcover"
                break
        sku = (item.get("sku") or "").lower()
        if fmt == "unknown" and sku:
            if "hard" in sku or "-hc" in sku or sku.startswith("hc") or "_hc" in sku:
                fmt = "hardcover"
            elif "soft" in sku or "-sc" in sku or sku.startswith("sc") or "_sc" in sku or "pb" in sku:
                fmt = "softcover"
        title = (item.get("title") or "").lower()
        if fmt == "unknown" and title:
            if any(k in title for k in ("hardcover", "hard cover", "hardback", "тверд")):
                fmt = "hardcover"
            elif any(k in title for k in ("softcover", "soft cover", "paperback", "м'як")):
                fmt = "softcover"
        details.append((fmt, int(item.get("quantity") or 1)))

    if all(f == "unknown" for f, _ in details):
        ref = (gelato_reference or "").lower()
        if "hard" in ref or "hc" in ref:
            return "Hardcover книга"
        if "soft" in ref or "sc" in ref:
            return "Softcover книга"

    hard = sum(q for f, q in details if f == "hardcover")
    soft = sum(q for f, q in details if f == "softcover")
    if hard and soft:
        return f"{f'{hard}x ' if hard > 1 else ''}Hardcover + {f'{soft}x ' if soft > 1 else ''}Softcover книга"
    if hard:
        return f"{f'{hard}x ' if hard > 1 else ''}Hardcover книга"
    if soft:
        return f"{f'{soft}x ' if soft > 1 else ''}Softcover книга"
    return items[0].get("title") or "Книга"


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


_DIGITS = re.compile(r"\d+")


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


def _p_dead(p: dict) -> bool:
    return str(p.get("status") or "").lower() in ("canceled", "cancelled")


def _g_dead(g: dict) -> bool:
    return (str(g.get("fulfillmentStatus") or "").lower() in ("canceled", "cancelled")
            or str(g.get("orderType") or "").lower() == "draft")


def match(etsy_orders: list, printify_orders: list, gelato_orders: list, links: dict, eur_rate: float = 1.085,
          reserved: frozenset | set = frozenset()) -> list:
    printify_by_id = {str(p.get("id")): p for p in printify_orders}
    gelato_by_id = {str(g.get("id")): g for g in gelato_orders}
    p_free = [f"printify:{p.get('id')}" not in reserved for p in printify_orders]
    g_free = [f"gelato:{g.get('id')}" not in reserved for g in gelato_orders]
    rid_set = {str(eo["receipt_id"]) for eo in etsy_orders}
    rid_lengths = {len(r) for r in rid_set}

    p_to_etsy: dict[str, list[str]] = {}
    etsy_to_p: dict[str, dict] = {}
    etsy_p_type: dict[str, str] = {}
    g_to_etsy: dict[str, list[str]] = {}
    etsy_to_g: dict[str, dict] = {}
    etsy_g_type: dict[str, str] = {}
    blocked: set[str] = set()

    def bind_p(rid: str, p: dict, kind: str) -> None:
        etsy_to_p[rid] = p
        etsy_p_type[rid] = kind
        bucket = p_to_etsy.setdefault(str(p["id"]), [])
        if rid not in bucket:
            bucket.append(rid)

    def bind_g(rid: str, g: dict, kind: str) -> None:
        etsy_to_g[rid] = g
        etsy_g_type[rid] = kind
        bucket = g_to_etsy.setdefault(str(g["id"]), [])
        if rid not in bucket:
            bucket.append(rid)

    def done(rid: str) -> bool:
        return rid in etsy_to_p or rid in etsy_to_g or rid in blocked

    # 1. manual links
    for eo in etsy_orders:
        rid = str(eo["receipt_id"])
        link = links.get(rid)
        if not link:
            continue
        provider, order_id = link.get("provider"), str(link.get("orderId") or "")
        if provider == "none":
            blocked.add(rid)
        elif provider == "printify" and order_id in printify_by_id:
            bind_p(rid, printify_by_id[order_id], "manual")
        elif provider == "gelato" and order_id in gelato_by_id:
            bind_g(rid, gelato_by_id[order_id], "manual")

    # 2. Printify: receipt number in shop_order_id or line-item titles (first order in Printify's list wins,
    #    live orders before cancelled ones)
    for pi in sorted(range(len(printify_orders)), key=lambda i: _p_dead(printify_orders[i])):
        if not p_free[pi]:
            continue
        p = printify_orders[pi]
        hits: set[str] = set()
        shop_order_id = (p.get("metadata") or {}).get("shop_order_id")
        if shop_order_id and str(shop_order_id) in rid_set:
            hits.add(str(shop_order_id))
        for li in p.get("line_items") or []:
            text = f"{(li.get('metadata') or {}).get('title') or ''} {li.get('title') or ''}"
            hits |= _receipt_ids_in(text, rid_set, rid_lengths)
        for rid in hits:
            if not done(rid):
                bind_p(rid, p, "auto")

    # 3. Printify: recipient name (closest order in time when several)
    p_names = _NameIndex([_full_name((p.get("address_to") or {}).get("first_name"),
                                     (p.get("address_to") or {}).get("last_name")) for p in printify_orders])
    p_times = [parse_time(p.get("created_at")) for p in printify_orders]
    for eo in etsy_orders:
        rid = str(eo["receipt_id"])
        if done(rid):
            continue
        name = eo.get("customer_shipping_name") or ""
        if len(name.strip()) < 3:
            continue
        idx = [i for i in p_names.candidates(name) if p_free[i]]
        if idx:
            t = parse_time(eo.get("created_at"))
            idx.sort(key=lambda i: (_p_dead(printify_orders[i]), _distance(p_times[i], t)))
            bind_p(rid, printify_orders[idx[0]], "auto")

    # 4. Gelato: receipt number in orderReferenceId, then recipient name
    first_ref: dict[str, int] = {}
    for gi in sorted(range(len(gelato_orders)), key=lambda i: _g_dead(gelato_orders[i])):
        g = gelato_orders[gi]
        if g.get("orderReferenceId") and g_free[gi]:
            for rid in _receipt_ids_in(str(g["orderReferenceId"]), rid_set, rid_lengths):
                first_ref.setdefault(rid, gi)
    g_names = _NameIndex([_full_name(g.get("firstName"), g.get("lastName")) for g in gelato_orders])
    g_times = [parse_time(g.get("createdAt")) for g in gelato_orders]
    for eo in etsy_orders:
        rid = str(eo["receipt_id"])
        if done(rid):
            continue
        if rid in first_ref:
            bind_g(rid, gelato_orders[first_ref[rid]], "auto")
            continue
        name = eo.get("customer_shipping_name") or ""
        if name and len(name.strip()) > 2:
            idx = [i for i in g_names.candidates(name) if g_free[i]]
            if idx:
                t = parse_time(eo.get("created_at"))
                idx.sort(key=lambda i: (_g_dead(gelato_orders[i]), _distance(g_times[i], t)))
                bind_g(rid, gelato_orders[idx[0]], "auto")

    # 5. results with fair cost allocation
    rows = []
    for eo in etsy_orders:
        rid = str(eo["receipt_id"])
        net = eo.get("etsy_net") or 0.0
        row = {
            "id": rid,
            "etsy_receipt_id": rid,
            "customer_name": eo.get("customer_shipping_name") or "",
            "created_at": eo.get("created_at"),
            "status": eo.get("status"),
            "is_shipped": eo.get("is_shipped"),
            "etsy_gross": eo.get("etsy_gross"),
            "etsy_fees": eo.get("etsy_fees"),
            "etsy_net": net,
            "etsy_currency": eo.get("currency") or "USD",
            "is_net_estimated": eo.get("is_net_estimated", False),
            "fee_breakdown": eo.get("fee_breakdown"),
            "items": eo.get("items") or [],
            "shipping_address": eo.get("shipping_address") or {},
            "link_blocked": rid in blocked,
        }
        if rid in etsy_to_p:
            p = etsy_to_p[rid]
            bundle = len(p_to_etsy.get(str(p["id"]), [rid])) or 1
            prod_c, ship_c, tax_c = _num(p.get("total_price")), _num(p.get("total_shipping")), _num(p.get("total_tax"))
            full_cost = _js_round(prod_c + ship_c + tax_c) / 100
            alloc_prod = r2(prod_c / 100 / bundle)
            alloc_ship = r2(ship_c / 100 / bundle)
            alloc_cost = r2(full_cost / bundle)
            profit = r2(net - alloc_cost)
            addr = p.get("address_to") or {}
            row.update({
                "match_type": etsy_p_type.get(rid, "auto"),
                "pod_provider": "printify",
                "pod_total_cost": alloc_cost,
                "printify_order_id": str(p["id"]),
                "app_order_id": str(p["id"])[-6:].upper(),
                "printify_app_order_id": p.get("app_order_id"),
                "printify_status": p.get("status"),
                "matched_printify_recipient": _full_name(addr.get("first_name"), addr.get("last_name")),
                "printify_production_cost": alloc_prod,
                "printify_shipping_cost": alloc_ship,
                "printify_total_cost": alloc_cost,
                "profit": profit,
                "profit_margin": r1(profit / net * 100) if net > 0 else 0,
                "is_bundle": bundle > 1,
                "bundle_count": bundle if bundle > 1 else None,
            })
        elif rid in etsy_to_g:
            g = etsy_to_g[rid]
            bundle = len(g_to_etsy.get(str(g["id"]), [rid])) or 1
            raw_cost = _num(g.get("totalInclVat"))
            full_usd = gelato_cost_to_usd(raw_cost, g.get("currency"), eur_rate)
            alloc_usd = r2(full_usd / bundle)
            profit = r2(net - alloc_usd)
            row.update({
                "match_type": etsy_g_type.get(rid, "auto"),
                "pod_provider": "gelato",
                "pod_total_cost": alloc_usd,
                "gelato_order_id": str(g["id"]),
                "gelato_order_reference": g.get("orderReferenceId"),
                "matched_gelato_recipient": _full_name(g.get("firstName"), g.get("lastName")),
                "gelato_cost": r2(raw_cost / bundle),
                "gelato_currency": g.get("currency"),
                "gelato_status": g.get("fulfillmentStatus"),
                "printify_production_cost": 0,
                "printify_shipping_cost": 0,
                "printify_total_cost": alloc_usd,
                "profit": profit,
                "profit_margin": r1(profit / net * 100) if net > 0 else 0,
                "is_bundle": bundle > 1,
                "bundle_count": bundle if bundle > 1 else None,
            })
        else:
            row.update({
                "match_type": "unmatched",
                "pod_provider": None,
                "pod_total_cost": 0,
                "printify_production_cost": 0,
                "printify_shipping_cost": 0,
                "printify_total_cost": 0,
                "profit": None,
                "profit_margin": None,
                "is_bundle": False,
                "bundle_count": None,
            })
        row["cover_label"] = cover_label(row["items"], row.get("gelato_order_reference"))
        rows.append(row)
    return rows


def printify_only_rows(printify_orders: list) -> list:
    """Printify orders shown on their own while Etsy is not connected (no profit)."""
    rows = []
    for p in printify_orders:
        addr = p.get("address_to") or {}
        name = _SPACES.sub(" ", _full_name(addr.get("first_name"), addr.get("last_name"))).strip() or "Без імені"
        prod_c = sum(_num(li.get("cost")) * (_num(li.get("quantity")) or 1) for li in (p.get("line_items") or []))
        ship_c, tax_c = _num(p.get("total_shipping")), _num(p.get("total_tax"))
        rows.append({
            "id": str(p.get("id")),
            "customer_name": name,
            "created_at": p.get("created_at"),
            "match_type": "printify_only",
            "pod_provider": "printify",
            "printify_order_id": str(p.get("id")),
            "app_order_id": p.get("app_order_id") or str(p.get("id")),
            "printify_status": p.get("status"),
            "printify_production_cost": _js_round(prod_c) / 100,
            "printify_shipping_cost": _js_round(ship_c) / 100,
            "printify_tax_cost": _js_round(tax_c) / 100,
            "printify_total_cost": _js_round(prod_c + ship_c + tax_c) / 100,
            "pod_total_cost": _js_round(prod_c + ship_c + tax_c) / 100,
            "items": [],
            "profit": None,
            "profit_margin": None,
            "cover_label": "Книга",
        })
    return rows
