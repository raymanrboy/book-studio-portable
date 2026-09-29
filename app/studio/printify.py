"""Safe Printify API client.

Allowed writes are exactly three: image upload, a new (unpublished) product, and — only through
create_order_on_hold() — an order that Printify keeps "On hold": it is produced and charged only when
"Submit order" is pressed in Printify (the store's order approval must be Manual, which the user
confirms once in the app). Sending to production, cancelling, Express orders, publishing, product
updates and deletes are blocked by an allowlist.

From 1 October 2026 nothing is written at all: every new book goes to Gelato (retired()).
"""
from __future__ import annotations

import base64
import json
import re
import threading
from datetime import date
from pathlib import Path
from typing import Any

from . import core, httpc
from .server import ApiError, Request, route
from .vault import vault

API = "https://api.printify.com/v1"

_READ = [
    re.compile(r"^shops\.json$"),
    re.compile(r"^shops/\d+/products\.json$"),
    re.compile(r"^shops/\d+/products/[0-9a-f]+\.json$"),
    re.compile(r"^shops/\d+/orders\.json$"),
    re.compile(r"^uploads/[0-9a-f]+\.json$"),
    re.compile(r"^catalog/[\w/.-]+\.json$"),
]
_WRITE = [
    re.compile(r"^uploads/images\.json$"),
    re.compile(r"^shops/\d+/products\.json$"),
]


def _audit_log():
    return httpc.audit_log("studio.printify", "printify.log")


class PrintifySecurityError(ApiError):
    pass


class PrintifyError(ApiError):
    pass


def token() -> str:
    value = vault.get("printify_token")
    if not value:
        raise PrintifyError("Printify токен не налаштовано. Відкрийте Налаштування → Printify.", 400,
                            {"code": "printify_token"})
    return value


_ORDER = re.compile(r"^shops/\d+/orders\.json$")
# From 1 October 2026 every new book is printed by Gelato, on the owner's own account (owner, 29.09.2026). Printify is
# only read: its earlier orders keep their stage, tracking, archive days and cost; nothing new is made there.
READ_ONLY_FROM = date(2026, 10, 1)
RETIRED_TEXT = "З 1 жовтня Printify лише для читання — нові книги друкує Gelato."


def retired(today: date | None = None) -> bool:
    """Whether Printify only reads now (from READ_ONLY_FROM on this computer's calendar)."""
    return (today or date.today()) >= READ_ONLY_FROM


def _check(method: str, path: str, order: bool = False) -> None:
    """order=True is passed only by create_order_on_hold(): the one way an order can be created."""
    if method != "GET" and retired():
        _audit_log().error("BLOCKED %s /%s (read only)", method, path)
        raise PrintifySecurityError(RETIRED_TEXT, 403)
    rules = _READ if method == "GET" else _WRITE if method == "POST" else []
    lowered = path.lower()
    forbidden = any(word in lowered for word in ("publish", "send_to_production", "unpublish", "cancel", "express"))
    on_hold_order = order and method == "POST" and bool(_ORDER.match(path))
    if forbidden or not (on_hold_order or any(r.match(path) for r in rules)) \
            or (method == "POST" and "orders" in lowered and not on_hold_order):
        _audit_log().error("BLOCKED %s /%s", method, path)
        raise PrintifySecurityError(f"Заблоковано з міркувань безпеки: {method} /{path}", 403)


def _human(err: httpc.HttpError, action: str) -> PrintifyError:
    return PrintifyError(*httpc.human(err, "Printify", action, "токен", "printify_token"))


