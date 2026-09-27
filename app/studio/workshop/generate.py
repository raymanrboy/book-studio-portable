"""The generation mode: «Генерувати» puts a row's prompt into the clipboard and waits; the first new picture that
appears in Downloads after that (finished downloading) goes into the row — cut and flipped — and, for the whole book,
the next row's prompt is already in the clipboard. The work is the server's: it goes on while the window is behind
Gemini, or while the owner is elsewhere in Book Studio.

A caught picture is **moved** out of Downloads into the book's `originals/`, named by its row (the owner, 2026-09-26:
"it should live in the program"); nothing else in Downloads is touched. Only files that appear after the press count,
only pictures (PNG, JPEG, WEBP), never a half-downloaded one.

A row that needs several things pasted (the cover's margins: the picture with its white margins, then the outpaint
prompt; a hero variant's spread) gives them one by one: the first goes into the clipboard at once, «Далі» in the
window or F8 anywhere puts in the next. The cover's picture, once in, goes on to its margins by itself.
"""
from __future__ import annotations

import os
import threading
import time
from pathlib import Path

from .. import clipboard, core, desktop
from ..server import ApiError
from . import books, pictures, rows

PARTIAL = (".crdownload", ".part", ".tmp", ".download", ".partial")
SERIES_ORDER = [f"spread{n}" for n in rows.SPREADS] + ["page1", "page30"]  # as the pipeline generates them


def downloads_folder() -> Path:
    """Where the browser saves downloads; the sandbox has a made-up one in its data folder."""
    if core.SANDBOX:
        return core.data_path("downloads")
    return Path(desktop.downloads_folder() or Path.home() / "Downloads")


# ---------------------------------------------------------------- what a row asks to paste

def _items(book_id: str, key: str, variant: str | None) -> tuple[str, list[dict]]:
    """The row's label and the things to paste, in order: {"kind": "text"|"image", "label", "text"|"path"|"spread"}."""
    detail = books.detail(book_id)
    path = books.book_path(book_id)
    if key == "cover-wrap":
        c = detail["cover"]
        if not (c["expanded"] and c["outpaint"]):
            raise ApiError("Спершу сама обкладинка — перший етап.")
        return "Обкладинка · поля", [
            {"kind": "image", "label": "обкладинка з полями", "path": str(path / books.ORIGINALS / c["expanded"])},
            {"kind": "text", "label": "промпт аутпейнту", "text": c["outpaint"]}]
    if variant:
        v = next((x for x in detail["variants"] if x["name"] == variant), None)
        if not v:
            raise ApiError("Варіант не знайдено.", 404)
        canonical = path / books.AGENT / "canonical.png"
        if key == "hero":
            if not v["heroPrompt"]:
                raise ApiError(f"У варіанті {variant} ще немає hero-prompt.md — його пише агент.")
            items = [{"kind": "text", "label": "промпт героя", "text": v["heroPrompt"]}]
            if canonical.is_file():
                items.insert(0, {"kind": "image", "label": "основний герой", "path": str(canonical)})
            return f"{variant}: герой", items
        r = next((x for x in v["rows"] if x["key"] == key), None)
        if not r:
            raise ApiError("Для цього розвороту у варіанті немає промпту.")
        base = next((x for x in detail["rows"] if x["key"] == key), None)
        if not base or not base["pictures"]:
            raise ApiError(f"{r['label']}: спершу потрібен основний розворот — у варіанті змінюється саме він.")
        hero = pictures.variant_dir(path, variant) / "hero.png"
        if not hero.is_file():
            raise ApiError(f"Спершу герой варіанта {variant} (hero.png) — згенеруйте його вгорі вкладки.")
        return f"{variant}: {r['label']}", [
            {"kind": "image", "label": "основний розворот", "spread": key},
            {"kind": "image", "label": "герой варіанта", "path": str(hero)},
            {"kind": "text", "label": "промпт", "text": r["prompt"]}]
    if key == "hero":
        if not detail["heroPrompt"]:
            raise ApiError("Промпту героя ще немає — його пише агент (canonical-prompt.md).")
        return "Герой", [{"kind": "text", "label": "промпт героя", "text": detail["heroPrompt"]}]
    r = next((x for x in detail["rows"] if x["key"] == key), None)
    if not r:
        raise ApiError("Невідомий рядок книги.")
    if not r["prompt"]:
        raise ApiError(f"{r['label']}: промпту ще немає — його пише агент.")
    return r["label"], [{"kind": "text", "label": "промпт", "text": r["prompt"]}]


