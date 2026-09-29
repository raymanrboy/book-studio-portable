"""The Workshop's books: one folder each in the pipeline's `books/`, read by the files that exist in it.

    pipeline/books/41.some-book/
      agent/      the agents' files (formula.md, canonical.png, book-text.md, the prompt files …) — only read, except
                  the hero the Workshop catches (canonical.png, a variant's hero.png)
      pictures/   the pages, cut and named: Cover.png, 1.png … 30.png — the set for Canva («Сторінки»)
      originals/  the pictures as they came (moved out of Downloads), named by their row: spread-04-05.jpg …
      .replaced/  whatever a new picture replaced or a removal took — never deleted
      mockups/    the Mockups' pictures, the Canva cover (canva-cover.png), the cut-outs, the slides' scenes
      etsy/       what goes into the Etsy listing: the slides (Listing 1.png …), the photo mockups (photo-main.png …),
                  copies of the whole-scene mockups (Cover & Open 1, All & Open 1)
      book.json   the Workshop's own state: the steps ticked by hand, each row's marks, the cover's layout on the
                  printer's template, the library book it was passed on as, the photo mockups' templates

A book's id is its folder's name. Nothing is cached: every call looks at the files, so a file an agent has just
written counts at once.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import threading
from pathlib import Path

from .. import core, desktop, library
from ..jobs import jobs
from ..server import ApiError

AGENT, PICTURES, ORIGINALS, STATE = "agent", "pictures", "originals", "book.json"
MOCKUPS = "mockups"   # the book's mockups, their cut-outs, the slides' scenes (since 29.09.2026)
ETSY = "etsy"         # what goes into the Etsy listing: the slides and the photo mockups (since 30.09.2026)
AREAS = (AGENT, PICTURES, ORIGINALS, MOCKUPS, ETSY)
TEXT_SUFFIXES = (".md", ".txt", ".json")
TEXT_LIMIT = 2_000_000

# The book's rows under the cover: page 1, spreads 2–3 … 28–29, page 30 — and the pages each one fills.
ROWS = [("page1", (1,))] + [(f"spread{n}", library.spread_pages(n)) for n in library.SPREAD_NUMBERS] + [("page30", (30,))]

# The path strip. `files` are the agent's files a step shows; Canva and the mockups are ticked by the owner, the
# photo mockups by all seven photos (or by hand — a category may be skipped), the library by passing the book on.
STEPS = [
    {"key": "formula", "label": "Формула", "files": ["formula.md"]},
    {"key": "hero", "label": "Герой", "files": ["canonical.png", "canonical-prompt.md", "character-card.md"]},
    {"key": "story", "label": "Історія", "files": ["story-blueprint.md"]},
    {"key": "text", "label": "Текст", "files": ["book-text.md"]},
    {"key": "prompts", "label": "Промпти", "files": ["spread-prompts-json.md", "endpage-prompts-json.md"]},
    {"key": "pictures", "label": "Картинки", "files": []},
    {"key": "cover", "label": "Обкладинка", "files": ["cover-prompts-json.md"]},
    {"key": "canva", "label": "Canva", "files": [], "manual": True},
    {"key": "mockups", "label": "Мокапи", "files": [], "manual": True},
    {"key": "photos", "label": "Фото", "files": [], "manual": True},
    {"key": "library", "label": "Бібліотека", "files": []},
]
MANUAL = {s["key"] for s in STEPS if s.get("manual")}

_TIER = re.compile(r"Tier\W{0,6}(H|S)\b", re.IGNORECASE)
_NUMBER = re.compile(r"^(\d+)\.\s*(.+)$")
_state_lock = threading.RLock()


def books_dir() -> Path:
    return core.WORKSHOP_BOOKS


def _names(folder: Path) -> list[str]:
    """A folder's files. os.scandir: on Windows a listing already says what is a file (and each file's size and
    time), so nothing is asked of the disk file by file — the page asks every 1.5 s (7–8× faster, 26.09.2026)."""
    try:
        with os.scandir(folder) as entries:
            return sorted(e.name for e in entries if e.is_file())
    except OSError:
        return []


def book_path(book_id: str) -> Path:
    """A book's folder by its name; anything that isn't a folder right inside `books/` is refused."""
    base = books_dir().resolve()
    if not book_id or book_id != Path(book_id).name or book_id.startswith("."):
        raise ApiError("Книгу не знайдено.", 404)
    path = (base / book_id).resolve()
    if path.parent != base or not path.is_dir():
        raise ApiError("Книгу не знайдено.", 404)
    return path


def book_ids() -> list[str]:
    """The books in number order (a folder without a number goes last)."""
    try:
        with os.scandir(books_dir()) as entries:
            dirs = [e.name for e in entries if e.is_dir() and not e.name.startswith((".", "_"))]
    except OSError:
        return []
    return sorted(dirs, key=lambda n: (int(m.group(1)) if (m := _NUMBER.match(n)) else 10**9, n.lower()))


def read_text(path: Path, limit: int = TEXT_LIMIT) -> str | None:
    try:
        if path.stat().st_size > limit:
            return None
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None


# ---------------------------------------------------------------- the Workshop's own state (book.json)

def state(path: Path) -> dict:
    try:
        data = json.loads((path / STATE).read_text(encoding="utf-8-sig"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def update_state(path: Path, change) -> dict:
    """Reads book.json, lets `change(data)` edit it, writes it back — one writer at a time (the page and the
    Downloads watcher may both write)."""
    with _state_lock:
        data = state(path)
        change(data)
        core.write_json(path / STATE, data, backup=False)
        return data


def library_book(path: Path) -> dict | None:
    """The library book this one was passed on as — while it is still in the library (not in its trash)."""
    passed = state(path).get("library") or {}
    book_id = str(passed.get("id") or "")
    if re.fullmatch(r"[0-9a-f]{32}", book_id) and (library.BOOKS_DIR / book_id / "book.json").is_file():
        return passed
    return None


# ---------------------------------------------------------------- what the files say

def tier(agent_files: set[str], agent: Path) -> str | None:
    """H (a recurring child hero) or S, from Agent 0's formula.md, else the blueprint's header."""
    for name in ("formula.md", "story-blueprint.md"):
        if name in agent_files:
            m = _TIER.search(read_text(agent / name, 200_000) or "")
            if m:
                return m.group(1).upper()
    return None


def cover_title(agent_files: set[str], agent: Path) -> str:
    """The first line under `## Cover` in book-text.md (the title printed on the front)."""
    if "book-text.md" not in agent_files:
        return ""
    lines = (read_text(agent / "book-text.md") or "").splitlines()
    for i, line in enumerate(lines):
        if re.match(r"^##\s+Cover\b", line, re.IGNORECASE):
            for nxt in lines[i + 1:]:
                s = nxt.strip()
                if s.startswith("#"):
                    return ""
                if s and not s.startswith(("[", "---", ">")):
                    return s.strip("*_ ")
            return ""
    return ""


def picture(names: set[str], page) -> str | None:
    """The file of a page (or of `Cover`) among a folder's names, whatever its picture format."""
    for suffix in core.IMAGE_EXTS:
        for candidate in (f"{page}{suffix}", f"{page}{suffix.upper()}"):
            if candidate in names:
                return candidate
    return None


