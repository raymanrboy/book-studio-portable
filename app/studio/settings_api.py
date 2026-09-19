"""App info, settings, secrets and one-click import of keys from the older tools."""
from __future__ import annotations

import re
from pathlib import Path

from . import core, desktop, etsy, library, tunnel
from .server import ApiError, Request, route, state
from .vault import SECRET_NAMES, unprotect_powershell_securestring, vault

EDITABLE_SECRETS = ("etsy_keystring", "etsy_shared_secret", "printify_token", "gelato_api_key")
DESKTOP = core.ROOT.parent.parent  # the program lives in "Book Studio/app" on the Desktop
# The Order Creator folder was renamed at some point; accept both names.
ORDER_CREATOR_LOCAL = next((p for p in (DESKTOP / "Order Creator" / ".local", DESKTOP / "Order Creator Printify" / ".local")
                            if p.exists()), DESKTOP / "Order Creator" / ".local")
PROFIT_CALC_DIR = DESKTOP / "Etsy Profit Calculator"


def integrations() -> dict:
    p = core.settings.section("printify")
    return {
        "etsy": etsy.status(),
        "printify": {**vault.status("printify_token"), "shopTitle": p.get("shopTitle"), "shopId": p.get("shopId"),
                     "masterTitle": (p.get("master") or {}).get("title")},
        "gelato": vault.status("gelato_api_key"),
    }


@route("GET", "/api/app")
def _app(req: Request):
    books = library.all_books()
    return {
        "name": core.APP_NAME,
        "version": core.APP_VERSION,
        "dataDir": str(core.DATA_DIR),
        "port": state.port,
        "ui": core.settings.section("ui"),
        "integrations": integrations(),
        "cloudflared": tunnel.CLOUDFLARED.exists(),
        "library": {"active": sum(1 for b in books if not b.get("archived")),
                    "archived": sum(1 for b in books if b.get("archived"))},
    }


@route("GET", "/api/settings")
def _settings(req: Request):
    data = core.settings.get()
    return {
        "ui": data["ui"],
        "etsy": {**data["etsy"], **etsy.status()},
        "printify": data["printify"],
        "gelato": data["gelato"],
        "textcheck": {k: data["textcheck"].get(k) for k in ("enabled", "model")},  # Ollama's state: /api/textcheck/status
        "secrets": {name: vault.status(name) for name in EDITABLE_SECRETS},
        "dataDir": str(core.DATA_DIR),
        "legacy": legacy_sources(),
    }


@route("POST", "/api/settings/ui")
def _ui(req: Request):
    body = req.json or {}
    patch = {}
    if body.get("theme") in ("dark", "light", "system"):
        patch["theme"] = body["theme"]
    if isinstance(body.get("reduceMotion"), bool):
        patch["reduceMotion"] = body["reduceMotion"]
    return core.settings.update({"ui": patch})["ui"]


@route("POST", "/api/settings/etsy")
def _etsy_settings(req: Request):
    redirect = str((req.json or {}).get("redirectUri") or "").strip()
    if redirect and not re.match(r"^https?://", redirect):
        raise ApiError("Redirect URI має починатися з http:// або https://")
    core.settings.update({"etsy": {"redirectUri": redirect}})
    return etsy.status()


@route("POST", "/api/settings/gelato")
def _gelato_settings(req: Request):
    body = req.json or {}
    patch: dict = {}
    if "eurUsdRate" in body:
        try:
            rate = float(body["eurUsdRate"])
        except (TypeError, ValueError):
            raise ApiError("Курс має бути числом.")
        if not 0.5 < rate < 3:
            raise ApiError("Курс EUR→USD виглядає некоректно.")
        patch["eurUsdRate"] = rate
    if "tunnelKeepAliveSeconds" in body:
        minutes = int(body["tunnelKeepAliveSeconds"]) // 60
        patch["tunnelKeepAliveSeconds"] = max(5, min(60, minutes)) * 60
    return core.settings.update({"gelato": patch})["gelato"]


@route("POST", "/api/settings/printify")
def _printify_settings(req: Request):
    body = req.json or {}
    patch: dict = {}
    for key in ("coverSize", "pageSize"):
        if key in body:
            value = body[key]
            if not (isinstance(value, list) and len(value) == 2 and all(isinstance(v, int) and 100 < v < 20000 for v in value)):
                raise ApiError("Розмір має бути парою цілих чисел (ширина, висота).")
            patch[key] = value
    if "shopId" in body:
        patch["shopId"] = int(body["shopId"])
        patch["shopTitle"] = body.get("shopTitle")
    return core.settings.update({"printify": patch})["printify"]


@route("POST", "/api/secrets")
def _secret(req: Request):
    body = req.json or {}
    name = body.get("name")
    if name not in EDITABLE_SECRETS:
        raise ApiError("Невідомий ключ.")
    value = str(body.get("value") or "").strip()
    if value and len(value) < 6:
        raise ApiError("Значення закоротке — перевірте, що скопіювали повністю.")
    vault.set(name, value or None)
    return {"secrets": {n: vault.status(n) for n in EDITABLE_SECRETS}, "integrations": integrations()}


