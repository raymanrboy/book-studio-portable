"""Safe Gelato API client.

Reads: product catalog, cover dimensions, single orders, order search (POST used
as a query). The only write is creating an order whose orderType is forced to
"draft" — a draft never goes to production until confirmed in Gelato by hand.

Two accounts during the move to the owner's own one (27.09.2026, gelato_accounts.py): "main" — the key everything
is done with; "old" — the account before the switch, only read (its orders, their tracking) until they are done.
"""
from __future__ import annotations

import hashlib
import threading
import time
from typing import Any

from . import core, httpc, printorders
from .server import ApiError, Request, route
from .vault import vault

ORDER_API = "https://order.gelatoapis.com/v4"
PRODUCT_API = "https://product.gelatoapis.com/v3"
_FORBIDDEN = ("cancel", "publish", "production", "confirm", ":convert", "patch")


def _audit_log():
    return httpc.audit_log("studio.gelato", "gelato.log")


class GelatoError(ApiError):
    pass


KEYS = {"main": "gelato_api_key", "old": "gelato_old_api_key"}  # the vault's names; the old one only reads
OLD_NAME = "Gelato (старий акаунт)"


def api_key(account: str = "main") -> str:
    value = vault.get(KEYS[account])
    if not value:
        if account == "old":
            raise GelatoError("Ключа старого акаунта Gelato немає.", 400, {"code": "gelato_key"})
        raise GelatoError("API-ключ Gelato не налаштовано. Відкрийте Налаштування → Gelato.", 400,
                          {"code": "gelato_key"})
    return value


def account_id(key: str) -> str:
    """Which account an order came from, told by its key without keeping the key (a hash, never reversible)."""
    return hashlib.sha256(key.encode()).hexdigest()[:12]


def accounts() -> list[tuple[str, str]]:
    """(slot, account id) of every Gelato account the program has a key for, the main one first."""
    return [(slot, account_id(key)) for slot, name in KEYS.items() if (key := vault.get(name))]


def untagged_account() -> str | None:
    """The account of an order kept from before orders carried theirs: the one read before the first switch, else
    the main one."""
    first = core.settings.section("gelato").get("firstAccount")
    key = vault.get(KEYS["main"])
    return first or (account_id(key) if key else None)


def _allowed(method: str, url: str, body: Any, account: str = "main") -> bool:
    lowered = url.lower()
    if any(word in lowered for word in _FORBIDDEN):
        return False
    if method == "GET":
        return url.startswith(PRODUCT_API + "/") or url.startswith(ORDER_API + "/orders/")
    if method == "POST":
        if url == f"{ORDER_API}/orders:search":
            return True
        if url == f"{ORDER_API}/orders":  # the old account never gets anything new
            return account == "main" and isinstance(body, dict) and body.get("orderType") == "draft"
    return False


def _human(err: httpc.HttpError, action: str) -> GelatoError:
    return GelatoError(*httpc.human(err, "Gelato", action, "API-ключ", "gelato_key"))


def call(method: str, url: str, body: Any = None, action: str = "Запит до Gelato", timeout: float = 60,
         retries: int = 3, idempotent: bool | None = None, account: str = "main", key: str | None = None) -> Any:
    """`account` picks the key ("old" only reads); `key` — a new key checked before it is stored (reads only)."""
    method = method.upper()
    if not _allowed(method, url, body, "old" if key else account):
        _audit_log().error("BLOCKED %s %s (%s)", method, url, account)
        raise GelatoError(f"Заблоковано з міркувань безпеки: {method} {url}", 403)
    _audit_log().info("%s %s%s", method, url, " (new key)" if key else "" if account == "main" else " (old)")
    try:
        return httpc.request_json(method, url, headers={"X-API-KEY": key or api_key(account)}, json_body=body,
                                  timeout=timeout, retries=retries, idempotent=idempotent)
    except httpc.HttpError as err:
        _audit_log().warning("%s %s -> %s %s", method, url, err.status, httpc.short_body(err.body, 300))
        raise _human(err, action) from None


