"""Etsy Open API v3: credentials, OAuth 2.0 (PKCE), session keys, listings, receipts.

Etsy is strictly read-only here. The interactive OAuth consent must happen on
the Kyiv computer: the app either opens the link in the local browser (when it
runs there) or gives a link to open on the Kyiv PC and accepts the final
redirect URL pasted back.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import secrets
import threading
import time
import urllib.parse
from typing import Any

from . import core, httpc
from .server import ApiError, Request, html_response, route, state
from .vault import vault

API = "https://openapi.etsy.com/v3/application"
TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
CONNECT_URL = "https://www.etsy.com/oauth/connect"
SCOPES = "shops_r transactions_r"
SYNC_FALLBACK_SECRET = "etsy-vault-fallback-secret-2026"  # used by Profit Calculator when no secret is set

_token_lock = threading.Lock()
_pending: dict[str, dict] = {}  # OAuth state -> {verifier, redirect, created}
_last_oauth_event: dict = {}


class EtsyError(ApiError):
    pass


# ---------------------------------------------------------------- credentials

def keys() -> tuple[str, str]:
    keystring = vault.get("etsy_keystring") or ""
    secret = vault.get("etsy_shared_secret") or ""
    if not keystring:
        raise EtsyError("Etsy Keystring не налаштовано. Відкрийте Налаштування → Etsy.", 400, {"code": "etsy_keys"})
    return keystring, secret


def api_key_header() -> dict:
    keystring, secret = keys()
    return {"x-api-key": f"{keystring}:{secret}" if secret else keystring}


def default_redirect_uri() -> str:
    # Always the registered port: even when it is busy, the paste-back flow still accepts the code.
    return f"http://localhost:{state.wanted_port}/etsy/callback"


def redirect_uri() -> str:
    return (core.settings.section("etsy").get("redirectUri") or "").strip() or default_redirect_uri()


def tokens() -> dict | None:
    data = vault.get_json("etsy_tokens")
    return data if isinstance(data, dict) and data.get("access_token") else None


def save_tokens(data: dict) -> None:
    data = dict(data)
    data["updated_at"] = core.now_iso()
    vault.set_json("etsy_tokens", data)
    if data.get("shop_id"):
        core.settings.update({"etsy": {"shopId": data.get("shop_id"), "shopName": data.get("shop_name")}})


def port_warning() -> str | None:
    """The default callback contains the port; if another program took it, Etsy would reject the new one."""
    custom = (core.settings.section("etsy").get("redirectUri") or "").strip()
    if custom or state.port == state.wanted_port:
        return None
    return (f"Порт {state.wanted_port} зайняла інша програма, тому Book Studio зараз працює на порту {state.port}. "
            f"Після входу в Etsy сторінка повернення не відкриється сама — скопіюйте адресу з браузера й вставте "
            f"її сюди, або закрийте програму, що зайняла порт, і перезапустіть Book Studio.")


def status() -> dict:
    t = tokens()
    return {
        "portWarning": port_warning(),
        "keysConfigured": bool(vault.get("etsy_keystring")),
        "secretConfigured": bool(vault.get("etsy_shared_secret")),
        "connected": bool(t),
        "shopId": (t or {}).get("shop_id") or core.settings.section("etsy").get("shopId"),
        "shopName": (t or {}).get("shop_name") or core.settings.section("etsy").get("shopName"),
        "userId": (t or {}).get("user_id"),
        "expiresAt": (t or {}).get("expires_at"),
        "redirectUri": redirect_uri(),
        "defaultRedirectUri": default_redirect_uri(),
    }


# ---------------------------------------------------------------- errors

def _human(err: httpc.HttpError, action: str) -> EtsyError:
    body = httpc.short_body(err.body)
    if err.status in (401, 403):
        if "invalid_grant" in body or "invalid_token" in body or "expired" in body.lower():
            return EtsyError(f"{action}: авторизація Etsy недійсна або прострочена. Підключіть Etsy заново.", 400,
                             {"code": "etsy_auth"})
        return EtsyError(f"{action}: Etsy відмовив у доступі ({err.status}). Перевірте ключі в Налаштуваннях. {body}",
                         400, {"code": "etsy_auth"})
    if err.status == 404:
        return EtsyError(f"{action}: Etsy не знайшов об'єкт (404).", 404)
    if err.status == 429:
        return EtsyError(f"{action}: перевищено ліміт запитів Etsy. Спробуйте за хвилину.", 429)
    if err.status is None:
        return EtsyError(f"{action}: немає з'єднання з Etsy. Перевірте інтернет.", 502)
    return EtsyError(f"{action}: помилка Etsy ({err.status}). {body}", 502)


# ---------------------------------------------------------------- OAuth / tokens

def _b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _user_id_from(access_token: str) -> str:
    return access_token.split(".")[0] if "." in access_token else ""


def start_oauth() -> dict:
    keystring, _ = keys()
    verifier = _b64url(secrets.token_bytes(32))
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    oauth_state = secrets.token_hex(16)
    redirect = redirect_uri()
    _pending[oauth_state] = {"verifier": verifier, "redirect": redirect, "created": time.time()}
    for key in [k for k, v in _pending.items() if time.time() - v["created"] > 3600]:
        _pending.pop(key, None)
    query = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": keystring,
        "redirect_uri": redirect,
        "scope": SCOPES,
        "state": oauth_state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }, quote_via=urllib.parse.quote)
    return {"authUrl": f"{CONNECT_URL}?{query}", "redirectUri": redirect, "state": oauth_state}


def complete_oauth(code: str, oauth_state: str) -> dict:
    pending = _pending.pop(oauth_state, None)
    if not pending:
        raise EtsyError("Посилання авторизації застаріло або вже використане. Почніть підключення заново.")
    keystring, _ = keys()
    try:
        data = httpc.request_json("POST", TOKEN_URL, form={
            "grant_type": "authorization_code",
            "client_id": keystring,
            "redirect_uri": pending["redirect"],
            "code": code,
            "code_verifier": pending["verifier"],
        }, retries=1, timeout=30)
    except httpc.HttpError as err:
        if err.status in (400, 401):
            raise EtsyError("Etsy не прийняв код авторизації: код уже використано або він застарів (діє кілька хвилин), "
                            "чи Callback URL не збігається із зареєстрованим. Почніть підключення заново.", 400,
                            {"code": "etsy_auth"}) from None
        raise _human(err, "Обмін коду Etsy") from None
    access = data.get("access_token") or ""
    record = {
        "access_token": access,
        "refresh_token": data.get("refresh_token") or "",
        "expires_at": int(time.time() * 1000) + int(data.get("expires_in") or 3600) * 1000,
        "user_id": _user_id_from(access),
    }
    save_tokens(record)
    try:
        ensure_shop()
    except EtsyError:
        core.log.warning("Shop lookup right after OAuth failed; will retry on next request")
    return status()


def refresh_tokens(force: bool = False) -> dict:
    with _token_lock:
        t = tokens()
        if not t:
            raise EtsyError("Etsy не підключено. Відкрийте Налаштування → Etsy.", 400, {"code": "etsy_not_connected"})
        expires = int(t.get("expires_at") or 0)
        if not force and expires - int(time.time() * 1000) > 300_000:
            return t
        if not t.get("refresh_token"):
            return t
        keystring, _ = keys()
        try:
            data = httpc.request_json("POST", TOKEN_URL, form={
                "grant_type": "refresh_token",
                "client_id": keystring,
                "refresh_token": t["refresh_token"],
            }, retries=2, timeout=30)
        except httpc.HttpError as err:
            # Etsy answers a dead refresh token with 400 (often with an empty body), not 401.
            if err.status in (400, 401, 403):
                raise EtsyError(
                    "Сесія Etsy більше не дійсна. Etsy видає одноразові ключі оновлення: якщо цю саму сесію "
                    "оновила інша програма (наприклад, Profit Calculator), тут вона перестає працювати. "
                    "Перенесіть сесію знову (Налаштування → Etsy) або авторизуйтесь з київського ПК.",
                    400, {"code": "etsy_auth"}) from None
            raise _human(err, "Оновлення доступу Etsy") from None
        access = data.get("access_token") or t["access_token"]
        t.update({
            "access_token": access,
            "refresh_token": data.get("refresh_token") or t["refresh_token"],
            "expires_at": int(time.time() * 1000) + int(data.get("expires_in") or 3600) * 1000,
            "user_id": _user_id_from(access) or t.get("user_id"),
        })
        save_tokens(t)
        return t


def _auth_headers() -> dict:
    t = refresh_tokens()
    return {**api_key_header(), "Authorization": f"Bearer {t['access_token']}"}


def get(path: str, params: dict | None = None, action: str = "Запит до Etsy", auth: bool = True) -> Any:
    url = f"{API}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    headers = _auth_headers() if auth else api_key_header()
    try:
        return httpc.request_json("GET", url, headers=headers, timeout=45)
    except httpc.HttpError as err:
        if auth and err.status == 401:
            # Access token may have been revoked/rotated early — refresh once and retry.
            refresh_tokens(force=True)
            try:
                return httpc.request_json("GET", url, headers=_auth_headers(), timeout=45)
            except httpc.HttpError as err2:
                raise _human(err2, action) from None
        raise _human(err, action) from None


def ensure_shop() -> tuple[Any, str]:
    t = refresh_tokens()
    if t.get("shop_id"):
        return t["shop_id"], t.get("shop_name") or ""
    user_id = t.get("user_id") or _user_id_from(t.get("access_token", ""))
    shop_id = shop_name = None
    try:
        # getMe (scope shops_r) returns user_id + shop_id in one documented call.
        me = get("/users/me", action="Дані акаунта Etsy")
        shop_id, user_id = me.get("shop_id"), me.get("user_id") or user_id
        if shop_id:
            shop_name = (get(f"/shops/{shop_id}", action="Дані магазину Etsy") or {}).get("shop_name")
    except EtsyError:
        pass  # older grants / missing scope: fall back to the owner lookup below
    if not shop_id:
        data = get(f"/users/{user_id}/shops", action="Пошук магазину Etsy")
        if isinstance(data, dict):
            if data.get("results"):
                shop_id, shop_name = data["results"][0].get("shop_id"), data["results"][0].get("shop_name")
            elif data.get("shop_id"):
                shop_id, shop_name = data.get("shop_id"), data.get("shop_name")
    if not shop_id:
        raise EtsyError("Etsy не повернув магазин для цього акаунта.", 404)
    with _token_lock:
        # Re-read: the lookups above may have rotated the refresh token; never write back a stale one.
        fresh = tokens() or t
        fresh.update({"shop_id": shop_id, "shop_name": shop_name, "user_id": str(user_id)})
        save_tokens(fresh)
    return shop_id, shop_name or ""


def disconnect() -> None:
    vault.set("etsy_tokens", None)
    core.settings.update({"etsy": {"shopId": None, "shopName": None}})


# ---------------------------------------------------------------- session keys (Profit Calculator compatible)

def _session_key_material(secret: str) -> bytes:
    return hashlib.sha256((secret or SYNC_FALLBACK_SECRET).encode("utf-8")).digest()


def decode_session_key(raw: str) -> dict:
    """Accepts a sync key or a full `?sync=` link from Etsy Profit Calculator."""
    text = (raw or "").strip()
    if not text:
        raise EtsyError("Вставте ключ сесії або посилання.")
    if "sync=" in text:
        parsed = urllib.parse.urlsplit(text)
        text = (urllib.parse.parse_qs(parsed.query).get("sync") or [""])[0].strip()
    parts = text.split(":")
    secret = vault.get("etsy_shared_secret") or ""
    data: Any = None
    if len(parts) == 3 and all(re.fullmatch(r"[0-9a-fA-F]+", p or "x") for p in parts):
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            raise EtsyError("Для імпорту ключа потрібен пакет Python «cryptography».") from None
        iv, tag, cipher = (bytes.fromhex(p) for p in parts)
        last_error = None
        for candidate in (secret, SYNC_FALLBACK_SECRET) if secret else (SYNC_FALLBACK_SECRET,):
            try:
                plain = AESGCM(_session_key_material(candidate)).decrypt(iv, cipher + tag, None)
                data = json.loads(plain.decode("utf-8"))
                break
            except Exception as err:  # wrong secret -> InvalidTag
                last_error = err
        if data is None:
            raise EtsyError("Не вдалося розшифрувати ключ. Перевірте, що Shared Secret у Налаштуваннях той самий, "
                            "що й у Profit Calculator.") from last_error
    else:
        try:
            data = json.loads(base64.b64decode(text + "=" * (-len(text) % 4)).decode("utf-8"))
        except Exception:
            raise EtsyError("Невірний формат ключа сесії.") from None
    if not isinstance(data, dict) or not data.get("access_token"):
        raise EtsyError("Ключ не містить токена доступу Etsy.")
    return data


def encode_session_key(data: dict) -> str:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    iv = secrets.token_bytes(16)
    sealed = AESGCM(_session_key_material(vault.get("etsy_shared_secret") or "")).encrypt(
        iv, json.dumps(data, separators=(",", ":")).encode("utf-8"), None)
    cipher, tag = sealed[:-16], sealed[-16:]
    return f"{iv.hex()}:{tag.hex()}:{cipher.hex()}"


def import_session(raw: str) -> dict:
    data = decode_session_key(raw)
    record = {
        "access_token": data["access_token"],
        "refresh_token": data.get("refresh_token") or "",
        "expires_at": int(data.get("expires_at") or 0),
        "user_id": str(data.get("user_id") or _user_id_from(data["access_token"])),
        "shop_id": data.get("shop_id"),
        "shop_name": data.get("shop_name"),
    }
    save_tokens(record)
    try:
        refresh_tokens()
        ensure_shop()
    except EtsyError as err:
        if err.extra.get("code") == "etsy_auth":
            disconnect()  # the imported session is dead — do not keep it
            raise
        core.log.warning("Imported Etsy session could not be verified yet: %s", err)
        return {**status(), "warning": str(err)}
    return status()


# ---------------------------------------------------------------- listings

def parse_listing_ref(ref: str) -> str:
    text = (ref or "").strip()
    m = re.search(r"/listing/(\d{5,})", text) or re.fullmatch(r"\s*(\d{5,})\s*", text)
    if not m:
        raise EtsyError("Вставте посилання на лістинг Etsy (etsy.com/listing/…) або його числовий ID.")
    return m.group(1)


def fetch_listing(listing_id: str) -> dict:
    # One request: getListing can embed the images (includes=Images).
    data = get(f"/listings/{listing_id}", {"includes": "Images"}, action="Перевірка лістингу", auth=False)
    results = list(data.get("images") or [])
    if not results:
        try:
            results = list((get(f"/listings/{listing_id}/images", action="Фото лістингу", auth=False) or {}).get("results") or [])
        except EtsyError:
            results = []
    image_url = None
    if results:
        results.sort(key=lambda r: r.get("rank") or 0)
        image_url = results[0].get("url_fullxfull") or results[0].get("url_570xN")
    return {
        "id": str(data.get("listing_id") or listing_id),
        "title": data.get("title") or "",
        "state": data.get("state") or "",
        "shopId": data.get("shop_id"),
        "url": data.get("url") or f"https://www.etsy.com/listing/{listing_id}",
        "imageUrl": image_url,
        "verifiedAt": core.now_iso(),
    }


# ---------------------------------------------------------------- receipts

def fetch_all_receipts(progress=None, min_last_modified: int | None = None) -> tuple[list, Any, str]:
    """Paid receipts (cancelled and refunded ones included — they stay was_paid), newest first.

    With min_last_modified only receipts changed since then (epoch seconds) are returned.
    """
    shop_id, shop_name = ensure_shop()
    receipts: list = []
    offset, total = 0, None
    while True:
        params = {"limit": 100, "offset": offset, "was_paid": "true", "sort_on": "created", "sort_order": "desc"}
        if min_last_modified:
            params["min_last_modified"] = int(min_last_modified)
        data = get(f"/shops/{shop_id}/receipts", params, action="Завантаження замовлень Etsy")
        batch = (data or {}).get("results") or []
        total = (data or {}).get("count", total)
        receipts.extend(batch)
        offset += len(batch)
        if progress:
            progress(len(receipts), total)
        if not batch or len(batch) < 100 or (total is not None and offset >= total) or offset >= 20000:
            break
        time.sleep(0.12)  # stay far below Etsy's rate limit
    return receipts, shop_id, shop_name


# ---------------------------------------------------------------- routes

@route("GET", "/api/etsy/status")
def _status(req: Request):
    return status()


@route("POST", "/api/etsy/oauth/start")
def _oauth_start(req: Request):
    return start_oauth()


@route("POST", "/api/etsy/oauth/complete")
def _oauth_complete(req: Request):
    body = req.json or {}
    url = (body.get("url") or "").strip()
    parsed = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qs(parsed.query)
    if q.get("error"):
        raise EtsyError(f"Etsy відхилив авторизацію: {(q.get('error_description') or q['error'])[0]}")
    code = (q.get("code") or [""])[0]
    oauth_state = (q.get("state") or [""])[0]
    if not code or not oauth_state:
        raise EtsyError("У посиланні немає коду авторизації. Скопіюйте повну адресу сторінки після входу.")
    return complete_oauth(code, oauth_state)


@route("GET", "/etsy/callback", auth="none")
def _oauth_callback(req: Request):
    code, oauth_state = req.param("code", ""), req.param("state", "")
    title, message, ok = "Etsy підключено", "Можна закрити це вікно й повернутися в Book Studio.", True
    if req.param("error"):
        title, message, ok = "Авторизацію скасовано", req.param("error_description") or req.param("error"), False
    else:
        try:
            result = complete_oauth(code, oauth_state)
            if result.get("shopName"):
                message = f"Магазин {result['shopName']} підключено. Можна закрити це вікно."
        except ApiError as err:
            title, message, ok = "Не вдалося підключити Etsy", str(err), False
    _last_oauth_event.update({"ok": ok, "message": message, "at": time.time()})
    color = "#16a34a" if ok else "#e11d48"
    return html_response(f"""<!doctype html><meta charset="utf-8"><title>{title}</title>
<body style="font-family:Segoe UI,sans-serif;background:#111;color:#eee;display:grid;place-items:center;height:100vh;margin:0">
<div style="text-align:center;max-width:520px"><div style="font-size:44px;color:{color}">{'✓' if ok else '!'}</div>
<h2>{title}</h2><p style="color:#aaa">{message}</p></div></body>""")


@route("POST", "/api/etsy/session/import")
def _session_import(req: Request):
    return import_session((req.json or {}).get("key", ""))


@route("GET", "/api/etsy/session/export")
def _session_export(req: Request):
    t = tokens()
    if not t:
        raise EtsyError("На цьому комп'ютері немає активної сесії Etsy.", 400)
    try:
        return {"key": encode_session_key(t)}
    except ImportError:
        raise EtsyError("Для експорту ключа потрібен пакет Python «cryptography».") from None


@route("POST", "/api/etsy/disconnect")
def _disconnect(req: Request):
    disconnect()
    return status()


@route("GET", "/api/etsy/listing")
def _listing(req: Request):
    return fetch_listing(parse_listing_ref(req.param("ref", "")))
