"""The slides' routes: the Mockups' step «Зробити слайди», the editor (a scene read and saved, its pictures), the
headless page that bakes (media routes — the token in the query)."""
from __future__ import annotations

import re
from pathlib import Path

from .. import core, desktop, images
from ..jobs import jobs
from ..server import ApiError, Request, SESSION_TOKEN, base_url, file_response, route
from . import cutout, store, work

EXCLUSIVE = "slides"


def _where(req: Request, body: dict | None = None) -> str:
    return store.valid_where((body or {}).get("w") if body is not None else req.param("w"))


def _slide(value) -> str:
    return store.valid_slide(str(value or ""))


def _url(set_id: str, part: str, name: str) -> str:
    path = store.set_dir(set_id) / part / name
    try:
        v = path.stat().st_mtime_ns
    except OSError:
        v = 0
    return f"/media/slides/file/{set_id}/{part}/{name}?t={SESSION_TOKEN}&v={v}"


def assets(where: str) -> dict:
    """What the drawing needs besides the scene: the books in their slots (the picture, its shadow, where the book sits
    in it), the flat pictures, the numbers. The template is shown with the newest book's pictures."""
    set_id = where if where != store.TEMPLATE else store.newest_set()
    if not set_id:
        return {"set": None, "books": {}, "pictures": {}, "numbers": dict(store.NUMBERS)}
    rec = store.read_set(set_id)
    books = {slot: {**info, "src": _url(set_id, "books", f"{store.slot_file(slot)}.png"),
                    "shadow": _url(set_id, "books", f"{store.slot_file(slot)}_shadow.png")}
             for slot, info in rec.get("books", {}).items()}
    pictures = {slot: {**info, "src": _url(set_id, "pictures", f"{slot}.png")}
                for slot, info in rec.get("pictures", {}).items()}
    return {"set": set_id, "name": rec.get("name"), "books": books, "pictures": pictures,
            "numbers": {**store.NUMBERS, **(rec.get("numbers") or {})}}


def _view(where: str) -> dict:
    rec = store.read_set(where) if where != store.TEMPLATE else None
    busy = jobs.running(EXCLUSIVE)
    return {
        "where": where, "name": rec.get("name") if rec else "Шаблон", "folder": rec.get("folder") if rec else "",
        "numbers": {**store.NUMBERS, **((rec or {}).get("numbers") or {})},
        "slides": [{"id": s, "title": work.title(s)} for s in store.SLIDES],
        "pictures": work.pictures(rec) if rec else [],
        "slots": [{"slot": s, "label": store.SLOT_LABEL[s], "kind": "book" if s in store.BOOK_SLOTS else "picture"}
                  for s in store.BOOK_SLOTS + store.PICTURE_SLOTS],
        "sig": store.sig(where), "jobId": busy.id if busy else None,
    }


@route("GET", "/api/slides/sets")
def _sets(req: Request):
    """The books whose slides are kept (the last dozen), newest first — the Mockups' header opens their editor."""
    return {"sets": [{"id": r["id"], "name": r.get("name") or "", "created": r.get("created") or "",
                      "folder": r.get("folder") or "", "baked": len(work.pictures(r))} for r in store.list_sets()]}


@route("GET", "/api/slides/state")
def _state(req: Request):
    return _view(_where(req))


@route("GET", "/api/slides/scene")
@route("GET", "/media/slides/scene", auth="media")        # the headless page that bakes
def _scene(req: Request):
    where, slide = _where(req), _slide(req.param("s"))
    scene, version = store.load(where, slide)
    return {"scene": scene, "version": version}


@route("GET", "/api/slides/assets")
@route("GET", "/media/slides/assets", auth="media")
def _assets(req: Request):
    return assets(_where(req))


@route("GET", r"/media/slides/file/(\d{8}-\d{6}-[0-9a-f]{6})/(books|pictures)/([\w.-]+\.png)", auth="media")
def _file(req: Request):
    set_id, part, name = req.groups
    path = store.set_dir(set_id) / part / name
    if not path.is_file():
        raise ApiError("Не знайдено.", 404)
    return file_response(path, "image/png", cache="private, max-age=3600")


@route("GET", "/api/slides/sig")
def _sig(req: Request):
    return {"sig": store.sig(_where(req))}


@route("POST", "/api/slides/scene")
def _save(req: Request):
    body = req.json or {}
    where, slide = _where(req, body), _slide(body.get("s"))
    base = body.get("base")
    return {"version": store.save(where, slide, body.get("scene"), str(base) if base is not None else "")}


@route("POST", "/api/slides/reset")
def _reset(req: Request):
    body = req.json or {}
    scene, version = store.reset(_where(req, body), _slide(body.get("s")))
    return {"scene": scene, "version": version}


@route("POST", "/api/slides/to-template")
def _to_template(req: Request):
    body = req.json or {}
    where = _where(req, body)
    if where == store.TEMPLATE:
        raise ApiError("Це вже шаблон.")
    store.to_template(where, _slide(body.get("s")))
    core.log.info("Slides: %s of set %s became the template", body.get("s"), where)
    return {"ok": True}