def search_orders(offset: int = 0, limit: int = 100, account: str = "main", key: str | None = None) -> list:
    # Drafts are asked for by name: a draft made from Book Studio moves its receipt to "in work".
    body = {"limit": limit, "offset": offset, "orderTypes": ["order", "draft"]}
    data = call("POST", f"{ORDER_API}/orders:search", body, action="Замовлення Gelato", idempotent=True,  # a query
                account=account, key=key)
    return list((data or {}).get("orders") or [])


def check_key(key: str) -> None:
    """Reads one order with a key not stored yet: a mistyped or foreign key is told before anything changes."""
    search_orders(0, 1, key=key)


def all_orders(progress=None, cap: int = 5000, account: str = "main") -> httpc.Listing:
    """Every order and draft, newest first; a list that stopped at `cap` says so (Listing.complete)."""
    orders = httpc.Listing()
    offset = 0
    while True:
        if offset >= cap:
            orders.complete = False
            core.log.warning("Gelato orders: stopped at %s — older orders are not loaded", cap)
            break
        batch = search_orders(offset, account=account)
        orders.extend(batch)
        offset += len(batch)
        if progress:
            progress(len(orders))
        if len(batch) < 100:
            break
    orders.sort(key=lambda g: g.get("createdAt") or "", reverse=True)
    return orders


def slim_order(g: dict, account: str | None = None) -> dict:
    """An order as the snapshot keeps it; `account` — the id of the account it was read from (account_id())."""
    out = {k: g.get(k) for k in ("id", "orderReferenceId", "firstName", "lastName", "totalInclVat", "currency",
                                 "fulfillmentStatus", "financialStatus", "createdAt", "orderType")}
    if account:
        out["account"] = account
    return out


_products: dict = {}
_geometry: dict = {}
CATALOG_HOURS = 6  # the catalogue is read again after this long, or at once with another API key
_catalog = {"since": time.monotonic(), "key": None}


def _fresh_catalog() -> None:
    """What Gelato's catalogue said is kept for a few hours, not for the whole run: Gelato may change a
    product's page counts or sizes, and another key may see other products (22.09.2026 audit)."""
    key = hashlib.sha256((vault.get("gelato_api_key") or "").encode()).hexdigest()  # which key, not the key
    if time.monotonic() - _catalog["since"] > CATALOG_HOURS * 3600 or key != _catalog["key"]:
        _products.clear()
        _geometry.clear()
        _catalog.update(since=time.monotonic(), key=key)


def product(product_uid: str) -> dict:
    """One product's catalog card (sizes, allowed page counts); read once in CATALOG_HOURS."""
    _fresh_catalog()
    if product_uid not in _products:
        _products[product_uid] = call("GET", f"{PRODUCT_API}/products/{product_uid}",
                                      action="Параметри продукту Gelato", timeout=20, retries=2) or {}
    return _products[product_uid]


def page_counts(product_uid: str) -> list[int]:
    """Inner page counts Gelato prints this product with (its catalog's validPageCounts)."""
    return sorted(int(n) for n in product(product_uid).get("validPageCounts") or [])


