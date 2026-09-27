"""The Workshop's routes: the books and their pictures, the generation mode, Antigravity, «Зберегти як»."""
from __future__ import annotations

import shutil
from pathlib import Path

from .. import clipboard, core, desktop, images, library
from ..server import ApiError, Request, file_response, route
from . import books, generate, pictures

def _variant(body_or_value) -> str | None:
    value = body_or_value.get("variant") if isinstance(body_or_value, dict) else body_or_value
    return str(value) if value else None


# ---------------------------------------------------------------- the books

def _live(book_id: str | None = None) -> dict:
    """What a page is drawn from, to tell a change by: the books' files (or one book's) and the generation mode."""
    gen = generate.status()
    return {"sig": f"{books.signature(book_id)}-{gen['version']}", "gen": gen}


@route("GET", "/api/workshop/books")
def _list(req: Request):
    return {"books": books.all_books(), "folder": str(books.books_dir()), **_live()}


@route("GET", "/api/workshop/sig")
def _sig(req: Request):
    return _live(req.param("book") or None)


@route("GET", r"/api/workshop/books/([^/]+)")
def _get(req: Request):
    return {"book": books.detail(req.groups[0]), **_live(req.groups[0])}


@route("DELETE", r"/api/workshop/books/([^/]+)")
def _delete(req: Request):
    generate.stop(req.groups[0])  # nothing waits for a picture of a book that's gone
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
    books.open_in_windows(body.get("book") or None, str(body.get("what") or ""), str(body.get("name") or ""))
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
    """A picture dropped onto a row (or picked in the Windows dialog): copied in, cut and flipped by the row's rules."""
    book_id, key = req.groups[0], req.param("key") or ""
    name = Path(req.param("name") or "picture.png").name[:200]
    books.book_path(book_id)  # refused before the file is even taken
    tmp = core.data_path("tmp", f"upload-{core.new_id()}{Path(name).suffix.lower()}")
    try:
        req.body_to_file(tmp, library.MAX_IMAGE_BYTES)
        result = pictures.place(book_id, key, tmp, name, _variant(req.param("variant")))
    finally:
        tmp.unlink(missing_ok=True)
    if key == "cover" and not generate.status()["active"]:
        generate.session().start(book_id, "cover-wrap")  # the cover's picture goes on to its margins by itself
    return result


@route("POST", r"/api/workshop/books/([^/]+)/flip")
def _flip(req: Request):
    body = req.json or {}
    return pictures.flip(req.groups[0], str(body.get("key") or ""), _variant(body))


@route("POST", r"/api/workshop/books/([^/]+)/remove")
def _remove(req: Request):
    body = req.json or {}
    return pictures.remove(req.groups[0], str(body.get("key") or ""), _variant(body))


@route("POST", r"/api/workshop/books/([^/]+)/no-margins")
def _no_margins(req: Request):
    generate.stop(req.groups[0])
    return pictures.skip_margins(req.groups[0])


@route("POST", r"/api/workshop/books/([^/]+)/copy-picture")
def _copy_picture(req: Request):
    """«Копіювати картинку»: a spread as Gemini made it (e.g. for Agent 6's "best frame"), a page, the cover."""
    clipboard.set_image(pictures.picture_for_clipboard(req.groups[0], str((req.json or {}).get("key") or "")))
    return {"ok": True}


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


@route("GET", r"/media/workshop/([^/]+)/(agent|pictures|originals)(?:/v/([^/]+))?/([^/]+)", auth="media")
def _media(req: Request):
    """A book's picture — a preview (?w=) or the file. With its version (?v=) the browser keeps it for good: a
    replaced picture comes with a new version."""
    book_id, area, variant, name = req.groups
    path = books.media_file(book_id, area, name, variant)
    cache = "private, max-age=31536000, immutable" if req.param("v") else "no-cache"
    if req.param("w"):
        return file_response(images.preview(path, req.int_param("w", 480, 64, 4096)), "image/jpeg", cache=cache)
    return file_response(path, cache=cache)


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
