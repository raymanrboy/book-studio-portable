"""Safe Gelato API client.

Reads: product catalog, cover dimensions, single orders, order search (POST used
as a query). The only write is creating an order whose orderType is forced to
"draft" — a draft never goes to production until confirmed in Gelato by hand.
"""
from __future__ import annotations

import hashlib
import time
from typing import Any

from . import core, httpc
from .server import ApiError, Request, route
from .vault import vault

ORDER_API = "https://order.gelatoapis.com/v4"
PRODUCT_API = "https://product.gelatoapis.com/v3"
_FORBIDDEN = ("cancel", "publish", "production", "confirm", ":convert", "patch")


def _audit_log():
    return httpc.audit_log("studio.gelato", "gelato.log")


class GelatoError(ApiError):
    pass


def api_key() -> str:
    value = vault.get("gelato_api_key")
    if not value:
        raise GelatoError("API-ключ Gelato не налаштовано. Відкрийте Налаштування → Gelato.", 400,
                          {"code": "gelato_key"})
    return value


def _allowed(method: str, url: str, body: Any) -> bool:
    lowered = url.lower()
    if any(word in lowered for word in _FORBIDDEN):
        return False
    if method == "GET":
        return url.startswith(PRODUCT_API + "/") or url.startswith(ORDER_API + "/orders/")
    if method == "POST":
        if url == f"{ORDER_API}/orders:search":
            return True
        if url == f"{ORDER_API}/orders":
            return isinstance(body, dict) and body.get("orderType") == "draft"
    return False


def _human(err: httpc.HttpError, action: str) -> GelatoError:
    return GelatoError(*httpc.human(err, "Gelato", action, "API-ключ", "gelato_key"))


def call(method: str, url: str, body: Any = None, action: str = "Запит до Gelato", timeout: float = 60,
         retries: int = 3, idempotent: bool | None = None) -> Any:
    method = method.upper()
    if not _allowed(method, url, body):
        _audit_log().error("BLOCKED %s %s", method, url)
        raise GelatoError(f"Заблоковано з міркувань безпеки: {method} {url}", 403)
    _audit_log().info("%s %s", method, url)
    try:
        return httpc.request_json(method, url, headers={"X-API-KEY": api_key()}, json_body=body,
                                  timeout=timeout, retries=retries, idempotent=idempotent)
    except httpc.HttpError as err:
        _audit_log().warning("%s %s -> %s %s", method, url, err.status, httpc.short_body(err.body, 300))
        raise _human(err, action) from None


def search_orders(offset: int = 0, limit: int = 100) -> list:
    # Drafts are asked for by name: a draft made from Book Studio moves its receipt to "in work".
    body = {"limit": limit, "offset": offset, "orderTypes": ["order", "draft"]}
    data = call("POST", f"{ORDER_API}/orders:search", body, action="Замовлення Gelato", idempotent=True)  # a query
    return list((data or {}).get("orders") or [])


def all_orders(progress=None, cap: int = 5000) -> httpc.Listing:
    """Every order and draft, newest first; a list that stopped at `cap` says so (Listing.complete)."""
    orders = httpc.Listing()
    offset = 0
    while True:
        if offset >= cap:
            orders.complete = False
            core.log.warning("Gelato orders: stopped at %s — older orders are not loaded", cap)
            break
        batch = search_orders(offset)
        orders.extend(batch)
        offset += len(batch)
        if progress:
            progress(len(orders))
        if len(batch) < 100:
            break
    orders.sort(key=lambda g: g.get("createdAt") or "", reverse=True)
    return orders


def slim_order(g: dict) -> dict:
    return {k: g.get(k) for k in ("id", "orderReferenceId", "firstName", "lastName", "totalInclVat", "currency",
                                  "fulfillmentStatus", "financialStatus", "createdAt", "orderType")}


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


def get_order(order_id: str) -> dict:
    return call("GET", f"{ORDER_API}/orders/{order_id}", action="Статус замовлення Gelato")


# Statuses of an order that has left the printer (https://dashboard.gelato.com/docs/orders/order_details/).
SHIPPED = ("shipped", "in_transit", "delivered", "returned")
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


def attach_shipments(orders: list, previous: list) -> int:
    """Gives shipped orders (slim, from the search) their tracking, which the search leaves out.

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
        elif str(status or "").lower() in SHIPPED:
            if old.get("shipmentsFor") == status:
                g["shipments"], g["shipmentsFor"] = [], status
            else:
                todo.append(g)
    failed = []

    def read(g: dict) -> None:
        try:
            g["shipments"] = shipments_of(get_order(g["id"]))
            g["shipmentsFor"] = g.get("fulfillmentStatus")
        except ApiError:
            failed.append(g["id"])

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(read, todo[:TRACKING_READS]))
    return len(failed)


@route("POST", "/api/gelato/test")
def _test(req: Request):
    orders = all_orders(cap=3000)
    return {"ok": True, "ordersCount": len(orders),
            "message": f"З'єднання успішне! Знайдено {len(orders)} замовлень у кабінеті Gelato."}