def rows_filled(pictures: set[str]) -> int:
    return sum(1 for _, pages in ROWS if all(picture(pictures, p) for p in pages))


def _file_entry(agent_files: set[str], name: str) -> dict:
    kind = "image" if name.lower().endswith(core.IMAGE_EXTS) else "text"
    return {"name": name, "kind": kind, "area": AGENT, "exists": name in agent_files}


def steps(path: Path) -> list[dict]:
    """The path strip: each step `done`, `part` (started), `todo` or `skip` (a Tier S book has no hero) — by the files
    that exist; the first one not done is `next`."""
    from .rows import book_check, cover_state
    agent = path / AGENT
    a = set(_names(agent))
    p = set(_names(path / PICTURES))
    marks = state(path).get("marks") or {}
    canonicals = sorted(n for n in a if n.lower().startswith("canonical") and n.lower().endswith(core.IMAGE_EXTS))
    out = []
    for s in STEPS:
        key = s["key"]
        files = [_file_entry(a, n) for n in s["files"]]
        extra: dict = {}
        if key in ("formula", "story", "text"):
            st = "done" if files[0]["exists"] else "todo"
        elif key == "hero":
            files = [_file_entry(a, n) for n in canonicals or ["canonical.png"]] + files[1:]
            if canonicals:
                st, extra["thumb"] = "done", canonicals[0]
            elif tier(a, agent) == "S":
                st = "skip"
            else:
                st = "part" if "canonical-prompt.md" in a or "character-card.md" in a else "todo"
        elif key == "prompts":
            if "abc-prompts-json.md" in a:
                files = [_file_entry(a, "abc-prompts-json.md")]
            have = sum(f["exists"] for f in files)
            st = "done" if have == len(files) else "part" if have else "todo"
            check = book_check(path)  # the book check (GO) once any prompt file is there
            if check is not None:
                extra["check"] = {"go": check["go"], "fails": len(check["fails"]), "warns": len(check["warns"])}
        elif key == "pictures":
            n = rows_filled(p)
            extra.update(count=n, total=len(ROWS))
            st = "done" if n == len(ROWS) else "part" if n else "todo"
        elif key == "cover":
            c = cover_state(path)
            if c["final"]:
                files.insert(0, {"name": c["final"], "kind": "image", "area": PICTURES, "exists": True})
                st = "done"
            else:
                st = "part" if c["art"] or "cover-prompts-json.md" in a else "todo"
        elif key == "library":
            st = "done" if library_book(path) else "todo"
        elif key == "photos":
            from .. import photos
            n = photos.count(path)
            extra.update(count=n, total=len(photos.CATEGORIES))
            st = "done" if n == len(photos.CATEGORIES) or marks.get(key) else "part" if n else "todo"
        else:
            st = "done" if marks.get(key) else "todo"
            if key == "mockups":
                extra.update(mockups_state(path))
        out.append({"key": key, "label": s["label"], "state": st, "manual": key in MANUAL, "files": files, **extra})
    for s in out:  # the next step to do: the first that isn't done (a skipped one doesn't count)
        if s["state"] in ("todo", "part"):
            s["next"] = True
            break
    return out


