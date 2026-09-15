"""Safe Gelato API client.

Reads: product catalog, cover dimensions, single orders, order search (POST used
as a query). The only write is creating an order whose orderType is forced to
"draft" — a draft never goes to production until confirmed in Gelato by hand.
"""
from __future__ import annotations

import logging
import threading
from logging.handlers import RotatingFileHandler
from typing import Any

from . import core, httpc
from .server import ApiError, Request, route
from .vault import vault

ORDER_API = "https://order.gelatoapis.com/v4"
PRODUCT_API = "https://product.gelatoapis.com/v3"
_FORBIDDEN = ("cancel", "publish", "production", "confirm", ":convert", "patch")

audit = logging.getLogger("studio.gelato")
_audit_ready = threading.Lock()


def _audit_log() -> logging.Logger:
    with _audit_ready:
        if not audit.handlers:
            core.data_path("logs").mkdir(parents=True, exist_ok=True)
            h = RotatingFileHandler(core.data_path("logs", "gelato.log"), maxBytes=2_000_000, backupCount=3,
                                    encoding="utf-8")
            h.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
            audit.addHandler(h)
    return audit


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
    body = httpc.short_body(err.body)
    if err.status == 401:
        return GelatoError(f"{action}: API-ключ Gelato недійсний.", 400, {"code": "gelato_key"})
    if err.status == 403:
        return GelatoError(f"{action}: ключ Gelato не має прав для цієї дії.", 400, {"code": "gelato_key"})
    if err.status == 404:
        return GelatoError(f"{action}: Gelato не знайшов об'єкт (404).", 404)
    if err.status is None:
        return GelatoError(f"{action}: немає з'єднання з Gelato. Перевірте інтернет.", 502)
    if err.status == 400:
        return GelatoError(f"{action}: Gelato відхилив дані. {body}", 400)
    return GelatoError(f"{action}: помилка Gelato {err.status}. {body}", 502)


def call(method: str, url: str, body: Any = None, action: str = "Запит до Gelato", timeout: float = 60,
         retries: int = 3) -> Any:
    method = method.upper()
    if not _allowed(method, url, body):
        _audit_log().error("BLOCKED %s %s", method, url)
        raise GelatoError(f"Заблоковано з міркувань безпеки: {method} {url}", 403)
    _audit_log().info("%s %s", method, url)
    try:
        return httpc.request_json(method, url, headers={"X-API-KEY": api_key()}, json_body=body,
                                  timeout=timeout, retries=retries)
    except httpc.HttpError as err:
        _audit_log().warning("%s %s -> %s %s", method, url, err.status, httpc.short_body(err.body, 300))
        raise _human(err, action) from None


def search_orders(offset: int = 0, limit: int = 100) -> list:
    data = call("POST", f"{ORDER_API}/orders:search", {"limit": limit, "offset": offset}, action="Замовлення Gelato")
    return list((data or {}).get("orders") or [])


def all_orders(progress=None, cap: int = 5000) -> list:
    orders: list = []
    offset = 0
    while offset < cap:
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


def create_draft_order(payload: dict) -> dict:
    safe = dict(payload)
    safe["orderType"] = "draft"  # enforced here regardless of the caller
    return call("POST", f"{ORDER_API}/orders", safe, action="Створення чернетки Gelato", timeout=120, retries=1)


def get_order(order_id: str) -> dict:
    return call("GET", f"{ORDER_API}/orders/{order_id}", action="Статус замовлення Gelato")


@route("POST", "/api/gelato/test")
def _test(req: Request):
    orders = all_orders(cap=3000)
    return {"ok": True, "ordersCount": len(orders),
            "message": f"З'єднання успішне! Знайдено {len(orders)} замовлень у кабінеті Gelato."}
