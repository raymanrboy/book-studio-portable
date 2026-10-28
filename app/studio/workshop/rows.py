"""A book's 17 rows — page 1, spreads 2–3 … 28–29, page 30 and, last, the cover — each with its prompt and its text,
read straight from the agents' files, and the book check behind the strip's «Промпти · GO».

    book-text.md              ## Cover (title), ## Spread 01 (dedication), ## Spread 02..15, ## Afterword
    endpage-prompts-json.md   2 square prompts: [0] Dedication → page 1, [1] Afterword → page 30
    spread-prompts-json.md    14 panorama prompts, in order → spreads 2..15
    cover-prompts-json.md     the final wide image (Agent 6) → the cover; the first prompt is taken

The cover comes in two stages: the picture from Agent 6's prompt, then its margins outpainted to the printer's
template (the owner, 2026-09-26) — cover_state(), outpaint_prompt(), TEMPLATE.
"""
from __future__ import annotations

import json
import math
import os
import re
import threading
from pathlib import Path

from .. import library
from ..server import ApiError
from . import books, check

SPREADS = library.SPREAD_NUMBERS
# The spreads the owner's flipper mirrors — those whose left page divides by 4: 4–5, 8–9 … 28–29.
MIRRORED = frozenset(n for n in SPREADS if library.spread_pages(n)[0] % 4 == 0)
PROMPT_FILES = ("spread-prompts-json.md", "endpage-prompts-json.md", "cover-prompts-json.md", "abc-prompts-json.md")

# The printer's template for the 8×8 hardcover's cover (the owner's, 2026-09-26; Printify SKU 11688-12031), in
# inches: the whole file with what wraps round the boards, the finished size (back 8 + spine 0.40 + front 8), the
# safety zones (inset 0.125″ from the outer edges and ~0.31″ from the spine). The cover's picture is laid on the
# finished size by its width; the rest is margin for the generator to fill.
TEMPLATE = {"full": (17.90, 9.50), "trim": (16.40, 8.00), "spine": 0.40, "safe_outer": 0.125,
            "safe_spine": 0.3113, "px": (5370, 2850), "dpi": 300}


