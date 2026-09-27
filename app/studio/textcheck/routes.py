"""The text check's routes, and a printed page turned back into the library's text (the passport learns it)."""
from __future__ import annotations

import difflib
import re
import unicodedata

from .. import core, library
from ..jobs import jobs
from ..wording import alike
from ..server import ApiError, Request, route
from . import ollama
from .ollama import _ollama_command, _settings
from .texts import COMMON, _NAME_SLOT
from .run import cancel, check_order, warm
from .journal import mark


@route("GET", "/api/textcheck/status")
def _status(req: Request):
    return ollama.status()


@route("POST", "/api/settings/textcheck")
def _save_settings(req: Request):
    body = req.json or {}
    patch = {}
    if "enabled" in body:
        patch["enabled"] = bool(body["enabled"])
    if "prescan" in body:
        patch["prescan"] = bool(body["prescan"])
    if "model" in body:
        model = str(body.get("model") or "").strip()
        if not re.fullmatch(r"[\w.\-/:]{1,120}", model):
            raise ApiError("Некоректна назва моделі.")
        patch["model"] = model
    if patch:
        core.settings.update({"textcheck": patch})
    return ollama.status()


@route("POST", "/api/textcheck/start")
def _start(req: Request):
    if not ollama.start_ollama():
        raise ApiError("Ollama не запустилась — запустіть її з меню «Пуск»." if _ollama_command()
                       else "Ollama не встановлена на цьому комп'ютері.")
    return ollama.status()


def _passport_words(text: str, template: str, child: str) -> dict[int, bool]:
    """Where a printed word stands in the passport text: word start -> True when it stands in the place of
    {Name}, False when it is the passport's own word. Words the passport does not have are left out."""
    name = [w.casefold() for w in re.findall(r"\w+", alike(child))]
    ref, slot = [], []
    for n, part in enumerate(_NAME_SLOT.split(alike(template))):
        if n:
            ref += name
            slot += [True] * len(name)
        found = [w.casefold() for w in re.findall(r"\w+", part)]
        ref += found
        slot += [False] * len(found)
    printed = list(re.finditer(r"\w+", text))
    matcher = difflib.SequenceMatcher(a=ref, b=[m.group().casefold() for m in printed], autojunk=False)
    out = {}
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            out.update({printed[j].start(): slot[i] for i, j in zip(range(i1, i2), range(j1, j2))})
    return out


def as_template(text: str, child: str, template: str = "") -> str:
    """A printed page as a library text: the child's name becomes {Name} again — only as a whole word
    («Eve», not the «eve» of «every»), and only where the passport had {Name}: where it had the same word
    of its own («Hope» the girl, «hope» the word), the word stays. In lines the passport does not have yet,
    a name that is also an everyday word becomes {Name} only when it starts with a capital."""
    text = re.sub(r"\n{3,}", "\n\n", unicodedata.normalize("NFC", text.strip()))
    child = unicodedata.normalize("NFC", child.strip())
    if not child:
        return text
    same = alike(text)
    pattern = r"\s+".join(re.escape(part) for part in alike(child).split())
    hits = [m.span() for m in re.finditer(rf"(?<!\w){pattern}(?!\w)", same, re.I)]
    known = _passport_words(same, template, child)
    own = {w.casefold() for w in re.findall(r"\w+", _NAME_SLOT.sub(" ", template or ""))}
    everyday = child.casefold() in COMMON or child.casefold() in own
    out = text
    for start, end in reversed(hits):
        where = [known.get(m.start() + start) for m in re.finditer(r"\w+", same[start:end])]
        if False in where:
            continue  # the passport's own word
        if None in where and everyday and not text[start].isupper():
            continue  # «hope» in a new line: a word, not the girl
        out = out[:start] + "{Name}" + out[end:]
    return out


def _passport_texts(book: dict, pages: list, child: str) -> dict[str, str]:
    allowed = {"cover"} | {f"spread{n}" for n in library.SPREAD_NUMBERS}
    texts = {}
    for page in pages:
        key, text = str((page or {}).get("key") or ""), str((page or {}).get("text") or "").strip()
        if key not in allowed or not text or len(text) > 4000:
            raise ApiError("Некоректний текст сторінки.")
        texts[key] = as_template(text, child, (book.get("text") or {}).get(key) or "")
    return texts


@route("POST", "/api/textcheck/passport")
def _passport(req: Request):
    """«Так у шаблоні Canva»: the book's texts for these pages become what was printed (owner's click only).
    With "preview" nothing is saved: the owner first sees the texts as they would be kept."""
    body = req.json or {}
    child = str(body.get("child") or "").strip()
    pages = body.get("pages") or []
    if not child or not isinstance(pages, list) or not pages:
        raise ApiError("Немає що оновлювати.")
    book_id = str(body.get("bookId") or "")
    texts = _passport_texts(library.load(book_id), pages, child)
    if body.get("preview"):
        return {"texts": texts}
    book = library.update_texts(book_id, texts)
    core.log.info("Passport texts of %s updated from a print: %s", book["id"], ", ".join(texts))
    return {"updated": sorted(texts)}


@route("POST", "/api/textcheck/mark")
def _mark(req: Request):
    """The owner marked a finding «це не помилка»: kept in that check's journal for the next calibration."""
    body = req.json or {}
    return {"kept": mark(str(body.get("journal") or ""), str(body.get("id") or ""))}


@route("POST", "/api/textcheck/warm")
def _warm(req: Request):
    """The card is taking files: the model is asked for now, so the check does not wait for it later."""
    return {"warming": warm()}


@route("POST", r"/api/orders/(\d{5,20})/textcheck/cancel")
def _cancel(req: Request):
    return {"stopped": cancel(req.groups[0], str((req.json or {}).get("jobId") or "") or None)}


@route("POST", r"/api/orders/(\d{5,20})/textcheck")
def _check(req: Request):
    rid = req.groups[0]
    body = req.json or {}
    if not _settings()["enabled"]:
        return {"off": True}
    try:
        count, pick = int(body.get("pages") or 0), int(body.get("pick") or 0)
    except (TypeError, ValueError):
        raise ApiError("Некоректний запит.") from None
    folder = str(body.get("folder") or "")
    job = jobs.start("textcheck", lambda job: check_order(job, rid, folder, count, pick))
    return {"jobId": job.id}