def mockups_state(path: Path) -> dict:
    """What the book holds of its mockups: the mockups, their cut-outs, the listing slides (in etsy/ since 30.09.2026;
    «Listing N.png» beside the mockups before)."""
    from ..slides.cutout import NO_BG
    folder = path / MOCKUPS
    pictures = [n for n in _names(folder) if n.lower().endswith(".png") and not n.lower().startswith("canva-cover")]
    slides = [n for n in _names(path / ETSY) if n.lower().startswith("listing") and n.lower().endswith(".png")]
    old = [n for n in pictures if n.lower().startswith("listing ")]
    return {"mockups": len(pictures) - len(old), "noBg": len(_names(folder / NO_BG)),
            "slides": len(slides) + len(old), "editable": (folder / "slides" / "set.json").is_file()}


def _title(book_id: str) -> tuple[int | None, str]:
    m = _NUMBER.match(book_id)
    number, slug = (int(m.group(1)), m.group(2)) if m else (None, book_id)
    text = " ".join(slug.replace("_", " ").replace("-", " ").split())
    return number, (text[:1].upper() + text[1:]) if text else book_id


def display_name(book_id: str) -> str:
    """How a book is named in words: «№41 Little lamb prayers»."""
    number, title = _title(book_id)
    return f"№{number} {title}" if number is not None else title


def _updated(path: Path) -> float:
    latest = 0.0
    for folder in (path / AGENT, path / PICTURES, path / ORIGINALS):
        try:
            for entry in os.scandir(folder):
                latest = max(latest, entry.stat().st_mtime)
        except OSError:
            pass
    try:
        latest = max(latest, (path / STATE).stat().st_mtime)
    except OSError:
        pass
    return latest