def photobook_geometry(product_uid: str, page_count: int) -> dict:
    """Physical sizes (mm) Gelato prints a photo book at, straight from its product catalog.

    coverMm   — the whole cover sheet (back + spine + front, with wrap or bleed);
    pageMm    — one inner page including bleed;
    marginMm  — how far the visible cover starts from the sheet edge (wrap for hardcover, bleed for softcover).
    """
    _fresh_catalog()
    key = (product_uid, int(page_count))
    if key in _geometry:
        return _geometry[key]
    valid = page_counts(product_uid)
    if valid and int(page_count) not in valid:
        raise GelatoError(f"Gelato не друкує цей формат на {page_count} сторінках "
                          f"(можна від {min(valid)} до {max(valid)}, парна кількість).", 400)
    dims = product(product_uid).get("dimensions") or {}

    def mm(name: str) -> float | None:
        try:
            return float((dims.get(name) or {}).get("value"))
        except (TypeError, ValueError):
            return None

    def with_bleed(name: str) -> float | None:
        value = mm(name)
        return value + 6 if value else None  # Gelato adds 3 mm bleed on every side of an inner page

    page_w = mm("Text block total width") or with_bleed("Width")
    page_h = mm("Text block total height") or with_bleed("Height")
    cover = call("GET", f"{PRODUCT_API}/products/{product_uid}/cover-dimensions?pageCount={int(page_count)}",
                 action="Розміри обкладинки Gelato") or {}
    areas = [v for v in cover.values() if isinstance(v, dict) and "width" in v and "height" in v]
    if not areas or not page_w or not page_h:
        raise GelatoError("Gelato не повернув розміри цього формату фотокниги.", 502)
    cover_w = max(float(a.get("left") or 0) + float(a["width"]) for a in areas)
    cover_h = max(float(a.get("top") or 0) + float(a["height"]) for a in areas)
    content = [a for k, a in cover.items() if k.startswith("content") and isinstance(a, dict)]
    margin = min((min(float(a.get("left") or 0), float(a.get("top") or 0)) for a in content), default=3.0)
    geo = {"coverMm": [round(cover_w, 2), round(cover_h, 2)], "pageMm": [round(page_w, 2), round(page_h, 2)],
           "marginMm": margin, "productPages": cover.get("pagesCount")}
    _geometry[key] = geo
    return geo


def create_draft_order(payload: dict) -> dict:
    safe = dict(payload)
    safe["orderType"] = "draft"  # enforced here regardless of the caller
    return call("POST", f"{ORDER_API}/orders", safe, action="Створення чернетки Gelato", timeout=120, retries=1)


def get_order(order_id: str, account: str = "main") -> dict:
    return call("GET", f"{ORDER_API}/orders/{order_id}", action="Статус замовлення Gelato", account=account)


TRACKING_READS = 60  # full orders read per sync at most; the rest wait for the next one


def shipments_of(order: dict) -> list:
    """Tracking of a full order: one entry per package, carrier = the shipment method ("UPS Surepost")."""
    ship = order.get("shipment") or {}
    method = ship.get("shipmentMethodName") or ""
    out = [{"carrier": method, "number": p.get("trackingCode"), "url": p.get("trackingUrl") or ""}
           for p in ship.get("packages") or [] if p.get("trackingCode")]
    if not out:  # some orders keep tracking only on their items
        for item in order.get("items") or []:
            for f in item.get("fulfillments") or []:
                code = f.get("trackingCode")
                if code and all(s["number"] != code for s in out):
                    out.append({"carrier": f.get("shipmentMethodName") or method, "number": code,
                                "url": f.get("trackingUrl") or ""})
    return out


def attach_shipments(orders: list, previous: list, account: str = "main") -> int:
    """Gives shipped orders (slim, from the search of one account) their tracking, which the search leaves out.

    Each shipped order is read in full once; again only while no tracking was found and its status
    changes. Tracking already found is carried over from the previous snapshot. Returns how many
    orders could not be read (they are tried again on the next sync).
    """
    from concurrent.futures import ThreadPoolExecutor

    before = {g.get("id"): g for g in previous or []}
    todo = []
    for g in orders:
        old = before.get(g.get("id")) or {}
        status = g.get("fulfillmentStatus")
        if old.get("shipments"):
            g["shipments"] = old["shipments"]
        elif str(status or "").lower() in printorders.GELATO_SHIPPED:
            if old.get("shipmentsFor") == status:
                g["shipments"], g["shipmentsFor"] = [], status
            else:
                todo.append(g)
    failed = []

    def read(g: dict) -> None:
        try:
            g["shipments"] = shipments_of(get_order(g["id"], account))
            g["shipmentsFor"] = g.get("fulfillmentStatus")
        except ApiError:
            failed.append(g["id"])

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(read, todo[:TRACKING_READS]))
    return len(failed)


def slot_of(order: dict) -> str:
    """Which key reads this order (slim, from the snapshot): "old" for an order of the old account, else "main"."""
    old = vault.get(KEYS["old"])
    tag = order.get("account") or untagged_account()
    return "old" if old and tag == account_id(old) else "main"