def template_layout(w: int, h: int) -> dict:
    """Where a w×h cover picture goes on the template, in pixels of the canvas the generator gets: its width is the
    finished width (so every visible pixel is the picture's own), unless it's too tall for the whole template."""
    fw, fh = TEMPLATE["full"]
    tw, _ = TEMPLATE["trim"]
    s = max(w / tw, h / fh)                                    # pixels per inch
    cw, ch = round(fw * s), round(fh * s)
    return {"canvas": [cw, ch], "art": [(cw - w) // 2, (ch - h) // 2, w, h], "ppi": round(s, 2)}


def template_guides() -> dict:
    """The template's lines as fractions of the whole file — the page draws them over the cover."""
    fw, fh = TEMPLATE["full"]
    tw, th = TEMPLATE["trim"]
    left, top = (fw - tw) / 2, (fh - th) / 2
    half = (tw - TEMPLATE["spine"]) / 2
    so, ss = TEMPLATE["safe_outer"], TEMPLATE["safe_spine"]

    def box(x, y, w, h):
        return [round(x / fw, 5), round(y / fh, 5), round(w / fw, 5), round(h / fh, 5)]
    return {"trim": box(left, top, tw, th), "spine": box(left + half, top, TEMPLATE["spine"], th),
            "back": box(left + so, top + so, half - so - ss, th - 2 * so),
            "front": box(left + half + TEMPLATE["spine"] + ss, top + so, half - so - ss, th - 2 * so)}


# Gelato's 8×8 hardcover template, in mm, measured from its PDF (2026-10-24): the whole file 458×246 with a 20 mm wrap
# all round; the spine 226–232; each side with its hinge a 206 mm square (back 20–226, front 232–438, top 20–226).
# The photo mockups use it; and the covers made of two squares (2026-10-25…27, «Два квадрати», taken out) are on it.
SQUARES = {"mm": (458, 246), "wrap": 20, "spine": (226, 232), "hinge": (218, 240), "back": (20, 20, 206),
           "front": (232, 20, 206), "dpi": 300}
# Agent 6's two square prompts of those days (no longer used: the cover row ignores them).
OLD_SQUARE_IDS = ("title-square", "quiet-square")


def squares_guides() -> dict:
    """Gelato's lines as fractions of the spread — the page draws them over a cover made of the two squares: what folds
    round the boards, the hinges, the spine, the two squares."""
    w, h = SQUARES["mm"]
    wrap = SQUARES["wrap"]

    def box(x, y, bw, bh):
        return [round(x / w, 5), round(y / h, 5), round(bw / w, 5), round(bh / h, 5)]
    (sl, sr), (hl, hr) = SQUARES["spine"], SQUARES["hinge"]
    return {"trim": box(wrap, wrap, w - 2 * wrap, h - 2 * wrap), "spine": box(sl, wrap, sr - sl, h - 2 * wrap),
            "hinges": [box(hl, wrap, 0, h - 2 * wrap), box(hr, wrap, 0, h - 2 * wrap)],
            "back": box(*SQUARES["back"][:2], SQUARES["back"][2], SQUARES["back"][2]),
            "front": box(*SQUARES["front"][:2], SQUARES["front"][2], SQUARES["front"][2])}


def _prompts_word(n: int) -> str:
    if n % 10 == 1 and n % 100 != 11:
        return f"{n} промпт"
    return f"{n} промпти" if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14) else f"{n} промптів"


SINGLE_LABELS = {"page1": "Сторінка 1 · присвята", "page30": "Сторінка 30 · післяслово"}


def row_list() -> list[dict]:
    """The rows in the book's order (`books.ROWS`), the cover last — it's generated last (Agent 6, after the spreads)."""
    out = []
    for key, pages in books.ROWS:
        if key in SINGLE_LABELS:
            out.append({"key": key, "label": SINGLE_LABELS[key], "pages": list(pages), "kind": "single"})
        else:
            out.append({"key": key, "label": f"Розворот {pages[0]}–{pages[1]}", "pages": list(pages),
                        "kind": "spread", "mirrored": int(key[len("spread"):]) in MIRRORED})
    out.append({"key": "cover", "label": "Обкладинка", "pages": ["Cover"], "kind": "cover"})
    return out


def row(key: str) -> dict:
    for r in row_list():
        if r["key"] == key:
            return r
    raise ApiError("Невідомий рядок книги.")


def original_stem(key: str) -> str:
    """The name a row's picture keeps in originals/: page-01, spread-04-05, page-30, cover-art, cover-wrap, hero."""
    if key == "page1":
        return "page-01"
    if key == "page30":
        return "page-30"
    if key.startswith("spread"):
        a, b = library.spread_pages(int(key[6:]))
        return f"spread-{a:02d}-{b:02d}"
    return {"cover": "cover-art", "cover-wrap": "cover-wrap", "hero": "hero"}[key]


def original_of(names, key: str) -> str | None:
    stem = original_stem(key)
    return next((n for n in sorted(names) if Path(n).stem == stem), None)


def text_sections(book_text: str) -> dict[str, str]:
    """book-text.md → {"cover", "page1", "spread2".."spread15", "page30": text}. A section starts at `## Cover`,
    `## Spread NN` or `## Afterword`; any other heading (e.g. a critic's report) ends it. `---` lines go; blank
    lines inside the text stay (paragraphs); `[Name]` becomes `{Name}`."""
    sections: dict[str, str] = {}
    key, lines = None, []

    def close():
        if key:
            body = re.sub(r"\n{3,}", "\n\n", "\n".join(lines).strip("\n")).strip()
            for word in ("Name", "Gifter"):
                body = body.replace(f"[{word}]", f"{{{word}}}").replace(f"`{{{word}}}`", f"{{{word}}}")
            if body:
                sections[key] = body

    for line in book_text.splitlines():
        if line.startswith("#"):
            m = re.match(r"^##\s+(?:(cover)|spread\s+0*(\d+)|(afterword))\b", line, re.IGNORECASE)
            close()
            key, lines = None, []
            if m and m.group(1):
                key = "cover"
            elif m and m.group(2):
                n = int(m.group(2))
                key = "page1" if n == 1 else f"spread{n}" if n in SPREADS else None
            elif m and m.group(3):
                key = "page30"
            continue
        if key and line.strip() not in ("---", "***", "___"):
            lines.append(line.rstrip())
    close()
    return sections


def book_texts(path: Path) -> dict[str, str]:
    """The book's texts, by row — what the library gets as the reference for the text check."""
    return text_sections(books.read_text(path / books.AGENT / "book-text.md") or "")


def prompt_objects(raw: str) -> tuple[list[dict], str | None]:
    """Prompt objects from fenced ```json block(s) or a raw JSON document, in order; a block that doesn't parse
    is named (the objects before it still count)."""
    blobs = re.findall(r"```json\s*(.*?)```", raw, re.DOTALL) or [raw]
    out: list[dict] = []
    for i, blob in enumerate(blobs, 1):
        try:
            data = json.loads(blob)
        except json.JSONDecodeError as err:
            return out, f"блок {i}: JSON не читається (рядок {err.lineno})"
        items = data if isinstance(data, list) else [data]
        out.extend(x for x in items if isinstance(x, dict))
    return out, None


def as_prompt(obj: dict) -> str:
    """The prompt exactly as the generator gets it: the whole JSON object, pretty-printed."""
    return json.dumps(obj, indent=2, ensure_ascii=False)


def first_prompt(raw: str) -> str:
    """The prompt inside an agent's note: its first ```json block pretty-printed, else the whole text."""
    m = re.search(r"```json\s*(.*?)```", raw, re.DOTALL)
    blob = m.group(1) if m else raw
    try:
        return as_prompt(json.loads(blob))
    except json.JSONDecodeError:
        return blob.strip()


def book_rows(path: Path) -> dict:
    """The rows with their prompts, texts, pictures and marks; what's wrong with the agents' files, in `notes`."""
    agent = path / books.AGENT
    names = set(books._names(agent))
    pictures = set(books._names(path / books.PICTURES))
    notes: list[str] = []

    def load(name):
        if name not in names:
            return None
        raw = books.read_text(agent / name)
        if raw is None:
            notes.append(f"{name}: файл завеликий або не читається")
            return None
        objs, err = prompt_objects(raw)
        if err:
            notes.append(f"{name}: {err}")
        return objs

    if "abc-prompts-json.md" in names:
        notes.append("Це абетка (28 квадратів) — рядки Майстерні розраховані на 30 сторінок, промпти абетки тут не показано.")
    texts = book_texts(path) if "book-text.md" in names else {}
    prompts: dict[str, str] = {}
    spreads, ends, covers = load("spread-prompts-json.md"), load("endpage-prompts-json.md"), load("cover-prompts-json.md")
    if spreads is not None:
        if len(spreads) != 14:
            notes.append(f"spread-prompts-json.md: {_prompts_word(len(spreads))} замість 14 — розкладено по порядку з розвороту 2–3")
        prompts.update({f"spread{n}": as_prompt(p) for n, p in zip(SPREADS, spreads)})
    if ends is not None:
        if len(ends) != 2:
            notes.append(f"endpage-prompts-json.md: {_prompts_word(len(ends))} замість 2 (перший — сторінка 1, другий — 30)")
        if ends:
            prompts["page1"] = as_prompt(ends[0])
        if len(ends) > 1:
            prompts["page30"] = as_prompt(ends[1])
    refs = {}
    if covers:
        wide = [p for p in covers if str(p.get("id") or "") not in OLD_SQUARE_IDS]
        if len(wide) < len(covers):
            notes.append("cover-prompts-json.md: промпти двох квадратів більше не використовуються — "
                         "агент 6 пише одну картинку 2:1")
        if wide:
            prompts["cover"] = as_prompt(wide[0])
            if ref := reference_file(agent, wide[0]):
                refs["cover"] = ref
            if len(wide) > 1:
                notes.append(f"cover-prompts-json.md: {_prompts_word(len(wide))} 2:1 — взято перший")

    marks = books.state(path).get("rows") or {}
    originals = set(books._names(path / books.ORIGINALS))
    rows = []
    for r in row_list():
        pics = [books.picture(pictures, p) for p in r["pages"]]
        rows.append({**r, "prompt": prompts.get(r["key"], ""), "text": texts.get(r["key"], ""),
                     "pictures": pics if all(pics) else [], "marks": marks.get(r["key"], {}),
                     "original": original_of(originals, r["key"])})
    cover = cover_state(path)
    cover["refs"] = refs
    from . import cover as cover_tool
    cover["tool"] = cover_tool.tool_state(path, rows, cover)
    return {"rows": rows, "notes": notes,
            "counts": {"prompts": len(prompts), "texts": sum(1 for r in rows if r["text"]),
                       "pictures": sum(1 for r in rows if r["pictures"]), "total": len(rows)},
            "heroPrompt": first_prompt(books.read_text(agent / "canonical-prompt.md") or "") if "canonical-prompt.md" in names else "",
            "variants": variants(path), "cover": cover}


REFERENCE_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")


def reference_file(agent: Path, prompt: dict) -> str:
    """The picture a cover prompt names as its `reference_image` (Agent 6 copies the best frame into `agent/` as
    `ref_cover_….jpg`) — its file name when it is a picture lying right in `agent/`, else "" («Референс у буфер»)."""
    ref = prompt.get("reference_image")
    ref = ref[0] if isinstance(ref, list) and ref else ref
    name = str(ref or "")
    if not name or name != Path(name).name or not name.lower().endswith(REFERENCE_SUFFIXES):
        return ""
    return name if (agent / name).is_file() else ""


# ---------------------------------------------------------------- the cover: the picture, then its margins

def cover_state(path: Path) -> dict:
    """Stage 1 — the picture Gemini made from Agent 6's prompt (originals/cover-art.*); the Workshop lays it on the
    printer's template, the rest white (originals/cover-expanded.png, `template_layout()`); stage 2 — the generator
    fills the white margins (outpaint) → pictures/Cover.png, brought to the template's exact 5370×2850 px at 300 dpi.
    «Без полів» takes the picture as it is. A Cover.png made of two squares in the days of «Два квадрати»
    (2026-10-25…27, marked `squares` in cover-wrap) stays the book's until a new one comes: shown with Gelato's lines."""
    originals = set(books._names(path / books.ORIGINALS))
    marks = books.state(path).get("rows") or {}
    final = books.picture(set(books._names(path / books.PICTURES)), "Cover")
    wrap = marks.get("cover-wrap", {})
    final_sq = bool(final and wrap.get("squares"))
    ppmm = SQUARES["dpi"] / 25.4
    tpl = ({"guides": squares_guides(), "template": {"px": [round(SQUARES["mm"][0] * ppmm), round(SQUARES["mm"][1] * ppmm)],
                                                     "dpi": SQUARES["dpi"]}} if final_sq
           else {"guides": template_guides(), "template": {"px": list(TEMPLATE["px"]), "dpi": TEMPLATE["dpi"]}})
    expanded = "cover-expanded.png" if "cover-expanded.png" in originals else None
    layout = marks.get("cover-expanded", {})
    size = layout.get("size")
    return {"art": original_of(originals, "cover"), "final": final, "wrapOriginal": original_of(originals, "cover-wrap"),
            "skipped": bool(wrap.get("skipped")), "artMarks": marks.get("cover", {}), "wrapMarks": wrap,
            **tpl, "finalSquares": final_sq, "expanded": expanded, "layout": layout,
            "wideTemplate": {"px": list(TEMPLATE["px"]), "dpi": TEMPLATE["dpi"]},   # a variant's cover is always on it
            "outpaint": outpaint_prompt(size) if expanded and size else ""}


def outpaint_prompt(size) -> str:
    """The prompt for filling the white margins around the picture — nothing inside it may change. Written in the
    pipeline's image-only language (no words about print or the object it becomes)."""
    w, h = size
    g = math.gcd(w, h)
    return as_prompt({
        "task": "outpaint: extend the attached illustration into the plain white margin around it",
        "input": "Image 1 is a finished watercolor illustration placed in the middle of a larger canvas; "
                 "everything outside it is a plain white margin",
        "edit_scope": "fill ONLY the white margin; the illustration inside it stays exactly as it is",
        "preserve_exactly": [
            "every pixel of the existing illustration, untouched",
            "its position and scale on the canvas",
            "all characters, faces, poses and expressions",
            "composition, colors, lighting, brushwork and paper texture",
        ],
        "extension": {
            "method": "continue the existing scene outward, as if the artwork had always been this wide and tall",
            "continue": ["sky, clouds and light", "ground, grass, leaves and plants",
                         "the same soft watercolor style, palette and paper texture", "the same light direction"],
            "content": "calm, low-detail continuation of what already touches each edge; nothing new that draws the eye",
            "blend": "no visible join line, edge, frame, vignette or change of color where the new area meets the old",
        },
        "output": {"canvas": f"{w} × {h} px — the same size as Image 1", "aspect_ratio": f"{w // g}:{h // g}",
                   "fill": "the whole canvas edge to edge, no white left"},
        "negative": ["changing, redrawing or recoloring the original illustration", "cropping or zooming",
                     "new characters or new focal objects", "text, letters, numbers, logos, watermarks",
                     "borders, frames, drop shadows", "3D render, vector, photorealism"],
    })


# ---------------------------------------------------------------- hero variants (Tier H)

def variant_names(path: Path) -> list[str]:
    folder = path / books.AGENT / "variants"
    try:
        with os.scandir(folder) as entries:
            return sorted(e.name for e in entries if e.is_dir() and not e.name.startswith((".", "_")))
    except OSError:
        return []


def variants(path: Path) -> list[dict]:
    """agent/variants/<G2_brunette>/: hero-prompt.md (the canonical's edit), hero.png (caught by the Workshop),
    2.json … 15.json — one swap prompt per spread. Their pages go to pictures/variants/<name>/, and so does the
    variant's own cover (Cover.png — one frame, the finished wide cover at once, no prompt; the owner, 2026-09-27)."""
    out = []
    marks = books.state(path).get("rows") or {}
    for name in variant_names(path):
        folder = path / books.AGENT / "variants" / name
        files = set(books._names(folder))
        pics = set(books._names(path / books.PICTURES / "variants" / name))
        rows = []
        for n in SPREADS:
            raw = next((books.read_text(folder / f"{n}{s}") for s in (".json", ".md") if f"{n}{s}" in files), None)
            if raw is None:
                continue
            pages = list(library.spread_pages(n))
            found = [books.picture(pics, p) for p in pages]
            rows.append({"key": f"spread{n}", "label": f"Розворот {pages[0]}–{pages[1]}", "pages": pages,
                         "kind": "spread", "mirrored": n in MIRRORED, "prompt": first_prompt(raw),
                         "pictures": found if all(found) else [], "marks": marks.get(f"{name}/spread{n}", {})})
        hero_file = next((f for f in ("hero-prompt.md", "hero-prompt.json") if f in files), None)
        out.append({"name": name, "hero": "hero.png" if "hero.png" in files else None,
                    "heroPrompt": first_prompt(books.read_text(folder / hero_file) or "") if hero_file else "",
                    "rows": rows, "done": sum(1 for r in rows if r["pictures"]),
                    "cover": {"final": books.picture(pics, "Cover"), "marks": marks.get(f"{name}/cover-wrap", {})}})
    return out


# ---------------------------------------------------------------- the book check (GO)

_checked: dict[str, tuple[str, dict]] = {}
_check_lock = threading.Lock()


def _agent_key(agent: Path) -> str:
    """What the check reads, as sizes and times: agent/ and its _work/ (the agent's story blueprint lives there)."""
    parts = []
    for folder in (agent, agent / "_work"):
        for name in books._names(folder):
            try:
                st = (folder / name).stat()
            except OSError:
                continue
            parts.append(f"{folder.name}/{name}:{st.st_size}:{st.st_mtime_ns}")
    return "|".join(parts)


def book_check(path: Path) -> dict | None:
    """The old validator's rules on the book's agent/ folder, once any prompt file is there (before that there's
    nothing to check). Run again only when an agent's file changed."""
    agent = path / books.AGENT
    if not set(books._names(agent)) & set(PROMPT_FILES):
        return None
    key = _agent_key(agent)
    with _check_lock:
        hit = _checked.get(str(path))
        if hit and hit[0] == key:
            return hit[1]
    findings = check.run(str(path))
    fails = [m for level, m in findings if level == "FAIL"]
    warns = [m for level, m in findings if level == "WARN"]
    result = {"go": not fails, "fails": fails, "warns": warns,
              "passed": sum(1 for level, _ in findings if level == "PASS")}
    with _check_lock:
        _checked[str(path)] = (key, result)
    return result
