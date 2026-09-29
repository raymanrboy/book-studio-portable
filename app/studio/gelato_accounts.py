"""The move to the owner's own Gelato account (agreed 27.09.2026, "the smooth switch"): Settings → «Перейти на новий
акаунт Gelato». The owner pastes the new key; the program checks it by reading one order, then keeps the current key as
the old account's — only read, inside the vault — and the new one does everything from then on. Every sync reads both
(sync._gelato_part()); each order knows its account. The old key is no longer needed once none of the owner's orders
there is still waiting, printing or on the way; removing it leaves those orders as they were last seen."""
from __future__ import annotations

from . import core, gelato, stages
from .jobs import JobError, jobs
from .server import ApiError, Request, route
from .vault import vault

OPEN_STAGES = ("new", "work", "sent")  # a draft waiting, in print, shipped by Gelato but not yet marked on Etsy


def old_id() -> str | None:
    key = vault.get(gelato.KEYS["old"])
    return gelato.account_id(key) if key else None


def open_orders() -> int:
    """How many of the owner's Etsy orders still follow an order in the old account: the program still needs to see
    it confirmed, printed or shipped. 0 — the old key can go."""
    old = old_id()
    if not old:
        return 0
    try:
        receipts = stages.facts()["receipts"].values()
    except Exception:
        core.log.exception("Gelato accounts: order stages unavailable")
        return 0
    return sum(1 for one in receipts if one["provider"] == "gelato" and one["stage"] in OPEN_STAGES
               and ((one.get("order") or {}).get("order") or {}).get("account") == old)


def status() -> dict:
    """For Settings: the old account, while its key is kept — since when, and how many orders still follow it."""
    if not vault.get(gelato.KEYS["old"]):
        return {"old": None}
    return {"old": {**vault.status(gelato.KEYS["old"]), "since": core.settings.section("gelato").get("switchedAt"),
                    "open": open_orders()}}


def _resync() -> None:
    """Both accounts are read at once, so the queue shows where each order stands."""
    try:
        from . import sync
        jobs.start("profit-sync", lambda j: sync._sync(j), exclusive="profit-sync")
    except JobError:
        pass


@route("POST", "/api/gelato/switch")
def _switch(req: Request):
    if core.SAMPLE:  # the preview server never reaches Gelato, not even to check a key
        raise ApiError("Це тестовий сервер на вигаданих даних — ключі тут не зберігаються.")
    new = str((req.json or {}).get("key") or "").strip()
    if len(new) < 6:
        raise ApiError("Вставте ключ нового акаунта повністю.")
    current = vault.get(gelato.KEYS["main"])
    if not current:
        raise ApiError("Ключа Gelato ще немає — збережіть новий ключ звичайним способом.")
    if vault.get(gelato.KEYS["old"]):
        raise ApiError("Перехід уже зроблено. Щоб перейти ще раз, спершу приберіть старий акаунт.")
    if gelato.account_id(new) == gelato.account_id(current):
        raise ApiError("Це той самий ключ, що вже збережено.")
    if jobs.running("profit-sync"):
        raise ApiError("Зараз оновлюються замовлення — спробуйте за хвилину.", 409)
    gelato.check_key(new)  # a mistyped or dead key is told here, before anything changes
    cfg = core.settings.section("gelato")
    # Orders kept from before they carried their account belong to the one read until now.
    core.settings.update({"gelato": {"switchedAt": core.now_iso(),
                                     "firstAccount": cfg.get("firstAccount") or gelato.account_id(current)}})
    vault.set(gelato.KEYS["old"], current)
    vault.set(gelato.KEYS["main"], new)
    core.log.info("Gelato: switched to a new account; the old one is read only")
    _resync()
    return {"ok": True, **status()}


@route("POST", "/api/gelato/old/forget")
def _forget(req: Request):
    """The old key goes; the old account's orders stay as they were last seen (sync keeps them)."""
    vault.set(gelato.KEYS["old"], None)
    core.log.info("Gelato: the old account's key removed")
    return {"ok": True, **status()}
