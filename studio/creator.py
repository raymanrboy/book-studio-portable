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
import struct
import threading
import time
import uuid
import zipfile
import zlib
from concurrent.futures import CancelledError, ThreadPoolExecutor
from pathlib import Path

from . import core, desktop, gelato, images, printify, profit, tunnel
from .jobs import JobError, jobs
from .server import ApiError, Request, file_response, route
from .vault import vault

UPLOAD_CACHE = core.data_path("creator", "upload-cache.json")
_cache_lock = threading.Lock()
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


STRIP_PREVIEW = 360  # page thumbnails in the order card's strip (web/js/pages/orders.js asks for this size)


def _warm_previews(paths: list[str]) -> None:
    """Prepares previews in the background so the viewer and the page strip open instantly
    (the small one is cut from the large one, so it costs almost nothing extra)."""
    for p in paths:
        try:
            images.preview(Path(p), 1400)
            images.preview(Path(p), STRIP_PREVIEW)
        except Exception:
            pass


# ---------------------------------------------------------------- dropped folders and archives
# The app window never learns where a dragged folder lives on disk, so its pictures (or a ZIP)
# are copied into a scratch folder first. Everything there is wiped when the program starts.
DROPS = core.data_path("tmp", "dropped")
DROP_IMAGE = re.compile(r"\.(png|jpe?g|webp)$", re.I)
MAX_DROP_FILE = 400 * 1024 * 1024
MAX_DROP_ZIP = 6 * 1024 * 1024 * 1024
_DROP_SESSION = re.compile(r"[0-9a-f]{32}")


def clear_drops(keep: str | None = None, older_than: float = 0) -> None:
    if not DROPS.is_dir():
        return
    now = time.time()
    for entry in DROPS.iterdir():
        if entry.name == keep:
            continue
        try:
            if now - entry.stat().st_mtime >= older_than:
                shutil.rmtree(entry, ignore_errors=True) if entry.is_dir() else entry.unlink(missing_ok=True)
        except OSError:
            pass


def _drop_root(session: str | None) -> Path:
    if not _DROP_SESSION.fullmatch(session or ""):
        raise ApiError("Некоректний запит.")
    return DROPS / session


def _drop_rel(name: str, with_text: bool = False) -> Path | None:
    """A relative path from the dropped folder or archive, or None when it is not a picture we can use
    (with_text also lets the library's book-text JSON through)."""
    parts = [p for p in re.split(r"[\\/]+", name or "") if p not in ("", ".")]
    if not parts or len(parts) > 6 or any(p == ".." or ":" in p or p == "__MACOSX" for p in parts):
        return None
    usable = DROP_IMAGE.search(parts[-1]) or (with_text and parts[-1].lower().endswith(".json"))
    if parts[-1].startswith("._") or not usable:
        return None
    return Path(*[re.sub(r'[<>"|?*\x00-\x1f]', "_", p).rstrip(" .") or "_" for p in parts])


def extract_zip(archive: Path, target: Path, with_text: bool = False) -> int:
    try:
        zf = zipfile.ZipFile(archive)
    except (zipfile.BadZipFile, OSError):
        raise ApiError("Архів пошкоджений або це не ZIP.") from None
    count = total = 0
    with zf:
        for info in zf.infolist():
            rel = None if info.is_dir() else _drop_rel(info.filename, with_text)
            if rel is None:
                continue
            total += info.file_size
            if total > MAX_DROP_ZIP:
                raise ApiError("Архів завеликий.")
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as src, open(dest, "wb") as out:
                shutil.copyfileobj(src, out, 1024 * 1024)
            count += 1
    if not count:
        raise ApiError("В архіві немає зображень PNG." if not with_text else "В архіві немає ні зображень, ні тексту книги.")
    return count


def dropped_folder(root: Path) -> Path:
    """The folder with Cover.png in what was dropped (the shallowest one), else the folder holding the pictures."""
    files = [p for p in root.rglob("*") if p.is_file()]
    covers = sorted({p.parent for p in files if p.name.lower() == "cover.png"}, key=lambda d: len(d.parts))
    if covers:
        return covers[0]
    holders = {p.parent for p in files}
    return holders.pop() if len(holders) == 1 else root


@route("POST", "/api/creator/drop/file")
def _drop_file(req: Request):
    root = _drop_root(req.param("session"))
    rel = _drop_rel(req.param("name") or "")
    if rel is None:
        raise ApiError("Перетягніть папку з PNG-файлами або ZIP-архів.")
    req.body_to_file(root / rel, MAX_DROP_FILE)
    return {"ok": True}


