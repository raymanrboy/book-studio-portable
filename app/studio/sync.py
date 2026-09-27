"""Pulling the orders: Etsy receipts (only the changed ones, a full re-read once a week), every Printify and Gelato
order — into the snapshot (records.SNAPSHOT), once at start-up and then only by the refresh button (the owner,
16.09.2026). After each sync the order archive looks at its books again."""
from __future__ import annotations

import html
import time
from datetime import datetime, timezone

from . import archive, core, etsy, gelato, printify, profit, records
from .fees import calculate_ukrainian_etsy_fees, money, r2
from .jobs import JobError, jobs
from .server import ApiError, Request, route
from .vault import vault

FULL_SYNC_EVERY = 7 * 86400   # a complete Etsy re-read once a week; otherwise only changed receipts
SYNC_OVERLAP = 3600           # re-read the last hour again so nothing slips between two syncs


def plain(value) -> str:
    """Etsy sends buyer-entered and listing text HTML-escaped (8&quot; × 8&quot;, Cover Type &amp; Size)."""
    return html.unescape(value) if isinstance(value, str) else ("" if value is None else str(value))


def normalize_receipt(r: dict) -> dict:
    """One Etsy receipt as the program keeps it: its money (the Ukrainian shop's fees), items, address and refunds,
    every text unescaped once, here."""
    fees = calculate_ukrainian_etsy_fees(r)
    items = []
    for t in r.get("transactions") or []:
        raw_vars = t.get("variations") or t.get("selected_variations")
        variations = None
        if isinstance(raw_vars, list):
            variations = [{
                "name": plain(v.get("formatted_name") or v.get("name") or v.get("property_name") or ""),
                "value": plain(v.get("formatted_value") or v.get("value") or v.get("value_name") or ""),
            } for v in raw_vars]
        items.append({
            "title": plain(t.get("title")) or "Товар без назви",
            "quantity": t.get("quantity") or 1,
            "price": money(t.get("price")),
            "variations": variations,
            "sku": t.get("sku") or "",
            "listing_id": t.get("listing_id"),
        })
    ts = r.get("create_timestamp") or r.get("created_timestamp") or 0
    created = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    grand = r.get("grandtotal") or {}
    refunds = [{
        "amount": money(rf.get("amount")),
        "at": rf.get("created_timestamp"),
        "reason": plain(rf.get("reason")),
        "note": plain(rf.get("note_from_issuer")),
        "status": rf.get("status") or "",
    } for rf in r.get("refunds") or [] if isinstance(rf, dict)]
    return {
        "receipt_id": str(r.get("receipt_id")),
        "created_at": created,
        "create_timestamp": ts,
        "customer_shipping_name": plain(r.get("name")) or "Анонімний замовник",
        "message_from_buyer": plain(r.get("message_from_buyer")),
        "shipping_address": {
            "name": plain(r.get("name")),
            "first_line": plain(r.get("first_line")),
            "second_line": plain(r.get("second_line")),
            "city": plain(r.get("city")),
            "state": plain(r.get("state")),
            "zip": plain(r.get("zip")),
            "country_iso": r.get("country_iso") or "",
        },
        "items": items,
        "status": r.get("status") or ("Completed" if r.get("is_shipped") else "Paid"),
        "is_shipped": bool(r.get("is_shipped")),
        "etsy_gross": fees["gross"],
        "etsy_fees": fees["total_etsy_fees"],
        "etsy_net": fees["net_payout"],
        "fee_breakdown": fees,
        "currency": grand.get("currency_code") or "USD",
        "refunds": refunds,
        "refund_total": r2(sum(x["amount"] for x in refunds)),
    }


def merge_receipts(old: list, changed: list) -> list:
    """Replaces changed receipts in place, adds new ones, newest first (same order as a full read)."""
    by_id = {r["receipt_id"]: r for r in old}
    for r in changed:
        by_id[r["receipt_id"]] = r
    return sorted(by_id.values(), key=lambda r: (r.get("create_timestamp") or 0, r["receipt_id"]), reverse=True)


# ---------------------------------------------------------------- one sync

def _loaded(snap: dict, warnings: list, source: str, items, name: str) -> None:
    """A list loaded whole notes when; a list cut at its cap says which part is missing, and keeps its old time: the
    archive must not read an order missing from it as a deleted draft."""
    if getattr(items, "complete", True):
        snap["loaded"][source] = core.now_iso()
    else:
        warnings.append(f"{name}: завантажено лише останні {len(items)} — старіші не видно.")


def _etsy_part(job, snap: dict, warnings: list, full: bool) -> int | None:
    """Only receipts changed since the last sync (new orders, cancellations, refunds, shipping); a complete re-read on
    request, on the first sync, with another shop and once a week. An Etsy failure fails the whole sync. Returns how
    many receipts changed (None after a full read)."""
    started = int(time.time())
    incremental = (not full and snap["receipts"] and snap["etsyCursor"] and snap["etsyFullAt"]
                   and started - int(snap["etsyFullAt"]) < FULL_SYNC_EVERY
                   and str(snap.get("shopId") or "") == str(etsy.tokens().get("shop_id") or snap.get("shopId") or ""))
    job.progress("Завантаження замовлень Etsy…", 5, "Лише змінені чеки" if incremental else "Усі чеки магазину")

    def on_receipts(done: int, total) -> None:
        job.progress(None, 5 + (40 * done / total if total else 20), f"Чеки Etsy: {done}" + (f" з {total}" if total else ""))

    since = int(snap["etsyCursor"]) - SYNC_OVERLAP if incremental else None
    raw, shop_id, shop_name = etsy.fetch_all_receipts(on_receipts, min_last_modified=since)
    fresh = [normalize_receipt(r) for r in raw]
    # Etsy pages by offset, newest first: an order placed while a full read runs shifts every later page by one, and
    # a receipt then comes twice — merged, each is kept once.
    snap["receipts"] = merge_receipts(snap["receipts"] if incremental else [], fresh)
    if not incremental:
        snap["etsyFullAt"] = started
    snap["etsyCursor"] = started
    snap["shopId"], snap["shopName"] = shop_id, shop_name
    _loaded(snap, warnings, "etsy", raw, "Etsy")
    return len(fresh) if incremental else None