# What Gelato's own event log may call a time, a status and a text: the log's entries were empty in every draft
# the program ever read, so only the likely names are tried; the shape found is written to the audit log.
_EVENT_TIME = ("createdAt", "created", "timestamp", "time", "occurredAt", "date", "at", "updatedAt")
_EVENT_STATUS = ("fulfillmentStatus", "status", "toStatus", "newStatus", "event", "type", "name", "code")
_EVENT_TEXT = ("message", "comment", "description", "details", "reason", "text")
_MILESTONES = (("createdAt", "created"), ("orderedAt", "ordered"), ("shippedAt", "shipped"))  # on the order itself


def _first(entry: dict, names: tuple) -> str:
    for name in names:
        value = entry.get(name)
        if isinstance(value, (str, int, float)) and str(value).strip():
            return str(value).strip()
    return ""


def _moment(text: str) -> float:
    try:
        from datetime import datetime, timezone
        when = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return (when if when.tzinfo else when.replace(tzinfo=timezone.utc)).timestamp()
    except ValueError:
        return 0.0


def history(order: dict) -> dict:
    """What the order card's history shows, from a full order: the printer's status now, its events newest first
    (each `at`, `status`, `text`; Gelato's own event log of the items, plus the order's own dates for what the log
    lacks), the tracking, and when Gelato expects it delivered. Read only."""
    events: list[dict] = []
    shapes: set[str] = set()
    for item in order.get("items") or []:
        for entry in item.get("eventLog") or []:
            if not isinstance(entry, dict):
                entry = {"text": str(entry)}
            shapes.add(",".join(sorted(entry)))
            at, status = _first(entry, _EVENT_TIME), _first(entry, _EVENT_STATUS)
            text = _first(entry, _EVENT_TEXT)
            if text.lower() == status.lower():
                text = ""
            if (at or status or text) and {"at": at, "status": status, "text": text} not in events:
                events.append({"at": at, "status": status, "text": text})
    if shapes:  # field names only, never their values: they tell what to read next time without exposing a customer
        _audit_log().info("History: event log entries have %s", " | ".join(sorted(shapes)))
    seen = {e["status"].lower() for e in events}
    for field, status in _MILESTONES:
        at = order.get(field)
        if at and status not in seen:
            events.append({"at": str(at), "status": status, "text": ""})
    events.sort(key=lambda e: _moment(e["at"]), reverse=True)  # without a time — last, as they came
    ship = order.get("shipment") or {}
    due = [ship.get(k) for k in ("minDeliveryDate", "maxDeliveryDate") if ship.get(k)]
    return {"status": order.get("fulfillmentStatus") or "", "events": events, "shipments": shipments_of(order),
            "due": due}


_history: dict[str, tuple[float, dict]] = {}
_history_lock = threading.Lock()
HISTORY_FRESH = 60   # seconds a read is kept: leaving the card and coming back is not a new question to Gelato
HISTORY_DONE = {"delivered", "canceled", "returned"}  # nothing changes after these: kept until the program closes


def cached_history(order_id: str, account: str = "main", fresh: bool = False) -> dict:
    """The history of one order, read from Gelato when the card is opened (never in bulk, never at launch)."""
    with _history_lock:
        kept = _history.get(order_id)
    if kept and not fresh and (kept[1]["status"] in HISTORY_DONE or time.monotonic() - kept[0] < HISTORY_FRESH):
        return kept[1]
    data = history(get_order(order_id, account))
    with _history_lock:
        if len(_history) > 300:
            _history.clear()
        _history[order_id] = (time.monotonic(), data)
    return data


@route("POST", "/api/gelato/test")
def _test(req: Request):
    account = "old" if (req.json or {}).get("account") == "old" else "main"
    orders = all_orders(cap=3000, account=account)
    return {"ok": True, "ordersCount": len(orders),
            "message": f"З'єднання успішне! Знайдено {len(orders)} замовлень у "
                       + ("старому акаунті Gelato." if account == "old" else "кабінеті Gelato.")}