def call(method: str, path: str, body: Any = None, action: str = "Запит до Printify", timeout: float = 60,
         retries: int = 3, params: str = "", order: bool = False) -> Any:
    method = method.upper()
    path = path.lstrip("/")
    _check(method, path, order)
    url = f"{API}/{path}{('?' + params) if params else ''}"
    _audit_log().info("%s /%s%s", method, path, f"?{params}" if params else "")
    try:
        encoded = {"json_bytes": body} if isinstance(body, bytes) else {"json_body": body}
        return httpc.request_json(method, url, headers={"Authorization": f"Bearer {token()}"},
                                  timeout=timeout, retries=retries, **encoded)
    except httpc.HttpError as err:
        _audit_log().warning("%s /%s -> %s %s", method, path, err.status, httpc.short_body(err.body, 300))
        raise _human(err, action) from None


# ---------------------------------------------------------------- read helpers

def shops() -> list:
    data = call("GET", "shops.json", action="Список магазинів Printify")
    return data if isinstance(data, list) else []


def products(shop_id: int, page: int = 1, limit: int = 50) -> dict:
    return call("GET", f"shops/{shop_id}/products.json", action="Список продуктів Printify",
                params=f"page={page}&limit={limit}")


def product(shop_id: int, product_id: str) -> dict:
    return call("GET", f"shops/{shop_id}/products/{product_id}.json", action="Читання продукту Printify")


def upload_exists(image_id: str) -> bool:
    try:
        data = call("GET", f"uploads/{image_id}.json", action="Перевірка зображення", retries=2)
        return bool(data.get("id"))
    except PrintifyError as err:
        if err.status == 404:
            return False
        raise


MAX_ORDER_PAGES = 400  # 50 orders each


def all_orders(shop_id: int, progress=None) -> httpc.Listing:
    """Every order of the shop; a shop with more than MAX_ORDER_PAGES pages is cut and says so (Listing.complete)."""
    from concurrent.futures import ThreadPoolExecutor

    first = call("GET", f"shops/{shop_id}/orders.json", action="Замовлення Printify", params="page=1&limit=50")
    orders = httpc.Listing(first.get("data") or [])
    last_page = int(first.get("last_page") or 1)
    if progress:
        progress(1, last_page)
    if last_page > MAX_ORDER_PAGES:
        orders.complete = False
        core.log.warning("Printify orders: %s pages, only the first %s are loaded", last_page, MAX_ORDER_PAGES)
    if last_page > 1:
        done = [1]
        lock = threading.Lock()

        def fetch(page: int) -> list:
            data = call("GET", f"shops/{shop_id}/orders.json", action="Замовлення Printify",
                        params=f"page={page}&limit=50")
            with lock:
                done[0] += 1
                if progress:
                    progress(done[0], last_page)
            return list(data.get("data") or [])

        with ThreadPoolExecutor(max_workers=4) as pool:
            for batch in pool.map(fetch, range(2, min(last_page, MAX_ORDER_PAGES) + 1)):
                orders.extend(batch)
    return orders


def slim_order(p: dict) -> dict:
    """Keeps only the fields used for reconciliation (smaller local snapshot)."""
    addr = p.get("address_to") or {}
    return {
        "id": p.get("id"),
        "app_order_id": p.get("app_order_id"),
        "total_price": p.get("total_price"),
        "total_shipping": p.get("total_shipping"),
        "total_tax": p.get("total_tax"),
        "created_at": p.get("created_at"),
        "status": p.get("status"),
        "metadata": {"shop_order_id": (p.get("metadata") or {}).get("shop_order_id")},
        # tracking once the print provider has shipped: carrier code ("usps"), number, link, and when the carrier
        # delivered it (printorders.shown_status())
        "shipments": [{k: s.get(k) for k in ("carrier", "number", "url", "delivered_at")}
                      for s in p.get("shipments") or [] if s.get("number")],
        "address_to": {k: addr.get(k) for k in ("first_name", "last_name", "country", "region", "city", "zip", "address1")},
        "line_items": [
            {"title": li.get("title"), "quantity": li.get("quantity"), "cost": li.get("cost"),
             "metadata": {"title": (li.get("metadata") or {}).get("title"), "sku": (li.get("metadata") or {}).get("sku")}}
            for li in (p.get("line_items") or [])
        ],
    }


# ---------------------------------------------------------------- write helpers

