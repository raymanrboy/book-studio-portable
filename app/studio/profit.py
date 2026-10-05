"""The Profit view: every Etsy order's row — its print order and money (outcomes.rows()) — cached until a file it is
made from changes, and the Profit page's routes: the rows, one row, the print orders to pick from, a manual link, a
manual state. Pulling the orders is sync.py's; the files are records.py's."""
from __future__ import annotations

import threading
import time
from datetime import datetime

from . import core, etsy, gelato, ledger, outcomes, printorders, reconcile, records
from .fees import r2
from .server import ApiError, Request, route
from .vault import vault

# Bookkeeping starts on 1 October 2026 (owner, 25 and 27.09.2026: "it must not include earlier orders at all"): the
# Profit page counts, shows and offers nothing older. The queue, the stages and the archive still read every order —
# they take cached_view()["full"], which is not cut.
ACCOUNTING_FROM = datetime(2026, 10, 1)  # midnight on this computer's clock
# What Etsy takes outside any order — Etsy Ads ($0.99 + 20% VAT a day) and new listings ($0.24 each) — from the owner's
# statements of September–October 2026: about $1.38 a day. The page takes it off the net profit quietly, no card of its
# own (2026-10-05); the ledger check below counts it into what the program expects on the Etsy balance.
OVERHEAD_PER_DAY = 1.38


def counted(created) -> bool:
    """Whether a sale or a print order made at `created` belongs to the bookkeeping."""
    at = reconcile.parse_time(created)
    return at is not None and at >= ACCOUNTING_FROM.timestamp() * 1000


def build_view() -> dict:
    snap = records.load_snapshot()
    states = records.load_states()
    rates = printorders.rates()
    receipts = snap.get("receipts") or []
    p_orders = snap.get("printify") or []
    g_orders = snap.get("gelato") or []
    if receipts:
        rows = outcomes.rows(receipts, p_orders, g_orders, records.load_links(), states, records.load_sends(), rates)
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
    for f in printorders.all_facts(snap, rates).values():
        info = outcomes.order_info(f)
        candidates.append({**{k: info[k] for k in ("provider", "id", "name", "createdAt", "status", "label", "dead")},
                           "cost": info["fullCost"], "usedBy": used.get(f["key"])})
    candidates.sort(key=lambda c: c.get("createdAt") or "", reverse=True)
    real = ledger.view(receipts) if receipts else {}
    for row in rows:
        got = (real.get("receipts") or {}).get(str(row.get("etsy_receipt_id") or ""))
        if got:
            row["etsy_net_actual"] = r2(got["net"])
            row["etsy_lines"] = got["lines"]
            if row.get("etsy_net") is not None:
                row["etsy_check"] = r2(got["net"] - row["etsy_net"])
    return {
        "mode": mode,
        "syncedAt": snap.get("syncedAt"),
        "shopName": snap.get("shopName"),
        # Only the printers connected now: no Printify token — no Printify in the page's header (2026-10-05).
        "printifyShop": snap.get("printifyShop") if vault.get("printify_token") else None,
        "gelatoConnected": bool(gelato.accounts()),
        "warnings": snap.get("warnings") or [],
        "counts": {"receipts": len(receipts), "printify": len(p_orders), "gelato": len(g_orders)},
        "rows": rows,
        "candidates": candidates,
        "etsyConnected": bool(etsy.tokens()),
        "etsyBalance": _balance_check(real, rows),
    }


def _balance_check(real: dict, rows: list) -> dict | None:
    """The Etsy balance (what Etsy pays out next) beside what the program expects on it: what the last payout left on the
    balance, plus its own Etsy Net of the receipts made since, less the ads and new listings a day. And the last payout
    beside the same sum for the days it covered. None — no ledger."""
    if not real:
        return None
    full = {r["id"]: r for r in rows}

    def expected(start: float, end: float, left: float) -> dict:
        net, n = ledger.window_net(full, start, end)
        return {"amount": r2(left + net - OVERHEAD_PER_DAY * (end - start) / 86400), "orders": n, "from": start, "to": end}

    payouts = real.get("payouts") or []
    if not payouts:
        return {"balance": r2(real["balance"]), "at": real["at"]}
    last = payouts[-1]
    out = {"balance": r2(real["balance"]), "at": real["at"], "expected": expected(last["at"], time.time(), last["left"])}
    if len(payouts) >= 2:
        before = payouts[-2]
        out["lastPayout"] = {"at": last["at"], "amount": r2(last["amount"]),
                             "expected": expected(before["at"], last["at"], before["left"] - last["left"])}
    return out


# Fields the table needs; the heavy rest (fees, address, items) is fetched when a row is opened.
SLIM_FIELDS = (
    "id", "etsy_receipt_id", "customer_name", "created_at", "status", "is_shipped", "etsy_gross", "etsy_fees",
    "etsy_net", "match_type", "pod_provider", "pod_total_cost", "printify_total_cost", "printify_order_id",
    "app_order_id", "gelato_order_id", "gelato_order_reference", "is_bundle", "bundle_count", "profit",
    "profit_margin", "cover_label", "link_blocked", "state", "state_manual", "refund_amount", "pod_dead",
    "replacement_cost", "cost_total", "impact", "needs_link", "etsy_net_original", "cost_unknown",
    "etsy_net_actual", "etsy_check",
)
_view_lock = threading.Lock()
_view_cache: dict = {"key": None}


