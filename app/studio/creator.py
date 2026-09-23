"""Order Creator: Printify unpublished photo-book products and Gelato draft orders.

Printify: folder with Cover.png + 1..N.png (N from the Master, 24) ->
  strict validation -> upload artwork (hash cache) -> new product built from the
  read-only Master configuration -> verification -> Master untouched check.
Gelato: folder with Cover.png + 1..30.png (or 1..28.png) -> light validation -> interior PDF ->
  temporary public link -> draft order (orderType=draft) -> link kept 15 min.
Nothing is ever published, ordered or sent to production.
"""
from __future__ import annotations

import contextlib
import copy
import math
import os
import re
import shutil
import struct
import threading
import time
import uuid
import zipfile
import zlib
from collections import Counter
from concurrent.futures import CancelledError, ThreadPoolExecutor
from pathlib import Path

from . import archive, core, desktop, gelato, images, printify, profit, sendlog, tunnel, wording
from .jobs import JobError, jobs
from .server import ApiError, Request, file_response, route
from .vault import vault

UPLOAD_CACHE = core.data_path("creator", "upload-cache.json")
REPLACED = ".replaced"          # the pages a new one was put over, kept here so «Повернути» can work
_cache_lock = threading.Lock()
_validation_cache: dict[tuple, dict] = {}
# (mode, folder) -> the number of the newest check the page asked for: an older one of the same folder stops
# (new files or a replaced page start a new check; two full checks of one folder need not run side by side).
_validating: dict[tuple, int] = {}

REQUIRED_ADDRESS = ("firstName", "lastName", "addressLine1", "city", "postCode", "country")
STATE_REQUIRED = {"US", "CA", "AU"}


# ---------------------------------------------------------------- folder listing / validation

def _natural_key(name: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", name)]


def _files_by_lower(folder: Path) -> dict[str, Path]:
    return {p.name.lower(): p for p in folder.iterdir() if p.is_file()}


def _signature(folder: Path) -> tuple:
    return tuple(sorted((p.name, st.st_size, st.st_mtime_ns) for p in folder.iterdir() if p.is_file()
                        for st in [p.stat()]))


def _backups(folder: Path, name: str) -> list[Path]:
    """The previous versions of one page, oldest first: what «Повернути» can put back."""
    keep = folder / REPLACED
    return sorted(keep.glob(f"{name}.*")) if keep.is_dir() else []


_sending: Counter[str] = Counter()  # print folder -> sends reading it right now (two printers at once: 2)
_sending_lock = threading.Lock()


@contextlib.contextmanager
def _while_sending(folders):
    """A send checks the files, then uploads them, builds the PDF and copies them to the archive — all by
    reading the same paths again. While that runs, the pages must not change under it, or what the printer
    gets is not what passed the check. Replacing a page waits for the send to finish."""
    mine = {str(Path(f).resolve()) for f in folders if f}
    with _sending_lock:
        _sending.update(mine)
    try:
        yield
    finally:
        with _sending_lock:
            _sending.subtract(mine)
            for key in mine:
                if _sending[key] <= 0:
                    del _sending[key]


@contextlib.contextmanager
def _not_while_sending(folder: Path):
    """A page changes only while no send reads its folder — and no send starts until the change is done."""
    with _sending_lock:
        if _sending.get(str(folder.resolve())):
            raise ApiError("Книга саме відправляється в друкарню — зачекайте, поки відправка завершиться.")
        yield


def gelato_page_options() -> list[int]:
    """How long a Gelato book may be: as long as the Canva export — 30 pages, or 28 without one spread."""
    return sorted(int(n) for n in core.settings.section("gelato").get("pageCounts") or [28, 30])


def _gelato_page_count(present: dict[str, Path]) -> int:
    """The book length a Gelato folder is meant for: the shortest allowed one that holds its highest page."""
    options = gelato_page_options()
    top = max((int(m.group(1)) for name in present if (m := re.fullmatch(r"(\d+)\.png", name))), default=0)
    return next((n for n in options if n >= top), options[-1])


def expected_files(mode: str, count: int | None = None) -> list[dict]:
    if mode == "printify":
        cfg = core.settings.section("printify")
        count = int(cfg.get("pageCount") or 24)
        cover, page = cfg.get("coverSize") or [4672, 2464], cfg.get("pageSize") or [4000, 4000]
        out = [{"file": "Cover.png", "position": "cover", "size": cover}]
        out += [{"file": f"{i}.png", "position": f"page_{i}", "size": page} for i in range(1, count + 1)]
        return out
    count = count or gelato_page_options()[-1]
    out = [{"file": "Cover.png", "position": "cover", "size": None}]
    out += [{"file": f"{i}.png", "position": f"page_{i}", "size": None} for i in range(1, count + 1)]
    return out


def _forget_validation(folder: Path) -> None:
    """A page of this folder changed: its earlier results go (other folders' stay)."""
    here = str(folder.resolve())
    with _cache_lock:
        for key in [k for k in _validation_cache if k[1] == here]:
            del _validation_cache[key]


def validate(mode: str, folder_raw: str, job=None) -> dict:
    """The full check of a print folder. The result is the caller's own copy (a send keeps using its rows).
    With a job (the page asked): a newer check of the same folder stops this one; a send's own check
    (no job) is never stopped."""
    folder = Path((folder_raw or "").strip().strip('"'))
    if not folder_raw or not folder.is_dir():
        expected = expected_files(mode)
        return {"ok": False, "folder": str(folder), "errors": ["Папку не знайдено або шлях некоректний."],
                "warnings": [], "files": [], "found": 0, "expected": len(expected), "pageCount": len(expected) - 1}
    present = _files_by_lower(folder)
    expected = expected_files(mode, _gelato_page_count(present) if mode == "gelato" else None)
    key = (mode, str(folder.resolve()), _signature(folder),
           tuple((e["file"], tuple(e["size"] or ())) for e in expected))
    with _cache_lock:
        if key in _validation_cache:
            return copy.deepcopy(_validation_cache[key])
        ticket = None
        if job is not None:
            slot = key[:2]
            _validating[slot] = _validating.get(slot, 0) + 1
            ticket = (slot, _validating[slot])

    def superseded() -> bool:
        return ticket is not None and _validating.get(ticket[0]) != ticket[1]

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
        if superseded():
            raise JobError("Цю перевірку замінила новіша.")
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
        # «Повернути» is offered from what is on disk, so it survives leaving the card and a restart.
        row["replaced"] = bool(_backups(folder, entry["file"]))
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
        "pageCount": len(expected) - 1,
        "totalBytes": sum(r.get("bytes", 0) for r in rows),
    }
    with _cache_lock:
        if len(_validation_cache) > 40:
            _validation_cache.pop(next(iter(_validation_cache)))  # the oldest goes
        _validation_cache[key] = copy.deepcopy(result)
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


