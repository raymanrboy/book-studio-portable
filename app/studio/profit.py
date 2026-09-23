"""Profit module: manual sync of Etsy + Printify + Gelato, local snapshot, manual links, order states."""
from __future__ import annotations

import html
import threading
import time
from datetime import datetime, timezone

from . import core, etsy, gelato, outcomes, printify, reconcile
from .fees import calculate_ukrainian_etsy_fees, money, r2
from .jobs import JobError, jobs
from .server import ApiError, Request, route
from .vault import vault

SNAPSHOT = core.data_path("profit", "snapshot.json")
LINKS = core.data_path("profit", "links.json")
STATES = core.data_path("profit", "states.json")  # receipt id -> manual state (cancel / refund / replacement)
SENDS = core.data_path("profit", "print-orders.json")  # receipt id -> the print orders this program sent
_links_lock = threading.Lock()
FULL_SYNC_EVERY = 7 * 86400   # a complete Etsy re-read once a week; otherwise only changed receipts
SYNC_OVERLAP = 3600           # re-read the last hour again so nothing slips between two syncs


def plain(value) -> str:
    """Etsy sends buyer-entered and listing text HTML-escaped (8&quot; × 8&quot;, Cover Type &amp; Size)."""
    return html.unescape(value) if isinstance(value, str) else ("" if value is None else str(value))


def normalize_receipt(r: dict) -> dict:
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
            "transaction_id": t.get("transaction_id"),
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
        "reason": rf.get("reason") or "",
        "note": rf.get("note_from_issuer") or "",
        "status": rf.get("status") or "",
    } for rf in r.get("refunds") or [] if isinstance(rf, dict)]
    return {
        "receipt_id": str(r.get("receipt_id")),
        "created_at": created,
        "create_timestamp": ts,
        "customer_shipping_name": plain(r.get("name")) or "Анонімний замовник",
        "buyer_email": r.get("buyer_email") or "",
        "message_from_buyer": plain(r.get("message_from_buyer")),
        "shipping_address": {
            "name": plain(r.get("name")),
            "first_line": plain(r.get("first_line")),
            "second_line": plain(r.get("second_line")),
            "city": plain(r.get("city")),
            "state": plain(r.get("state")),
            "zip": plain(r.get("zip")),
            "country_iso": r.get("country_iso") or "",
            "formatted_address": plain(r.get("formatted_address")),
        },
        "items": items,
        "status": r.get("status") or ("Completed" if r.get("is_shipped") else "Paid"),
        "is_shipped": bool(r.get("is_shipped")),
        "is_paid": bool(r.get("is_paid")),
        "etsy_gross": fees["gross"],
        "etsy_fees": fees["total_etsy_fees"],
        "etsy_net": fees["net_payout"],
        "is_net_estimated": False,
        "fee_breakdown": fees,
        "currency": grand.get("currency_code") or "USD",
        "refunds": refunds,
        "refund_total": r2(sum(x["amount"] for x in refunds)),
        "update_timestamp": r.get("update_timestamp") or r.get("updated_timestamp") or ts,
    }


_snapshot = {"key": None, "data": None}
_snapshot_lock = threading.Lock()


def load_snapshot() -> dict:
    """The last sync's orders, parsed once per change of the file (opening one order card used to parse it
    four times — 22.09.2026 audit). Callers only read it: a sync builds a new snapshot and saves that."""
    try:
        st = SNAPSHOT.stat()
        # The file's own id too: every write_json() puts a new file in place, while its time of change
        # moves in ~16 ms ticks — two saves within one tick would otherwise look alike.
        key = (st.st_ino, st.st_mtime_ns, st.st_size)
    except FileNotFoundError:
        return {}
    with _snapshot_lock:
        if _snapshot["key"] != key:
            _snapshot.update(key=key, data=core.read_json(SNAPSHOT, {}) or {})
        return _snapshot["data"]


def load_links() -> dict:
    return core.read_json(LINKS, {}) or {}


def load_states() -> dict:
    return core.read_json(STATES, {}) or {}


def load_sends() -> dict:
    return core.read_json(SENDS, {}) or {}