def cached_view() -> dict:
    """build_view() again only when a file it is made from, the rates or the Etsy connection change. "key" names this
    build: stages.py keeps its own facts per build."""
    key = (tuple(records.stamp(p) for p in (records.SNAPSHOT, records.LINKS, records.STATES, records.SENDS, ledger.LEDGER)),
           tuple(sorted(printorders.rates().items())), bool(etsy.tokens()))
    with _view_lock:
        if _view_cache.get("key") != key:
            view = build_view()
            slim = []
            for r in view["rows"]:
                if not counted(r.get("created_at")):
                    continue
                s = {k: r.get(k) for k in SLIM_FIELDS}
                s["search"] = " ".join([r.get("customer_name") or "", r.get("etsy_receipt_id") or "",
                                        r.get("app_order_id") or ""] + [i.get("title") or "" for i in r.get("items") or []]).lower()
                slim.append(s)
            _view_cache.update({
                "key": key,
                "full": {r["id"]: r for r in view["rows"]},
                "candidates": view["candidates"],
                "summary": {**{k: v for k, v in view.items() if k not in ("rows", "candidates")}, "rows": slim,
                            "accountingFrom": ACCOUNTING_FROM.date().isoformat(), "overheadPerDay": OVERHEAD_PER_DAY},
            })
        return _view_cache


# ---------------------------------------------------------------- routes

@route("GET", "/api/profit/data")
def _data(req: Request):
    return cached_view()["summary"]


@route("GET", "/api/profit/row")
def _row(req: Request):
    row = cached_view()["full"].get(req.param("id") or "")
    if not row or not counted(row.get("created_at")):
        raise ApiError("Замовлення не знайдено. Оновіть сторінку.", 404)
    return row


@route("GET", "/api/profit/candidates")
def _candidates(req: Request):
    return {"candidates": [c for c in cached_view()["candidates"] if counted(c.get("createdAt"))]}


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
    for rid, entry in records.load_states().items():
        if entry.get("status") == "replacement" and rid != receipt \
                and records.has_ref(entry.get("replacementOrders"), provider, order_id):
            raise ApiError(f"Це замовлення позначене як заміна для чека #{rid}. Спершу приберіть його звідти.")
    with records.lock:
        links = records.load_links()
        links[receipt] = {"provider": provider, "orderId": order_id or None, "at": core.now_iso()}
        records.save(records.LINKS, links)
    return {"ok": True}


@route("DELETE", "/api/profit/links")
def _delete_link(req: Request):
    receipt = (req.param("receipt") or "").strip()
    with records.lock:
        links = records.load_links()
        links.pop(receipt, None)
        records.save(records.LINKS, links)
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


def _replacement_orders(body: dict, receipt_id: str) -> list[dict]:
    """The print orders a replacement names, checked: known, not this receipt's own order, not linked by hand to
    another receipt; each once."""
    view = cached_view()
    row = view["full"].get(receipt_id) or {}
    primary = {f"printify:{row.get('printify_order_id')}", f"gelato:{row.get('gelato_order_id')}"}
    linked = {f"{l.get('provider')}:{l.get('orderId')}": rid for rid, l in records.load_links().items()}
    known = {f"{c['provider']}:{c['id']}" for c in view["candidates"]}
    refs: list[dict] = []
    for ref in body.get("replacementOrders") or []:
        key = f"{ref.get('provider')}:{ref.get('orderId')}"
        if key not in known:
            raise ApiError("Замовлення заміни не знайдено серед замовлень Printify/Gelato. Оновіть дані.")
        if key in primary:
            raise ApiError("Це основне замовлення цього чека — для заміни оберіть інше.")
        if key in linked and linked[key] != receipt_id:
            raise ApiError(f"Це замовлення вручну зв'язане з чеком #{linked[key]}. Спершу скиньте той зв'язок.")
        if not records.has_ref(refs, ref["provider"], ref["orderId"]):
            refs.append({"provider": ref["provider"], "orderId": str(ref["orderId"])})
    return refs


@route("POST", "/api/profit/state")
def _set_state(req: Request):
    """Operator's status for one Etsy order: cancelled, full/partial refund or replacement reprint."""
    body = req.json or {}
    receipt_id = str(body.get("receiptId") or "").strip()
    status = body.get("status")
    receipt = next((r for r in records.load_snapshot().get("receipts") or []
                    if str(r.get("receipt_id")) == receipt_id), None)
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
        entry["replacementOrders"] = _replacement_orders(body, receipt_id)
        cost = _amount(body.get("replacementCost"), "Витрати на заміну")
        if cost:
            entry["replacementCost"] = cost
    with records.lock:
        states = records.load_states()
        if status == "auto":
            states.pop(receipt_id, None)
        else:
            states[receipt_id] = entry
        records.save(records.STATES, states)
    return {"ok": True, "row": cached_view()["full"].get(receipt_id)}