def dropped_top(root: Path) -> Path:
    """The dropped folder itself (the library's importer reads its generated/ and pages/ too): down through
    folders that hold nothing but one folder."""
    folder = root
    while True:
        items = list(folder.iterdir())
        if len(items) != 1 or not items[0].is_dir():
            return folder
        folder = items[0]


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
    rel = _drop_rel(req.param("name") or "", with_text=req.param("text") == "1")
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
    body = req.json or {}
    session = str(body.get("session") or "")
    root = _drop_root(session)
    if not root.is_dir():
        raise ApiError("Файли не отримано — перетягніть папку ще раз.")
    clear_drops(keep=session, older_than=2 * 3600)
    return {"path": str(dropped_top(root) if body.get("whole") else dropped_folder(root))}


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


UPLOADS_KEPT = 5000  # pictures whose Printify id is remembered (~40 books a month for a year); the oldest go


def _remember_upload(sha: str, image_id: str) -> None:
    with _cache_lock:
        cache = _load_upload_cache()
        cache.pop(sha, None)
        cache[sha] = image_id  # newest last
        for old in list(cache)[:max(0, len(cache) - UPLOADS_KEPT)]:
            del cache[old]      # an old picture sent again is simply uploaded again
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


def printify_order_payload(title: str, lines: list[tuple[str, int]], address: dict, receipt: str | None = None) -> dict:
    """One order for the whole receipt: a line item per book of it, all to the same address."""
    a = {k: str(v or "").strip() for k, v in (address or {}).items()}
    to = {"first_name": a.get("firstName", ""), "last_name": a.get("lastName", ""), "address1": a.get("addressLine1", ""),
          "address2": a.get("addressLine2", ""), "city": a.get("city", ""), "region": a.get("state", ""),
          "zip": a.get("postCode", ""), "country": a.get("country", "").upper()}
    if a.get("phone"):
        to["phone"] = a["phone"]
    return {
        "external_id": f"{receipt or 'book'}-{uuid.uuid4().hex[:8]}",
        "label": title[:100],
        "line_items": [{"product_id": pid, "variant_id": vid, "quantity": 1} for pid, vid in lines],
        "shipping_method": 1,  # standard
        "is_printify_express": False,
        "is_economy_shipping": False,
        "send_shipping_notification": False,
        "address_to": to,
    }


def receipt_for(title: str, given=None) -> str | None:
    """The Etsy receipt a send belongs to: the one the page names (the order it came from), else the number
    in front of the title typed by hand. A title that names another receipt than its order is refused —
    the printer's reference, the archive and the local records must not tell two different orders."""
    given = str(given or "").strip()
    if given and not re.fullmatch(r"\d{6,20}", given):
        raise JobError("Некоректний номер замовлення Etsy.")
    typed = archive.receipt_of(title)
    if given and typed and typed != given:
        raise JobError(f"Назва «{title}» починається з номера {typed}, а книга із замовлення {given}. "
                       f"Виправте номер у назві.")
    return given or typed


def books_of(raw) -> list[dict]:
    """The books of one Etsy order as the page sends them — a folder, a name, its receipt and (Gelato) a format
    each. An order with two or three books goes to the printer as one order to one address (owner, 20.09.2026)."""
    books = []
    for item in raw if isinstance(raw, list) else [raw]:
        item = item if isinstance(item, dict) else {}
        title = str(item.get("title") or "").strip()
        if not title:
            raise JobError("Введіть назву книги.")
        books.append({"folder": str(item.get("folder") or "").strip().strip('"'), "title": title,
                      "format": str(item.get("format") or "").strip(),
                      "receipt": receipt_for(title, item.get("receiptId"))})
    if not books:
        raise JobError("Немає жодної книги для відправки.")
    return books


def joint_title(books: list[dict]) -> str:
    """The name of an order of several books: «4100000001 - Emma, Liam». The receipt number stays in front,
    so the print order still finds its Etsy receipt at the next sync."""
    if len(books) == 1:
        return books[0]["title"]
    receipt = books[0].get("receipt")
    names = [archive.child_of(b["title"]) for b in books]
    return (f"{receipt} - {', '.join(names)}" if receipt else " + ".join(b["title"] for b in books))[:100]


def create_printify_draft(books, job, address: dict | None = None) -> dict:
    """Unpublished Printify books, one per book of the order; with an address also a single order for all
    of them that waits "On hold". Every attempt is written to the send journal."""
    books = books_of(books)
    with sendlog.attempt("printify", "book+order" if address else "book", joint_title(books)) as log, \
            _while_sending(b["folder"] for b in books):
        result = _printify_draft(books, job, address, log)
        log["result"] = result
    return _journaled(result, log)


def _journaled(result: dict, log: dict) -> dict:
    """The journal's file name, known only once the attempt is written, goes to the result and the archive."""
    result["sendLog"] = log["file"]
    for eid in {b.get("archiveId") for b in result.get("books") or []} | {result.get("archiveId")}:
        if eid:
            archive.update(eid, sendLog=log["file"])
    return result


def _to_archive(log: dict, job, warnings: list[str], provider: str, files: list[tuple[Path, str]], meta: dict) -> str | None:
    """Keeps what was just sent in the order archive. A failure here never undoes the send: the book is
    in Printify / Gelato, the result only says the archive copy is missing."""
    job.progress("Збереження в архів замовлень…", 97, f"{len(files)} файлів")
    try:
        eid = archive.store(provider, files, meta)
    except Exception as err:
        core.log.exception("Archive: store failed")
        warnings.append(f"Книгу відправлено, але в архів замовлень її не збережено: {err}")
        sendlog.step(log, "archive", error=str(err))
        return None
    sendlog.step(log, "archive", id=eid)
    return eid