def _printify_part(job, snap: dict, warnings: list) -> None:
    """Every Printify order of the shop (with tracking); a failure keeps the previous orders and says so."""
    job.progress("Завантаження замовлень Printify…", 48, "Собівартість друку та доставки")
    try:
        shop_id = core.settings.section("printify").get("shopId")
        shop_list = printify.shops()
        shop = next((s for s in shop_list if s.get("id") == shop_id), shop_list[0] if shop_list else None)
        if not shop:
            raise ApiError("У Printify немає магазинів.")
        raw = printify.all_orders(shop["id"], lambda d, t: job.progress(None, 48 + 27 * d / max(t, 1),
                                                                        f"Printify: сторінка {d} з {t}"))
        snap["printify"] = [printify.slim_order(p) for p in raw]
        snap["printifyShop"] = {"id": shop.get("id"), "title": shop.get("title")}
        _loaded(snap, warnings, "printify", raw, "Printify")
    except ApiError as err:
        warnings.append(f"Printify: {err}. Використано попередні дані.")


def _gelato_part(job, snap: dict, warnings: list) -> None:
    """Every Gelato order, with the tracking of the shipped ones; a failure keeps the previous orders."""
    job.progress("Завантаження замовлень Gelato…", 78, "Собівартість Gelato")
    try:
        raw = gelato.all_orders(lambda n: job.progress(None, 78 + min(12, n / 100), f"Gelato: {n} замовлень"))
        slim = [gelato.slim_order(g) for g in raw]
        job.progress(None, 91, "Gelato: трек-номери відправлених")
        if gelato.attach_shipments(slim, snap["gelato"]):
            warnings.append("Gelato: не всі трек-номери вдалося прочитати — спробую при наступному оновленні.")
        snap["gelato"] = slim
        _loaded(snap, warnings, "gelato", raw, "Gelato")
    except ApiError as err:
        warnings.append(f"Gelato: {err}. Використано попередні дані.")


def _sync(job, full: bool = False) -> dict:
    prev = records.load_snapshot()
    snap = {key: prev.get(key) for key in ("shopName", "shopId", "printifyShop", "etsyCursor", "etsyFullAt")}
    snap.update(receipts=prev.get("receipts") or [], printify=prev.get("printify") or [],
                gelato=prev.get("gelato") or [], loaded=dict(prev.get("loaded") or {}))
    warnings: list[str] = []
    etsy_connected = bool(etsy.tokens())
    changed = None
    if etsy_connected:
        changed = _etsy_part(job, snap, warnings, full)
    else:
        snap["receipts"] = []
        warnings.append("Etsy не підключено — показано лише замовлення Printify.")
    if vault.get("printify_token"):
        _printify_part(job, snap, warnings)
    else:
        warnings.append("Printify токен не налаштовано — собівартість Printify недоступна.")
    if vault.get("gelato_api_key"):
        _gelato_part(job, snap, warnings)

    job.progress("Зіставлення замовлень…", 94, "")
    snap["syncedAt"] = core.now_iso()
    snap["warnings"] = warnings
    records.save(records.SNAPSHOT, snap)
    archive.refresh_quietly()  # orders that reached the buyer start their 14 days; expired books go

    matched = sum(1 for r in profit.cached_view()["full"].values()
                  if r.get("profit") is not None and r.get("match_type") not in (None, "unmatched"))
    return {"receipts": len(snap["receipts"]), "matched": matched, "printify": len(snap["printify"]),
            "gelato": len(snap["gelato"]), "warnings": warnings, "etsyConnected": etsy_connected,
            "changed": changed}


def _connected() -> bool:
    return bool(etsy.tokens() or vault.get("printify_token"))


@route("POST", "/api/profit/sync")
def _start_sync(req: Request):
    if not _connected():
        raise ApiError("Немає жодного підключення. Підключіть Etsy та Printify у Налаштуваннях.", 400,
                       {"code": "not_configured"})
    full = bool((req.json or {}).get("full"))
    running = jobs.running("profit-sync")
    if running and not full:
        return {"jobId": running.id}  # already syncing (another window or the order picker) — wait for that one
    job = jobs.start("profit-sync", lambda j: _sync(j, full=full), exclusive="profit-sync")
    return {"jobId": job.id}


@route("GET", "/api/profit/sync")
def _sync_state(req: Request):
    """The sync running right now (the one at start-up, or one started by the refresh button), if any."""
    running = jobs.running("profit-sync")
    return {"jobId": running.id if running else None}


def startup_sync() -> None:
    """Orders are pulled once when the program starts; after that only by the refresh button."""
    if not _connected():
        return
    try:
        jobs.start("profit-sync", lambda j: _sync(j), exclusive="profit-sync")
    except JobError:
        pass