def remember_print_order(receipt_id: str | None, provider: str, order_id: str | None) -> bool:
    """What this program itself sent to a printer for a receipt. Books of one order can go in two goes
    (some ready now, the rest later) or to two printers, and then one receipt honestly has two print
    orders. Matching finds one of them by itself; only this record proves the others belong here too —
    a receipt number inside a printer's own text also appears on reprints, so it cannot be trusted for
    money. Reprints are not written here: they are replacements (mark_reprint)."""
    if not receipt_id or not order_id:
        return False
    with _links_lock:
        sends = load_sends()
        refs = sends.setdefault(str(receipt_id), [])
        if any(r.get("provider") == provider and str(r.get("orderId")) == str(order_id) for r in refs):
            return False
        refs.append({"provider": provider, "orderId": str(order_id), "at": core.now_iso()})
        _save(SENDS, sends)
    return True


def reserved_orders(states: dict) -> set[str]:
    """Provider orders marked as replacement reprints are kept out of automatic matching."""
    return {f"{ref.get('provider')}:{ref.get('orderId')}"
            for entry in states.values() if entry.get("status") == "replacement"
            for ref in entry.get("replacementOrders") or []}


def build_view() -> dict:
    snap = load_snapshot()
    links = load_links()
    states = load_states()
    rate = float(core.settings.section("gelato").get("eurUsdRate") or 1.085)
    receipts = snap.get("receipts") or []
    p_orders = snap.get("printify") or []
    g_orders = snap.get("gelato") or []
    orders = {f"printify:{p.get('id')}": p for p in p_orders}
    orders.update({f"gelato:{g.get('id')}": g for g in g_orders})
    if receipts:
        rows = reconcile.match(receipts, p_orders, g_orders, links, rate, reserved=reserved_orders(states),
                               sent=load_sends())
        by_id = {str(r["receipt_id"]): r for r in receipts}
        for row in rows:
            outcomes.apply(row, by_id[row["id"]], states.get(row["id"]), orders, rate)
        mode = "etsy"
    else:
        rows = reconcile.printify_only_rows(p_orders)
        mode = "printify_only" if p_orders else "empty"

    # Which receipt already uses each provider order (shown in the pickers).
    used: dict[str, dict] = {}
    for row in rows:
        if row.get("printify_order_id") and row.get("match_type") not in (None, "unmatched", "printify_only"):
            used.setdefault(f"printify:{row['printify_order_id']}", {"kind": "primary", "receipt": row["id"], "name": row.get("customer_name")})
        if row.get("gelato_order_id"):
            used.setdefault(f"gelato:{row['gelato_order_id']}", {"kind": "primary", "receipt": row["id"], "name": row.get("customer_name")})
        for o in row.get("replacement_orders") or []:
            used[f"{o['provider']}:{o['id']}"] = {"kind": "replacement", "receipt": row["id"], "name": row.get("customer_name")}
    candidates = []
    for key, order in orders.items():
        provider = key.split(":", 1)[0]
        info = outcomes.pod_order_info(provider, order, rate)
        candidates.append({**{k: info[k] for k in ("provider", "id", "name", "createdAt", "status", "label", "dead")},
                           "cost": info["fullCost"], "usedBy": used.get(key)})
    candidates.sort(key=lambda c: c.get("createdAt") or "", reverse=True)
    return {
        "mode": mode,
        "syncedAt": snap.get("syncedAt"),
        "shopName": snap.get("shopName"),
        "printifyShop": snap.get("printifyShop"),
        "warnings": snap.get("warnings") or [],
        "counts": {"receipts": len(receipts), "printify": len(p_orders), "gelato": len(g_orders)},
        "rows": rows,
        "candidates": candidates,
        "etsyConnected": bool(etsy.tokens()),
    }


# Fields the table needs; the heavy rest (fees, address, items) is fetched when a row is opened.
SLIM_FIELDS = (
    "id", "etsy_receipt_id", "customer_name", "created_at", "status", "is_shipped", "etsy_gross", "etsy_fees",
    "etsy_net", "match_type", "pod_provider", "pod_total_cost", "printify_total_cost", "printify_order_id",
    "app_order_id", "gelato_order_id", "gelato_order_reference", "is_bundle", "bundle_count", "profit",
    "profit_margin", "cover_label", "link_blocked", "state", "state_manual", "refund_amount", "pod_dead",
    "replacement_cost", "cost_total", "impact", "needs_link", "etsy_net_original",
)
_view_lock = threading.Lock()
_view_cache: dict = {"key": None}
_writes = [0]  # bumped on every save below: two saves within one file-clock tick keep the same mtime