def _walk(path: Path):
    """Every file of a book's own areas (their subfolders too — the hero variants): (area, path inside it, stat) —
    by os.scandir, whose entries already carry the size and time on Windows."""
    def walk(folder: str, prefix: str):
        try:
            with os.scandir(folder) as it:
                entries = sorted(it, key=lambda e: e.name)
        except OSError:
            return
        for e in entries:
            try:
                if e.is_dir():
                    yield from walk(e.path, f"{prefix}{e.name}/")
                elif e.is_file():
                    yield f"{prefix}{e.name}", e.stat()
            except OSError:
                continue

    for area in AREAS:
        for rel, st in walk(str(path / area), ""):
            yield area, rel, st


def versions(path: Path) -> dict[str, str]:
    """Every file of the book with a tag that changes when the file does: a picture's address carries it (`?v=<tag>`)
    and the browser keeps the picture for good — nothing reloads or blinks when the page redraws itself; a text step
    the page has open is fetched again only when its tag changed (since 2026-09-26)."""
    return {f"{area}/{rel}": f"{st.st_size:x}{st.st_mtime_ns:x}" for area, rel, st in _walk(path)}


def signature(book_id: str | None = None) -> str:
    """Changes whenever a file of the book (or of any book) appears, changes or goes — the page asks for it to know
    when to redraw itself."""
    h = hashlib.sha1()
    for bid in [book_id] if book_id else book_ids():
        h.update(bid.encode("utf-8", "replace") + b"\0")
        path = books_dir() / bid
        try:
            st = (path / STATE).stat()
            h.update(f"state:{st.st_size}:{st.st_mtime_ns}\0".encode())
        except OSError:
            pass
        for area, rel, st in _walk(path):
            h.update(f"{area}/{rel}:{st.st_size}:{st.st_mtime_ns}\0".encode("utf-8", "replace"))
    return h.hexdigest()[:16]


# ---------------------------------------------------------------- for the page

def _version(path: Path, area: str, name: str) -> str:
    """One picture's tag (as versions() gives it), from one look at that file."""
    try:
        st = (path / area / name).stat()
    except OSError:
        return ""
    return f"{st.st_size:x}{st.st_mtime_ns:x}"


def summary(book_id: str, path: Path | None = None, st: list[dict] | None = None) -> dict:
    """A gallery card: the title, the steps, the pictures count and the thumbnail — the cover, else the cover's
    picture, else the first finished spread, else the hero. (`path`, `st` — already worked out by detail().)"""
    path = path or book_path(book_id)
    agent = path / AGENT
    a = set(_names(agent))
    p = set(_names(path / PICTURES))
    number, title = _title(book_id)
    st = st if st is not None else steps(path)
    cover = picture(p, "Cover")
    art = next((n for n in _names(path / ORIGINALS) if n.startswith("cover-art.")), None)
    hero = next((s.get("thumb") for s in st if s["key"] == "hero"), None)
    first = next((picture(p, pages[0]) for _, pages in ROWS[1:-1] if all(picture(p, x) for x in pages)), None)
    thumb = ({"area": PICTURES, "name": cover, "kind": "cover"} if cover
             else {"area": ORIGINALS, "name": art, "kind": "cover"} if art
             else {"area": PICTURES, "name": first, "kind": "page"} if first
             else {"area": AGENT, "name": hero, "kind": "hero"} if hero else None)
    passed = library_book(path)
    return {
        "id": book_id, "number": number, "title": title, "coverTitle": cover_title(a, agent), "tier": tier(a, agent),
        "steps": [{"key": s["key"], "label": s["label"], "state": s["state"], **({"check": s["check"]} if "check" in s else {})}
                  for s in st],
        "pictures": rows_filled(p), "picturesTotal": len(ROWS), "thumb": thumb, "updated": _updated(path),
        "library": passed,
        "v": {f"{thumb['area']}/{thumb['name']}": _version(path, thumb["area"], thumb["name"])} if thumb else {},
    }


