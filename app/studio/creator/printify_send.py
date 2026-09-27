"""Printify: unpublished books built from the read-only Master, their pictures uploaded once (a hash cache), an
order «On hold» for all the books of an Etsy order, and a reprint from the archive."""
from __future__ import annotations

import threading
import uuid
from concurrent.futures import CancelledError, ThreadPoolExecutor
from pathlib import Path

from .. import archive, core, printify, sendlog
from ..jobs import JobError
from ..server import ApiError
from .printfolder import expected_files
from .sending import (_mark_reprint, _to_archive, _unknown_outcome, books_of, checked_files, joint_title,
                      journaled_send, mark_books, receipt_for, record_order, validate_address)


UPLOAD_CACHE = core.data_path("creator", "upload-cache.json")


def _load_upload_cache() -> dict:
    return core.read_json(UPLOAD_CACHE, {}) or {}


UPLOADS_KEPT = 5000  # pictures whose Printify id is remembered (~40 books a month for a year); the oldest go

_upload_lock = threading.Lock()


def _remember_upload(sha: str, image_id: str) -> None:
    with _upload_lock:
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


def create_printify_draft(books, job, address: dict | None = None) -> dict:
    """Unpublished Printify books, one per book of the order; with an address also a single order for all
    of them that waits "On hold". Every attempt is written to the send journal."""
    books = books_of(books)
    return journaled_send("printify", "book+order" if address else "book", joint_title(books),
                          (b["folder"] for b in books), lambda log: _printify_draft(books, job, address, log))


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
    """One unpublished book from its uploaded images, built by the Master's configuration, then read back to
    see every page on its own position."""
    image_ids = book["images"]
    job.progress(f"Створення книги в Printify{book['mark']}…", span(0), "Збирання структури за Master-продуктом")
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

    job.progress(f"Перевірка результату{book['mark']}…", span(0.6), "Звірка сторінок")
    warnings: list[str] = []
    verified = False
    try:  # the book exists now: nothing after this point may fail the send, or a repeat would make it twice
        new_product = printify.product(shop_id, product_id)
        placed = {}
        for area in new_product.get("print_areas") or []:
            for ph in area.get("placeholders") or []:
                placed[ph.get("position")] = [i.get("id") for i in ph.get("images") or []]
        mismatched = [pos for pos, img in image_ids.items() if img not in (placed.get(pos) or [])]
        verified = not mismatched
        if mismatched:
            warnings.append(f"Позиції не збіглися з очікуваними: {', '.join(mismatched[:6])}. Перевірте книгу вручну.")
    except Exception as err:
        core.log.exception("Printify: the new book not read back")
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
    mark_books(books)
    log["folder"] = str(books[0]["folder"])
    log["books"] = [{"title": b["title"], "folder": str(b["folder"])} for b in books]
    cfg, shop_id, variant_id = _printify_setup(address)
    master = cfg.get("master") or {}

    for book in books:  # no book of an order is made while another one's files are still wrong
        book["checked"] = checked_files("printify", book, job, log, 2)

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

    # Every book's pictures go up before any book is made: a failed upload of the second book must not leave
    # the first one made already — a repeat would make it a second time.
    for i, book in enumerate(books):
        low, step = 10 + 76 * i / len(books), 76 / len(books)
        book["images"] = _printify_images(book, job, log, lambda p, low=low, step=step: low + step * p)
    made: list[dict] = []
    for i, book in enumerate(books):
        low, step = 86 + 8 * i / len(books), 8 / len(books)
        made.append(_printify_product(book, job, log, cfg, shop_id, lambda p, low=low, step=step: low + step * p))

    warnings = [f"{m['title']}: {w}" if len(made) > 1 else w for m in made for w in m["warnings"]]
    master_safe = None
    try:
        after = printify.product(shop_id, master["productId"])
        master_safe = _master_fingerprint(after) == fingerprint_before
        if not master_safe:
            warnings.append("Увага: Master-продукт має зміни після створення — перевірте його в Printify.")
    except Exception as err:  # the books exist: a failed look at the Master is said, never a failed send
        core.log.exception("Printify: the Master not read after the send")
        warnings.append(f"Не вдалося перевірити Master: {err}")
    sendlog.step(log, "masterSafe", ok=master_safe)

    order = order_error = None
    if address:
        order, order_error = _printify_order(books, made, variant_id, address, job, log, cfg, shop_id)

    # The books are in Printify now (with or without their order): keep exactly these files in the archive.
    if order:
        record_order(log, warnings, "printify", books, order["id"], reprint_of)
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
    return journaled_send("printify", "reprint", title, (archive.folder(eid) for eid in [archive_id]),
                          lambda log: _printify_reprint(archive_id, title, address, job, log))


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
