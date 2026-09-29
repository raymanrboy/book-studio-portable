"""The Order Creator's routes, and the pictures of a print folder for the page and the viewer."""
from __future__ import annotations

from pathlib import Path

from .. import archive, core, desktop, images, printify, tunnel
from ..jobs import jobs
from ..server import ApiError, Request, file_response, route
from ..vault import vault
from .printfolder import _files_by_lower, gelato_page_options, replace_page, restore_page, validate
from .printify_send import create_printify_draft, create_printify_reprint, matte_variant
from .gelato_send import _pages_problem, create_gelato_draft, gelato_page_counts


@route("GET", "/api/creator/status")
def _status(req: Request):
    p = core.settings.section("printify")
    g = core.settings.section("gelato")
    return {
        "printify": {
            "masterId": (p.get("master") or {}).get("productId"), "pageCount": p.get("pageCount"),
            "coverSize": p.get("coverSize"),
            "tokenConfigured": bool(vault.get("printify_token")),
            "manualApproval": printify.manual_approval_confirmed(),
            "matteVariant": bool(matte_variant(p.get("master") or {})),
            "retired": printify.retired(),
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
    if printify.retired():
        raise ApiError(printify.RETIRED_TEXT, 403)
    body = req.json or {}
    # Every book of an Etsy order at once — they then share one order to one address.
    books = body.get("books") if isinstance(body.get("books"), list) else []
    address = body.get("address") if isinstance(body.get("address"), dict) else None  # with it: books + order on hold
    job = jobs.start("printify-create", lambda j: create_printify_draft(books, j, address), exclusive="printify-create")
    return {"jobId": job.id}


@route("POST", "/api/creator/printify/reprint")
def _reprint_printify(req: Request):
    """Reprint from the order archive: a new order on hold for the archived Printify book."""
    if printify.retired():
        raise ApiError(printify.RETIRED_TEXT, 403)
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
    # Every book of an Etsy order at once — they then travel as items of one draft.
    books = body.get("books") if isinstance(body.get("books"), list) else []
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
    if not folder.is_dir() or "/" in name or "\\" in name or Path(name).suffix.lower() not in core.IMAGE_EXTS:
        raise ApiError("Не знайдено.", 404)
    target = _files_by_lower(folder).get(name.lower())
    if not target:
        raise ApiError("Не знайдено.", 404)
    size = req.int_param("w", 480, 64, 4096)
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
        if "/" in name or "\\" in name or Path(name).suffix.lower() not in core.IMAGE_EXTS:
            raise ApiError("Не знайдено.", 404)
        sides.append(present.get(name.lower()))
    if not any(sides):
        raise ApiError("Не знайдено.", 404)
    height = req.int_param("h", 1200, 200, 2400)
    return file_response(images.compose_spread(sides[0], sides[1], height), "image/jpeg", cache="private, max-age=600")