def detail(book_id: str) -> dict:
    """A book's page: its card, the whole strip, the rows, the book check, every picture's version — each worked
    out once (the strip and the versions were twice, 26.09.2026)."""
    from .. import photos
    from .rows import book_check, book_rows
    path = book_path(book_id)
    st = steps(path)
    out = summary(book_id, path, st)
    out["steps"] = st
    out.update(book_rows(path))
    out["photos"] = photos.state(path)
    out["check"] = book_check(path)  # remembered by steps() a moment ago
    out["v"] = versions(path)
    return out


def all_books() -> list[dict]:
    out = []
    for book_id in book_ids():
        try:
            out.append(summary(book_id))
        except ApiError:  # gone between the listing and the look (renamed, deleted)
            continue
    return out


def media_file(book_id: str, area: str, name: str, variant: str | None = None) -> Path:
    """A picture of a book, only by a name that really is in that folder (a hero variant's: in its subfolder)."""
    if area not in AREAS or not name.lower().endswith(core.IMAGE_EXTS):
        raise ApiError("Не знайдено.", 404)
    folder = book_path(book_id) / area
    if variant:
        if variant != Path(variant).name or variant.startswith("."):
            raise ApiError("Не знайдено.", 404)
        folder = folder / "variants" / variant
    if name not in _names(folder):
        raise ApiError("Не знайдено.", 404)
    return folder / name


def agent_text(book_id: str, name: str) -> str:
    """One of the agent's text files, only by a name that really is in `agent/`."""
    agent = book_path(book_id) / AGENT
    text = read_text(agent / name) if name.lower().endswith(TEXT_SUFFIXES) and name in _names(agent) else None
    if text is None:
        raise ApiError("Файл не знайдено.", 404)
    return text


def set_mark(book_id: str, step: str, on: bool) -> dict:
    """Ticks (or unticks) a step done outside Book Studio — Canva, the mockups; the photo mockups with a category
    skipped."""
    if step not in MANUAL:
        raise ApiError("Цей крок позначається сам.")
    path = book_path(book_id)

    def change(data):
        marks = dict(data.get("marks") or {})
        if on:
            marks[step] = True
        else:
            marks.pop(step, None)
        data["marks"] = marks
    update_state(path, change)
    return detail(book_id)


# ---------------------------------------------------------------- outside Book Studio

def open_in_windows(book_id: str | None, what: str, name: str = "", variant: str = "") -> None:
    """In Windows: the books' folder; a book's folder, its pages or its originals (Explorer), or one file there — a
    picture of the pages or the originals (a hero variant's: in its subfolder), an agent's file — in its usual
    program. Only inside the book."""
    if what == "books":
        target = books_dir()
        target.mkdir(parents=True, exist_ok=True)
    elif what in ("folder", AGENT, PICTURES, ORIGINALS, MOCKUPS, ETSY):
        path = book_path(book_id or "")
        target = path if what == "folder" else path / what
        if variant:
            if what not in (PICTURES, ORIGINALS) or variant != Path(variant).name or variant.startswith("."):
                raise ApiError("Не знайдено.", 404)
            target = target / "variants" / variant
        if name:
            if what == "folder" or name not in _names(target) or not name.lower().endswith(core.IMAGE_EXTS + TEXT_SUFFIXES):
                raise ApiError("Файл не знайдено.", 404)
            target = target / name
        else:
            target.mkdir(exist_ok=True)
    else:
        raise ApiError("Не знайдено.", 404)
    if core.SANDBOX:
        return
    if target.is_file():
        os.startfile(str(target))  # noqa: S606 — a picture or a text of the book's, in its usual program
    else:
        desktop.open_in_explorer(target)


def antigravity() -> Path | None:
    base = os.environ.get("LOCALAPPDATA")
    exe = Path(base) / "Programs" / "antigravity" / "Antigravity.exe" if base else None
    return exe if exe and exe.is_file() else None