def _save(path, data) -> None:
    core.write_json(path, data)
    with _view_lock:
        _writes[0] += 1


def _mtime(path) -> int:
    try:
        return path.stat().st_mtime_ns
    except FileNotFoundError:
        return 0


def cached_view() -> dict:
    """build_view() is recomputed only when the snapshot, links or settings change."""
    key = (_writes[0], _mtime(SNAPSHOT), _mtime(LINKS), _mtime(STATES),
           core.settings.section("gelato").get("eurUsdRate"), bool(etsy.tokens()))
    with _view_lock:
        if _view_cache.get("key") != key:
            view = build_view()
            slim = []
            for r in view["rows"]:
                s = {k: r.get(k) for k in SLIM_FIELDS}
                s["search"] = " ".join([r.get("customer_name") or "", r.get("etsy_receipt_id") or "",
                                        r.get("app_order_id") or ""] + [i.get("title") or "" for i in r.get("items") or []]).lower()
                slim.append(s)
            _view_cache.update({
                "key": key,
                "full": {r["id"]: r for r in view["rows"]},
                "candidates": view["candidates"],
                "summary": {**{k: v for k, v in view.items() if k not in ("rows", "candidates")}, "rows": slim},
            })
        return _view_cache


def merge_receipts(old: list, changed: list) -> list:
    """Replaces changed receipts in place, adds new ones, newest first (same order as a full read)."""
    by_id = {r["receipt_id"]: r for r in old}
    for r in changed:
        by_id[r["receipt_id"]] = r
    return sorted(by_id.values(), key=lambda r: (r.get("create_timestamp") or 0, r["receipt_id"]), reverse=True)


def _sync(job, full: bool = False) -> dict:
    prev = load_snapshot()
    warnings: list[str] = []
    snap = {
        "receipts": prev.get("receipts") or [],
        "printify": prev.get("printify") or [],
        "gelato": prev.get("gelato") or [],
        "shopName": prev.get("shopName"),
        "shopId": prev.get("shopId"),
        "printifyShop": prev.get("printifyShop"),
        "etsyCursor": prev.get("etsyCursor"),
        "etsyFullAt": prev.get("etsyFullAt"),
        # When each list was last loaded whole. A list that failed keeps its old orders and its old time:
        # the archive must not read an order missing from a stale list as a deleted draft.
        "loaded": dict(prev.get("loaded") or {}),
    }
    etsy_connected = bool(etsy.tokens())
    changed = None

    def loaded(source: str, items, name: str) -> None:
        if getattr(items, "complete", True):
            snap["loaded"][source] = core.now_iso()
        else:
            warnings.append(f"{name}: завантажено лише останні {len(items)} — старіші не видно.")

    if etsy_connected:
        started = int(time.time())
        # Only receipts changed since the last sync (new orders, cancellations, refunds, shipping);
        # a complete re-read on request, on the first sync and once a week.
        incremental = (not full and snap["receipts"] and snap["etsyCursor"] and snap["etsyFullAt"]
                       and started - int(snap["etsyFullAt"]) < FULL_SYNC_EVERY
                       and str(snap.get("shopId") or "") == str(etsy.tokens().get("shop_id") or snap.get("shopId") or ""))
        job.progress("Завантаження замовлень Etsy…", 5, "Лише змінені чеки" if incremental else "Усі чеки магазину")

        def on_receipts(done: int, total) -> None:
            pct = 5 + (40 * done / total if total else 20)
            job.progress(None, pct, f"Чеки Etsy: {done}" + (f" з {total}" if total else ""))

        since = int(snap["etsyCursor"]) - SYNC_OVERLAP if incremental else None
        raw, shop_id, shop_name = etsy.fetch_all_receipts(on_receipts, min_last_modified=since)  # Etsy failure = sync failure
        fresh = [normalize_receipt(r) for r in raw]
        if incremental:
            snap["receipts"] = merge_receipts(snap["receipts"], fresh)
            changed = len(fresh)
        else:
            snap["receipts"] = fresh
            snap["etsyFullAt"] = started
        snap["etsyCursor"] = started
        snap["shopId"], snap["shopName"] = shop_id, shop_name
        loaded("etsy", raw, "Etsy")
    else:
        snap["receipts"] = []
        warnings.append("Etsy не підключено — показано лише замовлення Printify.")

    if vault.get("printify_token"):
        job.progress("Завантаження замовлень Printify…", 48, "Собівартість друку та доставки")
        try:
            cfg = core.settings.section("printify")
            shop_id = cfg.get("shopId")
            shop_list = printify.shops()
            shop = next((s for s in shop_list if s.get("id") == shop_id), shop_list[0] if shop_list else None)
            if not shop:
                raise ApiError("У Printify немає магазинів.")
            raw_p = printify.all_orders(shop["id"], lambda d, t: job.progress(None, 48 + 27 * d / max(t, 1),
                                                                               f"Printify: сторінка {d} з {t}"))
            snap["printify"] = [printify.slim_order(p) for p in raw_p]
            snap["printifyShop"] = {"id": shop.get("id"), "title": shop.get("title")}
            loaded("printify", raw_p, "Printify")
        except ApiError as err:
            warnings.append(f"Printify: {err}. Використано попередні дані.")
    else:
        warnings.append("Printify токен не налаштовано — собівартість Printify недоступна.")

    if vault.get("gelato_api_key"):
        job.progress("Завантаження замовлень Gelato…", 78, "Собівартість Gelato")
        try:
            raw_g = gelato.all_orders(lambda n: job.progress(None, 78 + min(12, n / 100), f"Gelato: {n} замовлень"))
            slim_g = [gelato.slim_order(g) for g in raw_g]
            job.progress(None, 91, "Gelato: трек-номери відправлених")
            if gelato.attach_shipments(slim_g, snap["gelato"]):
                warnings.append("Gelato: не всі трек-номери вдалося прочитати — спробую при наступному оновленні.")
            snap["gelato"] = slim_g
            loaded("gelato", raw_g, "Gelato")
        except ApiError as err:
            warnings.append(f"Gelato: {err}. Використано попередні дані.")

    job.progress("Зіставлення замовлень…", 94, "")
    snap["syncedAt"] = core.now_iso()
    snap["warnings"] = warnings
    _save(SNAPSHOT, snap)

    from . import archive  # late: the archive reads this module's view
    archive.refresh_quietly()  # orders that reached the buyer start their 14 days; expired books go

    matched = sum(1 for r in cached_view()["full"].values()
                  if r.get("profit") is not None and r.get("match_type") not in (None, "unmatched"))
    return {"receipts": len(snap["receipts"]), "matched": matched, "printify": len(snap["printify"]),
            "gelato": len(snap["gelato"]), "warnings": warnings, "etsyConnected": etsy_connected,
            "changed": changed}


