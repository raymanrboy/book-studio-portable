"""The Workshop's routes: the books and their pictures, the generation mode, upscaling, Antigravity, «Зберегти як»,
the photo mockups (their templates, a book's photos)."""
from __future__ import annotations

import shutil
from pathlib import Path

from .. import clipboard, core, desktop, images, library, photos
from ..jobs import jobs
from ..server import ApiError, Request, file_response, route
from . import books, generate, pictures, rows, upscale

def _variant(body_or_value) -> str | None:
    value = body_or_value.get("variant") if isinstance(body_or_value, dict) else body_or_value
    return str(value) if value else None


# ---------------------------------------------------------------- the books

def _live(book_id: str | None = None) -> dict:
    """What a page is drawn from, to tell a change by: the books' files (or one book's), the generation mode, the
    upscaling's queue and progress (a book's page only — the gallery doesn't show it)."""
    gen = generate.status()
    up = f"-{upscale.version()}" if book_id else ""
    return {"sig": f"{books.signature(book_id)}-{gen['version']}{up}", "gen": gen}


@route("GET", "/api/workshop/books")
def _list(req: Request):
    live = _live()  # first, like a book's page (_get)
    return {"books": books.all_books(), "folder": str(books.books_dir()), **live}


@route("GET", "/api/workshop/sig")
def _sig(req: Request):
    return _live(req.param("book") or None)


@route("GET", r"/api/workshop/books/([^/]+)")
def _get(req: Request):
    # What the page was drawn from is taken first: a change that comes while the book is read (an upscale that ends
    # meanwhile) then shows at the next look, instead of the old state standing under the new signature.
    live = _live(req.groups[0])
    book_id = req.groups[0]
    return {"book": {**books.detail(book_id), "upscale": upscale.status(book_id),
                     "leftBehind": pictures.left_behind(book_id)}, **live}


@route("DELETE", r"/api/workshop/books/([^/]+)")
def _delete(req: Request):
    generate.stop(req.groups[0])  # nothing waits for a picture of a book that's gone
    upscale.forget(req.groups[0])
    return books.delete_book(req.groups[0])


@route("GET", r"/api/workshop/books/([^/]+)/file")
def _file(req: Request):
    name = req.param("name") or ""
    return {"name": name, "text": books.agent_text(req.groups[0], name)}


@route("POST", r"/api/workshop/books/([^/]+)/mark")
def _mark(req: Request):
    body = req.json or {}
    return books.set_mark(req.groups[0], str(body.get("step") or ""), bool(body.get("on")))


@route("POST", "/api/workshop/open")
def _open(req: Request):
    """The books' folder, a book's folder, its pages or originals, an agent's file — in Windows."""
    body = req.json or {}
    books.open_in_windows(body.get("book") or None, str(body.get("what") or ""), str(body.get("name") or ""),
                          str(body.get("variant") or ""))
    return {"ok": True}


@route("POST", "/api/workshop/agent")
def _agent(req: Request):
    return {"clip": books.open_agent((req.json or {}).get("book") or None)}


@route("POST", r"/api/workshop/books/([^/]+)/to-library")
def _to_library(req: Request):
    return books.to_library(req.groups[0], req.json or {})


# ---------------------------------------------------------------- pictures

@route("POST", r"/api/workshop/books/([^/]+)/place")
def _place(req: Request):
    """A picture dropped onto a row (or picked in the Windows dialog): copied in, cut and flipped by the row's rules.
    `photo:<category>` — a finished photo mockup into etsy/; `canva-cover` — the photo mockups' Canva cover."""
    book_id, key = req.groups[0], req.param("key") or ""
    name = Path(req.param("name") or "picture.png").name[:200]
    book = books.book_path(book_id)  # refused before the file is even taken
    tmp = core.data_path("tmp", f"upload-{core.new_id()}{Path(name).suffix.lower()}")
    try:
        req.body_to_file(tmp, library.MAX_IMAGE_BYTES)
        if key.startswith("photo:"):
            return photos.place(book_id, key[6:], tmp, name)
        if key == photos.CANVA_COVER:
            return photos.set_canva_cover(book, tmp, name)
        result = pictures.place(book_id, key, tmp, name, _variant(req.param("variant")))
    finally:
        tmp.unlink(missing_ok=True)
    if key == "cover" and not generate.status()["active"]:
        generate.session().start(book_id, "cover-wrap")  # the cover's picture goes on to its margins by itself
    return result


@route("POST", r"/api/workshop/books/([^/]+)/cover-squares")
def _cover_squares(req: Request):
    """The cover tool's choices for «Два квадрати»: the soft edge, a side's layout guide, the front's reference."""
    from . import cover
    return cover.set_settings(req.groups[0], req.json or {})


@route("POST", r"/api/workshop/books/([^/]+)/cover-mode")
def _cover_mode(req: Request):
    """The cover row's switch «2:1 · Два квадрати» — a wait for the other way's outpaint ends (its result would be
    brought to the wrong template)."""
    result = pictures.set_cover_mode(req.groups[0], str((req.json or {}).get("mode") or ""))
    a = generate.status()["active"]
    if a and a.get("book") == req.groups[0] and not a.get("variant") and str(a.get("key") or "").startswith("cover"):
        generate.stop(req.groups[0])  # a spread awaited meanwhile goes on
    return result