@route("POST", "/api/creator/drop/zip")
def _drop_zip(req: Request):
    root = _drop_root(req.param("session"))
    stem = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", Path(req.param("name") or "archive.zip").stem).strip(" .")[:80]
    archive = DROPS / f"{root.name}.zip"  # beside the folder, never inside it
    try:
        req.body_to_file(archive, MAX_DROP_ZIP)
        extract_zip(archive, root / (stem or "archive"), with_text=req.param("text") == "1")
    finally:
        archive.unlink(missing_ok=True)
    return {"ok": True}


@route("POST", "/api/creator/drop/done")
def _drop_done(req: Request):
    session = str((req.json or {}).get("session") or "")
    root = _drop_root(session)
    if not root.is_dir():
        raise ApiError("Файли не отримано — перетягніть папку ще раз.")
    clear_drops(keep=session, older_than=2 * 3600)
    return {"path": str(dropped_folder(root))}


# ---------------------------------------------------------------- start empty

def forget_old_form() -> None:
    """Order Creator starts empty every time. Earlier versions remembered the folders, the last
    buyer address and a list of recent drafts — those leftovers are removed once."""
    core.settings.drop_section("creator")
    history = core.data_path("creator", "history.json")
    for path in (history, history.with_name(history.name + ".bak")):
        path.unlink(missing_ok=True)


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
            raise JobError(f"Шаблон Printify (Master) не має позиції «{pos}». Книгу не створено.")
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


def matte_variant(master: dict) -> int | None:
    """The book's finish is always matte: the enabled Master variant whose title says "Matte"."""
    for v in master.get("variants") or []:
        if v.get("is_enabled") and "matte" in str(v.get("title") or "").lower():
            return int(v["id"])
    return None


def printify_order_payload(title: str, product_id: str, variant_id: int, address: dict) -> dict:
    a = {k: str(v or "").strip() for k, v in (address or {}).items()}
    receipt = re.match(r"\s*(\d{6,20})\b", title)  # the Etsy receipt number from "4100000001 - Emma"
    to = {"first_name": a.get("firstName", ""), "last_name": a.get("lastName", ""), "address1": a.get("addressLine1", ""),
          "address2": a.get("addressLine2", ""), "city": a.get("city", ""), "region": a.get("state", ""),
          "zip": a.get("postCode", ""), "country": a.get("country", "").upper()}
    if a.get("phone"):
        to["phone"] = a["phone"]
    return {
        "external_id": f"{receipt.group(1) if receipt else 'book'}-{uuid.uuid4().hex[:8]}",
        "label": title[:100],
        "line_items": [{"product_id": product_id, "variant_id": variant_id, "quantity": 1}],
        "shipping_method": 1,  # standard
        "is_printify_express": False,
        "is_economy_shipping": False,
        "send_shipping_notification": False,
        "address_to": to,
    }


def create_printify_draft(folder: str, title: str, job, address: dict | None = None) -> dict:
    """An unpublished Printify book; with an address also an order for it that waits "On hold"."""
    title = (title or "").strip()
    if not title:
        raise JobError("Введіть назву книги.")
    cfg = core.settings.section("printify")
    master = cfg.get("master") or {}
    shop_id = int(cfg.get("shopId") or 0)
    if not shop_id or not master.get("productId"):
        raise JobError("Не налаштовано магазин або Master-продукт Printify (Налаштування → Printify).")
    printify.token()
    variant_id = None
    if address:  # everything about the order is checked before a single file is uploaded
        problems = validate_address(address)
        if problems:
            raise JobError("\n".join(problems))
        if not printify.manual_approval_confirmed():
            raise JobError("Спершу підтвердіть, що в Printify увімкнене ручне затвердження замовлень.")
        variant_id = matte_variant(master)
        if not variant_id:
            raise JobError("У шаблоні Printify (Master) немає увімкненого матового варіанту — замовлення не створено.")

    job.progress("Перевірка файлів…", 2, "Повна перевірка всіх PNG")
    result = validate("printify", folder, None)
    if not result["ok"]:
        raise JobError("Файли не пройшли перевірку:\n" + "\n".join(result["errors"]))

    job.progress("Читання Master-продукту…", 8, master.get("title") or master["productId"])
    before = printify.product(shop_id, master["productId"])
    if before.get("blueprint_id") != master.get("blueprintId") or before.get("print_provider_id") != master.get("printProviderId"):
        raise JobError("Шаблон Printify (Master) змінився: інший тип книги або постачальник друку. "
                       "Книгу не створено — перевірте Master-продукт у Printify.")
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

    order = order_error = None
    if address:
        job.progress("Чернетка замовлення в Printify…", 98, "Замовлення на утриманні — без відправки у виробництво")
        try:
            placed = printify.create_order_on_hold(shop_id, printify_order_payload(title, product_id, variant_id, address))
            order = {"id": placed.get("id"), "variant": next((v.get("title") for v in master.get("variants") or []
                                                             if int(v.get("id") or 0) == variant_id), "Matte")}
        except ApiError as err:
            # The book itself exists; the order is what failed — say which, so nothing is placed twice.
            if (err.extra or {}).get("ambiguous") or ((err.extra or {}).get("upstream") or 0) >= 500:
                order_error = ("Зв'язок обірвався під час створення замовлення — результат невідомий. Спершу перевірте "
                               "Printify → Orders; якщо замовлення там немає — оформіть його вручну з цієї книги.")
            else:
                order_error = f"Книгу створено, але Printify відхилив замовлення: {err}. Його можна оформити вручну з цієї книги."

    return {"productId": product_id, "url": url, "title": title, "uploaded": uploaded, "reused": reused,
            "total": len(image_ids), "verified": verified, "masterSafe": master_safe, "warnings": warnings,
            "order": order, "orderError": order_error}


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


