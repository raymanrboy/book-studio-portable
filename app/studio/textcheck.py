"""Text check before print: a local vision model (Gemma in Ollama, on this computer's graphics card)
reads every page of the Canva export, and the program compares what is printed with what must be —
the book's texts from the library with the child's name, the dedication and who the book is from.

Two passes (the scheme that found every planted mistake on the owner's own Canva pages without a false
alarm, 19.09.2026 — wiki/plans/roadmap.md):
  read   the story pages are copied blind, only their first lines — enough to learn which pages carry
         text and which library text each one is (a Printify book lacks three spreads, a 28-page
         Gelato book one);
  check  every text page, the cover and the first and last page again, now with the text they must
         carry: the model copies the page exactly and judges it, the program compares that copy word by
         word. Names and leftover placeholders are always the program's own call.
A book without texts in the library gets the light check: names, placeholders, other orders' children,
cut-off text. The pictures never leave the computer (Ollama answers on 127.0.0.1 only); a journal of
every check is kept in data/logs/checks/.
"""
from __future__ import annotations

import base64
import difflib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import threading
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image

from . import core, creator, images, library, orders, profit
from .jobs import UserError, jobs
from .server import ApiError, Request, route

DEFAULT_MODEL = "gemma4:12b-it-qat"
DEFAULT_URL = "http://127.0.0.1:11434"
PARALLEL = 4             # pages in flight at once — the owner set OLLAMA_NUM_PARALLEL=4
IMAGE_SIDE = 1024        # tested: 768–2000 px read equally well; smaller is faster to send
KEEP_ALIVE = "2m"        # a fallback: the model is let go right after each check (_release_model())
# The same options on every call: another context size would make Ollama load the model again.
OPTIONS = {"temperature": 0, "num_ctx": 8192}
READ_TOKENS = 64         # the read pass needs only the first lines of a page
JUDGE_TOKENS = 1000      # a page's copy and verdict fit easily; a model that runs on is stopped here
CALL_TIMEOUT = 300       # a call may also load the model: ~4 s from memory, ~70 s from disk
PROBE_TIMEOUT = 1.0      # "is Ollama there": on Windows a refused connection takes 2 s to say so
MATCH = 0.45             # how alike a page's first lines and a library text must be to call them one
# What images.text_score() says about a page. Measured on the owner's five real books (20.09.2026):
# a page with text scores 2.4-2.6, a page with only a picture 0.9-1.5. Anything in between is «not sure»
# and goes to the model exactly as before — the heuristic may only save work, never decide alone.
LOOKS_TEXT = 2.2
LOOKS_PICTURE = 1.6
CHECKS = core.data_path("logs", "checks")
KEEP = 400

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

EXPECTED:
{expected}"""

LOOSE_PROMPT = """You check a page of a personalized children's book before it is printed.
{name_line}{context}1. Transcribe all visible text exactly as printed (keep spelling, accents, capitals and braces). Do not correct anything.
2. Report only clear mistakes: the child's name misspelled or missing an accent, a different child's name, a leftover
   placeholder in curly braces, a word cut off at the edge of the page, words stuck together without a space, an
   obvious typo.{extra} Different line breaks, quote or dash styles and small edits by the designer are NOT problems.