def _remember_sent(log: dict, warnings: list[str], books: list, provider: str, order_id: str | None) -> None:
    """Which print order this program made for which receipt. The books of one order can go in two goes,
    or to two printers, and then one receipt really has two print orders; nothing else proves it, because
    a receipt number in the printer's own text also appears on reprints. Never fails a finished send —
    but a record that could not be written is said, like the reprint mark's."""
    receipts = {b.get("receipt") for b in books}
    try:
        written = [r for r in receipts if r and profit.remember_print_order(r, provider, order_id)]
    except Exception as err:
        core.log.exception("Print order not remembered")
        sendlog.step(log, "printOrderRemembered", ok=False, error=str(err))
        warnings.append(f"Замовлення вже створено в {provider.capitalize()}, але програма не записала, до якого "
                        f"замовлення Etsy воно належить: {err}. Не надсилайте ще раз.")
        return
    sendlog.step(log, "printOrderRemembered", ok=bool(written), receipts=sorted(r for r in receipts if r))


def _mark_reprint(log: dict, warnings: list[str], receipt: str | None, provider: str, order_id: str | None) -> None:
    """A reprint is recorded as a replacement of its Etsy order (the queue keeps the first print order).
    A failure here never undoes the send — but it must not be quiet either: the order is already in the
    printer, so the owner has to know that only the local record is missing, and not send it again."""
    try:
        marked = profit.mark_reprint(receipt, provider, order_id)
    except Exception as err:
        core.log.exception("Reprint mark failed")
        sendlog.step(log, "reprintMarked", ok=False, error=str(err))
        warnings.append(f"Замовлення вже створено в {provider.capitalize()}, але програма не записала його "
                        f"як передрук: {err}. Не надсилайте ще раз — перевірте собівартість вручну.")
        return
    sendlog.step(log, "reprintMarked", ok=marked)


def _printify_files(book: dict, job, log: dict, at: float) -> dict:
    """Every PNG of one book read in full — before anything at all is uploaded."""
    job.progress(f"Перевірка файлів{book['mark']}…", at, "Повна перевірка всіх PNG")
    result = validate("printify", book["folder"], None)
    sendlog.step(log, "files", book=book["title"], folder=str(book["folder"]), ok=result["ok"],
                 pageCount=result.get("pageCount"), errors=result["errors"], warnings=result["warnings"],
                 files=[{k: r.get(k) for k in ("file", "width", "height", "bytes", "sha256", "ok", "error")}
                        for r in result["files"]])
    if not result["ok"]:
        raise JobError(f"Файли{book['mark']} не пройшли перевірку:\n" + "\n".join(result["errors"]))
    return result