# ---------------------------------------------------------------- routes

@route("GET", "/api/profit/data")
def _data(req: Request):
    return cached_view()["summary"]


@route("GET", "/api/profit/row")
def _row(req: Request):
    row = cached_view()["full"].get(req.param("id") or "")
    if not row:
        raise ApiError("Замовлення не знайдено. Оновіть сторінку.", 404)
    return row


@route("GET", "/api/profit/candidates")
def _candidates(req: Request):
    return {"candidates": cached_view()["candidates"]}


@route("POST", "/api/profit/sync")
def _start_sync(req: Request):
    if not etsy.tokens() and not vault.get("printify_token"):
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
    if not etsy.tokens() and not vault.get("printify_token"):
        return
    try:
        jobs.start("profit-sync", lambda j: _sync(j), exclusive="profit-sync")
    except JobError:
        pass


@route("POST", "/api/profit/links")
def _set_link(req: Request):
    body = req.json or {}
    receipt = str(body.get("receiptId") or "").strip()
    provider = body.get("provider")
    order_id = str(body.get("orderId") or "").strip()
    if not receipt or provider not in ("printify", "gelato", "none"):
        raise ApiError("Некоректні дані зв'язку.")
    if provider != "none" and not order_id:
        raise ApiError("Оберіть замовлення постачальника.")
    for rid, entry in load_states().items():
        if entry.get("status") == "replacement" and rid != receipt and any(
                r.get("provider") == provider and str(r.get("orderId")) == order_id for r in entry.get("replacementOrders") or []):
            raise ApiError(f"Це замовлення позначене як заміна для чека #{rid}. Спершу приберіть його звідти.")
    with _links_lock:
        links = load_links()
        links[receipt] = {"provider": provider, "orderId": order_id or None, "at": core.now_iso()}
        _save(LINKS, links)
    return {"ok": True}