MM_TO_PT = 72 / 25.4
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _one_idat(src: Path, dst: Path) -> Path:
    """The same PNG with its compressed pixel data in a single IDAT chunk — nothing is re-encoded.

    Canva writes thousands of 8 KB IDAT chunks; img2pdf 0.6 joins them one by one (quadratic copying,
    ~3 s per page). Joined once here, img2pdf reads the page in milliseconds.
    """
    data = src.read_bytes()
    if data[:8] != PNG_SIGNATURE:
        return src
    chunks, idat, pos = [], [], 8
    while pos + 8 <= len(data):
        length, kind = struct.unpack(">I4s", data[pos:pos + 8])
        chunks.append((kind, data[pos:pos + 12 + length]))
        if kind == b"IDAT":
            idat.append(data[pos + 8:pos + 8 + length])
        pos += 12 + length
    if len(idat) <= 1:
        return src
    body = b"".join(idat)
    merged = struct.pack(">I", len(body)) + b"IDAT" + body + struct.pack(">I", zlib.crc32(b"IDAT" + body) & 0xFFFFFFFF)
    out, placed = [PNG_SIGNATURE], False
    for kind, raw in chunks:
        if kind == b"IDAT":
            if not placed:
                out.append(merged)
                placed = True
            continue
        out.append(raw)
    dst.write_bytes(b"".join(out))
    return dst