@route("POST", r"/api/workshop/books/([^/]+)/adopt")
def _adopt(req: Request):
    """«Підхопити з папки»: the pictures the owner put into originals/ by hand (the base book's, or `variant`'s) go
    the usual way — cut, flipped, upscaled. A job: the button shows how far it is."""
    book_id, variant = req.groups[0], _variant(req.json or {})
    keys = pictures.left_behind(book_id).get(variant or "", [])
    if not keys:
        raise ApiError("У папці оригіналів немає нових картинок для цих рядків.")

    def run(job) -> dict:
        return pictures.adopt(book_id, variant, lambda i, n: job.progress(f"Підхоплюю {i} з {n}…", 100 * i / max(n, 1)))
    return {"jobId": jobs.start("workshop-adopt", run, exclusive=f"workshop-adopt-{book_id}").id}


@route("POST", r"/api/workshop/books/([^/]+)/flip")
def _flip(req: Request):
    body = req.json or {}
    return pictures.flip(req.groups[0], str(body.get("key") or ""), _variant(body))


@route("POST", r"/api/workshop/books/([^/]+)/remove")
def _remove(req: Request):
    body = req.json or {}
    return pictures.remove(req.groups[0], str(body.get("key") or ""), _variant(body))


@route("POST", r"/api/workshop/books/([^/]+)/restore")
def _restore(req: Request):
    """«Скасувати» after «Прибрати»: the pictures come back from .replaced/ (the `undo` that `remove` handed out)."""
    return pictures.restore(req.groups[0], (req.json or {}).get("undo") or {})


@route("POST", r"/api/workshop/books/([^/]+)/no-margins")
def _no_margins(req: Request):
    generate.stop(req.groups[0])
    return pictures.skip_margins(req.groups[0])


@route("POST", r"/api/workshop/books/([^/]+)/copy-picture")
def _copy_picture(req: Request):
    """«Копіювати картинку»: a spread as Gemini made it (e.g. for Agent 6's "best frame"), a page, the cover."""
    clipboard.set_image(pictures.picture_for_clipboard(req.groups[0], str((req.json or {}).get("key") or "")))
    return {"ok": True}


@route("POST", r"/api/workshop/books/([^/]+)/copy-reference")
def _copy_reference(req: Request):
    """«Референс у буфер» (the owner, 24.10.2026): the picture a cover prompt names as its `reference_image` (Agent 6's
    `ref_cover_….jpg` in `agent/`), so it goes into Gemini without hunting for it in the folder."""
    key = str((req.json or {}).get("key") or "")
    name = rows.book_rows(books.book_path(req.groups[0]))["cover"].get("refs", {}).get(key)
    if not name:
        raise ApiError("Промпт обкладинки не називає картинку-референс, або її немає в папці agent.")
    clipboard.set_image(books.book_path(req.groups[0]) / books.AGENT / name)
    return {"ok": True, "name": name}


@route("POST", r"/api/workshop/books/([^/]+)/copy-hero")
def _copy_hero(req: Request):
    """The hero (canonical.png, or a variant's hero.png) as a picture — the first thing in a new Gemini chat."""
    book = books.book_path(req.groups[0])
    variant = _variant(req.json or {})
    hero = pictures.variant_dir(book, variant) / "hero.png" if variant else book / books.AGENT / "canonical.png"
    if not hero.is_file():
        raise ApiError("Героя ще немає.")
    clipboard.set_image(hero)
    return {"ok": True}


@route("POST", r"/api/workshop/books/([^/]+)/save-as")
def _save_as(req: Request):
    """«Зберегти як…»: one of the book's pictures copied wherever the owner says, in the Windows dialog; the folder
    is remembered for the next time."""
    body = req.json or {}
    book_id, area, name = req.groups[0], str(body.get("area") or ""), str(body.get("name") or "")
    source = books.media_file(book_id, area, name, _variant(body))
    suggested = f"{book_id} — {name}" if area == books.PICTURES and name[:1].isdigit() else name
    remembered = core.settings.section("workshop").get("saveDir", "")
    if core.SANDBOX:
        target = core.data_path("saved", suggested)
        target.parent.mkdir(parents=True, exist_ok=True)
    else:
        chosen = desktop.save_file("Зберегти картинку", suggested, remembered)
        if not chosen:
            return {"saved": False}
        target = Path(chosen)
    if target.suffix.lower() != source.suffix.lower():
        target = target.with_suffix(source.suffix.lower())
    shutil.copyfile(source, target)
    core.settings.update({"workshop": {"saveDir": str(target.parent)}})
    return {"saved": True, "path": str(target), "name": target.name}


