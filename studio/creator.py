"""Order Creator: Printify unpublished photo-book products and Gelato draft orders.

Printify: folder with Cover.png + 1..N.png (N from the Master, 24) ->
  strict validation -> upload artwork (hash cache) -> new product built from the
  read-only Master configuration -> verification -> Master untouched check.
Gelato: folder with Cover.png + 1..30.png -> light validation -> interior PDF ->
  temporary public link -> draft order (orderType=draft) -> link kept 15 min.
Nothing is ever published, ordered or sent to production.
"""
from __future__ import annotations

import re
import shutil
import threading
import uuid
from concurrent.futures import CancelledError, ThreadPoolExecutor
from pathlib import Path

from . import core, desktop, gelato, images, printify, profit, tunnel
from .jobs import JobError, jobs
from .server import ApiError, Request, file_response, route
from .vault import vault

UPLOAD_CACHE = core.data_path("creator", "upload-cache.json")
HISTORY = core.data_path("creator", "history.json")
_cache_lock = threading.Lock()
_history_lock = threading.Lock()
_validation_cache: dict[tuple, dict] = {}

REQUIRED_ADDRESS = ("firstName", "lastName", "addressLine1", "city", "postCode", "country")
STATE_REQUIRED = {"US", "CA", "AU"}


# ---------------------------------------------------------------- folder listing / validation