def _amount(value, what: str, upper: float = 100000.0) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ApiError(f"{what}: введіть число.") from None
    if not 0 <= number <= upper:
        raise ApiError(f"{what}: сума виглядає некоректно.")
    return r2(number)


@route("POST", "/api/profit/state")
def _set_state(req: Request):
    """Operator's status for one Etsy order: cancelled, full/partial refund or replacement reprint."""
    body = req.json or {}
    receipt_id = str(body.get("receiptId") or "").strip()
    status = body.get("status")
    receipt = next((r for r in load_snapshot().get("receipts") or [] if str(r.get("receipt_id")) == receipt_id), None)
    if not receipt:
        raise ApiError("Замовлення не знайдено. Оновіть сторінку.", 404)
    if status not in ("auto", *outcomes.STATES):
        raise ApiError("Невідомий статус.")
    entry: dict = {"status": status, "at": core.now_iso()}
    note = str(body.get("note") or "").strip()[:500]
    if note:
        entry["note"] = note
    if status == "refund_partial":
        gross = (receipt.get("fee_breakdown") or {}).get("gross") or 0
        amount = _amount(body.get("refundAmount"), "Сума повернення", gross or 100000)
        if amount is not None:
            entry["refundAmount"] = amount
    if status == "replacement":
        view = cached_view()
        row = view["full"].get(receipt_id) or {}
        primary = {f"printify:{row.get('printify_order_id')}", f"gelato:{row.get('gelato_order_id')}"}
        linked = {f"{l.get('provider')}:{l.get('orderId')}": rid for rid, l in load_links().items()}
        known = {f"{c['provider']}:{c['id']}" for c in view["candidates"]}
        refs = []
        for ref in body.get("replacementOrders") or []:
            key = f"{ref.get('provider')}:{ref.get('orderId')}"
            if key not in known:
                raise ApiError("Замовлення заміни не знайдено серед замовлень Printify/Gelato. Оновіть дані.")
            if key in primary:
                raise ApiError("Це основне замовлення цього чека — для заміни оберіть інше.")
            if key in linked and linked[key] != receipt_id:
                raise ApiError(f"Це замовлення вручну зв'язане з чеком #{linked[key]}. Спершу скиньте той зв'язок.")
            if key not in {f"{r['provider']}:{r['orderId']}" for r in refs}:
                refs.append({"provider": ref["provider"], "orderId": str(ref["orderId"])})
        entry["replacementOrders"] = refs
        cost = _amount(body.get("replacementCost"), "Витрати на заміну")
        if cost:
            entry["replacementCost"] = cost
    with _links_lock:
        states = load_states()
        if status == "auto":
            states.pop(receipt_id, None)
        else:
            states[receipt_id] = entry
        _save(STATES, states)
    row = cached_view()["full"].get(receipt_id)
    return {"ok": True, "row": row}


def mark_reprint(receipt_id: str | None, provider: str, order_id: str | None) -> bool:
    """A reprint made from the order archive is recorded as a replacement of its receipt, so matching
    keeps the receipt's first print order (the queue stage does not jump) and the reprint is not
    counted as a new sale. A receipt with another manual state (cancelled, refunded) is left as it is.
    So is one whose print order was cancelled at the printer: the reprint is then its only live print
    order and is matched as usual, so the queue moves the order on instead of keeping it in "new".
    Returns whether the reprint was recorded."""
    if not receipt_id or not order_id:
        return False
    try:
        row = cached_view()["full"].get(str(receipt_id))
        if row and print_order(row, placed_orders(load_snapshot()))[0] is None:
            return False
    except Exception:
        core.log.exception("Reprint: the receipt's print order could not be read; recorded as a replacement")
    with _links_lock:
        states = load_states()
        entry = states.get(receipt_id)
        if entry and entry.get("status") not in ("normal", "replacement"):
            return False
        if not entry or entry.get("status") != "replacement":
            entry = {"status": "replacement", "at": core.now_iso(), "replacementOrders": [], "byArchive": True}
        refs = entry.setdefault("replacementOrders", [])
        if not any(r.get("provider") == provider and str(r.get("orderId")) == str(order_id) for r in refs):
            refs.append({"provider": provider, "orderId": str(order_id)})
        states[receipt_id] = entry
        _save(STATES, states)
    return True


