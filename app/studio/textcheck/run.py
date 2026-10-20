"""One check: the print files, the two passes (read, then check), the model's answers cached by a file's content,
four pages in flight, a newer check of the same book stopping this one."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image

from .. import core, images, library, orders, stages
from ..jobs import UserError
from ..wording import guess_child_name, words
from . import ollama
from .ollama import ModelError, TimedOut, Unavailable, _settings
from .texts import assign, fill, personalization, similarity
from .rules import (_all_issues, _label, _learnable, _one_alarm, _ordered, _saw_nothing, _strange, _vocabulary,
                    _wrong_book, has_text, page_issues)
from .journal import _journal


PARALLEL = 4             # pages in flight at once — the owner set OLLAMA_NUM_PARALLEL=4
IMAGE_SIDE = 1024        # tested: 768–2000 px read equally well; smaller is faster to send

READ_TOKENS = 64         # the read pass needs only the first lines of a page
JUDGE_TOKENS = 1000      # a page's copy and verdict fit easily; a model that runs on is stopped here

# What images.text_score() says about a page. Measured on the owner's five real books (20.09.2026):
# a page with text scores 2.4-2.6, a page with only a picture 0.9-1.5. Anything in between is «not sure»
# and goes to the model exactly as before — the heuristic may only save work, never decide alone.
LOOKS_TEXT = 2.2
LOOKS_PICTURE = 1.6

READ_PROMPT = ("Transcribe all text printed on this book page exactly, character by character. Keep the exact "
               "spelling even if a word looks misspelled, keep capitals, accents, punctuation and curly braces, and "
               "put each printed line on its own line. Ignore pictures and decorations. Output only the text.")

STRICT_PROMPT = """You check a page of a personalized children's book before it is printed.
{name_line}The EXPECTED text below is exactly what must be printed on this page.
1. Transcribe all visible text exactly as printed (keep spelling, accents, capitals and braces). Do not correct anything.
2. Compare it with the EXPECTED text word by word. Problems: a misspelled or wrong name, a missing accent, a leftover
   placeholder in curly braces, a missing, extra or changed word, text cut off. Different line breaks, quote or dash
   styles are NOT problems.
3. Verdict: ok (identical words) or error. Explain every problem in Ukrainian.
4. only_punctuation: true when every problem is only about punctuation, quotes, spaces or capital letters (all the
   words themselves are right), otherwise false.

EXPECTED:
{expected}"""

LOOSE_PROMPT = """You check a page of a personalized children's book before it is printed.
{name_line}{context}1. Transcribe all visible text exactly as printed (keep spelling, accents, capitals and braces). Do not correct anything.
2. Report only clear mistakes: the child's name misspelled or missing an accent, a different child's name, a leftover
   placeholder in curly braces, a word cut off at the edge of the page, words stuck together without a space, an
   obvious typo.{extra} Different line breaks, quote or dash styles and small edits by the designer are NOT problems.