def _natural_key(name: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def _files_by_lower(folder: Path) -> dict[str, Path]:
    return {p.name.lower(): p for p in folder.iterdir() if p.is_file()}


def _signature(folder: Path) -> tuple:
    return tuple(sorted((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in folder.iterdir() if p.is_file()))


def expected_files(mode: str) -> list[dict]:
    if mode == "printify":
        cfg = core.settings.section("printify")
        count = int(cfg.get("pageCount") or 24)
        cover, page = cfg.get("coverSize") or [4672, 2464], cfg.get("pageSize") or [4000, 4000]
        out = [{"file": "Cover.png", "position": "cover", "size": cover}]
        out += [{"file": f"{i}.png", "position": f"page_{i}", "size": page} for i in range(1, count + 1)]
        return out
    count = int(core.settings.section("gelato").get("pageCount") or 30)
    out = [{"file": "Cover.png", "position": "cover", "size": None}]
    out += [{"file": f"{i}.png", "position": f"page_{i}", "size": None} for i in range(1, count + 1)]
    return out


def validate(mode: str, folder_raw: str, job=None) -> dict:
    folder = Path((folder_raw or "").strip().strip('"'))
    if not folder_raw or not folder.is_dir():
        return {"ok": False, "folder": str(folder), "errors": ["Папку не знайдено або шлях некоректний."],
                "warnings": [], "files": [], "found": 0, "expected": len(expected_files(mode))}
    expected = expected_files(mode)
    key = (mode, str(folder.resolve()), _signature(folder),
           tuple((e["file"], tuple(e["size"] or ())) for e in expected))
    if key in _validation_cache:
        return _validation_cache[key]

    present = _files_by_lower(folder)
    errors: list[str] = []
    warnings: list[str] = []
    missing = [e["file"] for e in expected if e["file"].lower() not in present]
    expected_lower = {e["file"].lower() for e in expected}
    extra = sorted((p.name for n, p in present.items() if n not in expected_lower and not n.startswith(".")
                    and n not in ("thumbs.db", "desktop.ini")), key=_natural_key)
    if missing:
        pretty = ", ".join(m.replace(".png", "") if m[0].isdigit() else m for m in missing)
        errors.append(f"Відсутні файли ({len(missing)} шт.): {pretty}")
    if extra:
        warnings.append(f"Додаткові файли не буде використано ({len(extra)} шт.): {', '.join(extra[:12])}"
                        + ("…" if len(extra) > 12 else ""))

    rows: list[dict] = []
    todo = [e for e in expected if e["file"].lower() in present]

    def check(entry: dict) -> dict:
        path = present[entry["file"].lower()]
        info, err = images.check_png(path, full_decode=True)
        row = {"file": entry["file"], "position": entry["position"], "path": str(path), "ok": err is None,
               "error": err}
        if info:
            row.update({"width": info["width"], "height": info["height"], "bytes": info["bytes"]})
            if info.get("frames", 1) != 1:
                row["ok"], row["error"] = False, "анімований PNG не підтримується"
            size = entry.get("size")
            if row["ok"] and size and (info["width"], info["height"]) != tuple(size):
                row["ok"] = False
                row["error"] = (f"розмір {info['width']}×{info['height']} px, очікується рівно {size[0]}×{size[1]} px")
        if row["ok"] and mode == "printify":
            row["sha256"] = images.sha256_file(path)
        return row

    done = [0]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for row in pool.map(check, todo):
            rows.append(row)
            done[0] += 1
            if job:
                job.progress("Перевірка файлів…", 100 * done[0] / max(len(todo), 1), row["file"])
    order = {e["file"]: i for i, e in enumerate(expected)}
    rows.sort(key=lambda r: order[r["file"]])
    for row in rows:
        if not row["ok"]:
            label = "Обкладинка" if row["position"] == "cover" else f"Сторінка {row['file'][:-4]}"
            errors.append(f"{label} ({row['file']}): {row['error']}")
    if mode == "printify":
        seen: dict[str, str] = {}
        for row in rows:
            sha = row.get("sha256")
            if sha and sha in seen:
                warnings.append(f"Файли {seen[sha]} і {row['file']} однакові (дублікат зображення).")
            elif sha:
                seen[sha] = row["file"]
    result = {
        "ok": not errors and len(rows) == len(expected),
        "folder": str(folder),
        "errors": errors,
        "warnings": warnings,
        "files": rows,
        "found": len(rows),
        "expected": len(expected),
        "totalBytes": sum(r.get("bytes", 0) for r in rows),
    }
    if len(_validation_cache) > 40:
        _validation_cache.clear()
    _validation_cache[key] = result
    threading.Thread(target=_warm_previews, args=([r["path"] for r in rows],), daemon=True).start()
    return result


def _warm_previews(paths: list[str]) -> None:
    """Prepares the spread previews in the background so the viewer opens instantly."""
    for p in paths:
        try:
            images.preview(Path(p), 1400)
        except Exception:
            pass


# ---------------------------------------------------------------- history

def add_history(entry: dict) -> None:
    with _history_lock:
        items = core.read_json(HISTORY, []) or []
        items.insert(0, {**entry, "at": core.now_iso()})
        core.write_json(HISTORY, items[:200])


# ---------------------------------------------------------------- Printify draft

def _load_upload_cache() -> dict:
    return core.read_json(UPLOAD_CACHE, {}) or {}


def _remember_upload(sha: str, image_id: str) -> None:
    with _cache_lock:
        cache = _load_upload_cache()
        cache[sha] = image_id
        core.write_json(UPLOAD_CACHE, cache, backup=False)


def build_printify_payload(title: str, image_ids: dict[str, str], cfg: dict) -> dict:
    master = cfg["master"]
    placements = master.get("placements") or {}
    placeholders = []
    for entry in expected_files("printify"):
        pos = entry["position"]
        coords = placements.get(pos)
        if not coords:
            raise JobError(f"У налаштуваннях Master немає позиції «{pos}». Проаналізуйте Master заново.")
        placeholders.append({
            "position": pos,
            "images": [{"id": image_ids[pos], "x": coords["x"], "y": coords["y"],
                        "scale": coords["scale"], "angle": coords["angle"]}],
        })
    return {
        "title": title,
        "description": master.get("description") or "<p></p>",
        "blueprint_id": master["blueprintId"],
        "print_provider_id": master["printProviderId"],
        "variants": [{"id": v["id"], "price": v["price"], "is_enabled": bool(v["is_enabled"])}
                     for v in master.get("variants") or []],
        "print_areas": [{
            "variant_ids": master.get("printAreaVariantIds") or [v["id"] for v in master.get("variants") or []],
            "placeholders": placeholders,
            "background": master.get("background") or "#ffffff",
        }],
    }


def _master_fingerprint(product: dict) -> dict:
    ids = []
    for area in product.get("print_areas") or []:
        for ph in area.get("placeholders") or []:
            ids.append((ph.get("position"), tuple(i.get("id") for i in ph.get("images") or [])))
    return {"title": product.get("title"), "updated_at": product.get("updated_at"), "images": sorted(ids, key=str),
            "visible": product.get("visible"), "external": product.get("external")}


def create_printify_draft(folder: str, title: str, job) -> dict:
    title = (title or "").strip()
    if not title:
        raise JobError("Введіть назву книги.")
    cfg = core.settings.section("printify")
    master = cfg.get("master") or {}
    shop_id = int(cfg.get("shopId") or 0)
    if not shop_id or not master.get("productId"):
        raise JobError("Не налаштовано магазин або Master-продукт Printify (Налаштування → Printify).")
    printify.token()

    job.progress("Перевірка файлів…", 2, "Повна перевірка всіх PNG")
    result = validate("printify", folder, None)
    if not result["ok"]:
        raise JobError("Файли не пройшли перевірку:\n" + "\n".join(result["errors"]))

    job.progress("Читання Master-продукту…", 8, master.get("title") or master["productId"])
    before = printify.product(shop_id, master["productId"])
    if before.get("blueprint_id") != master.get("blueprintId") or before.get("print_provider_id") != master.get("printProviderId"):
        raise JobError("Master-продукт у Printify змінився (blueprint/постачальник). "
                       "Проаналізуйте Master заново в Налаштуваннях.")
    snapshot_dir = core.data_path("creator", "master-snapshots")
    core.write_json(snapshot_dir / f"{core.now_iso().replace(':', '-')}-before.json", before, backup=False)
    fingerprint_before = _master_fingerprint(before)

    cache = _load_upload_cache()
    image_ids: dict[str, str] = {}
    files = result["files"]

    # Already uploaded earlier (same file hash) and still present in Printify -> reuse.
    job.progress("Перевірка вже завантажених файлів…", 10, "")
    cached_rows = [r for r in files if cache.get(r["sha256"])]
    with ThreadPoolExecutor(max_workers=4) as pool:
        alive = list(pool.map(lambda r: printify.upload_exists(cache[r["sha256"]]), cached_rows))
    for row, ok in zip(cached_rows, alive):
        if ok:
            image_ids[row["position"]] = cache[row["sha256"]]
    reused = len(image_ids)
    todo = [r for r in files if r["position"] not in image_ids]

    # New files: three uploads at a time (each is a large base64 request).
    done_count = [0]
    progress_lock = threading.Lock()

    def upload(row: dict) -> tuple[str, str]:
        resp = printify.upload_image(Path(row["path"]), row["file"])
        image_id = resp.get("id")
        if not image_id:
            raise ApiError(f"Printify не повернув ID зображення для {row['file']}.")
        _remember_upload(row["sha256"], image_id)
        with progress_lock:
            done_count[0] += 1
            job.progress(f"Завантаження ілюстрацій… {reused + done_count[0]} з {len(files)}",
                         12 + 74 * done_count[0] / max(len(todo), 1), f"Завантажено {row['file']}")
        return row["position"], image_id

    failures: list[str] = []
    if todo:
        job.progress(f"Завантаження ілюстрацій… {reused} з {len(files)}", 12,
                     f"{len(todo)} файлів · {sum(r.get('bytes', 0) for r in todo) // (1024 * 1024)} МБ")
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {pool.submit(upload, r): r for r in todo}
            for fut, row in futures.items():
                try:
                    pos, image_id = fut.result()
                    image_ids[pos] = image_id
                except CancelledError:
                    continue
                except (ApiError, OSError) as err:
                    failures.append(f"{row['file']}: {err}")
                    for other in futures:
                        other.cancel()  # not-yet-started uploads are skipped; running ones finish
    if failures:
        raise JobError(f"Не вдалося завантажити {failures[0]}\n"
                       f"Уже завантажені файли збережено — повторний запуск продовжить з цього місця.")
    uploaded = len(image_ids) - reused

    expected = expected_files("printify")
    if len(image_ids) != len(expected):
        raise JobError(f"Підготовлено лише {len(image_ids)} з {len(expected)} зображень. Книгу не створено.")

    job.progress("Створення книги в Printify…", 88, "Збирання структури за Master-продуктом")
    payload = build_printify_payload(title, image_ids, cfg)
    try:
        created = printify.create_product(shop_id, payload)
    except ApiError as err:
        upstream = (err.extra or {}).get("upstream")
        if (err.extra or {}).get("ambiguous") or (upstream or 0) >= 500:
            raise JobError("Зв'язок обірвався під час створення — результат невідомий. НЕ запускайте повторно одразу: "
                           "спершу перевірте Printify → My Products, чи з'явилась книга «" + title + "».") from None
        raise JobError(f"Printify відхилив створення книги: {err}") from None
    product_id = created.get("id")
    if not product_id:
        raise JobError("Printify не повернув ID нової книги.")
    url = f"https://printify.com/app/product-details/{product_id}?fromProductsPage=1"
    add_history({"mode": "printify", "title": title, "id": product_id, "url": url, "folder": result["folder"]})

    job.progress("Перевірка результату…", 95, "Звірка сторінок і захисту Master")
    warnings: list[str] = []
    verified = False
    try:
        new_product = printify.product(shop_id, product_id)
        placed = {}
        for area in new_product.get("print_areas") or []:
            for ph in area.get("placeholders") or []:
                placed[ph.get("position")] = [i.get("id") for i in ph.get("images") or []]
        mismatched = [pos for pos, img in image_ids.items() if img not in (placed.get(pos) or [])]
        verified = not mismatched
        if mismatched:
            warnings.append(f"Позиції не збіглися з очікуваними: {', '.join(mismatched[:6])}. Перевірте книгу вручну.")
    except ApiError as err:
        warnings.append(f"Не вдалося перечитати нову книгу: {err}")
    master_safe = None
    try:
        after = printify.product(shop_id, master["productId"])
        master_safe = _master_fingerprint(after) == fingerprint_before
        if not master_safe:
            warnings.append("Увага: Master-продукт має зміни після створення — перевірте його в Printify.")
    except ApiError as err:
        warnings.append(f"Не вдалося перевірити Master: {err}")

    return {"productId": product_id, "url": url, "title": title, "uploaded": uploaded, "reused": reused,
            "total": len(image_ids), "verified": verified, "masterSafe": master_safe, "warnings": warnings}


# ---------------------------------------------------------------- Gelato draft

def validate_address(address: dict) -> list[str]:
    errors = []
    names = {"firstName": "Ім'я", "lastName": "Прізвище", "addressLine1": "Адреса", "city": "Місто",
             "postCode": "Індекс", "country": "Країна"}
    for key in REQUIRED_ADDRESS:
        if not str(address.get(key) or "").strip():
            errors.append(f"Не заповнено поле «{names[key]}».")
    country = str(address.get("country") or "").strip().upper()
    if country in STATE_REQUIRED and not str(address.get("state") or "").strip():
        errors.append(f"Для країни {country} потрібно вказати штат/провінцію.")
    return errors


def create_gelato_draft(folder: str, title: str, format_key: str, address: dict, job) -> dict:
    title = (title or "").strip()
    if not title:
        raise JobError("Введіть назву книги.")
    cfg = core.settings.section("gelato")
    fmt = (cfg.get("formats") or {}).get(format_key)
    if not fmt:
        raise JobError("Оберіть формат книги.")
    gelato.api_key()
    address = {k: str(v).strip() for k, v in (address or {}).items() if v is not None and str(v).strip()}
    if address.get("country"):
        address["country"] = address["country"].upper()
    problems = validate_address(address)
    if problems:
        raise JobError("\n".join(problems))

    job.progress("Перевірка файлів…", 4, "Наявність і цілісність PNG")
    result = validate("gelato", folder, None)
    if not result["ok"]:
        raise JobError("Файли не пройшли перевірку:\n" + "\n".join(result["errors"]))
    pages = [Path(r["path"]) for r in result["files"] if r["position"] != "cover"]
    cover = next(Path(r["path"]) for r in result["files"] if r["position"] == "cover")

    session = uuid.uuid4().hex[:12]
    session_dir = core.data_path("tmp", "gelato", session)
    session_dir.mkdir(parents=True, exist_ok=True)
    link: tunnel.FileTunnel | None = None
    try:
        job.progress("Збирання внутрішнього блоку в PDF…", 15, f"{len(pages)} сторінок без перестиснення")
        import img2pdf
        with open(session_dir / "interior.pdf", "wb") as f:
            f.write(img2pdf.convert([str(p) for p in pages]))
        shutil.copy2(cover, session_dir / "cover.png")

        job.progress("Відкриття тимчасового доступу до файлів…", 35, "Cloudflare Tunnel")
        link = tunnel.FileTunnel(session_dir, ("cover.png", "interior.pdf"))
        try:
            base = link.start()
        except tunnel.TunnelError as err:
            raise JobError(str(err)) from None

        payload = {
            "orderType": "draft",
            "orderReferenceId": f"draft-{session}",
            "customerReferenceId": f"local-review-{session}",
            "currency": cfg.get("currency") or "USD",
            "items": [{
                "itemReferenceId": f"item-{session}",
                "productUid": fmt["productUid"],
                "pageCount": int(cfg.get("pageCount") or 30),
                "quantity": 1,
                "files": [{"type": "default", "url": f"{base}/cover.png"},
                          {"type": "inside", "url": f"{base}/interior.pdf"}],
            }],
            "shippingAddress": address,
            "metadata": [
                {"key": "title", "value": title[:100]},
                {"key": "format", "value": format_key},
                {"key": "source", "value": "book-studio"},
            ],
        }
        job.progress("Створення чернетки в Gelato…", 70, "Очікування відповіді")
        try:
            created = gelato.create_draft_order(payload)
        except ApiError as err:
            raise JobError(f"Gelato відхилив створення чернетки: {err}") from None
        order_id = created.get("id")
        if not order_id:
            raise JobError("Gelato не повернув ID чернетки.")
        keep = int(cfg.get("tunnelKeepAliveSeconds") or 900)
        tunnel.registry.keep(order_id, link, session_dir, keep)
        link = None  # owned by the registry now
        add_history({"mode": "gelato", "title": title, "id": order_id, "reference": payload["orderReferenceId"],
                     "format": fmt.get("label"), "folder": result["folder"]})
        return {"orderId": order_id, "orderReferenceId": payload["orderReferenceId"],
                "fulfillmentStatus": created.get("fulfillmentStatus"), "orderType": created.get("orderType"),
                "format": fmt.get("label"), "keepAliveSeconds": keep, "title": title}
    finally:
        if link is not None:
            link.stop()
            shutil.rmtree(session_dir, ignore_errors=True)


# ---------------------------------------------------------------- personalization helpers

_NAME_HINT = re.compile(r"(child|kid|baby|boy|girl|name|ім'я|имя)", re.I)


def guess_child_name(items: list) -> str:
    for item in items or []:
        for v in item.get("variations") or []:
            name, value = (v.get("name") or ""), (v.get("value") or "").strip()
            if _NAME_HINT.search(name) and value and len(value) <= 40 and "\n" not in value:
                return value
        for v in item.get("variations") or []:
            value = (v.get("value") or "")
            m = re.search(r"(?:child'?s?\s*name|name)\s*[:\-–]\s*([^\n,;]{2,40})", value, re.I)
            if m:
                return m.group(1).strip()
    return ""


# ---------------------------------------------------------------- routes

@route("GET", "/api/creator/status")
def _status(req: Request):
    p = core.settings.section("printify")
    g = core.settings.section("gelato")
    c = core.settings.section("creator")
    return {
        "printify": {
            "shopId": p.get("shopId"), "shopTitle": p.get("shopTitle"),
            "masterId": (p.get("master") or {}).get("productId"), "masterTitle": (p.get("master") or {}).get("title"),
            "pageCount": p.get("pageCount"), "coverSize": p.get("coverSize"), "pageSize": p.get("pageSize"),
            "enabledVariants": [v.get("title") for v in (p.get("master") or {}).get("variants") or [] if v.get("is_enabled")],
            "coverCoords": ((p.get("master") or {}).get("placements") or {}).get("cover"),
            "tokenConfigured": bool(vault.get("printify_token")),
        },
        "gelato": {
            "pageCount": g.get("pageCount"), "keyConfigured": bool(vault.get("gelato_api_key")),
            "formats": [{"key": k, "label": v.get("label")} for k, v in (g.get("formats") or {}).items()],
            "keepAliveSeconds": g.get("tunnelKeepAliveSeconds"),
            "cloudflared": tunnel.CLOUDFLARED.exists(),
            "activeTunnels": tunnel.registry.active(),
        },
        "creator": c,
        "history": (core.read_json(HISTORY, []) or [])[:12],
    }


@route("POST", "/api/creator/prefs")
def _prefs(req: Request):
    body = req.json or {}
    allowed = {k: body[k] for k in ("mode", "printifyFolder", "gelatoFolder", "gelatoFormat", "gelatoAddress") if k in body}
    core.settings.update({"creator": allowed})
    return {"ok": True}


@route("POST", "/api/creator/validate")
def _validate(req: Request):
    body = req.json or {}
    mode = body.get("mode")
    if mode not in ("printify", "gelato"):
        raise ApiError("Невідомий режим.")
    folder = body.get("folder") or ""
    job = jobs.start(f"validate-{mode}", lambda j: validate(mode, folder, j))
    return {"jobId": job.id}


@route("POST", "/api/creator/pick-folder")
def _pick(req: Request):
    body = req.json or {}
    path = desktop.pick_folder(body.get("title") or "Оберіть папку з ілюстраціями книги", body.get("initial") or "")
    return {"path": path}


@route("POST", "/api/creator/printify/create")
def _create_printify(req: Request):
    body = req.json or {}
    folder, title = body.get("folder") or "", body.get("title") or ""
    job = jobs.start("printify-create", lambda j: create_printify_draft(folder, title, j), exclusive="printify-create")
    return {"jobId": job.id}


@route("POST", "/api/creator/gelato/create")
def _create_gelato(req: Request):
    body = req.json or {}
    args = (body.get("folder") or "", body.get("title") or "", body.get("format") or "", body.get("address") or {})
    job = jobs.start("gelato-create", lambda j: create_gelato_draft(*args, j), exclusive="gelato-create")
    return {"jobId": job.id}


@route("POST", "/api/creator/gelato/close-tunnel")
def _close_tunnel(req: Request):
    return {"closed": tunnel.registry.close(str((req.json or {}).get("orderId") or ""))}


@route("GET", "/api/creator/etsy-orders")
def _etsy_orders(req: Request):
    orders = profit.recent_receipts(80)
    for o in orders:
        o["childName"] = guess_child_name(o["items"])
    return {"orders": orders, "syncedAt": profit.load_snapshot().get("syncedAt")}


@route("POST", "/api/creator/open-folder")
def _open_folder(req: Request):
    path = Path((req.json or {}).get("path") or "")
    if not path.is_dir():
        raise ApiError("Папку не знайдено.")
    desktop.open_in_explorer(path)
    return {"ok": True}


@route("GET", "/media/folder", auth="media")
def _folder_media(req: Request):
    folder = Path(req.param("path") or "")
    name = req.param("file") or ""
    if not folder.is_dir() or "/" in name or "\\" in name or Path(name).suffix.lower() not in images.IMAGE_EXTS:
        raise ApiError("Не знайдено.", 404)
    target = _files_by_lower(folder).get(name.lower())
    if not target:
        raise ApiError("Не знайдено.", 404)
    size = max(64, min(4096, int(req.param("w") or 480)))
    return file_response(images.preview(target, size), "image/jpeg", cache="private, max-age=600")


@route("GET", "/media/folder-spread", auth="media")
def _folder_spread(req: Request):
    folder = Path(req.param("path") or "")
    if not folder.is_dir():
        raise ApiError("Не знайдено.", 404)
    present = _files_by_lower(folder)
    sides = []
    for name in (req.param("left"), req.param("right")):
        if not name:
            sides.append(None)
            continue
        if "/" in name or "\\" in name or Path(name).suffix.lower() not in images.IMAGE_EXTS:
            raise ApiError("Не знайдено.", 404)
        sides.append(present.get(name.lower()))
    if not any(sides):
        raise ApiError("Не знайдено.", 404)
    height = max(200, min(2400, int(req.param("h") or 1200)))
    return file_response(images.compose_spread(sides[0], sides[1], height), "image/jpeg", cache="private, max-age=600")