def agent_words(book_id: str | None) -> str:
    """What to say to the book agent: a new book or which book goes on — with the pipeline's full paths. Antigravity 2
    ignores a folder given at its start: a new chat runs in the project last picked in it, and once that was the
    prototype's `Book Console`, so the agent wrote the book there (2026-09-26). The words name the rules and the
    books' folder themselves, whatever project the chat is in."""
    rules = core.PIPELINE_DIR / "GEMINI.md"
    if book_id:
        return f"Продовжуємо книгу {book_path(book_id)} (правила — {rules}; інших папок книг не чіпай)"
    return f"Нова книга. Спершу прочитай {rules}; книгу пиши тільки в {books_dir()}"


def open_agent(book_id: str | None) -> str:
    """Antigravity and, in the clipboard, the words for its agent (`agent_words()`). Which folder the agent works in
    is the project picked in Antigravity — Book Studio can't choose it."""
    say = agent_words(book_id)
    if not core.SANDBOX:
        exe = antigravity()
        if not exe:
            raise ApiError("Antigravity не знайдено (очікувався %LOCALAPPDATA%\\Programs\\antigravity\\Antigravity.exe).")
        subprocess.Popen([str(exe)], cwd=str(core.PIPELINE_DIR),
                         creationflags=desktop.CREATE_NO_WINDOW if os.name == "nt" else 0)
    from .. import clipboard
    clipboard.set_text(say)
    return say


def delete_book(book_id: str) -> dict:
    """The book out of the Workshop: its whole folder (the agents' files, the pages, the originals) into the
    Windows Recycle Bin — restorable until it is emptied (the owner, 2026-09-26: "the book and all its files").
    A book already in the library takes its pages from here: they are copied there first, so it keeps them."""
    path = book_path(book_id)
    number, title = _title(book_id)
    passed = library_book(path)
    if passed:
        library.keep_pages(passed["id"])
    desktop.to_recycle_bin(path)
    core.log.info("Workshop: book %s went to the Recycle Bin", book_id)
    return {"deleted": book_id, "title": title, "number": number}


# ---------------------------------------------------------------- into the library

def _slides_done(book_id: str) -> None:
    """The book is done: its listing slides' cache goes, the scenes stay a preset (the owner, 29.09.2026)."""
    try:
        from ..slides import store as slide_store
        slide_store.book_done(book_id)
    except Exception:
        core.log.warning("Workshop: the slides' cache of %s not cleaned", book_id, exc_info=True)


def to_library(book_id: str, body: dict) -> dict:
    """«Передати в бібліотеку»: a library book made from this one — its texts (book-text.md) and its Etsy listing
    (checked by the page, read only, or typed in); its cover and pages (pictures/: Cover.png, 1…30.png) it takes from
    this folder, not a copy (library.follow(), 27.09.2026). The book's last step ticks at once. A job: the page shows
    how the pages' previews are made."""
    from .rows import book_texts
    path = book_path(book_id)
    passed = library_book(path)
    if passed:
        raise ApiError("Цю книгу вже передано в бібліотеку.", 409, {"bookId": passed["id"]})
    listing = library.listing_of(body)
    book = library.create_book(listing, _title(book_id)[1], workshop=book_id,  # a listing another book has: 409
                               pagesFrom=library.PAGES_FROM_WORKSHOP)
    update_state(path, lambda d: d.update(library={"id": book["id"], "listingId": listing["id"], "at": core.now_iso()}))
    core.log.info("Workshop: %s passed to the library as %s, listing %s", book_id, book["id"], listing["id"])

    def run(job) -> dict:
        job.progress("Передаю сторінки…", 5)
        library.follow(book["id"], progress=lambda i, n: job.progress("Передаю сторінки…", 5 + 85 * i / n))
        pages = library.workshop_pages(library.load(book["id"]))
        texts = book_texts(path)
        if texts:
            library.update_texts(book["id"], texts)
        _slides_done(book_id)
        if body.get("useListingImage"):
            job.progress("Фото лістингу…", 97)
            library.take_listing_image(library.load(book["id"]))
        return {"book": library.summary(library.load(book["id"])), "pages": pages["found"], "errors": pages["unreadable"]}

    return {"jobId": jobs.start("workshop-to-library", run, exclusive=f"workshop-{book_id}").id}