def unmark_reprint(receipt_id: str | None, provider: str, order_id: str | None) -> bool:
    """Undoes mark_reprint() for a reprint that never went to print (its draft was deleted or the order
    cancelled): its reference goes, and so does a replacement state the archive made that holds nothing else."""
    if not receipt_id or not order_id:
        return False
    with _links_lock:
        states = load_states()
        entry = states.get(receipt_id)
        refs = (entry or {}).get("replacementOrders") or []
        rest = [r for r in refs if not (r.get("provider") == provider and str(r.get("orderId")) == str(order_id))]
        if not entry or entry.get("status") != "replacement" or len(rest) == len(refs):
            return False
        if not rest and entry.get("byArchive") and not entry.get("replacementCost"):
            states.pop(receipt_id)
        else:
            entry["replacementOrders"] = rest
        _save(STATES, states)
    return True


@route("DELETE", "/api/profit/links")
def _delete_link(req: Request):
    receipt = (req.param("receipt") or "").strip()
    with _links_lock:
        links = load_links()
        links.pop(receipt, None)
        _save(LINKS, links)
    return {"ok": True}


HOUR_MS = 3_600_000


# A print order that has left the printer: Printify marks it fulfilled, Gelato shipped / in transit / …
SENT_STATUSES = ("fulfilled", "partially-fulfilled") + gelato.SHIPPED
CARRIERS = {"usps": "USPS", "ups": "UPS", "dhl": "DHL", "fedex": "FedEx", "dpd": "DPD", "gls": "GLS",
            "royal-mail": "Royal Mail", "canada-post": "Canada Post", "australia-post": "Australia Post"}


def carrier_label(code: str) -> str:
    """Printify gives a carrier code ("usps"), Gelato a shipment method name ("UPS Surepost")."""
    code = str(code or "").strip()
    return CARRIERS.get(code.lower()) or (code.upper() if len(code) <= 4 else code)


# Only a print order really placed at the printer counts (owner, 18.09.2026): a draft, an order on hold or
# awaiting payment, or a cancelled one neither moves its Etsy order out of "new" nor puts its book in the
# order archive. Printify charges when an order goes to production: on hold and pending ones are not paid.
PRINTIFY_NOT_PLACED = ("on-hold", "pending", "payment-not-received", "canceled", "cancelled")
GELATO_NOT_PAID = ("draft", "pending", "canceled", "cancelled", "refused")
CANCELLED = ("canceled", "cancelled")


def is_placed(provider: str, order: dict) -> bool:
    """Whether a print order from the snapshot is really placed: ordered, paid and not cancelled."""
    if provider == "printify":
        return str(order.get("status") or "").lower() not in PRINTIFY_NOT_PLACED
    return (str(order.get("orderType") or "order").lower() == "order"
            and str(order.get("fulfillmentStatus") or "").lower() not in CANCELLED + ("draft",)
            and str(order.get("financialStatus") or "").lower() not in GELATO_NOT_PAID)


def placed_orders(snap: dict) -> dict:
    """Every print order by "provider:id": when it was made, its status as the printer words it, tracking,
    and whether it is really placed (is_placed())."""
    def facts(provider, order, created, status, shipments) -> dict:
        return {"created": created, "status": status, "placed": is_placed(provider, order),
                "tracking": [{"carrier": carrier_label(s.get("carrier")), "number": str(s["number"]),
                              "url": s.get("url") or ""} for s in shipments or [] if s.get("number")]}

    placed = {f"printify:{p.get('id')}": facts("printify", p, p.get("created_at"), p.get("status"), p.get("shipments"))
              for p in snap.get("printify") or []}
    placed.update({f"gelato:{g.get('id')}": facts("gelato", g, g.get("createdAt"), g.get("fulfillmentStatus"),
                                                  g.get("shipments"))
                   for g in snap.get("gelato") or []})
    return placed


def _matched_order(row: dict, placed: dict) -> tuple[str | None, dict]:
    """The print order matched to this receipt, unless it is an earlier order of a returning buyer."""
    provider = row.get("pod_provider")
    order_id = row.get("printify_order_id") if provider == "printify" else row.get("gelato_order_id")
    if not provider or not order_id:
        return None, {}
    facts = placed.get(f"{provider}:{order_id}") or {}
    if row.get("match_type") != "manual":
        t_order, t_receipt = reconcile.parse_time(facts.get("created")), reconcile.parse_time(row.get("created_at"))
        if t_order is not None and t_receipt is not None and t_order < t_receipt - HOUR_MS:
            return None, {}  # matched by name to an earlier order of a returning buyer
    return provider, facts