@route("POST", "/api/slides/numbers")
def _numbers(req: Request):
    body = req.json or {}
    where = _where(req, body)
    if where == store.TEMPLATE:
        raise ApiError("Числа — у слайдах книги.")
    rec = store.read_set(where)
    for key in store.NUMBERS:
        value = body.get(key)
        if value is not None:
            if not isinstance(value, int) or not 0 < value < 1000:
                raise ApiError("Число має бути від 1 до 999.")
            rec["numbers"][key] = value
    store.write_set(rec)
    return {"numbers": rec["numbers"]}


@route("POST", "/api/slides/picture")
def _picture(req: Request):
    """A flat picture of the set replaced by one the owner picks (page 30 when the demo book was gone)."""
    body = req.json or {}
    where = _where(req, body)
    slot = str(body.get("slot") or "")
    if where == store.TEMPLATE or slot not in store.PICTURE_SLOTS:
        raise ApiError("Некоректний запит.")
    path = desktop.pick_file(f"Картинка для «{store.SLOT_LABEL[slot]}»", "")
    if not path:
        return {"picked": False}
    if Path(path).suffix.lower() not in core.IMAGE_EXTS:
        raise ApiError("Це не картинка.")
    rec = store.read_set(where)
    store.put_picture(rec, slot, Path(path))
    store.write_set(rec)
    return {"picked": True}


# ---------------------------------------------------------------- the Mockups' step: cut-outs and «Зробити слайди»

def _folder(value) -> Path:
    folder = Path(str(value or ""))
    if not str(value or "") or not folder.is_dir():
        raise ApiError("Папку з мокапами не знайдено.")
    return folder


@route("GET", "/api/slides/cutouts")
def _cutouts(req: Request):
    """The mockups of a folder cut without background: which are ready (the Mockups' result card says it)."""
    folder = _folder(req.param("folder"))
    states = cutout.cutter.status(folder)
    for p in folder.glob("*.png"):
        if cutout.kind_of(p.name) in cutout.KINDS and p.name not in states and (folder / cutout.NO_BG / p.name).is_file():
            states[p.name] = "done"
    return {"files": states, "busy": cutout.cutter.busy(folder), "noBg": str(folder / cutout.NO_BG)}


def cut_later(png: Path, templates_dir: Path) -> None:
    """The Mockups hand every picture Photoshop saves (mockups.watch)."""
    try:
        cutout.cutter.add(png, templates_dir)
    except Exception:
        core.log.warning("Slides: %s not handed to the cutter", png, exc_info=True)


@route("POST", "/api/slides/make")
def _make(req: Request):
    from .. import mockups
    body = req.json or {}
    folder = _folder(body.get("folder"))
    order = [str(n) for n in body.get("order") or [] if isinstance(n, str)]
    numbers = {k: v for k, v in (body.get("numbers") or {}).items() if k in store.NUMBERS and isinstance(v, int) and 0 < v < 1000}
    page30, name = None, folder.name
    book_id = str(body.get("book") or "")
    if re.fullmatch(r"[0-9a-f]{16}", book_id):
        try:
            book = mockups._book(book_id)
            name = book.get("name") or name
            pages = book.get("pages") or {}
            if pages:
                page30 = Path(pages[max(pages)])   # the afterword — the book's last page
        except ApiError:
            pass
    templates_dir = mockups.places()["templates"]
    base, token = base_url(), SESSION_TOKEN
    core.log.info("Slides: making the six for «%s» from %s", name, folder)
    job = jobs.start("slides", lambda j: work.make(j, folder, name, order, page30, numbers, templates_dir, base, token),
                     exclusive=EXCLUSIVE)
    return {"jobId": job.id}


@route("POST", "/api/slides/bake")
def _bake(req: Request):
    body = req.json or {}
    where = _where(req, body)
    if where == store.TEMPLATE:
        raise ApiError("Запікаються слайди книги, не шаблон.")
    slides = [_slide(s) for s in body.get("slides") or store.SLIDES]
    rec = store.read_set(where)
    if not Path(rec.get("folder") or "").is_dir():
        raise ApiError("Папки цієї книги вже немає — слайди нікуди зберегти.")
    base, token = base_url(), SESSION_TOKEN
    job = jobs.start("slides", lambda j: {"set": where, "pictures": work.bake_set(j, rec, slides, base, token)},
                     exclusive=EXCLUSIVE)
    return {"jobId": job.id}


def _baked(where: str, slide: str) -> Path:
    rec = store.read_set(where)
    path = Path(rec.get("baked", {}).get(slide) or "")
    if not path.name or not path.is_file():
        raise ApiError("Картинку не знайдено.", 404)
    return path


@route("GET", r"/media/slides/out/(\d{8}-\d{6}-[0-9a-f]{6})/(slide[1-6])", auth="media")
def _out(req: Request):
    path = _baked(store.valid_where(req.groups[0]), req.groups[1])
    return file_response(images.preview(path, req.int_param("w", 480, 64, 4096)), "image/jpeg", cache="private, max-age=600")


@route("POST", "/api/slides/open-picture")
def _open_picture(req: Request):
    body = req.json or {}
    desktop.open_image_file(_baked(_where(req, body), _slide(body.get("s"))))
    return {"ok": True}


@route("POST", "/api/slides/open-folder")
def _open_folder(req: Request):
    body = req.json or {}
    rec = store.read_set(_where(req, body))
    folder = Path(rec.get("folder") or "")
    if body.get("noBg"):
        folder = folder / cutout.NO_BG
    if not folder.is_dir():
        raise ApiError("Папку не знайдено.")
    desktop.open_in_explorer(folder)
    return {"ok": True}
