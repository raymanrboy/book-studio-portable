"""App info, settings, secrets and one-click import of keys from the older tools."""
from __future__ import annotations

import re
from pathlib import Path

from . import core, desktop, etsy, gelato_accounts, library, portable, printify, tunnel
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
                     "masterTitle": (p.get("master") or {}).get("title"), "readOnly": printify.retired()},
        "gelato": vault.status("gelato_api_key"),
    }


@route("GET", "/api/app")
def _app(req: Request):
    return {
        "name": core.APP_NAME,
        "version": core.APP_VERSION,
        "dataDir": str(core.DATA_DIR),
        "port": state.port,
        "ui": core.settings.section("ui"),
        "integrations": integrations(),
        "cloudflared": tunnel.CLOUDFLARED.exists(),
        "library": library.counts(),
    }


@route("GET", "/api/settings")
def _settings(req: Request):
    data = core.settings.get()
    return {
        "ui": data["ui"],
        "security": {"etsyKyivOnly": core.etsy_kyiv_only()},
        "etsy": {**data["etsy"], **etsy.status()},
        "printify": {**data["printify"], "readOnly": printify.retired()},
        "gelato": {**data["gelato"], **gelato_accounts.status()},
        "textcheck": {k: data["textcheck"].get(k) for k in ("enabled", "prescan", "model")},  # Ollama: /api/textcheck/status
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
    # The owner's rule: Etsy may only ever be opened on the Kyiv computer (`core.etsy_kyiv_only()`; off in a copy for someone
    # else). The one exception is the Etsy sign-in page, which Settings opens only after the user confirms they are on it.
    parts = urllib.parse.urlsplit(url)
    host = (parts.hostname or "").lower().rstrip(".")      # «www.etsy.com.» is the same site
    if (core.etsy_kyiv_only() and any(host == d or host.endswith("." + d) for d in ("etsy.com", "etsy.me"))
            and parts.path.rstrip("/") != "/oauth/connect"):
        raise ApiError("Etsy не відкривається з цього комп'ютера — лише з київського.", 403)
    if not _open_in_profile(url, host):
        webbrowser.open(url)
    return {"ok": True}


def _open_in_profile(url: str, host: str) -> bool:
    """Sites the owner keeps in one browser profile (Gelato and Canva in Cent Browser's «Work», 01.10.2026) open in it.
    The settings' "browser" section: `exe`, `profile` (the profile's folder name, "Profile 6"), `hosts`. Not set, another
    site, or the browser not found → False, and the default browser opens the link as before. In the portable copy it is
    Edge with a profile of its own (`work-browser` in the data folder): a login cannot travel between PCs anyway. It starts
    with `--restore-last-session` (2026-10-14): without it Edge drops session cookies on exit, and the owner had to sign in to
    Gelato again every time (tried on Edge 155: the cookie survives a restart only with it; a running Edge just adds the tab).
    The Canva extension is installed in that profile once by hand — Edge 155 ignores `--load-extension` (tried)."""
    import subprocess
    cfg = core.settings.section("browser")
    if not any(host == h or host.endswith("." + h) for h in cfg.get("hosts") or []):
        return False
    if portable.root():        # the portable copy: Edge (every Windows has it) with a profile of its own in the data folder
        exe = desktop.find_browser()
        if exe:
            desktop.trim_profile(core.data_path("work-browser"))
        args = [exe, f"--user-data-dir={core.data_path('work-browser')}", "--no-first-run",
                "--no-default-browser-check", "--restore-last-session", *desktop.QUIET_EDGE, url] if exe else None
    else:
        exe, profile = cfg.get("exe"), cfg.get("profile")
        args = [exe, f"--profile-directory={profile}", url] if exe and profile and Path(exe).is_file() else None
    if not args:
        return False
    try:
        subprocess.Popen(args, close_fds=True,
                         creationflags=getattr(subprocess, "DETACHED_PROCESS", 0)
                         | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    except OSError:
        core.log.exception("Opening %s in the browser profile failed; the default browser opens it", host)
        return False
    return True


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


_legacy_seen: dict = {"files": None, "found": {}}


def _legacy_names() -> dict[str, str]:
    """name -> where an old key was found. The old files are decrypted again only when one of them changed:
    Settings asks on every opening (22.09.2026 audit), and the values themselves are not kept here."""
    files = [ORDER_CREATOR_LOCAL / "printify-token.dpapi", ORDER_CREATOR_LOCAL / "gelato-api-key.dpapi",
             PROFIT_CALC_DIR / ".env.local", PROFIT_CALC_DIR / ".env"]
    stamp = tuple(p.stat().st_mtime_ns if p.exists() else None for p in files)
    if _legacy_seen["files"] != stamp:
        _legacy_seen.update(files=stamp, found={name: source for name, (_, source) in _legacy_values().items()})
    return _legacy_seen["found"]


def legacy_sources() -> dict:
    if core.SAMPLE:  # the preview server never offers the owner's real keys
        return {"items": [], "uploadCache": 0}
    items = []
    try:
        found = _legacy_names()
    except Exception:
        core.log.exception("Legacy scan failed")
        found = {}
    labels = {"printify_token": "Printify токен", "gelato_api_key": "Gelato API-ключ",
              "etsy_keystring": "Etsy Keystring", "etsy_shared_secret": "Etsy Shared Secret"}
    for name, source in found.items():
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