3. Verdict: ok or error. Explain every problem in Ukrainian."""

SCHEMA = {"type": "object", "properties": {
    "transcript": {"type": "string"}, "verdict": {"type": "string", "enum": ["ok", "error"]},
    "problems": {"type": "array", "items": {"type": "string"}}}, "required": ["transcript", "verdict", "problems"]}


class ModelError(UserError):
    """Ollama or the model failed; the text says what to do."""


class Unavailable(ModelError):
    """Ollama does not answer at all."""


# ---------------------------------------------------------------- Ollama (this computer only)

_NO_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def _base() -> str:
    url = str(core.settings.section("textcheck").get("url") or DEFAULT_URL).rstrip("/")
    if (urllib.parse.urlsplit(url).hostname or "") not in ("127.0.0.1", "localhost", "::1"):
        raise ModelError("Перевірка тексту працює лише з моделлю на цьому комп'ютері (адреса 127.0.0.1).")
    return url


def _call(path: str, body: dict | None = None, timeout: float = 10) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(_base() + path, data=data, method="POST" if data is not None else "GET",
                                 headers={"Content-Type": "application/json"})
    try:
        with _NO_PROXY.open(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8") or "{}")
    except urllib.error.HTTPError as err:
        try:
            detail = str(json.loads(err.read().decode("utf-8")).get("error") or "")
        except Exception:
            detail = ""
        raise ModelError(f"Ollama відповіла помилкою {err.code}" + (f": {detail}" if detail else "") + ".") from None
    except TimeoutError:
        raise ModelError("Модель не відповіла вчасно.") from None
    except (urllib.error.URLError, ConnectionError, OSError) as err:
        if isinstance(getattr(err, "reason", None), TimeoutError):
            raise ModelError("Модель не відповіла вчасно.") from None
        raise Unavailable("Ollama не запущена.") from None


def _settings() -> dict:
    s = core.settings.section("textcheck")
    return {"enabled": bool(s.get("enabled", True)), "model": str(s.get("model") or DEFAULT_MODEL),
            "prescan": bool(s.get("prescan", True))}


def _same_model(a: str, b: str) -> bool:
    return a == b or a.removesuffix(":latest") == b.removesuffix(":latest")


def _ollama_command() -> list[str] | None:
    """How to start Ollama the way the Start menu does: its tray app next to ollama.exe on PATH."""
    found = shutil.which("ollama")
    folders = [Path(found).parent] if found else []
    if os.environ.get("LOCALAPPDATA"):
        folders.append(Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Ollama")
    for folder in folders:
        if (folder / "ollama app.exe").is_file():
            return [str(folder / "ollama app.exe")]
    return [found, "serve"] if found else None


def _alive() -> bool:
    try:
        _call("/api/version", timeout=PROBE_TIMEOUT)
        return True
    except ModelError:
        return False


def start_ollama(wait: float = 40) -> bool:
    """Starts Ollama when it is not running (it stays running after Book Studio closes, like from the
    Start menu). False when it is not installed or did not answer in time."""
    if _alive():
        return True
    command = _ollama_command()
    if not command:
        return False
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    try:
        subprocess.Popen(command, cwd=str(Path(command[0]).parent), creationflags=flags, close_fds=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        core.log.exception("Ollama did not start")
        return False
    core.log.info("Ollama started: %s", command[0])
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        if _alive():
            return True
        time.sleep(0.5)
    return False


def status() -> dict:
    """For Settings and the order card: is the check on, does Ollama answer, is the model there."""
    out = {**_settings(), "running": False, "version": None, "models": [], "installed": False, "loaded": False,
           "canStart": bool(_ollama_command())}
    try:
        out["version"] = _call("/api/version", timeout=PROBE_TIMEOUT).get("version")
        out["running"] = True
        tags = _call("/api/tags", timeout=5).get("models") or []
        out["models"] = [m.get("name") for m in tags if "vision" in (m.get("capabilities") or ["vision"])]
        out["installed"] = any(_same_model(n, out["model"]) for n in out["models"])
        out["loaded"] = any(_same_model(m.get("name") or "", out["model"])
                            for m in _call("/api/ps", timeout=5).get("models") or [])
    except ModelError:
        pass
    return out


def _ready(model: str, say) -> None:
    """Ollama running (started when needed), the model installed and loaded into the graphics card."""
    if not _alive():
        say("Запуск Ollama…")
        if not start_ollama():
            raise Unavailable("Ollama не запущена і не запустилась сама — запустіть її з меню «Пуск».")
    names = [m.get("name") or "" for m in _call("/api/tags", timeout=5).get("models") or []]
    if not any(_same_model(n, model) for n in names):
        raise ModelError(f"В Ollama немає моделі {model} — встановіть її або оберіть іншу в Налаштуваннях.")
    if not any(_same_model(m.get("name") or "", model) for m in _call("/api/ps", timeout=5).get("models") or []):
        say("Модель завантажується у відеокарту…")
        _call("/api/chat", {"model": model, "messages": [], "keep_alive": KEEP_ALIVE, "options": OPTIONS},
              timeout=CALL_TIMEOUT)


_warm_lock = threading.Lock()
_warmed_at = 0.0
WARM_AGAIN = 30  # seconds: one warm-up per folder is enough, however many files are dropped


def warm() -> bool:
    """Asks for the model while the card is still copying and checking the files, so the check that starts
    right after them does not wait for it (~4 s from this computer's memory, ~70 s from disk). Quiet: a
    model that cannot be had is the check's own thing to report, and the card hears it there."""
    global _warmed_at
    if not _settings()["enabled"]:
        return False
    with _warm_lock:
        if _active or time.monotonic() - _warmed_at < WARM_AGAIN:
            return False  # a check is already holding the model, or one folder asked twice
        _warmed_at = time.monotonic()
    model = _settings()["model"]

    def load() -> None:
        try:
            _ready(model, lambda step: None)
        except ModelError as err:
            core.log.info("Text check: the model was not warmed up (%s)", err)

    threading.Thread(target=load, name="textcheck-warm", daemon=True).start()
    return True


def _chat(model: str, prompt: str, picture: str, schema: dict | None = None, max_tokens: int | None = None) -> str:
    options = {**OPTIONS, **({"num_predict": max_tokens} if max_tokens else {})}
    body = {"model": model, "stream": False, "think": False, "keep_alive": KEEP_ALIVE, "options": options,
            "messages": [{"role": "user", "content": prompt, "images": [picture]}]}
    if schema:
        body["format"] = schema
    return str((_call("/api/chat", body, timeout=CALL_TIMEOUT).get("message") or {}).get("content") or "")


# ---------------------------------------------------------------- pictures

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


# ---------------------------------------------------------------- words

_QUOTES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "`": "'", "´": "'", "“": '"', "”": '"', "„": '"',
                         "«": '"', "»": '"'})