@route("GET", r"/media/workshop/([^/]+)/(agent|pictures|originals|mockups|etsy)(?:/v/([^/]+))?/([^/]+)", auth="media")
def _media(req: Request):
    """A book's picture — a preview (?w=) or the file. With its version (?v=) the browser keeps it for good: a
    replaced picture comes with a new version."""
    book_id, area, variant, name = req.groups
    path = books.media_file(book_id, area, name, variant)
    cache = "private, max-age=31536000, immutable" if req.param("v") else "no-cache"
    if req.param("w"):
        return file_response(images.preview(path, req.int_param("w", 480, 64, 4096)), "image/jpeg", cache=cache)
    return file_response(path, cache=cache)


# ---------------------------------------------------------------- upscaling

@route("POST", r"/api/workshop/books/([^/]+)/upscale")
def _upscale_on(req: Request):
    """The book's «Апскейл ×2» switch: on (the default) or off — a book left as the generator made it."""
    return upscale.set_on(req.groups[0], bool((req.json or {}).get("on")))


@route("POST", r"/api/workshop/books/([^/]+)/upscale/start")
def _upscale_start(req: Request):
    """«Апскейлити решту» / «Перерізати з великих оригіналів» — `keys` (every row not upscaled yet without them); with
    `key` — that row again."""
    body = req.json or {}
    raw = body.get("keys")
    keys = [str(body["key"])] if body.get("key") else [str(k) for k in raw] if isinstance(raw, list) and raw else None
    return upscale.start(req.groups[0], keys)


# ---------------------------------------------------------------- the generation mode

@route("GET", "/api/workshop/gen")
def _gen(req: Request):
    """The generation mode alone — what workshop-live.js asks while no Workshop page is on screen."""
    return generate.status()


@route("POST", "/api/workshop/gen/start")
def _gen_start(req: Request):
    body = req.json or {}
    return generate.session().start(str(body.get("book") or ""), body.get("key") or None, _variant(body),
                                    bool(body.get("series")))


@route("POST", "/api/workshop/gen/stop")
def _gen_stop(req: Request):
    generate.stop()
    return generate.status()


@route("POST", "/api/workshop/gen/next")
def _gen_next(req: Request):
    return generate.session().next_item()


@route("POST", "/api/workshop/gen/again")
def _gen_again(req: Request):
    return generate.session().again()


@route("POST", "/api/workshop/gen/photo")
def _gen_photo(req: Request):
    """A photo mockup: the template, the book's reference (with a book), the prompt — into the clipboard one by one."""
    body = req.json or {}
    return generate.session().start_photo(str(body.get("book") or "") or None, str(body.get("category") or ""),
                                          str(body.get("template") or ""))


# ---------------------------------------------------------------- the photo mockups (photos.py)

@route("GET", "/api/photos")
def _photos(req: Request):
    """The categories and their templates — the «Фотомокапи» page."""
    gen = generate.status()
    return {"categories": photos.templates(), "folder": str(photos.templates_dir()),
            "sig": f"{photos.signature()}-{gen['version']}", "gen": gen}


@route("GET", "/api/photos/sig")
def _photos_sig(req: Request):
    gen = generate.status()  # the templates and the generation mode: the page redraws when either changes
    return {"sig": f"{photos.signature()}-{gen['version']}", "gen": gen}


@route("GET", r"/media/photos/([^/]+)/([^/]+)", auth="media")
def _photo_media(req: Request):
    """A template — a preview (?w=) or the file; with its version (?v=) the browser keeps it for good."""
    path = photos.template_file(req.groups[0], req.groups[1])
    cache = "private, max-age=31536000, immutable" if req.param("v") else "no-cache"
    if req.param("w"):
        return file_response(images.preview(path, req.int_param("w", 480, 64, 4096)), "image/jpeg", cache=cache)
    return file_response(path, cache=cache)


@route("POST", "/api/photos/add")
def _photo_add(req: Request):
    """A photo dropped onto a category: a new template, named by the category's next number."""
    name = Path(req.param("name") or "picture.png").name[:200]
    photos.category(req.param("category") or "")
    tmp = core.data_path("tmp", f"upload-{core.new_id()}{Path(name).suffix.lower()}")
    try:
        req.body_to_file(tmp, library.MAX_IMAGE_BYTES)
        return photos.add_template(req.param("category") or "", tmp, name)
    finally:
        tmp.unlink(missing_ok=True)


@route("POST", "/api/photos/remove")
def _photo_remove(req: Request):
    body = req.json or {}
    return photos.remove_template(str(body.get("category") or ""), str(body.get("name") or ""))


@route("POST", "/api/photos/open")
def _photo_open(req: Request):
    photos.open_folder(str((req.json or {}).get("category") or ""))
    return {"ok": True}


@route("POST", "/api/photos/prompt")
def _photo_prompt(req: Request):
    """A category's prompt alone into the clipboard."""
    clipboard.set_text(photos.prompt(str((req.json or {}).get("category") or "")))
    return {"ok": True}


@route("POST", r"/api/workshop/books/([^/]+)/photos/remove")
def _book_photo_remove(req: Request):
    """A book's finished photo out of etsy/ — into its .replaced/."""
    return photos.remove(req.groups[0], str((req.json or {}).get("category") or ""))