@route("POST", "/api/app/open-data")
def _open_data(req: Request):
    desktop.open_in_explorer(core.DATA_DIR)
    return {"ok": True}


@route("POST", "/api/app/open-url")
def _open_url(req: Request):
    """External links open in the normal browser (where the user is logged in), not in the app window."""
    import urllib.parse
    import webbrowser
    url = str((req.json or {}).get("url") or "").strip()
    if not re.match(r"^https?://[^\s]+$", url):
        raise ApiError("Некоректне посилання.")
    # Etsy may only ever be opened on the Kyiv computer. The one exception is the Etsy sign-in page,
    # which Settings opens only after the user confirms they are working on that computer.
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower()
    if (host == "etsy.com" or host.endswith(".etsy.com")) and parts.path.rstrip("/") != "/oauth/connect":
        raise ApiError("Etsy не відкривається з цього комп'ютера — лише з київського.", 403)
    webbrowser.open(url)
    return {"ok": True}


@route("POST", "/api/app/pick-folder")
def _pick_folder(req: Request):
    body = req.json or {}
    return {"path": desktop.pick_folder(body.get("title") or "Оберіть папку", body.get("initial") or "")}


# ---------------------------------------------------------------- legacy import

def _read_env(path: Path) -> dict:
    values: dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            value = value.strip().strip('"').strip("'")
            if value:
                values[key.strip()] = value
    except OSError:
        pass
    return values


def _legacy_values() -> dict[str, tuple[str, str]]:
    """name -> (value, source description). Values stay inside the backend."""
    found: dict[str, tuple[str, str]] = {}
    for name, file in (("printify_token", "printify-token.dpapi"), ("gelato_api_key", "gelato-api-key.dpapi")):
        path = ORDER_CREATOR_LOCAL / file
        if path.exists():
            try:
                value = unprotect_powershell_securestring(path.read_text(encoding="utf-8-sig"))
                if value.strip():
                    found[name] = (value.strip(), "Order Creator")
            except (OSError, ValueError, UnicodeDecodeError):
                core.log.warning("Legacy secret %s could not be decrypted", file)
    env: dict[str, str] = {}
    for name in (".env.local", ".env"):
        env.update({k: v for k, v in _read_env(PROFIT_CALC_DIR / name).items() if k not in env})
    mapping = {"PRINTIFY_API_TOKEN": "printify_token", "GELATO_API_KEY": "gelato_api_key",
               "ETSY_KEYSTRING": "etsy_keystring", "ETSY_SHARED_SECRET": "etsy_shared_secret"}
    for env_name, name in mapping.items():
        if env.get(env_name) and name not in found:
            found[name] = (env[env_name], "Etsy Profit Calculator")
    return found


def legacy_sources() -> dict:
    items = []
    try:
        values = _legacy_values()
    except Exception:
        core.log.exception("Legacy scan failed")
        values = {}
    labels = {"printify_token": "Printify токен", "gelato_api_key": "Gelato API-ключ",
              "etsy_keystring": "Etsy Keystring", "etsy_shared_secret": "Etsy Shared Secret"}
    for name, (_, source) in values.items():
        items.append({"name": name, "label": labels[name], "source": source,
                      "alreadySet": vault.status(name)["configured"]})
    cache = ORDER_CREATOR_LOCAL / "upload_cache.json"
    cache_entries = len(core.read_json(cache, {}) or {}) if cache.exists() else 0
    return {"items": items, "uploadCache": cache_entries}


@route("POST", "/api/settings/legacy/import")
def _legacy_import(req: Request):
    body = req.json or {}
    overwrite = bool(body.get("overwrite"))
    wanted = set(body.get("names") or EDITABLE_SECRETS)
    imported, skipped = [], []
    for name, (value, source) in _legacy_values().items():
        if name not in wanted:
            continue
        if vault.status(name)["configured"] and not overwrite:
            skipped.append(name)
            continue
        vault.set(name, value)
        imported.append(name)
    cache_imported = 0
    if body.get("uploadCache", True):
        legacy_cache = core.read_json(ORDER_CREATOR_LOCAL / "upload_cache.json", {}) or {}
        if legacy_cache:
            from .creator import UPLOAD_CACHE
            current = core.read_json(UPLOAD_CACHE, {}) or {}
            for sha, image_id in legacy_cache.items():
                if isinstance(sha, str) and isinstance(image_id, str) and sha not in current:
                    current[sha] = image_id
                    cache_imported += 1
            core.write_json(UPLOAD_CACHE, current, backup=False)
    return {"imported": imported, "skipped": skipped, "uploadCache": cache_imported,
            "secrets": {n: vault.status(n) for n in EDITABLE_SECRETS}, "integrations": integrations()}


assert set(EDITABLE_SECRETS) <= set(SECRET_NAMES)