def upload_image(path: Path, file_name: str) -> dict:
    """One picture into Printify's media library, as JSON built straight in bytes: a 30 MB page used to be held about
    five times over (the file, base64 text, the JSON text, its bytes), three uploads at once."""
    contents = base64.b64encode(Path(path).read_bytes())
    body = b"".join((b'{"file_name": ', json.dumps(file_name).encode("utf-8"), b', "contents": "', contents, b'"}'))
    del contents
    # Tried again only when the upload certainly did not arrive (httpc): after a timeout Printify may
    # already keep the picture, and a second one would only clutter its media library.
    return call("POST", "uploads/images.json", body, action=f"Завантаження {file_name}", timeout=240, retries=3)


def create_product(shop_id: int, payload: dict) -> dict:
    # No automatic retry: a repeated POST after an unclear failure could duplicate the book.
    return call("POST", f"shops/{shop_id}/products.json", payload, action="Створення продукту", timeout=180, retries=1)


MANUAL_APPROVAL_NEEDED = "Спершу підтвердіть, що в Printify увімкнене ручне затвердження замовлень."


def manual_approval_confirmed() -> bool:
    return bool(core.settings.section("printify").get("manualApprovalConfirmedAt"))


def create_order_on_hold(shop_id: int, payload: dict) -> dict:
    """The only order Book Studio places. Printify keeps an API order "On hold" and, with Manual order
    approval, neither produces nor charges it until "Submit order" is pressed in Printify. Nothing here
    can send it on: send_to_production is blocked by the allowlist."""
    if not manual_approval_confirmed():
        raise PrintifySecurityError(MANUAL_APPROVAL_NEEDED, 403,
                                    {"code": "manual_approval"})
    safe = dict(payload)
    safe.update({"is_printify_express": False, "send_shipping_notification": False})
    # No automatic retry here either: a repeated POST could place the order twice.
    return call("POST", f"shops/{shop_id}/orders.json", safe, action="Створення чернетки замовлення", timeout=120,
                retries=1, order=True)


# ---------------------------------------------------------------- master analysis

def analyze_master(shop_id: int, product_id: str) -> dict:
    p = product(shop_id, product_id)
    areas = p.get("print_areas") or []
    if not areas:
        raise PrintifyError("У Master-продукту немає print areas.")
    area = areas[0]
    placements = {}
    for ph in area.get("placeholders") or []:
        imgs = ph.get("images") or []
        if not imgs:
            continue
        img = imgs[0]
        placements[ph.get("position")] = {k: img.get(k) for k in ("x", "y", "scale", "angle")}
    page_positions = sorted((k for k in placements if re.fullmatch(r"page_\d+", k)), key=lambda k: int(k[5:]))
    if "cover" not in placements or not page_positions:
        raise PrintifyError("Не вдалося визначити позиції cover / page_N у Master-продукту.")
    page_count = len(page_positions)
    if page_positions != [f"page_{i}" for i in range(1, page_count + 1)]:
        raise PrintifyError("Нумерація сторінок Master-продукту має пропуски — перевірте еталон.")
    sizes = {}
    for ph in area.get("placeholders") or []:
        imgs = ph.get("images") or []
        if imgs and imgs[0].get("width"):
            sizes[ph.get("position")] = [imgs[0].get("width"), imgs[0].get("height")]
    variants = [
        {"id": v.get("id"), "price": v.get("price"), "is_enabled": bool(v.get("is_enabled")), "title": v.get("title")}
        for v in (p.get("variants") or [])
    ]
    return {
        "productId": p.get("id"),
        "title": p.get("title"),
        "blueprintId": p.get("blueprint_id"),
        "printProviderId": p.get("print_provider_id"),
        "description": p.get("description") or "<p></p>",
        "background": area.get("background") or "#ffffff",
        "variants": variants,
        "printAreaVariantIds": area.get("variant_ids") or [v["id"] for v in variants],
        "placements": placements,
        "pageCount": page_count,
        "coverSize": sizes.get("cover"),
        "pageSize": sizes.get("page_1"),
        "analyzedAt": core.now_iso(),
        "updatedAt": p.get("updated_at"),
        "visible": p.get("visible"),
        "enabledVariants": [v["title"] for v in variants if v["is_enabled"]],
    }