# ---------------------------------------------------------------- the session

class Session:
    """One wait at a time, for the whole program: which row of which book, what's in the clipboard, what's queued."""

    def __init__(self, watch: bool = True):
        self.lock = threading.RLock()
        self.version = 0
        self.active: dict | None = None     # book, variant, key, label, items, item, queue, series, since, known, step, of
        self.last: dict | None = None       # the last catch: book, variant, key, label, note, file, at
        self.error = ""
        self.hotkey = clipboard.Hotkey(self.next_item)
        self._sizes: dict[str, int] = {}
        if watch:  # the tests look by hand (look())
            threading.Thread(target=self._watch, name="downloads", daemon=True).start()

    def status(self) -> dict:
        with self.lock:
            a = self.active
            return {
                "version": self.version,
                "active": None if not a else {
                    "book": a["book"], "title": books.display_name(a["book"]), "variant": a["variant"],
                    "key": a["key"], "label": a["label"], "item": a["item"], "items": [i["label"] for i in a["items"]], "queue": len(a["queue"]),
                    "series": a["series"], "since": a["since"], "step": a["step"], "of": a["of"]},
                "last": self.last, "error": self.error, "f8": self.hotkey.active, "f8Failed": self.hotkey.failed,
            }

    def _bump(self):
        self.version += 1

    # -- starting and stopping
    def start(self, book_id: str, key: str | None, variant: str | None = None, series: bool = False) -> dict:
        books.book_path(book_id)
        with self.lock:
            if key and not series:
                queue = [key]
            else:
                queue = self._series(book_id, variant)
                if key:
                    queue = [key] + [k for k in queue if k != key]
                if not queue:
                    raise ApiError("Усі рядки з промптами вже мають картинки." if not variant
                                   else f"У варіанті {variant} усі розвороти вже мають картинки.")
            self.error = ""
            self._begin(book_id, variant, queue, series, step=1, of=len(queue))
            return self.status()

    @staticmethod
    def _series(book_id: str, variant: str | None) -> list[str]:
        detail = books.detail(book_id)
        if variant:
            v = next((x for x in detail["variants"] if x["name"] == variant), None)
            return [r["key"] for r in (v["rows"] if v else []) if r["prompt"] and not r["pictures"]]
        by = {r["key"]: r for r in detail["rows"]}
        return [k for k in SERIES_ORDER if by[k]["prompt"] and not by[k]["pictures"]]

    def _begin(self, book_id, variant, queue, series, step=1, of=1):
        key, rest = queue[0], queue[1:]
        label, items = _items(book_id, key, variant)
        folder = downloads_folder()
        if not folder.is_dir():
            raise ApiError(f"Папку завантажень не знайдено: {folder}")
        try:
            known = {e.name for e in os.scandir(folder)}
        except OSError:
            known = set()
        self.active = {"book": book_id, "variant": variant, "key": key, "label": label, "items": items, "item": 0,
                       "queue": rest, "series": series, "since": time.time(), "known": known, "step": step, "of": of}
        self._sizes = {}
        self._put_item()
        self.hotkey.want(len(items) > 1)
        self._bump()

    def stop(self, book_id: str | None = None) -> dict:
        """Stops waiting — for any book, or only when it's this book's picture that is awaited (a deleted book)."""
        with self.lock:
            if self.active and (book_id is None or self.active["book"] == book_id):
                self.active = None
                self.hotkey.want(False)
                self._bump()
            return self.status()

    # -- the clipboard
    def _put_item(self):
        a = self.active
        item = a["items"][a["item"]]
        try:
            if item["kind"] == "text":
                clipboard.set_text(item["text"])
            elif "spread" in item:
                clipboard.set_image(pictures.spread_panorama(a["book"], item["spread"]))
            else:
                clipboard.set_image(item["path"])
            self.error = ""
        except (ApiError, OSError) as exc:
            self.error = str(exc)

    def next_item(self) -> dict:
        """«Далі» / F8: the next thing of the row into the clipboard."""
        with self.lock:
            a = self.active
            if a and a["item"] < len(a["items"]) - 1:
                a["item"] += 1
                self._put_item()
                if a["item"] == len(a["items"]) - 1:
                    self.hotkey.want(False)
                self._bump()
            return self.status()

    def again(self) -> dict:
        """The current thing into the clipboard once more (something else was copied meanwhile)."""
        with self.lock:
            if self.active:
                self._put_item()
                self._bump()
            return self.status()

    # -- watching Downloads
    def _watch(self):
        while True:
            time.sleep(0.6)
            try:
                self.look()
            except Exception:  # the watcher must never die
                core.log.exception("Workshop: watching Downloads failed")

    def look(self):
        """One look into Downloads: the first new picture that has finished downloading is caught."""
        with self.lock:
            a = self.active
            if not a:
                return
            known, since = a["known"], a["since"]
        try:
            entries = [e for e in os.scandir(downloads_folder()) if e.is_file() and e.name not in known]
        except OSError:
            return
        for e in sorted(entries, key=lambda e: e.stat().st_mtime):
            low = e.name.lower()
            if low.endswith(PARTIAL) or not low.endswith(core.IMAGE_EXTS):
                continue
            st = e.stat()
            if st.st_mtime < since - 2 or st.st_size == 0:
                with self.lock:
                    known.add(e.name)
                continue
            if self._sizes.get(e.name) != st.st_size:  # still growing: look again next time
                self._sizes[e.name] = st.st_size
                continue
            self._catch(Path(e.path))
            return

    def _catch(self, file: Path):
        with self.lock:
            a = self.active
            if not a or file.name in a["known"]:  # one picture is caught once
                return
            a["known"].add(file.name)
        try:
            # moved out of Downloads into the book's originals/ (named by its row), then cut into its pages
            result = pictures.place(a["book"], a["key"], file, file.name, a["variant"], take=True)
        except (ApiError, OSError) as exc:
            with self.lock:
                self.error = f"{file.name}: {exc}"
                self._bump()
            return
        with self.lock:
            self.last = {"book": a["book"], "variant": a["variant"], "key": a["key"], "label": a["label"],
                         "note": result.get("note", ""), "file": file.name, "at": time.time()}
            core.log.info("Workshop: caught %s → %s %s", file.name, a["book"], a["key"])
            if self.active is not a:
                # «Стоп», the book deleted or another row started while the picture was placed (0.5–3 s): the
                # picture is in its book, but that wait is over — its queue must not come back.
                self._bump()
                return
            queue = a["queue"]
            if a["key"] == "cover" and not queue:
                queue = ["cover-wrap"]  # the cover's picture goes on to its margins by itself
            self.active = None
            self.hotkey.want(False)
            while queue:
                try:
                    self._begin(a["book"], a["variant"], queue, a["series"],
                                step=a["step"] + 1 if a["series"] else 1, of=a["of"] if a["series"] else 1)
                    break
                except ApiError as exc:  # a row that can't go now (no prompt yet) is passed by
                    self.error = str(exc)
                    queue = queue[1:]
            self._bump()
            finished = a["series"] and not self.active
        if core.SANDBOX:
            return
        if finished:
            desktop.attention(core.APP_NAME)  # the whole queue is in: the taskbar button flashes, Windows chimes
        else:
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_OK)  # a short sound for each picture caught
            except Exception:
                pass


_session: Session | None = None
_session_lock = threading.Lock()
IDLE = {"version": 0, "active": None, "last": None, "error": "", "f8": False, "f8Failed": False}


def session() -> Session:
    """The generation mode — made (the Downloads watcher and the F8 thread started) the first time it is used."""
    global _session
    with _session_lock:
        if _session is None:
            _session = Session()
        return _session


def status() -> dict:
    """What the pages are told about the generation mode: before anything was ever started it is idle, and asking
    starts nothing (Book Studio's start and every background look used to start the watcher and F8's thread for the
    whole run, the Workshop used or not — 26.09.2026)."""
    with _session_lock:
        s = _session
    return s.status() if s else dict(IDLE)


def stop(book_id: str | None = None) -> None:
    """Nothing waits any more for a picture of this book (or of any): there is nothing to stop in an idle mode."""
    with _session_lock:
        s = _session
    if s:
        s.stop(book_id)