_DASHES = re.compile("[‐-―−]")
_TOKEN = re.compile(r"[\w{}\[\]'\-]+")


def words(text: str) -> list[str]:
    """Printed words without punctuation; quotes, apostrophes and dashes of every style made alike.
    Capitals and accents stay: «Zoe» is not «Zoë»."""
    text = _DASHES.sub("-", unicodedata.normalize("NFC", text or "").translate(_QUOTES))
    return [w for w in (t.strip("-'") for t in _TOKEN.findall(text)) if w]


def _caps(word: str) -> bool:
    return len(word) > 1 and word.isupper()  # set in capitals by the design: FLOWER GIRL OLIVIA


def _same(a: str, b: str) -> bool:
    return a == b or ((_caps(a) or _caps(b)) and a.casefold() == b.casefold())


def diff(expected: str, printed: str) -> list[dict]:
    """Where the printed words differ from the expected ones: [{expected, printed}], either side may be ''."""
    a, b = words(expected), words(printed)
    ops = []
    matcher = difflib.SequenceMatcher(a=[w.casefold() for w in a], b=[w.casefold() for w in b], autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            ops += [{"expected": x, "printed": y} for x, y in zip(a[i1:i2], b[j1:j2]) if not _same(x, y)]
        else:
            ops.append({"expected": " ".join(a[i1:i2]), "printed": " ".join(b[j1:j2])})
    return ops


def similarity(read: list[str], reference: list[str]) -> float:
    """How alike a page's first lines are to the start of a library text (0…1)."""
    if len(read) < 3 or not reference:
        return 0.0
    a = [w.casefold() for w in reference[:len(read) + 4]]
    return difflib.SequenceMatcher(a=a, b=[w.casefold() for w in read], autojunk=False).ratio()


def _plain(word: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", word.casefold()) if not unicodedata.combining(c))


def _distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _base_word(word: str) -> str:
    return re.sub(r"'s$", "", word, flags=re.I) if len(word) > 3 else word


# Everyday words that look like names to a spelling rule (Ann ~ And, Mila ~ Mile): never a child's name typo.
COMMON = set("""a about after again all always an and any are around as at away back be because bed been before
began being best big bless blessed blue book both bright but by came can close come could day days dear did do
does dream dreams each even ever every eyes far feel filled find first fly for forever friend friends from full
gave gentle get give glad go god good grace great grew grow had hand hands happy has have he heart hearts her here
high him his hold home hope how i if in into is it its joy just keep kind know laugh let life light like little
live long look love loved made make many may me mile miles more morning most much my name need never new night no
not now of off on once one only or our out over own peace play please rest ride right said saw say see she shine
shining side sky sleep smile so some soft soon star stars stay still such sun sweet take tell than that the their
them then there these they thing things this those through time to today together told too took tree true two up
upon us very want was way we well went were what when where which while who whole why will wish with world would
year years yes yet you young your yours""".split())


# ---------------------------------------------------------------- what the buyer asked for

_DEDICATION = re.compile(r"dedicat|closing|присвят", re.I)
_GIFTER = re.compile(r"\bfrom\b|від кого|gift", re.I)
_META = {"dedication", "closing", "message", "messages", "and", "default", "defaults", "please", "use", "the",
         "standard", "both", "is", "fine", "ok", "okay", "keep", "as", "one"}
_CLOSING = re.compile(r"\bclosing(?:\s+message)?\s*:", re.I)
_DEDICATION_HEAD = re.compile(r"^\s*dedication(?:\s+message)?\s*:\s*", re.I)
_NAME_SLOT = re.compile(r"\{\s*name\s*\}", re.I)
_GIFTER_SLOT = re.compile(r"\{\s*gifter\s*\}", re.I)
# «With Love, Aunt Kate & Uncle Tom»: the buyer's own greeting — the template's «With love,» line then goes.
_GREETING = re.compile(r"^\s*(?:with\s+(?:(?:all\s+)?(?:of\s+)?(?:my|our)\s+)?love|(?:lots\s+of\s+|much\s+|all\s+"
                       r"(?:my|our)\s+)?love|from|xoxo|hugs)\b", re.I)
_TEMPLATE_GREETING = re.compile(r"(?im)^[^\n{]{1,30},[ \t]*\n(?=[ \t]*\{\s*gifter\s*\})")


def is_default(value: str) -> bool:
    """«DEFAULT», "“DEFAULT “", «Dedication and Closing   Default» — the book's own text is wanted."""
    ws = [w.casefold() for w in words(value)]
    return not ws or (("default" in ws or "defaults" in ws) and all(w in _META for w in ws))


def personalization(item: dict) -> dict:
    """The child's name, who the book is from, and the buyer's own dedication / closing when there is one."""
    child = (item.get("childName") or creator.guess_child_name([item]) or "").strip()
    child = child.strip("\"'“”‘’«» ").rstrip(".,;:!").strip()  # «Leo & Mila.» — the full stop is not printed
    gifter, raw = "", ""
    for v in item.get("variations") or []:
        name, value = str(v.get("name") or ""), str(v.get("value") or "").strip()
        if _DEDICATION.search(name):
            raw = value
        elif _GIFTER.search(name) and not gifter:
            gifter = value
    # «"With love ,Anna and Mark"» → «With love, Anna and Mark»: the owner does not print the buyer's slips
    gifter = re.sub(r"\s+([,.!])", r"\1", gifter.strip().strip("\"'“”‘’«»").strip())
    gifter = re.sub(r",(?=[^\s\d])", ", ", gifter)
    dedication = closing = None
    if not is_default(raw):
        parts = _CLOSING.split(raw, maxsplit=1)
        dedication = _DEDICATION_HEAD.sub("", parts[0]).strip() or None
        if dedication and is_default(dedication):
            dedication = None
        if len(parts) > 1 and "default" not in {w.casefold() for w in words(parts[1])}:
            closing = parts[1].strip() or None
    return {"child": child, "gifter": gifter, "dedication": dedication, "closing": closing}


def fill(template: str, child: str, gifter: str) -> str | None:
    """A library text as it must be printed for this order; None when a placeholder cannot be filled."""
    text = template or ""
    if gifter and _GREETING.match(gifter.lstrip(" \"'“”‘’«»")):
        text = _TEMPLATE_GREETING.sub("", text)
    if (_NAME_SLOT.search(text) and not child) or (_GIFTER_SLOT.search(text) and not gifter):
        return None
    text = _GIFTER_SLOT.sub(lambda m: gifter, _NAME_SLOT.sub(lambda m: child, text))
    return None if "{" in text else text


# ---------------------------------------------------------------- which page is which text

def assign(count: int, reads: dict[int, str], refs: dict[str, str]) -> dict[int, str]:
    """Story page -> library text ("spread5"). A full book (30 pages) has every spread where the library
    has it — then a page that differs is still that spread's page, even when its text is another one. A
    shorter book lacks some spreads but keeps the order, so the best order-keeping match of first lines to
    texts wins (only matches above MATCH count)."""
    spreads = [[p for p in (first, first + 1) if p < count] for first in range(2, count, 2)]
    keys = [f"spread{n}" for n in library.SPREAD_NUMBERS if refs.get(f"spread{n}")]
    ref_words = {k: words(refs[k]) for k in keys}
    read_words = {p: words(reads.get(p, "")) for sp in spreads for p in sp}
    if len(spreads) == len(library.SPREAD_NUMBERS):
        out = {}
        for pair, n in zip(spreads, library.SPREAD_NUMBERS):
            key = f"spread{n}"
            lettered = [p for p in pair if read_words[p]]
            if key in ref_words and lettered:
                out[max(lettered, key=lambda p: (similarity(read_words[p], ref_words[key]), len(read_words[p])))] = key
        return out

    def score(i: int, j: int) -> tuple[float, int]:
        best = max(((similarity(read_words[p], ref_words[keys[j]]), p) for p in spreads[i]), default=(0.0, 0))
        return best if best[0] >= MATCH else (0.0, 0)

    scores = [[score(i, j) for j in range(len(keys))] for i in range(len(spreads))]
    total = [[0.0] * (len(keys) + 1) for _ in range(len(spreads) + 1)]
    for i in range(1, len(spreads) + 1):
        for j in range(1, len(keys) + 1):
            s = scores[i - 1][j - 1][0]
            total[i][j] = max(total[i - 1][j], total[i][j - 1], total[i - 1][j - 1] + s if s else 0.0)
    out: dict[int, str] = {}
    i, j = len(spreads), len(keys)
    while i and j:
        s, page = scores[i - 1][j - 1]
        if s and total[i][j] == total[i - 1][j - 1] + s:
            out[page] = keys[j - 1]
            i, j = i - 1, j - 1
        elif total[i][j] == total[i - 1][j]:
            i -= 1
        else:
            j -= 1
    return out


# ---------------------------------------------------------------- the program's own rules

def findings(printed: list[str], child: str, vocab: set[str], others: set[str]) -> list[dict]:
    """Placeholders left, the child's name spelled wrong or stuck to the next word, another order's child."""
    tokens = [t for t in words(child) if len(t) >= 2]
    folded = {t.casefold() for t in tokens}
    out, seen = [], set()
    for word in printed:
        if word in seen:
            continue
        base = _base_word(word)
        low = base.casefold()
        found = None
        if "{" in word or "}" in word or (word.startswith("[") and word.endswith("]")):
            found = {"kind": "placeholder"}
        elif any(_same(base, t) for t in tokens):
            continue
        else:
            for t in tokens:
                tl = t.casefold()
                if low == tl and low not in vocab:  # «olivia» — but «grace» in a story is just a word
                    found = {"kind": "case", "name": t}
                elif (len(t) >= 3 and len(base) >= 3 and base[0].isupper() and low not in vocab
                      and _plain(base)[:1] == _plain(t)[:1] and _distance(low, tl) <= (1 if len(t) <= 4 else 2)):
                    found = {"kind": "name", "name": t}
                elif (len(t) >= 4 and len(low) - len(tl) >= 3 and low not in vocab
                      and (low.startswith(tl) or low.endswith(tl))):
                    found = {"kind": "stuck", "name": t}
                if found:
                    break
            if not found and low in others and low not in folded and low not in vocab and base[:1].isupper():
                found = {"kind": "foreign"}
        if found:
            seen.add(word)
            out.append({**found, "printed": word})
    return out


# ---------------------------------------------------------------- one order

_cache: dict[str, str] = {}
_cache_lock = threading.Lock()
_runs: dict[str, tuple[threading.Event, str | None]] = {}  # order -> (stop, job id) of its running check
_runs_lock = threading.Lock()
_active = 0  # checks running now
_active_lock = threading.Lock()


def _cache_key(path: Path, part: str | None, model: str, prompt: str, max_tokens: int | None) -> str:
    stat = path.stat()
    raw = f"{path.resolve()}|{stat.st_mtime_ns}|{stat.st_size}|{part}|{model}|{max_tokens}|{prompt}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _label(page: int, part: str | None = None) -> str:
    if page == 0:
        return "Обкладинка, зворот" if part == "back" else "Обкладинка"
    return f"Стор. {page}"


def _issue(target: dict, level: str, text: str, note: str = "", kind: str = "page") -> dict:
    """kind: rule (the program's name/placeholder rules), diff (the page differs from the library text),
    model (only the model saw it), unmatched, buyer (the buyer's words), page (no text, unreadable)."""
    ident = hashlib.sha1(f"{target['file']}|{target.get('part')}|{text}".encode("utf-8")).hexdigest()[:12]
    return {"id": ident, "page": target["page"], "file": target["file"], "part": target.get("part"),
            "label": target["label"], "level": level, "text": text, "note": note, "kind": kind}


def _vocabulary(pers: dict) -> set[str]:
    """Words that are not a misspelt name: every library text, everyday words, what the buyer wrote."""
    vocab = set(COMMON)
    for book in library.all_books():
        for text in (book.get("text") or {}).values():
            vocab.update(w.casefold() for w in words(_NAME_SLOT.sub(" ", text or "")))
    for value in (pers["gifter"], pers["dedication"] or "", pers["closing"] or ""):
        vocab.update(w.casefold() for w in words(value))
    return vocab


def _other_children(receipt_id: str) -> set[str]:
    """First names of the children in other orders — a page with one of them was copied from an old design."""
    names: set[str] = set()
    for o in profit.picker_orders():
        if str(o.get("receiptId")) == str(receipt_id):
            continue
        for item in o.get("items") or []:
            names.update(t.casefold() for t in words(creator.guess_child_name([item])) if len(t) >= 3)
    return names


def _short(text: str, most: int = 7) -> str:
    parts = text.split()
    return " ".join(parts[:most]) + " …" if len(parts) > most else text


def _say_op(op: dict, others: set[str]) -> str:
    was, need = _short(op["printed"]), _short(op["expected"])
    if was and need:
        if _base_word(was).casefold() in others:
            return f"Чуже ім'я «{was}» замість «{need}»"
        return f"«{was}» замість «{need}»"
    return f"Пропущено «{need}»" if need else f"Зайве «{was}»"


FINDING_TEXT = {
    "placeholder": "Залишився шаблон «{printed}»",
    "case": "«{printed}» замість «{name}» — великі й малі літери",
    "name": "«{printed}» замість «{name}»",
    "stuck": "Злиплі слова «{printed}»",
    "foreign": "Чуже ім'я «{printed}» — з іншого замовлення",
}


def page_issues(target: dict, answer: dict, pers: dict, vocab: set[str], others: set[str]) -> list[dict]:
    """What is wrong on one page: the program's rules, the word-by-word comparison, the model's verdict.
    Red — certain; amber — worth a look (the model saw something the comparison did not, or the other way)."""
    text, verdict = answer.get("transcript") or "", answer.get("verdict")
    problems = [str(p).strip() for p in answer.get("problems") or [] if str(p).strip()]
    expected, mode = target.get("expected"), target["mode"]
    printed = words(text)
    page_vocab = vocab | {w.casefold() for w in words(expected or "")}
    out, covered = [], set()
    for f in findings(printed, pers["child"], page_vocab, others):
        sure = f["kind"] in ("placeholder", "case", "name") or expected is not None
        out.append(_issue(target, "error" if sure else "warn", FINDING_TEXT[f["kind"]].format(**f), kind="rule"))
        covered.add(f["printed"])
    if expected is not None:
        ops = [op for op in diff(expected, text) if not set(op["printed"].split()) & covered]
        names = {t.casefold() for t in words(pers["child"])}
        changed = sum(len(op["expected"].split()) + len(op["printed"].split()) for op in ops)
        heavy = len(ops) > 6 or changed > 16  # another text altogether: one line, not a word-by-word list
        if heavy:
            level = "error" if verdict == "error" and mode == "strict" else "warn"
            out.append(_issue(target, level, "Текст сторінки інший, ніж у паспорті книги", kind="diff"))
        for op in ops if not heavy else []:
            if mode == "strict":
                level = "error" if verdict == "error" else "warn"
            else:  # the first and last page: the owner may shape them; a lost name is still certain
                level = "error" if {w.casefold() for w in words(op["expected"])} & names else "warn"
            out.append(_issue(target, level, _say_op(op, others), kind="diff"))
    elif target["page"] in (1, target["count"]) and not printed:
        out.append(_issue(target, "warn", "На сторінці немає тексту"))
    if verdict == "error" and problems:
        if out:
            out[0]["note"] = " ".join(problems[:3])
        else:  # the model saw what the words alone do not show — a word cut off at the edge, say
            out += [_issue(target, "warn", p, kind="model") for p in problems[:3] if not _only_punctuation(p)]
    return out


_PUNCTUATION = re.compile(r"лапк|ком[аиуою]\b|крапк|пробіл|розділов|пунктуац|апостроф|тире|дефіс|перенес|"
                          r"нов(?:ий|ому) рядк|двокрапк|знак оклику|велик\S* літер|мал\S* літер|регістр|"
                          r"quote|comma|punctuation|capital|uppercase|lowercase", re.I)
_SUBSTANCE = re.compile(r"обріз|обірв|зрізан|за кра|злит|злип|між|разом|ім'я|імені|шаблон|плейсхолдер|\{|"
                        r"пропущ|відсутн\S* слов|зайв\S* слов|cut|missing word", re.I)


def _only_punctuation(problem: str) -> bool:
    """«Відсутні лапки», «пробіл після коми», «FIRST великими літерами»: the words compare equal, so this is
    the page's punctuation or lettering — the owner's to shape (a name in small letters the program catches
    itself). A cut-off or stuck word is never just punctuation."""
    return bool(_PUNCTUATION.search(problem)) and not _SUBSTANCE.search(problem)


def book_issues(targets: list[dict], answers: dict[int, dict], pers: dict, count: int) -> list[dict]:
    """The buyer's own words must reach the book: who it is from, their dedication and closing."""
    edge = [i for i, t in enumerate(targets) if t["page"] in (1, count) and t.get("part") is None]
    if not edge:
        return []
    printed = [w for i in edge for w in words((answers.get(i) or {}).get("transcript") or "")]
    seen = {_base_word(w).casefold() for w in printed}
    out = []

    def missing(value: str) -> list[str]:
        lost, told = [], set()
        for w in words(value):
            low = _base_word(w).casefold()
            if len(low) < 3 or low in _META or low in COMMON or low in seen or low in told:
                continue
            if len(low) >= 5 and any(abs(len(s) - len(low)) <= 1 and _distance(s, low) <= 1 for s in seen):
                continue  # a buyer's typo the owner fixed
            lost.append(w)
            told.add(low)
        return lost

    first = targets[edge[0]]
    lost = missing(pers["gifter"]) if first["mode"] == "loose" else []  # else the comparison already tells
    if lost:
        out.append(_issue(first, "warn", f"«Від кого» з Etsy: не знайдено «{' '.join(lost[:5])}»", kind="buyer"))
    lost = missing(" ".join(v for v in (pers["dedication"], pers["closing"]) if v))
    if lost:
        more = f" і ще {len(lost) - 5}" if len(lost) > 5 else ""
        out.append(_issue(first, "warn", f"Присвята покупця: не знайдено «{' '.join(lost[:5])}»{more}", kind="buyer"))
    return out


def _loose(child: str, context: str = "", extra: str = "") -> str:
    name_line = f'The child\'s name is "{child}".\n' if child else ""
    return LOOSE_PROMPT.format(name_line=name_line, context=context, extra=extra)


def _strict(child: str, expected: str) -> str:
    name_line = f'The child\'s name is "{child}". ' if child else ""
    return STRICT_PROMPT.format(name_line=name_line, expected=expected)


def _parse(content: str) -> dict:
    """The check pass's answer; a cut-off or broken one (the model ran on and on) is a failure."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return {"failed": "модель не змогла прочитати сторінку"}
    if not isinstance(data, dict):
        return {"failed": "модель не змогла прочитати сторінку"}
    data["transcript"] = re.sub(r"\n{3,}", "\n\n", str(data.get("transcript") or "")).strip()
    return data


def check_order(job, receipt_id: str, folder_raw: str, count: int, pick: int = 0) -> dict:
    """The whole check of one order's print folder (Cover.png + 1..count.png), for its book number `pick`."""
    order = next((o for o in profit.picker_orders() if str(o["receiptId"]) == str(receipt_id)), None)
    if not order:
        raise UserError("Замовлення не знайдено.")
    orders.enrich(order, orders.books_by_listing())
    items = order.get("items") or [{}]
    return check_book(job, str(receipt_id), items[pick] if 0 <= pick < len(items) else items[0], folder_raw, count)


def check_book(job, receipt_id: str, item: dict, folder_raw: str, count: int) -> dict:
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
    with _Run(job, receipt_id, _settings()["model"]) as run:
        targets, answers, layout = _passes(run, target, files, count, refs, pers, full, rules)
        run.say("Підсумок…")
    issues = _all_issues(targets, answers, layout, files, pers, count, rules)
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
    _journal(receipt_id, result, pers)
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
            t.update(mode="loose", key=None, prompt=_loose(
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
    run.say("Підготовка…")
    _ready(run.model, lambda step: run.job.progress(step, 1))
    run.say("Читання сторінок…")
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
    reading: dict[int, "Future"] = {}

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
        run.job.share({"issues": _ordered(found)})
    return answers, found


def _ordered(issues: list[dict]) -> list[dict]:
    """Findings in reading order, the certain ones before the ones only worth a look."""
    rank = {"error": 0, "warn": 1}
    return sorted(issues, key=lambda x: (x["page"] if x["page"] else -1, rank.get(x["level"], 2)))


def _all_issues(targets: list, answers: dict, layout: dict, files: dict, pers: dict, count: int,
                rules: tuple) -> list[dict]:
    issues: list[dict] = []
    for i, t in enumerate(targets):
        a = answers[i]
        if a.get("failed"):
            issues.append(_issue(t, "warn", f"Сторінку не вдалося перевірити — перегляньте її самі ({a['failed']})"))
        else:
            issues += page_issues(t, a, pers, *rules)
    issues += book_issues(targets, answers, pers, count)
    for pair in layout["blank"]:  # every story spread carries text on one of its pages
        issues.append(_issue({"page": pair[0], "file": files[pair[0]].name,
                              "label": f"Стор. {'–'.join(map(str, pair))}"}, "warn", "На розвороті немає тексту"))
    for page in layout["unmatched"]:
        issues.append(_issue({"page": page, "file": files[page].name, "label": _label(page)},
                             "warn", "Текст не схожий на жоден текст паспорта книги", kind="unmatched"))
    return _ordered(issues)


def _learnable(targets: list, issues: list) -> dict[int, str]:
    """Pages whose only fault is a difference from the library text can teach the passport (the owner decides):
    the library was written apart from the Canva template, and a template that differs would be red every time."""
    kinds: dict[tuple, set] = {}
    for i in issues:
        kinds.setdefault((i["page"], i.get("part")), set()).add(i["kind"])
    out = {}
    for i, t in enumerate(targets):
        k = kinds.get((t["page"], t.get("part")), set())
        if t["mode"] == "strict" and t.get("key") and "diff" in k and "rule" not in k:
            out[i] = t["key"]
    return out


class _Run:
    """One check's model calls: four at a time, cached, counted for the progress bar, stoppable. A newer check
    of the same order stops this one; the model leaves the graphics card when the last running check ends."""

    def __init__(self, job, receipt_id: str, model: str):
        self.job, self.receipt_id, self.model = job, receipt_id, model
        self.cancel = threading.Event()
        self.lock = threading.Lock()
        self.done, self.total = 0, 1
        self.pool: ThreadPoolExecutor | None = None

    def __enter__(self) -> "_Run":
        global _active
        with _runs_lock:
            old = _runs.get(self.receipt_id)
            if old:
                old[0].set()
            _runs[self.receipt_id] = (self.cancel, getattr(self.job, "id", None))
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
            if _runs.get(self.receipt_id, (None,))[0] is self.cancel:
                del _runs[self.receipt_id]
        with _active_lock:
            _active -= 1
            last = _active == 0
        if last:
            _release_model(self.model)
        return False

    def say(self, step: str) -> None:
        self.job.progress(step, 100 * self.done / max(1, self.total))

    def ask(self, path: Path, part: str | None, prompt: str, schema: dict | None = None,
            max_tokens: int | None = None) -> str:
        if self.cancel.is_set():
            raise UserError("Перевірку перервано.")
        key = _cache_key(path, part, self.model, prompt, max_tokens)
        with _cache_lock:
            answer = _cache.get(key)
        if answer is None:
            image = picture(path, part)
            try:
                answer = _chat(self.model, prompt, image, schema, max_tokens)
            except Unavailable:
                raise
            except ModelError:
                if self.cancel.is_set():
                    raise UserError("Перевірку перервано.") from None
                answer = _chat(self.model, prompt, image, schema, max_tokens)  # once more
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
    """Stops the running check of an order (only the one of that job, when given): the card was closed or
    got other files. Pages already with the model finish; the rest are not asked."""
    with _runs_lock:
        run = _runs.get(str(receipt_id))
        if not run or (job_id and run[1] != job_id):
            return False
        run[0].set()
        return True


def _release_model(model: str) -> None:
    """Frees the graphics card right after the check (19.09.2026: the model held 9 GB of 12 for five more minutes
    and the Book Studio window, drawn by the same card, lost smoothness). Loading it again takes ~4 s."""
    try:
        _call("/api/generate", {"model": model, "keep_alive": 0}, timeout=10)
    except ModelError:
        pass  # KEEP_ALIVE lets it go a little later anyway


_REFUSAL = re.compile(r"^\W*(?:i'?m sorry|i am sorry|sorry|i cannot|i can'?t|i'?m unable|i am unable|unable to|"
                      r"there is no|there'?s no|no (?:visible |legible |readable )?text|the (?:image|page) "
                      r"(?:does not|doesn'?t|contains no|has no))", re.I)


def _saw_nothing(read: str | None) -> bool:
    """The model found no writing at all on this page (not merely a short line)."""
    text = (read or "").strip()
    return not text or bool(_REFUSAL.match(text))


def has_text(read: str | None) -> bool:
    """A page with lettering worth checking: a few words, not the model's apology for illegible decoration."""
    return len(words(read or "")) >= 4 and not _REFUSAL.match(read or "")


def _journal(receipt_id: str, result: dict, pers: dict) -> None:
    """Every check, with what the model read — to see later why something was (not) flagged. Local only."""
    try:
        CHECKS.mkdir(parents=True, exist_ok=True)
        path = CHECKS / f"{time.strftime('%Y-%m-%d_%H%M%S')}_{receipt_id}.json"
        core.write_json(path, {"receiptId": receipt_id, "at": core.now_iso(), "personalization": pers, **result},
                        backup=False)
        for old in sorted(CHECKS.glob("*.json"))[:-KEEP]:
            old.unlink(missing_ok=True)
    except Exception:
        core.log.exception("Text check journal not written")


# ---------------------------------------------------------------- routes

@route("GET", "/api/textcheck/status")
def _status(req: Request):
    return status()


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
    return status()


@route("POST", "/api/textcheck/start")
def _start(req: Request):
    if not start_ollama():
        raise ApiError("Ollama не запустилась — запустіть її з меню «Пуск»." if _ollama_command()
                       else "Ollama не встановлена на цьому комп'ютері.")
    return status()


def as_template(text: str, child: str) -> str:
    """A printed page as a library text: the child's name becomes {Name} again (in any capitals)."""
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    return re.sub(re.escape(child), "{Name}", text, flags=re.I) if child else text


@route("POST", "/api/textcheck/passport")
def _passport(req: Request):
    """«Так у шаблоні Canva»: the book's texts for these pages become what was printed (owner's click only)."""
    body = req.json or {}
    allowed = {"cover"} | {f"spread{n}" for n in library.SPREAD_NUMBERS}
    child = str(body.get("child") or "").strip()
    pages = body.get("pages") or []
    if not child or not isinstance(pages, list) or not pages:
        raise ApiError("Немає що оновлювати.")
    texts = {}
    for page in pages:
        key, text = str((page or {}).get("key") or ""), str((page or {}).get("text") or "").strip()
        if key not in allowed or not text or len(text) > 4000:
            raise ApiError("Некоректний текст сторінки.")
        texts[key] = as_template(text, child)
    book = library.update_texts(str(body.get("bookId") or ""), texts)
    core.log.info("Passport texts of %s updated from a print: %s", book["id"], ", ".join(texts))
    return {"updated": sorted(texts)}


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