def build_photobook_pdf(cover: Path, pages: list[Path], out: Path, geo: dict) -> list[str]:
    """One PDF laid out the way Gelato prints a photo book (its only accepted file for books):

      page 1          — the cover sheet (back + spine + front);
      page 2          — blank: inside of the front cover;
      pages 3 … N+2   — the inner pages in order;
      last page       — blank: inside of the back cover.

    Every PDF page gets Gelato's physical size; pictures are embedded without recompression and
    scaled to fill their page (a slightly different aspect is trimmed evenly at the edges).
    Returns warnings when that trim would reach the visible part of the cover.
    """
    import img2pdf
    from PIL import Image

    cover_page = (geo["coverMm"][0] * MM_TO_PT, geo["coverMm"][1] * MM_TO_PT)
    inner_page = (geo["pageMm"][0] * MM_TO_PT, geo["pageMm"][1] * MM_TO_PT)
    work = out.parent / "pdf-work"
    work.mkdir(exist_ok=True)
    try:
        blank = work / "blank.png"
        Image.new("RGB", (16, 16), (255, 255, 255)).save(blank)
        ready = [_one_idat(p, work / f"{i:03d}.png") for i, p in enumerate([cover, *pages])]
        sequence = [(ready[0], cover_page), (blank, inner_page)] + [(p, inner_page) for p in ready[1:]] + [(blank, inner_page)]
        sizes = iter([size for _, size in sequence])  # img2pdf lays images out in the order they are given

        def layout(img_w: float, img_h: float, _dpi) -> tuple:
            page_w, page_h = next(sizes)
            scale = max(page_w / img_w, page_h / img_h)
            return page_w, page_h, img_w * scale, img_h * scale

        with open(out, "wb") as f:
            f.write(img2pdf.convert([str(p) for p, _ in sequence], layout_fun=layout))
    finally:
        shutil.rmtree(work, ignore_errors=True)

    warnings = []
    with Image.open(cover) as im:
        img_w, img_h = im.size
    want_w, want_h = geo["coverMm"]
    scale = max(want_w / img_w, want_h / img_h)
    trim_side = max(img_w * scale - want_w, img_h * scale - want_h) / 2
    if trim_side > geo.get("marginMm", 3) * 0.8:
        need = f"{round(want_w)}×{round(want_h)} мм (≈ {want_w / want_h:.3f}:1)"
        warnings.append(f"Пропорції Cover.png ({img_w}×{img_h}) відрізняються від обкладинки Gelato {need}: "
                        f"краї обріжуться на {trim_side:.1f} мм і зачеплять видиму частину. "
                        f"Експортуйте обкладинку з шаблону Gelato.")
    return warnings


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

    page_count = int(cfg.get("pageCount") or 30)
    job.progress("Розміри книги в Gelato…", 8, fmt.get("label") or format_key)
    try:
        geo = gelato.photobook_geometry(fmt["productUid"], page_count)
    except ApiError as err:
        raise JobError(str(err)) from None

    session = uuid.uuid4().hex[:12]
    session_dir = core.data_path("tmp", "gelato", session)
    session_dir.mkdir(parents=True, exist_ok=True)
    link: tunnel.FileTunnel | None = None
    try:
        job.progress("Збирання книги в один PDF…", 15, f"обкладинка + {len(pages)} сторінок, без перестиснення")
        warnings = build_photobook_pdf(cover, pages, session_dir / "book.pdf", geo)

        job.progress("Відкриття тимчасового доступу до файлів…", 35, "Cloudflare Tunnel")
        link = tunnel.FileTunnel(session_dir, ("book.pdf",))
        try:
            base = link.start()
        except tunnel.TunnelError as err:
            raise JobError(str(err)) from None

        # The Etsy receipt number from the title ("4100000001 - Emma") goes into the reference, so the
        # order is matched to its receipt at the next sync and leaves the "new" queue.
        receipt = re.match(r"\s*(\d{6,20})\b", title)
        payload = {
            "orderType": "draft",
            "orderReferenceId": f"{receipt.group(1)}-{session[:8]}" if receipt else f"draft-{session}",
            "customerReferenceId": f"local-review-{session}",
            "currency": cfg.get("currency") or "USD",
            "items": [{
                "itemReferenceId": f"item-{session}",
                "productUid": fmt["productUid"],
                "pageCount": page_count,  # inner pages; Gelato adds the four cover sides itself
                "quantity": 1,
                # A photo book takes one multi-page PDF of type "default" (cover sheet, blank, pages, blank).
                # ("inside" only exists for folded cards — Gelato then filled every page with the cover.)
                "files": [{"type": "default", "url": f"{base}/book.pdf"}],
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
        return {"orderId": order_id, "orderReferenceId": payload["orderReferenceId"],
                "fulfillmentStatus": created.get("fulfillmentStatus"), "orderType": created.get("orderType"),
                "format": fmt.get("label"), "keepAliveSeconds": keep, "title": title, "warnings": warnings,
                "pdfPages": len(pages) + 3}
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
    return {
        "printify": {
            "shopId": p.get("shopId"), "shopTitle": p.get("shopTitle"),
            "masterId": (p.get("master") or {}).get("productId"), "masterTitle": (p.get("master") or {}).get("title"),
            "pageCount": p.get("pageCount"), "coverSize": p.get("coverSize"), "pageSize": p.get("pageSize"),
            "enabledVariants": [v.get("title") for v in (p.get("master") or {}).get("variants") or [] if v.get("is_enabled")],
            "coverCoords": ((p.get("master") or {}).get("placements") or {}).get("cover"),
            "tokenConfigured": bool(vault.get("printify_token")),
            "manualApproval": printify.manual_approval_confirmed(),
            "matteVariant": bool(matte_variant(p.get("master") or {})),
        },
        "gelato": {
            "pageCount": g.get("pageCount"), "keyConfigured": bool(vault.get("gelato_api_key")),
            "formats": [{"key": k, "label": v.get("label")} for k, v in (g.get("formats") or {}).items()],
            "defaultFormat": g.get("defaultFormat"),
            "keepAliveSeconds": g.get("tunnelKeepAliveSeconds"),
            "cloudflared": tunnel.CLOUDFLARED.exists(),
            "activeTunnels": tunnel.registry.active(),
        },
    }


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
    address = body.get("address") if isinstance(body.get("address"), dict) else None  # with it: book + order on hold
    job = jobs.start("printify-create", lambda j: create_printify_draft(folder, title, j, address), exclusive="printify-create")
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
    orders = profit.picker_orders()
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