3. Verdict: ok or error. Explain every problem in Ukrainian.
4. only_punctuation: true when every problem is only about punctuation, quotes, spaces or capital letters (all the
   words themselves are right), otherwise false."""

SCHEMA = {"type": "object", "properties": {
    "transcript": {"type": "string"}, "verdict": {"type": "string", "enum": ["ok", "error"]},
    "problems": {"type": "array", "items": {"type": "string"}}, "only_punctuation": {"type": "boolean"}},
    "required": ["transcript", "verdict", "problems", "only_punctuation"]}

_warm_lock = threading.Lock()
_warmed_at = 0.0
WARM_AGAIN = 30  # seconds: one warm-up per folder is enough, however many files are dropped


def warm() -> bool:
    """Asks for the model while the card is still copying and checking the files, so the check that starts
    right after them does not wait for it (~4 s from this computer's memory, ~70 s from disk). Quiet: a
    model that cannot be had is the check's own thing to report, and the card hears it there."""
    global _warmed_at
    if core.SANDBOX or not _settings()["enabled"]:
        return False  # made-up or test data (the preview, tests) never starts the PC's real Ollama or fills its graphics card
    with _warm_lock:
        if _active or time.monotonic() - _warmed_at < WARM_AGAIN:
            return False  # a check is already holding the model, or one folder asked twice
        _warmed_at = time.monotonic()
    model = _settings()["model"]

    def load() -> None:
        try:
            ollama._ready(model, lambda step: None)
        except ModelError as err:
            core.log.info("Text check: the model was not warmed up (%s)", err)

    threading.Thread(target=load, name="textcheck-warm", daemon=True).start()
    return True


START_DELAY = 8  # seconds after the program's start: the window opens first


def start_quietly() -> None:
    """Ollama itself is started a little after the program (owner, 19.10.2026), so a check never waits for it — without the model:
    that is asked for by warm() when an order is opened or takes files, and only then fills the graphics card (05.10.2026).
    Hidden: no tray icon, no window. Never on made-up or test data (the preview, tests): they would start the PC's real Ollama."""
    from .. import modules, portable
    if core.SANDBOX or not _settings()["enabled"] or (portable.root() and not modules.installed("textcheck")):
        return
    time.sleep(START_DELAY)
    try:
        if not ollama.start_ollama(hidden=True):
            core.log.info("Text check: Ollama was not started at the program's start")
    except Exception:  # a thread of its own: unlogged, a failure here would vanish without a trace
        core.log.exception("Text check: Ollama's start at the program's start failed")


def picture(path: Path, part: str | None = None) -> str:
    """A page as the model sees it: a 1024-px JPEG cut from the preview the proof already made (no second
    decoding of the 4000-px file). The cover (back and front in one picture) is sent as two halves, each about
    as square as a page."""
    source = images.preview(path, 1400)
    with Image.open(source) as im:
        im = im.convert("RGB")
        if part:
            w, h = im.size
            im = im.crop((0, 0, w // 2, h) if part == "back" else (w - w // 2, 0, w, h))
        im.thumbnail((IMAGE_SIDE, IMAGE_SIDE), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=90)
    return base64.b64encode(buf.getvalue()).decode("ascii")


_cache: dict[str, str] = {}
_cache_lock = threading.Lock()
_runs: dict[str, tuple[threading.Event, str | None]] = {}  # book of an order -> (stop, job id) of its check
_runs_lock = threading.Lock()
_active = 0  # checks running now
_active_lock = threading.Lock()

_digests: dict[tuple, str] = {}
_digests_lock = threading.Lock()


def _digest(path: Path) -> str:
    """The file's content (sha1), read once per version of the file. Answers are kept by content, not by folder:
    every drop copies the files into a new folder, and a book dropped again with one page fixed used to be asked
    about page by page (~25–35 s) — now only the fixed page is (since 2026-09-26)."""
    stat = path.stat()
    key = (str(path.resolve()), stat.st_size, stat.st_mtime_ns)
    with _digests_lock:
        if key in _digests:
            return _digests[key]
    h = hashlib.sha1()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    with _digests_lock:
        if len(_digests) > 5000:
            _digests.clear()
        _digests[key] = h.hexdigest()
    return _digests[key]


def _cache_key(path: Path, part: str | None, model: str, prompt: str, max_tokens: int | None) -> str:
    raw = f"{_digest(path)}|{part}|{model}|{max_tokens}|{prompt}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _other_children(receipt_id: str) -> set[str]:
    """First names of the children in other orders — a page with one of them was copied from an old design."""
    names: set[str] = set()
    for o in stages.picker_orders():
        if str(o.get("receiptId")) == str(receipt_id):
            continue
        for item in o.get("items") or []:
            names.update(t.casefold() for t in words(guess_child_name([item])) if len(t) >= 3)
    return names


def _loose(child: str, context: str = "", extra: str = "") -> str:
    name_line = f'The child\'s name is "{child}".\n' if child else ""
    return LOOSE_PROMPT.format(name_line=name_line, context=context, extra=extra)


def _strict(child: str, expected: str) -> str:
    name_line = f'The child\'s name is "{child}". ' if child else ""
    return STRICT_PROMPT.format(name_line=name_line, expected=expected)


_UNREAD = "модель не змогла прочитати сторінку"
_TRANSCRIPT = re.compile(r'"transcript"\s*:\s*"((?:[^"\\]|\\.)*)"', re.S)


def _parse(content: str) -> dict:
    """The check pass's answer; a cut-off or broken one (the model ran on and on) is a failure — unless its copy
    of the page came through whole (`_salvage`)."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return _salvage(content)
    if not isinstance(data, dict):
        return {"failed": _UNREAD}
    data["transcript"] = re.sub(r"\n{3,}", "\n\n", str(data.get("transcript") or "")).strip()
    return data


def _salvage(content: str) -> dict:
    """gemma4 with a JSON schema sometimes copies a correct page word for word, then invents a mistake and apologises
    until JUDGE_TOKENS cuts it (ollama#15502). The copy is whole and its closing quote came before the loop: it is
    kept, with no verdict, and the program's own comparison decides (06.10.2026). A copy that is itself cut stays a
    failure."""
    found = _TRANSCRIPT.search(content or "")
    try:
        text = json.loads(f'"{found.group(1)}"') if found else ""
    except json.JSONDecodeError:
        text = ""
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    if not text:
        return {"failed": _UNREAD}
    return {"transcript": text, "verdict": None, "problems": [], "only_punctuation": None, "salvaged": True}


def run_key(receipt_id: str, pick: int = 0) -> str:
    """Which check is which: one per book of an order, so books of the same order do not stop each other."""
    return f"{receipt_id}#{max(0, pick)}"


def check_order(job, receipt_id: str, folder_raw: str, count: int, pick: int = 0) -> dict:
    """The whole check of one order's print folder (Cover.png + 1..count.png), for its book number `pick`."""
    order = stages.picker_order(str(receipt_id))
    if not order:
        raise UserError("Замовлення не знайдено.")
    orders.enrich(order, orders.books_by_listing())
    items = order.get("items") or [{}]
    if not 0 <= pick < len(items):
        pick = 0
    return check_book(job, str(receipt_id), items[pick], folder_raw, count, pick)


def check_book(job, receipt_id: str, item: dict, folder_raw: str, count: int, pick: int = 0) -> dict:
    """One book of an order (an enriched order item: variations, childName, book) against its print folder."""
    started = time.monotonic()
    files = _print_files(folder_raw, count)
    pers = personalization(item)
    book = library.load(item["book"]["id"]) if item.get("book") else None
    texts = (book or {}).get("text") or {}
    refs = {k: fill(texts.get(k) or "", pers["child"], pers["gifter"]) for k in library.TEXT_KEYS if texts.get(k)}
    full = bool(pers["child"]) and any(refs.get(f"spread{n}") for n in library.SPREAD_NUMBERS)
    target = _targets(files, count, refs, pers)
    rules = (_vocabulary(pers), _other_children(receipt_id))  # the program's own call on names and placeholders
    with _Run(job, receipt_id, _settings()["model"], pick) as run:
        targets, answers, layout = _passes(run, target, files, count, refs, pers, full, rules)
        run.say("Підсумок…")
    issues = _all_issues(targets, answers, layout, files, pers, count, rules, (book or {}).get("id"))
    learn = _learnable(targets, issues)
    found = set(layout["mapping"].values())
    result = {
        "mode": "full" if full else "light",
        "light": None if full else ("noBook" if not book else "noName" if not pers["child"] else "noTexts"),
        "bookId": (book or {}).get("id"),
        "model": run.model,
        "seconds": round(time.monotonic() - started, 1),
        "child": pers["child"],
        "pages": [{"page": t["page"], "part": t.get("part"), "file": t["file"], "label": t["label"],
                   "key": t.get("key"), "mode": t["mode"], "expected": t.get("expected"),
                   "learn": None if answers[i].get("failed") else learn.get(i),
                   "text": "" if answers[i].get("failed") else (answers[i].get("transcript") or "")}
                  for i, t in enumerate(targets)],
        "skipped": [n for n in library.SPREAD_NUMBERS if refs.get(f"spread{n}") and f"spread{n}" not in found] if full else [],
        "issues": issues,
    }
    result["journal"] = _journal(receipt_id, result, pers, pick, answers, layout)
    return result


def page_kinds(files: dict[int, Path], pages: list[int]) -> dict[int, str]:
    """A local, model-free guess for each story page: "text", "picture" or "unsure" (nothing is decided
    by it alone — see LOOKS_TEXT). It reads the 360 px preview the page strip has already made, so it
    costs about 5 ms a page; switched off in Settings, every page is "unsure" and the check is as it was."""
    if not _settings()["prescan"]:
        return {n: "unsure" for n in pages}
    kinds: dict[int, str] = {}
    with ThreadPoolExecutor(min(4, max(1, len(pages))), thread_name_prefix="prescan") as pool:
        for page, score in zip(pages, pool.map(lambda n: _page_score(files[n]), pages)):
            kinds[page] = ("unsure" if score is None else
                           "text" if score >= LOOKS_TEXT else "picture" if score < LOOKS_PICTURE else "unsure")
    return kinds


def _page_score(path: Path) -> float | None:
    try:
        return images.text_score(path)
    except Exception:  # a preview that cannot be made must not stop the check
        core.log.exception("Text check: page not scanned locally")
        return None


def _print_files(folder_raw: str, count: int) -> dict[int, Path]:
    """The print folder's Cover.png (as page 0) and 1..count.png."""
    folder = Path(str(folder_raw or "").strip().strip('"'))
    present = {p.name.lower(): p for p in folder.iterdir() if p.is_file()} if folder.is_dir() else {}
    files = {0: present.get("cover.png")} | {n: present.get(f"{n}.png") for n in range(1, count + 1)}
    if count < 3 or not all(files.values()):
        raise UserError("Файли книги змінилися — перетягніть їх ще раз.")
    return files


def _targets(files: dict[int, Path], count: int, refs: dict, pers: dict):
    """Makes a page to check: with the text it must carry (strict; the first and last page «personal»), or
    with only what is known of it (loose — the buyer's own dedication, a book without texts)."""
    child, gifter = pers["child"], pers["gifter"]
    who = f"The book is from: {gifter}\n" if gifter else ""

    def target(page: int, part: str | None = None, key: str | None = None, own: str | None = None) -> dict:
        t = {"page": page, "part": part, "file": files[page].name, "path": files[page], "label": _label(page, part),
             "count": count, "key": key, "expected": None}
        expected = refs.get(key) if key and not own and child else None
        if expected:
            t.update(mode="personal" if page in (1, count) else "strict", expected=expected,
                     prompt=_strict(child, expected))
        elif own:
            what = "dedication" if page == 1 else "closing message"
            t.update(mode="loose", key=None, own=own, prompt=_loose(
                child, f"The buyer asked for this {what} (the designer may split lines, fix punctuation and merge "
                       f"greetings like \"With love\"):\n{own}\n{who}",
                " Also report words of the buyer's message that are missing or changed."))
        else:
            t.update(mode="loose", key=None, prompt=_loose(child, who if page in (1, count) else ""))
        return t

    return target


def _passes(run: "_Run", target, files: dict, count: int, refs: dict, pers: dict, full: bool, rules: tuple):
    """Both passes. The cover's front, the dedication and the last page are always checked; the cover's back
    and the story pages when the read pass finds text there — in the full check only the pages that are a
    library text: the picture page of a spread may hold lettering the model cannot read and invents.
    A spread goes to the check pass the moment its own two pages are read (owner's wish, 20.09.2026): in a
    book as long as the passport every spread is its own, so nothing else has to be known first. A shorter
    book (24 or 28 pages) misses some spreads and keeps only their order, so its mapping is the best
    order-keeping match of every read at once — there the check pass still waits for the whole read pass."""
    fixed = [target(0, "front", "cover"), target(1, None, "page1", pers["dedication"]),
             target(count, None, "page30", pers["closing"])]
    story = list(range(2, count))
    spreads = [[p for p in (first, first + 1) if p < count] for first in range(2, count, 2)]
    run.total = len(story) + 1 + len(fixed) + len(spreads)
    run.say("Читання сторінок…")  # the model is readied by the first question that needs it (_Run.ready())
    pending = [(t, run.pool.submit(run.judge, t)) for t in fixed]
    back = run.pool.submit(run.read, files[0], "back")
    kinds = page_kinds(files, story)  # local, while the model is busy with the cover and the owner's pages

    by_place = full and len(spreads) == len(library.SPREAD_NUMBERS)
    places = [f"spread{n}" for n in library.SPREAD_NUMBERS] if by_place else []
    ref_words = {k: words(v) for k, v in refs.items()}
    # A page that only looks like a picture is not read at all; where the passport says what a spread must
    # carry and only one of its two pages looks like text, that page skips the read pass and goes straight
    # to the check (the whole read pass then disappears on a 30-page book).
    straight: dict[int, str] = {}
    to_read: list[int] = []
    for i, pair in enumerate(spreads):
        key = places[i] if by_place and places[i] in refs else None
        looks = [p for p in pair if kinds[p] != "picture"]
        if key and len(looks) == 1 and kinds[looks[0]] == "text":
            straight[looks[0]] = key
            continue
        to_read += looks or list(pair)  # a spread that looks empty is still confirmed by the model itself
    reading: dict[int, Future] = {}

    def read(page: int) -> str:
        """This page's first lines, for the pages worth reading ("" for the rest). The queue is kept a few
        pages long on purpose: with the whole book in it, a spread's check would have to wait behind every
        remaining read instead of slipping in next."""
        if page not in to_read:
            return ""
        for n in [p for p in to_read if p >= page][:PARALLEL + 2]:
            if n not in reading:  # setdefault() would ask the model again before looking
                reading[n] = run.pool.submit(run.read, files[n])
        return reading[page].result()

    mapping: dict[int, str] = dict(straight)
    if full and not by_place:
        mapping = assign(count, {n: read(n) for n in to_read if has_text(read(n))}, refs)
    blank, unmatched = [], []
    for i, pair in enumerate(spreads):
        lettered = [p for p in pair if has_text(read(p))]
        key = places[i] if by_place and places[i] in refs else None
        if key and lettered:
            best = max(lettered, key=lambda p: (similarity(words(read(p)), ref_words[key]), len(words(read(p)))))
            mapping[best] = key
        hit = next((p for p in pair if p in mapping), None)
        if hit:
            here = [target(hit, None, mapping[hit])]
            if hit in straight:  # nothing was read of this spread: keep the other page in case it was the one
                here[0] = {**here[0], "straight": next((p for p in pair if p != hit), None)}
        elif not lettered:
            blank.append(pair)
            here = []
        else:
            if full:
                unmatched.append(max(lettered, key=lambda p: len(words(read(p)))))
            here = [target(p) for p in lettered]
        pending += [(t, run.pool.submit(run.judge, t)) for t in here]
    if has_text(back.result()):
        t = target(0, "back")
        pending.append((t, run.pool.submit(run.judge, t)))
    run.total = run.done + sum(1 for _, fut in pending if not fut.done())
    run.unmatched = unmatched  # known before the check pass: another book's pages can be told at once
    answers, found = _collect(run, pending, pers, rules)
    _second_half(run, pending, answers, found, target, pers, rules, mapping)
    return [t for t, _ in pending], answers, {"mapping": mapping, "blank": blank, "unmatched": unmatched}


def _second_half(run: "_Run", pending: list, answers: dict, found: list, target, pers: dict, rules: tuple,
                 mapping: dict) -> None:
    """A page the local look sent straight to the check, on which the model then saw no text at all: the
    text must be on the other half of that spread, so that one is checked instead (rare, and cheap)."""
    again = [i for i, (t, _) in enumerate(pending)
             if t.get("straight") and not answers[i].get("failed") and _saw_nothing(answers[i].get("transcript"))]
    if not again:
        return
    run.say("Друга половина розвороту…")
    spoiled = {(pending[i][0]["page"], pending[i][0].get("part")) for i in again}
    found[:] = [f for f in found if (f["page"], f.get("part")) not in spoiled]
    for i in again:
        old = pending[i][0]
        mapping.pop(old["page"], None)
        other = target(old["straight"], None, old["key"])
        mapping[other["page"]] = old["key"]
        pending[i] = (other, run.pool.submit(run.judge, other))
    run.total += len(again)
    _collect(run, pending, pers, rules, answers, found, only=again)


def _collect(run: "_Run", pending: list, pers: dict, rules: tuple, answers: dict | None = None,
             found: list | None = None, only: list[int] | None = None) -> tuple[dict[int, dict], list[dict]]:
    """The answers as they come back. Each finished page adds its findings to what the card already shows,
    so the first mistakes can be read while the rest of the book is still with the model."""
    answers = {} if answers is None else answers
    found = [] if found is None else found
    wanted = set(range(len(pending)) if only is None else only)
    which = {fut: i for i, (_, fut) in enumerate(pending) if i in wanted}
    for fut in as_completed(which):
        i = which[fut]
        answers[i] = fut.result()
        if not answers[i].get("failed"):
            found += page_issues(pending[i][0], answers[i], pers, *rules)
        count = pending[i][0]["count"]
        strange = _strange(found, run.unmatched, count)
        run.job.share({"issues": _ordered(_one_alarm(found, strange, count) if _wrong_book(strange, count) else found)})
    return answers, found


class _Run:
    """One check's model calls: four at a time, cached, counted for the progress bar, stoppable. A newer check
    of the same book stops this one; other books of the same order carry on. The model leaves the graphics
    card when the last running check ends."""

    def __init__(self, job, receipt_id: str, model: str, pick: int = 0):
        self.job, self.model = job, model
        self.key = run_key(receipt_id, pick)
        self.cancel = threading.Event()
        self.lock = threading.Lock()
        self.done, self.total = 0, 1
        self.unmatched: list[int] = []  # story pages like no passport text, once the read pass knows them
        self.pool: ThreadPoolExecutor | None = None
        self._ready_lock = threading.Lock()
        self._readied: bool | ModelError = False
        self._pictures: dict[tuple, str] = {}  # a page read and then judged is made into a JPEG once

    def __enter__(self) -> "_Run":
        global _active
        with _runs_lock:
            old = _runs.get(self.key)
            if old:
                old[0].set()
            _runs[self.key] = (self.cancel, getattr(self.job, "id", None))
        with _active_lock:
            _active += 1
        self.pool = ThreadPoolExecutor(PARALLEL, thread_name_prefix="textcheck")
        return self

    def __exit__(self, kind, err, tb) -> bool:
        global _active
        if kind:
            self.cancel.set()  # the queued pages give up at once
        self.pool.shutdown(wait=True, cancel_futures=True)
        with _runs_lock:
            if _runs.get(self.key, (None,))[0] is self.cancel:
                del _runs[self.key]
        with _active_lock:
            _active -= 1
            last = _active == 0
        if last:
            ollama._release_model(self.model)
        return False

    def say(self, step: str) -> None:
        self.job.progress(step, 100 * self.done / max(1, self.total))

    def ready(self) -> None:
        """Ollama and the model, readied once — by the first question the cache can't answer, not at the start: a
        re-check of the same files is answered from memory and needs no model at all (it used to load 9 GB into the
        graphics card for nothing, ~4 s, up to ~70 s from disk). A failure stays the whole check's error."""
        with self._ready_lock:
            if self._readied is False:
                try:
                    ollama._ready(self.model, self.say)
                    self._readied = True
                except ModelError as err:
                    self._readied = err
            if isinstance(self._readied, ModelError):
                raise Unavailable(str(self._readied))

    def picture(self, path: Path, part: str | None) -> str:
        key = (str(path), part)
        if key not in self._pictures:
            self._pictures[key] = picture(path, part)
        return self._pictures[key]

    def ask(self, path: Path, part: str | None, prompt: str, schema: dict | None = None,
            max_tokens: int | None = None) -> str:
        if self.cancel.is_set():
            raise UserError("Перевірку перервано.")
        key = _cache_key(path, part, self.model, prompt, max_tokens)
        with _cache_lock:
            answer = _cache.get(key)
        if answer is None:
            self.ready()
            image = self.picture(path, part)
            try:
                answer = ollama._chat(self.model, prompt, image, schema, max_tokens)
            except (Unavailable, TimedOut):  # nothing to gain from a second try: one hung page held a check 10 min
                raise
            except ModelError:
                if self.cancel.is_set():
                    raise UserError("Перевірку перервано.") from None
                answer = ollama._chat(self.model, prompt, image, schema, max_tokens)  # once more
            # A broken answer (cut off, not JSON) is not kept: ↻ asks that page again instead of repeating the failure.
            if schema is None or not {"failed", "salvaged"} & _parse(answer).keys():
                with _cache_lock:
                    if len(_cache) > 3000:
                        _cache.clear()
                    _cache[key] = answer
        with self.lock:
            self.done += 1
            self.say("Звірка тексту…" if schema else "Читання сторінок…")
        return answer

    def read(self, path: Path, part: str | None = None) -> str:
        try:
            return self.ask(path, part, READ_PROMPT, None, READ_TOKENS)
        except Unavailable:
            raise
        except ModelError:
            return ""  # the check pass still reads the page when it turns out to carry text

    def judge(self, target: dict) -> dict:
        try:
            return _parse(self.ask(target["path"], target.get("part"), target["prompt"], SCHEMA, JUDGE_TOKENS))
        except Unavailable:
            raise
        except ModelError as err:
            return {"failed": str(err)}


def cancel(receipt_id: str, job_id: str | None = None) -> bool:
    """Stops running checks of an order: the one of that job when given, otherwise every book of the order
    (the whole card was closed). Pages already with the model finish; the rest are not asked."""
    prefix = f"{receipt_id}#"
    with _runs_lock:
        keys = [k for k in _runs if k.startswith(prefix) and (not job_id or _runs[k][1] == job_id)]
        for key in keys:
            _runs[key][0].set()
        return bool(keys)