def _printify_images(book: dict, job, log: dict, span) -> dict[str, str]:
    """This book's images in Printify: the ones sent before (same file hash, still there) are reused, the
    rest go up three at a time. A failure stops the send; a repeat carries on from where it stopped."""
    files = book["checked"]["files"]
    cache = _load_upload_cache()
    image_ids: dict[str, str] = {}
    job.progress(f"Перевірка вже завантажених файлів{book['mark']}…", span(0), "")
    cached_rows = [r for r in files if cache.get(r["sha256"])]
    with ThreadPoolExecutor(max_workers=4) as pool:
        alive = list(pool.map(lambda r: printify.upload_exists(cache[r["sha256"]]), cached_rows))
    for row, ok in zip(cached_rows, alive):
        if ok:
            image_ids[row["position"]] = cache[row["sha256"]]
    reused = len(image_ids)
    todo = [r for r in files if r["position"] not in image_ids]
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
            job.progress(f"Завантаження ілюстрацій{book['mark']}… {reused + done_count[0]} з {len(files)}",
                         span(done_count[0] / max(len(todo), 1)), f"Завантажено {row['file']}")
        return row["position"], image_id

    failures: list[str] = []
    if todo:
        job.progress(f"Завантаження ілюстрацій{book['mark']}… {reused} з {len(files)}", span(0),
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
    sendlog.step(log, "uploads", book=book["title"], reused=reused, uploaded=len(image_ids) - reused,
                 failures=failures, images={pos: image_ids[pos] for pos in sorted(image_ids)})
    if failures:
        raise JobError(f"Не вдалося завантажити {failures[0]}\n"
                       f"Уже завантажені файли збережено — повторний запуск продовжить з цього місця.")
    expected = expected_files("printify")
    if len(image_ids) != len(expected):
        raise JobError(f"Підготовлено лише {len(image_ids)} з {len(expected)} зображень. "
                       f"Книгу{book['mark']} не створено.")
    book["reused"] = reused
    return image_ids


def _printify_product(book: dict, job, log: dict, cfg: dict, shop_id: int, span) -> dict:
    """One unpublished book: its images uploaded, the product built by the Master's configuration, then read
    back to see every page on its own position."""
    image_ids = _printify_images(book, job, log, lambda p: span(0.02 + 0.84 * p))
    job.progress(f"Створення книги в Printify{book['mark']}…", span(0.88), "Збирання структури за Master-продуктом")
    payload = build_printify_payload(book["title"], image_ids, cfg)
    log.setdefault("request", payload)   # the first book's, as before; every book's is in its own step
    try:
        created = printify.create_product(shop_id, payload)
        log.setdefault("response", created)
        sendlog.step(log, "product", book=book["title"], request=payload, response=created)
    except ApiError as err:
        sendlog.step(log, "product", book=book["title"], request=payload, error=str(err))
        if _unknown_outcome(err):
            raise JobError("Зв'язок обірвався під час створення — результат невідомий. НЕ запускайте повторно одразу: "
                           "спершу перевірте Printify → My Products, чи з'явилась книга «" + book["title"] + "».") from None
        raise JobError(f"Printify відхилив створення книги: {err}") from None
    product_id = created.get("id")
    if not product_id:
        raise JobError("Printify не повернув ID нової книги.")

    job.progress(f"Перевірка результату{book['mark']}…", span(0.95), "Звірка сторінок")
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
    sendlog.step(log, "verify", book=book["title"], productId=product_id, verified=verified, warnings=list(warnings))
    return {"title": book["title"], "productId": product_id, "verified": verified, "warnings": warnings,
            "url": f"https://printify.com/app/product-details/{product_id}?fromProductsPage=1",
            "uploaded": len(image_ids) - book["reused"], "reused": book["reused"], "total": len(image_ids)}


def _printify_order(books: list[dict], made: list[dict], variant_id: int, address: dict, job, log: dict,
                    cfg: dict, shop_id: int) -> tuple[dict | None, str | None]:
    """One order "On hold" for every book of the receipt. The books themselves are already in Printify: an
    order that fails says so, and it can still be placed by hand from them."""
    master = cfg.get("master") or {}
    job.progress("Чернетка замовлення в Printify…", 96,
                 f"{'Книги' if len(made) > 1 else 'Замовлення'} на утриманні — без відправки у виробництво")
    payload = printify_order_payload(joint_title(books), [(m["productId"], variant_id) for m in made], address,
                                     books[0].get("receipt"))
    log["orderRequest"] = payload
    try:
        placed = printify.create_order_on_hold(shop_id, payload)
    except ApiError as err:
        log["orderError"] = str(err)
        # The books themselves exist; the order is what failed — say which, so nothing is placed twice.
        if _unknown_outcome(err):
            return None, ("Зв'язок обірвався під час створення замовлення — результат невідомий. Спершу перевірте "
                          "Printify → Orders; якщо замовлення там немає — оформіть його вручну з цих книг.")
        return None, (f"{'Книги' if len(made) > 1 else 'Книгу'} створено, але Printify відхилив замовлення: {err}. "
                      f"Його можна оформити вручну з них.")
    log["orderResponse"] = placed
    return {"id": placed.get("id"), "variant": _variant_title(master, variant_id), "books": len(made)}, None


def _unknown_outcome(err: ApiError) -> bool:
    """The printer may have done it anyway: the connection dropped after sending, or it failed on its own
    side. Then nothing may be sent again until the owner has looked — a second send makes a second one."""
    extra = err.extra or {}
    return bool(extra.get("ambiguous")) or (extra.get("upstream") or 0) >= 500


def _printify_setup(address: dict | None) -> tuple[dict, int, int | None]:
    """What every Printify send checks before a single file is uploaded: shop, Master and token; for an order
    also the address, the manual approval and the matte variant. Returns (settings, shop id, variant id)."""
    cfg = core.settings.section("printify")
    master = cfg.get("master") or {}
    shop_id = int(cfg.get("shopId") or 0)
    if not shop_id or not master.get("productId"):
        raise JobError("Не налаштовано магазин або Master-продукт Printify (Налаштування → Printify).")
    printify.token()
    if not address:
        return cfg, shop_id, None
    problems = validate_address(address)
    if problems:
        raise JobError("\n".join(problems))
    if not printify.manual_approval_confirmed():
        raise JobError(printify.MANUAL_APPROVAL_NEEDED)
    variant_id = matte_variant(master)
    if not variant_id:
        raise JobError("У шаблоні Printify (Master) немає увімкненого матового варіанту — замовлення не створено.")
    return cfg, shop_id, variant_id


def _variant_title(master: dict, variant_id: int) -> str:
    return next((v.get("title") for v in master.get("variants") or [] if int(v.get("id") or 0) == variant_id), "Matte")


def _printify_draft(books: list[dict], job, address: dict | None, log: dict, reprint_of: str | None = None) -> dict:
    for book in books:
        book["mark"] = f" · {book['title']}" if len(books) > 1 else ""
    log["folder"] = str(books[0]["folder"])
    log["books"] = [{"title": b["title"], "folder": str(b["folder"])} for b in books]
    cfg, shop_id, variant_id = _printify_setup(address)
    master = cfg.get("master") or {}

    for book in books:  # no book of an order is made while another one's files are still wrong
        book["checked"] = _printify_files(book, job, log, 2)

    job.progress("Читання Master-продукту…", 8, master.get("title") or master["productId"])
    before = printify.product(shop_id, master["productId"])
    sendlog.step(log, "master", productId=master["productId"], title=before.get("title"),
                 blueprintId=before.get("blueprint_id"), printProviderId=before.get("print_provider_id"),
                 updatedAt=before.get("updated_at"))
    if before.get("blueprint_id") != master.get("blueprintId") or before.get("print_provider_id") != master.get("printProviderId"):
        raise JobError("Шаблон Printify (Master) змінився: інший тип книги або постачальник друку. "
                       "Книгу не створено — перевірте Master-продукт у Printify.")
    snapshot_dir = core.data_path("creator", "master-snapshots")
    core.write_json(snapshot_dir / f"{core.now_iso().replace(':', '-')}-before.json", before, backup=False)
    fingerprint_before = _master_fingerprint(before)

    made: list[dict] = []
    for i, book in enumerate(books):
        low, step = 10 + 80 * i / len(books), 80 / len(books)
        made.append(_printify_product(book, job, log, cfg, shop_id, lambda p, low=low, step=step: low + step * p))

    warnings = [f"{m['title']}: {w}" if len(made) > 1 else w for m in made for w in m["warnings"]]
    master_safe = None
    try:
        after = printify.product(shop_id, master["productId"])
        master_safe = _master_fingerprint(after) == fingerprint_before
        if not master_safe:
            warnings.append("Увага: Master-продукт має зміни після створення — перевірте його в Printify.")
    except ApiError as err:
        warnings.append(f"Не вдалося перевірити Master: {err}")
    sendlog.step(log, "masterSafe", ok=master_safe)

    order = order_error = None
    if address:
        order, order_error = _printify_order(books, made, variant_id, address, job, log, cfg, shop_id)

    # The books are in Printify now (with or without their order): keep exactly these files in the archive.
    if order:
        if reprint_of:
            _mark_reprint(log, warnings, books[0].get("receipt"), "printify", order["id"])
        else:
            _remember_sent(log, warnings, books, "printify", order["id"])
    for book, m in zip(books, made):
        m["archiveId"] = _to_archive(log, job, warnings, "printify",
                                     [(Path(r["path"]), r["file"]) for r in book["checked"]["files"]],
                                     {"title": m["title"], "receiptId": book.get("receipt"),
                                      "productId": m["productId"], "url": m["url"],
                                      "orderId": order["id"] if order else None,
                                      "variant": order["variant"] if order else None,
                                      "address": address or None, "reprintOf": reprint_of})
        m.pop("warnings", None)

    first = made[0]
    return {"archiveId": first["archiveId"], "productId": first["productId"], "url": first["url"],
            "title": joint_title(books), "books": made, "uploaded": sum(m["uploaded"] for m in made),
            "reused": sum(m["reused"] for m in made), "total": sum(m["total"] for m in made),
            "verified": all(m["verified"] for m in made), "masterSafe": master_safe, "warnings": warnings,
            "order": order, "orderError": order_error}


def create_printify_reprint(archive_id: str, title: str, address: dict | None, job) -> dict:
    """A reprint of an archived Printify book: a new order "On hold" for the book already in Printify —
    nothing is uploaded and no product is made. If the book is gone from Printify, it is made again
    from the archived files (images already in Printify are reused). Journaled like every send."""
    title = (title or "").strip()
    with sendlog.attempt("printify", "reprint", title) as log, \
            _while_sending([archive.folder(archive_id)]):
        result = _printify_reprint(archive_id, title, address, job, log)
        log["result"] = result
    return _journaled(result, log)


def _printify_reprint(archive_id: str, title: str, address: dict | None, job, log: dict) -> dict:
    log["reprintOf"] = archive_id
    entry = archive.get(archive_id)
    if entry.get("provider") != "printify" or not entry.get("productId"):
        raise JobError("Ця книга надрукована не в Printify — для передруку створіть її як звичайну відправку.")
    if not title:
        raise JobError("Введіть назву книги.")
    if not address:
        raise JobError("Для передруку потрібна адреса отримувача.")
    receipt = receipt_for(title, entry.get("receiptId"))
    cfg, shop_id, variant_id = _printify_setup(address)
    master = cfg.get("master") or {}

    product_id = entry["productId"]
    job.progress("Книга в Printify…", 15, product_id)
    try:
        product = printify.product(shop_id, product_id)
    except ApiError as err:
        if getattr(err, "status", None) != 404:
            raise JobError(f"Не вдалося прочитати книгу в Printify: {err}") from None
        product = None
    sendlog.step(log, "product", productId=product_id, found=product is not None,
                 title=(product or {}).get("title"))
    if product is None:  # deleted in Printify meanwhile: the archived files make it again
        result = _printify_draft(books_of([{"folder": str(archive.folder(archive_id)), "title": title,
                                            "receiptId": receipt}]),
                                 job, address, log, reprint_of=archive_id)
        result["reprint"] = True
        result["warnings"].insert(0, "Книги в Printify вже не було — її створено заново з файлів архіву.")
        return result

    job.progress("Замовлення-передрук у Printify…", 60, "На утриманні — без відправки у виробництво")
    order_payload = printify_order_payload(title, [(product_id, variant_id)], address, receipt)
    log["orderRequest"] = order_payload
    try:
        placed = printify.create_order_on_hold(shop_id, order_payload)
    except ApiError as err:
        if _unknown_outcome(err):
            raise JobError("Зв'язок обірвався під час створення замовлення — результат невідомий. НЕ запускайте "
                           "повторно одразу: спершу перевірте Printify → Orders.") from None
        raise JobError(f"Printify відхилив замовлення-передрук: {err}") from None
    log["orderResponse"] = placed
    order = {"id": placed.get("id"), "variant": _variant_title(master, variant_id)}
    warnings: list[str] = []
    _mark_reprint(log, warnings, receipt, "printify", order["id"])
    url = entry.get("url") or f"https://printify.com/app/product-details/{product_id}?fromProductsPage=1"
    kept = archive.folder(archive_id)
    new_id = _to_archive(log, job, warnings, "printify", [(kept / r["file"], r["file"]) for r in entry.get("files") or []], {
        "title": title, "receiptId": receipt, "productId": product_id, "url": url, "orderId": order["id"],
        "variant": order["variant"], "address": address, "reprintOf": archive_id})
    return {"reprint": True, "archiveId": new_id, "productId": product_id, "url": url, "title": title,
            "order": order, "orderError": None, "warnings": warnings, "total": len(entry.get("files") or [])}


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


COVER_TRIM_WARN_MM = 10  # the Canva cover is always a few mm off Gelato's; only a wrong picture trims more
GELATO_PLACEHOLDER_PHONE = "+1 555 555 0100"  # a made-up number (555-01xx is reserved for fiction)
BLANK_DPI = 300  # the blank endpapers, as in the PDFs Gelato makes itself (1725 px for a 14 cm page)


def build_photobook_pdf(cover: Path, pages: list[Path], out: Path, geo: dict) -> dict:
    """One PDF laid out the way Gelato prints a photo book (its only accepted file for books):

      page 1          — the cover sheet (back + spine + front);
      page 2          — blank: the front endpaper (Gelato's draft view calls it "Page 0");
      pages 3 … N+2   — the inner pages in order ("Page 1" … "Page N");
      last page       — blank: the back endpaper (not shown in the draft view).

    The blanks are required: without them the book's page 1 took the endpaper's place ("Page 0")
    and the last page was left empty (test draft, 17.09.2026). The PDF Gelato itself printed for the
    owner's good API order (made over in Gelato's editor) has the same shape; only a book from that
    editor is listed without "Page 0". The blanks are white pictures at print resolution: Gelato rates
    the whole book by its poorest picture, and a 16-pixel blank made it 3 dpi.

    Every PDF page gets Gelato's physical size; pictures are embedded without recompression and
    scaled to fill their page (a slightly different aspect is trimmed evenly at the edges).
    Returns what was built, for the send journal, with a warning only when the cover loses much more
    than the usual few millimetres.
    """
    import img2pdf
    from PIL import Image

    cover_page = (geo["coverMm"][0] * MM_TO_PT, geo["coverMm"][1] * MM_TO_PT)
    inner_page = (geo["pageMm"][0] * MM_TO_PT, geo["pageMm"][1] * MM_TO_PT)
    work = out.parent / "pdf-work"
    work.mkdir(exist_ok=True)
    try:
        blank = work / "blank.png"
        blank_px = tuple(math.ceil(mm / 25.4 * BLANK_DPI) for mm in geo["pageMm"])
        Image.new("RGB", blank_px, (255, 255, 255)).save(blank)
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

    with Image.open(cover) as im:
        img_w, img_h = im.size
    want_w, want_h = geo["coverMm"]
    scale = max(want_w / img_w, want_h / img_h)
    trim_side = round(max(img_w * scale - want_w, img_h * scale - want_h) / 2, 2)
    warnings = []
    if trim_side > COVER_TRIM_WARN_MM:
        warnings.append(f"Cover.png ({img_w}×{img_h}) зовсім іншої форми, ніж обкладинка Gelato "
                        f"{round(want_w)}×{round(want_h)} мм: краї обріжуться на {trim_side:.0f} мм. "
                        f"Перевірте, що це справді обкладинка.")
    return {"pdfPages": len(sequence), "pdfBytes": out.stat().st_size, "coverPx": [img_w, img_h],
            "coverMm": geo["coverMm"], "pageMm": geo["pageMm"], "coverTrimMm": trim_side, "warnings": warnings}


def gelato_page_counts() -> dict[str, list[int] | None]:
    """For every Gelato format, the page counts its catalog accepts (read only). None where the catalog
    could not be read (no key, no internet): the draft checks again before anything is made."""
    formats = core.settings.section("gelato").get("formats") or {}

    def one(fmt: dict) -> list[int] | None:
        try:
            return gelato.page_counts(fmt["productUid"]) or None
        except ApiError:
            return None

    with ThreadPoolExecutor(max_workers=3) as pool:
        return dict(zip(formats, pool.map(one, formats.values())))


def _pages_problem(label: str, valid: list[int] | None, count: int) -> str | None:
    """The one wording of "Gelato does not print this length" — the order card and the Order Creator both show
    it (the page gets it ready-made from the page-counts route, 22.09.2026 audit)."""
    if not valid or count in valid:
        return None
    text = f"Gelato не друкує {label} на {count} сторінках (можна від {valid[0]})."
    other = next((n for n in gelato_page_options() if n in valid), None)
    return text + (f" Скачайте з Canva {other} сторінок." if other else "")


def gelato_pages_problem(format_key: str, count: int) -> str | None:
    """Why Gelato would refuse a book of `count` pages in this format; None when it is fine or unknown."""
    fmt = (core.settings.section("gelato").get("formats") or {}).get(format_key)
    if not fmt:
        return None
    try:
        valid = gelato.page_counts(fmt["productUid"])
    except ApiError:
        return None
    return _pages_problem(fmt.get("label") or format_key, valid, count)


def _journal_readback(log: dict, order_id: str, sizes: list[int]) -> None:
    """What Gelato itself recorded for the new draft (read only): usually it has already fetched the PDFs."""
    try:
        items = gelato.get_order(order_id).get("items") or []
    except ApiError as err:
        sendlog.step(log, "readback", error=str(err))
        return
    for item in items:
        files = [{k: f.get(k) for k in ("type", "mimeType", "sizeBytes")} for f in item.get("files") or []]
        sendlog.step(log, "readback", productUid=item.get("productUid"), pageCount=item.get("pageCount"),
                     status=item.get("fulfillmentStatus"), files=files,
                     fileFetched=any(f.get("sizeBytes") in sizes for f in files),
                     events=item.get("eventLog"), refusal=item.get("refusalReason"))


def create_gelato_draft(books, address: dict, job, reprint_of: str | None = None) -> dict:
    """A Gelato draft order for the books of one Etsy order — several books travel as items of one draft to
    one address. Every attempt is written to the send journal.
    reprint_of: the archived book this draft reprints (then the folder is that book's archive folder)."""
    books = books_of(books)
    with sendlog.attempt("gelato", "reprint" if reprint_of else "draft", joint_title(books)) as log, \
            _while_sending(b["folder"] for b in books):
        result = _gelato_draft(books, address, job, log, reprint_of)
        log["result"] = result
    return _journaled(result, log)


def _gelato_book(book: dict, job, log: dict, cfg: dict, at: float) -> dict:
    """One book of the draft: its files checked, its length taken from the folder and confirmed against
    Gelato's catalog, and the sizes of the book Gelato will print read from the same catalog."""
    fmt = (cfg.get("formats") or {}).get(book["format"])
    if not fmt:
        raise JobError("Оберіть формат книги.")
    job.progress(f"Перевірка файлів{book['mark']}…", at, "Наявність і цілісність PNG")
    result = validate("gelato", book["folder"], None)
    sendlog.step(log, "files", book=book["title"], folder=str(book["folder"]), ok=result["ok"],
                 pageCount=result.get("pageCount"), errors=result["errors"],
                 files=[{k: r.get(k) for k in ("file", "width", "height", "bytes", "ok", "error")} for r in result["files"]])
    if not result["ok"]:
        raise JobError(f"Файли{book['mark']} не пройшли перевірку:\n" + "\n".join(result["errors"]))
    pages = [Path(r["path"]) for r in result["files"] if r["position"] != "cover"]
    cover = next(Path(r["path"]) for r in result["files"] if r["position"] == "cover")

    page_count = len(pages)  # 28 or 30, as downloaded from Canva; the catalog below confirms Gelato prints it
    job.progress(f"Розміри книги в Gelato{book['mark']}…", at + 2, f"{fmt.get('label') or book['format']} · {page_count} стор.")
    problem = gelato_pages_problem(book["format"], page_count)
    if problem:
        raise JobError(f"{book['title']}: {problem}" if book["mark"] else problem)
    try:
        geo = gelato.photobook_geometry(fmt["productUid"], page_count)
    except ApiError as err:
        raise JobError(str(err)) from None
    sendlog.step(log, "catalog", book=book["title"], productUid=fmt["productUid"], pageCount=page_count, geometry=geo)
    return {**book, "fmt": fmt, "files": result["files"], "pages": pages, "cover": cover,
            "pageCount": page_count, "geometry": geo}


def _gelato_draft(books: list[dict], address: dict, job, log: dict, reprint_of: str | None = None) -> dict:
    if reprint_of:
        log["reprintOf"] = reprint_of
    cfg = core.settings.section("gelato")
    for book in books:
        book["mark"] = f" · {book['title']}" if len(books) > 1 else ""
    log["format"] = books[0]["format"]
    log["folder"] = str(books[0]["folder"])
    log["books"] = [{"title": b["title"], "folder": str(b["folder"]), "format": b["format"]} for b in books]
    gelato.api_key()
    address = {k: str(v).strip() for k, v in (address or {}).items() if v is not None and str(v).strip()}
    if address.get("country"):
        address["country"] = address["country"].upper()
    problems = validate_address(address)
    if problems:
        raise JobError("\n".join(problems))
    # Gelato will not let a draft be ordered without a phone; Etsy gives none, and a made-up one is the
    # owner's usual practice (18.09.2026).
    address.setdefault("phone", GELATO_PLACEHOLDER_PHONE)

    ready = [_gelato_book(book, job, log, cfg, 4 + 8 * i / len(books)) for i, book in enumerate(books)]
    title = joint_title(books)
    session = uuid.uuid4().hex[:12]
    session_dir = core.data_path("tmp", "gelato", session)
    session_dir.mkdir(parents=True, exist_ok=True)
    link: tunnel.FileTunnel | None = None
    try:
        for i, book in enumerate(ready, 1):
            book["pdfName"] = "book.pdf" if len(ready) == 1 else f"book-{i}.pdf"
            job.progress(f"Збирання книги в один PDF{book['mark']}…", 15 + 15 * (i - 1) / len(ready),
                         f"обкладинка + {book['pageCount']} сторінок, без перестиснення")
            book["pdf"] = build_photobook_pdf(book["cover"], book["pages"], session_dir / book["pdfName"], book["geometry"])
            sendlog.step(log, "pdf", book=book["title"], file=book["pdfName"], **book["pdf"])

        job.progress("Відкриття тимчасового доступу до файлів…", 35, "Cloudflare Tunnel")
        link = tunnel.FileTunnel(session_dir, tuple(b["pdfName"] for b in ready))
        try:
            base = link.start()
        except tunnel.TunnelError as err:
            raise JobError(str(err)) from None
        sendlog.step(log, "link", urls=[f"{base}/{b['pdfName']}" for b in ready], reachable=link.reachable)

        # The order's name in Gelato is the book's title, "4100000001 - Emma", as the owner names his own
        # orders; its receipt number matches the order to its receipt at the next sync.
        payload = {
            "orderType": "draft",
            "orderReferenceId": title[:100],
            "customerReferenceId": f"local-review-{session}",
            "currency": cfg.get("currency") or "USD",
            "items": [{
                "itemReferenceId": f"item-{session}" if len(ready) == 1 else f"item-{session}-{i}",
                "productUid": book["fmt"]["productUid"],
                "pageCount": book["pageCount"],  # inner pages only, as in the owner's own orders; covers are extra
                "quantity": 1,
                # A photo book takes one multi-page PDF of type "default" (cover sheet, blank, pages, blank).
                # ("inside" only exists for folded cards — Gelato then filled every page with the cover.)
                "files": [{"type": "default", "url": f"{base}/{book['pdfName']}"}],
            } for i, book in enumerate(ready, 1)],
            "shippingAddress": address,
            "metadata": [
                {"key": "title", "value": title[:100]},
                {"key": "format", "value": ", ".join(sorted({b["format"] for b in ready}))},
                {"key": "source", "value": "book-studio"},
            ],
        }
        log["request"] = payload
        job.progress("Створення чернетки в Gelato…", 70, "Очікування відповіді")
        keep = int(cfg.get("tunnelKeepAliveSeconds") or 900)
        try:
            created = gelato.create_draft_order(payload)
        except ApiError as err:
            if not _unknown_outcome(err):
                raise JobError(f"Gelato відхилив створення чернетки: {err}") from None
            # Gelato may have made the draft all the same and fetch its PDF in a moment: the link stays up
            # as for a made one, and the owner looks before sending again (22.09.2026 audit).
            log["outcome"] = "unknown"
            tunnel.registry.keep(f"unknown-{session}", link, session_dir, keep)
            link = None
            raise JobError("Зв'язок з Gelato обірвався під час створення чернетки — результат невідомий. НЕ надсилайте "
                           "повторно одразу: спершу перевірте Gelato → Orders → Drafts, чи з'явилась чернетка "
                           f"«{title}». Файли для неї доступні ще {max(1, keep // 60)} хв.") from None
        log["response"] = created
        order_id = created.get("id")
        if not order_id:
            raise JobError("Gelato не повернув ID чернетки.")
        _journal_readback(log, order_id, [b["pdf"]["pdfBytes"] for b in ready])
        tunnel.registry.keep(order_id, link, session_dir, keep)
        link = None  # owned by the registry now
        warnings = [f"{b['title']}: {w}" if b["mark"] else w for b in ready for w in b["pdf"]["warnings"]]
        if reprint_of:
            _mark_reprint(log, warnings, books[0].get("receipt"), "gelato", order_id)
        else:
            _remember_sent(log, warnings, ready, "gelato", order_id)
        for book in ready:
            book["archiveId"] = _to_archive(log, job, warnings, "gelato",
                                            [(Path(r["path"]), r["file"]) for r in book["files"]],
                                            {"title": book["title"], "receiptId": book.get("receipt"),
                                             "format": book["format"],
                                             "formatLabel": book["fmt"].get("label"),
                                             "productUid": book["fmt"]["productUid"], "orderId": order_id,
                                             "orderReferenceId": payload["orderReferenceId"], "address": address,
                                             "reprintOf": reprint_of})
        first = ready[0]
        return {"archiveId": first["archiveId"], "orderId": order_id, "orderReferenceId": payload["orderReferenceId"],
                "fulfillmentStatus": created.get("fulfillmentStatus"), "orderType": created.get("orderType"),
                "format": first["fmt"].get("label"), "keepAliveSeconds": keep, "title": title, "warnings": warnings,
                "pdfPages": first["pdf"]["pdfPages"], "pageCount": first["pageCount"], "reprint": bool(reprint_of),
                "books": [{"title": b["title"], "archiveId": b["archiveId"], "format": b["fmt"].get("label"),
                           "pageCount": b["pageCount"], "pdfPages": b["pdf"]["pdfPages"]} for b in ready]}
    finally:
        if link is not None:
            link.stop()
            shutil.rmtree(session_dir, ignore_errors=True)


# ---------------------------------------------------------------- one page replaced by hand

_PAGE_NAME = re.compile(r"(?:cover|\d{1,3})\.png", re.I)


def _print_page(folder_raw: str, file: str) -> tuple[Path, Path]:
    """The print folder and the page inside it, as they are really named on disk."""
    folder = Path(str(folder_raw or "").strip().strip('"'))
    if not folder.is_dir():
        raise ApiError("Папку з файлами не знайдено — перетягніть їх ще раз.", 404)
    if not _PAGE_NAME.fullmatch(str(file or "")):
        raise ApiError("Так сторінка книги не називається.")
    page = _files_by_lower(folder).get(str(file).lower())
    if not page:
        raise ApiError(f"У папці немає {file}.", 404)
    return folder, page


def replace_page(folder_raw: str, file: str, source_raw: str) -> dict:
    """Puts a page downloaded from Canva in place of one in the print folder (the owner fixed it in the
    template and wants only that page changed). The old one waits in `.replaced` for «Повернути»; the
    checks that follow are the usual ones, so a page of the wrong size is caught there."""
    folder, page = _print_page(folder_raw, file)
    source = Path(str(source_raw or "").strip().strip('"'))
    if not source.is_file():
        raise ApiError("Файл не знайдено.", 404)
    if source.resolve() == page.resolve():
        raise ApiError("Це той самий файл, що вже в папці.")
    info, error = images.check_png(source)
    if error or not info:
        raise ApiError(f"Це не придатний PNG: {error or 'файл не читається'}.")
    with _not_while_sending(folder):
        keep = folder / REPLACED
        keep.mkdir(exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        kept = keep / f"{page.name}.{stamp}"
        for n in range(2, 100):     # two replacements of one page within the same second keep both
            if not kept.exists():
                break
            kept = keep / f"{page.name}.{stamp}-{n}"
        shutil.copy2(page, kept)
        tmp = page.with_name(page.name + ".new")
        shutil.copy2(source, tmp)
        os.replace(tmp, page)   # the page is never half-written: it changes in one step
    _forget_validation(folder)
    core.log.info("Page %s replaced from %s", page.name, source.name)
    return {"file": page.name, "width": info["width"], "height": info["height"], "bytes": info["bytes"],
            "canRestore": True}


def restore_page(folder_raw: str, file: str) -> dict:
    """«Повернути»: the page that was there before the last replacement comes back."""
    folder, page = _print_page(folder_raw, file)
    with _not_while_sending(folder):
        kept = _backups(folder, page.name)
        if not kept:
            raise ApiError("Немає чого повертати.", 404)
        os.replace(kept[-1], page)
    _forget_validation(folder)
    core.log.info("Page %s restored", page.name)
    return {"file": page.name, "canRestore": bool(_backups(folder, page.name))}


# ---------------------------------------------------------------- personalization helpers

_NAME_HINT = re.compile(r"(child|kid|baby|boy|girl|name|ім'я|имя)", re.I)


def guess_child_name(items: list) -> str:
    for item in items or []:
        for v in item.get("variations") or []:
            name, value = (v.get("name") or ""), (v.get("value") or "").strip()
            if _NAME_HINT.search(name) and value and len(value) <= 40 and "\n" not in value:
                return wording.clean_name(value)
        for v in item.get("variations") or []:
            value = (v.get("value") or "")
            m = re.search(r"(?:child'?s?\s*name|name)\s*[:\-–]\s*([^\n,;]{2,40})", value, re.I)
            if m:
                return wording.clean_name(m.group(1))
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
            "pageCounts": gelato_page_options(), "keyConfigured": bool(vault.get("gelato_api_key")),
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
    # One book, or every book of an Etsy order at once — they then share one order to one address.
    books = body.get("books") if isinstance(body.get("books"), list) else [{"folder": body.get("folder"), "title": body.get("title")}]
    address = body.get("address") if isinstance(body.get("address"), dict) else None  # with it: books + order on hold
    job = jobs.start("printify-create", lambda j: create_printify_draft(books, j, address), exclusive="printify-create")
    return {"jobId": job.id}


@route("POST", "/api/creator/printify/reprint")
def _reprint_printify(req: Request):
    """Reprint from the order archive: a new order on hold for the archived Printify book."""
    body = req.json or {}
    archive_id = str(body.get("archiveId") or "")
    archive.reprintable(archive_id)  # refuses an unknown id, or a send that never went to print, before anything starts
    title = body.get("title") or ""
    address = body.get("address") if isinstance(body.get("address"), dict) else None
    job = jobs.start("printify-create", lambda j: create_printify_reprint(archive_id, title, address, j),
                     exclusive="printify-create")
    return {"jobId": job.id}


@route("POST", "/api/creator/gelato/create")
def _create_gelato(req: Request):
    body = req.json or {}
    # One book, or every book of an Etsy order at once — they then travel as items of one draft.
    books = body.get("books") if isinstance(body.get("books"), list) else [
        {"folder": body.get("folder"), "title": body.get("title"), "format": body.get("format")}]
    reprint_of = str(body.get("reprintOf") or "") or None
    if reprint_of:  # a reprint always uses the archived files, whatever folder the page holds
        entry = archive.reprintable(reprint_of)
        if entry.get("provider") != "gelato":
            raise ApiError("Ця книга з архіву надрукована не в Gelato — передрук робиться в тій самій друкарні.")
        first = books[0] if books and isinstance(books[0], dict) else {}
        books = [{**first, "folder": str(archive.folder(reprint_of)),
                  "receiptId": entry.get("receiptId") or first.get("receiptId")}]
    address = body.get("address") or {}
    job = jobs.start("gelato-create", lambda j: create_gelato_draft(books, address, j, reprint_of=reprint_of),
                     exclusive="gelato-create")
    return {"jobId": job.id}


@route("GET", "/api/creator/gelato/page-counts")
def _gelato_page_counts(req: Request):
    """Page counts per format, and for every book length the folder can have, what to tell when Gelato does not
    print that format at that length (the same words the send itself refuses with)."""
    counts = gelato_page_counts()
    formats = core.settings.section("gelato").get("formats") or {}
    problems = {key: {str(n): text for n in gelato_page_options()
                      if (text := _pages_problem((formats.get(key) or {}).get("label") or key, valid, n))}
                for key, valid in counts.items()}
    return {"formats": counts, "problems": problems}


@route("POST", "/api/creator/gelato/close-tunnel")
def _close_tunnel(req: Request):
    return {"closed": tunnel.registry.close(str((req.json or {}).get("orderId") or ""))}


@route("GET", "/api/creator/etsy-orders")
def _etsy_orders(req: Request):
    orders = profit.picker_orders()
    for o in orders:
        o["childName"] = guess_child_name(o["items"])
        for item in o["items"]:  # each book of the order its own child (the page names every book by it)
            item["childName"] = guess_child_name([item])
    return {"orders": orders, "syncedAt": profit.load_snapshot().get("syncedAt")}


@route("POST", "/api/creator/pick-file")
def _pick_file(req: Request):
    body = req.json or {}
    path = desktop.pick_file(body.get("title") or "Оберіть сторінку", body.get("initial") or "")
    return {"path": path or ""}


@route("POST", "/api/creator/replace-page")
def _replace_page(req: Request):
    """One page of a print folder is replaced by a file chosen on this computer."""
    body = req.json or {}
    return replace_page(body.get("folder") or "", body.get("file") or "", body.get("path") or "")


@route("POST", "/api/creator/restore-page")
def _restore_page(req: Request):
    body = req.json or {}
    return restore_page(body.get("folder") or "", body.get("file") or "")


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