# ---------------------------------------------------------------- routes

@route("POST", "/api/printify/test")
def _test(req: Request):
    shop_list = shops()
    if not shop_list:
        raise PrintifyError("У вашому акаунті Printify немає жодного магазину.")
    cfg = core.settings.section("printify")
    shop = next((s for s in shop_list if s.get("id") == cfg.get("shopId")), shop_list[0])
    orders = call("GET", f"shops/{shop['id']}/orders.json", action="Замовлення Printify", params="page=1&limit=1")
    return {"shopId": shop.get("id"), "shopTitle": shop.get("title"), "ordersCount": orders.get("total"),
            "shops": [{"id": s.get("id"), "title": s.get("title"), "channel": s.get("sales_channel")} for s in shop_list]}


@route("POST", "/api/printify/manual-approval")
def _manual_approval(req: Request):
    """The user confirms once that the Printify store approves orders manually (so an order from
    Book Studio waits "On hold" until they press Submit order themselves)."""
    core.settings.update({"printify": {"manualApprovalConfirmedAt": core.now_iso()}})
    return {"ok": True}


@route("GET", "/api/printify/shops")
def _shops(req: Request):
    return {"shops": [{"id": s.get("id"), "title": s.get("title"), "channel": s.get("sales_channel")} for s in shops()]}


@route("GET", "/api/printify/products")
def _products(req: Request):
    shop_id = req.int_param("shop", int(core.settings.section("printify").get("shopId") or 0))
    page = req.int_param("page", 1, 1)
    data = products(shop_id, page)
    items = [{
        "id": p.get("id"), "title": p.get("title"), "blueprintId": p.get("blueprint_id"),
        "providerId": p.get("print_provider_id"), "createdAt": p.get("created_at"),
        "image": next((i.get("src") for i in (p.get("images") or []) if i.get("is_default")), None)
        or ((p.get("images") or [{}])[0].get("src")),
    } for p in data.get("data") or []]
    return {"products": items, "page": data.get("current_page"), "lastPage": data.get("last_page")}


@route("POST", "/api/printify/master/analyze")
def _analyze(req: Request):
    body = req.json or {}
    shop_id = int(body.get("shopId") or core.settings.section("printify").get("shopId"))
    product_id = str(body.get("productId") or "").strip()
    m = re.search(r"([0-9a-f]{24})", product_id)
    if not m:
        raise PrintifyError("Вкажіть ID продукту Printify або посилання на нього.")
    analysis = analyze_master(shop_id, m.group(1))
    return analysis


@route("POST", "/api/printify/master/save")
def _save_master(req: Request):
    body = req.json or {}
    analysis = body.get("analysis") or {}
    shop_id = body.get("shopId")
    shop_title = body.get("shopTitle")
    if not analysis.get("productId") or not analysis.get("placements"):
        raise PrintifyError("Спочатку проаналізуйте Master-продукт.")
    master = {k: analysis.get(k) for k in (
        "productId", "title", "blueprintId", "printProviderId", "description", "background",
        "variants", "printAreaVariantIds", "placements", "analyzedAt")}
    patch: dict = {"master": master, "pageCount": analysis.get("pageCount") or 24}
    if analysis.get("coverSize"):
        patch["coverSize"] = analysis["coverSize"]
    if analysis.get("pageSize"):
        patch["pageSize"] = analysis["pageSize"]
    if shop_id:
        patch["shopId"] = int(shop_id)
        patch["shopTitle"] = shop_title
    cfg = core.settings.section("printify")
    cfg.update(patch)
    core.settings.replace_section("printify", cfg)
    return {"printify": cfg}