def print_order(row: dict, placed: dict) -> tuple[str | None, dict]:
    """The live print order made for this receipt: (provider, facts), or (None, {}) when there is none —
    never ordered, not placed yet (a draft, on hold, awaiting payment), cancelled at the printer, or only
    an earlier order of a returning buyer."""
    provider, facts = _matched_order(row, placed)
    if provider and not facts.get("placed", True):
        return None, {}  # the book still has to be ordered (or ordered again)
    return provider, facts


def waiting_order(row: dict, placed: dict) -> tuple[str | None, dict]:
    """A print order made for this receipt that waits at the printer — a draft, on hold or awaiting payment
    (not cancelled): shown on the order in "new" so a second one is not made by mistake."""
    provider, facts = _matched_order(row, placed)
    if provider and facts and not facts.get("placed", True) and str(facts.get("status") or "").lower() not in CANCELLED:
        return provider, facts
    return None, {}


def order_stage(row: dict, placed: dict) -> tuple[str, str | None]:
    """Where an Etsy order stands: ("new" | "work" | "sent" | "shipped" | "closed", provider).

    Etsy keeps the seller's own tabs such as "In Production" out of its API, so the signal is the
    print order: once Printify or Gelato has a placed order carrying the receipt number (not a draft, not on
    hold or unpaid, not cancelled — is_placed()), the book is in work;
    once the printer has shipped it (tracking or a shipped status), it is "sent" — waiting for the
    owner to mark it shipped on Etsy, after which Etsy's own flag makes it "shipped".
    placed is placed_orders().
    """
    if row.get("state") in ("canceled", "refund_full"):
        return "closed", None
    provider, facts = print_order(row, placed)
    if row.get("is_shipped"):
        return "shipped", provider
    if not provider:
        return ("work", None) if row.get("link_blocked") else ("new", None)
    if facts.get("tracking") or str(facts.get("status") or "").lower() in SENT_STATUSES:
        return "sent", provider
    return "work", provider


def picker_orders() -> list:
    """Every Etsy order for the order queue and the Order Creator picker, newest first, each with its
    stage and, once ordered, the printer's status and tracking. Cancelled and fully refunded orders are left out."""
    snap = load_snapshot()
    placed = placed_orders(snap)
    rows = cached_view()["full"]
    out = []
    for r in snap.get("receipts") or []:
        row = rows.get(str(r["receipt_id"]))
        if not row:
            continue
        stage, provider = order_stage(row, placed)
        if stage == "closed":
            continue
        facts = print_order(row, placed)[1] if provider else {}
        if stage == "new":  # a draft or unpaid order waiting at the printer: its status shows, the stage stays
            provider, facts = waiting_order(row, placed)
        # plain() again: receipts saved before the Etsy text was unescaped at sync time
        out.append({
            "receiptId": r["receipt_id"],
            "createdAt": r.get("created_at"),
            "name": plain(r.get("customer_shipping_name")),
            "address": {k: plain(v) for k, v in (r.get("shipping_address") or {}).items()},
            "stage": stage,
            "provider": provider,
            "printStatus": facts.get("status") or "",  # as Printify / Gelato word it, untranslated (owner's wish)
            "tracking": facts.get("tracking") or [],
            # books of this receipt sent in another go, or to the other printer: the row above describes
            # only the first order, so the card says there is more than one
            "alsoSent": [{"provider": f["provider"], "status": f.get("status") or ""}
                         for f in row.get("further_orders") or []],
            "books": sum(int(i.get("quantity") or 1) for i in r.get("items") or []),
            "items": [{"title": plain(i.get("title")), "quantity": i.get("quantity"), "sku": i.get("sku") or "",
                       "listingId": str(i.get("listing_id") or ""),
                       "variations": [{"name": plain(v.get("name")), "value": plain(v.get("value"))}
                                      for v in i.get("variations") or []]}
                      for i in r.get("items") or []],
            "coverLabel": row.get("cover_label") or reconcile.cover_label(r.get("items") or []),
        })
    return out
