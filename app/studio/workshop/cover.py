"""«Обкладинка» — the cover's own tool (the owner, 2026-10-25). One way since 2026-10-27 (the owner: back to 2:1 and the
outpaint; «Два квадрати» taken out): one 2:1 picture filled with the scene edge to edge, the title painted in its right
area and an empty room left for the name — the generator gets a **layout guide** picture first (where the name's room,
the title and the characters go, since 2026-11-01), then the book's reference, then Agent 6's prompt with the guide's
words put in; then the margins are outpainted on the printer's template as before (rows.cover_state()).

The choices of the book live in book.json under "coverTool": {"guide": name | "none", "ref": "" | "none" | spreadN}.
The guides are pictures of the program (web/img/cover-guides/); their words for the prompt are GUIDES below.
"""
from __future__ import annotations

import json
from pathlib import Path

from .. import core
from ..server import ApiError
from . import books

GUIDE_DIR = core.WEB_DIR / "img" / "cover-guides"
STATE_KEY = "coverTool"

_MAP = ("Image 1 is a STRICT position map with the same 2:1 proportions as your image; it tells WHERE things go and "
        "nothing else — its colors are only codes, never paint, light or tint. The green-grey field = the scene. ")
_NAME = "an empty part of the background where a name will be set later"
_RULES = ("RULE 1: the main characters and what they hold appear ONLY inside the yellow area — completely inside it, never "
          "over its left edge. RULE 2: from the left edge of the image up to the left edge of the yellow area there are NO "
          "characters and no part of them. RULE 3: the title lettering is only inside the brown-grey area; the blue area "
          "stays empty background. RULE 4: the blue, brown-grey and yellow areas share one vertical center line at three "
          "quarters of the image width — the characters are centered under the title, not to its left. RULE 5: in the "
          "finished picture there is no trace of the map — no blue, pink, brown or yellow patch, haze, glow, band or "
          "tinted rectangle where its areas were; the background behind the name's place, the title and the characters "
          "is the same smooth wash as around it.")
# name: (label, what goes where — the prompt's "layout_guide"). The guide is always Image 1 (it goes first, the reference
# second — the generator holds the first picture's layout best). The owner's tests on books 41/50, 2026-11-01: three
# zones stacked in the right area's middle (≈ 3/4 of the width — the front on the book), the yellow one the characters;
# strict words and "no trace of the map" — soft words let the characters drift left, "paint over it" left its patches.
GUIDES = {
    "wide-name-title": ("Ім'я, назва, персонажі",
                        _MAP + f"The pale blue area at the top right = {_NAME}. The brown-grey area under it = where the "
                        "title lettering goes. The yellow area under that = where the main characters are. " + _RULES),
    "wide-title-name": ("Назва, ім'я, персонажі",
                        _MAP + "The brown-grey area at the top right = where the title lettering goes. The pale blue area "
                        f"under it = {_NAME}. The yellow area under that = where the main characters are. " + _RULES),
}


# ---------------------------------------------------------------- the book's choices

def default_guide(path: Path) -> str:
    """The name's room where the title wants it: «{Name}'s …» — above the title, else under it. The title read as the
    rows read it (`[Name]` and `` `{Name}` `` made `{Name}`)."""
    from .rows import book_texts
    lines = [s.strip("*_ ") for s in book_texts(path).get("cover", "").splitlines() if s.strip()]
    return "wide-name-title" if lines and lines[0].startswith("{Name}") else "wide-title-name"


def _saved(path: Path) -> dict:
    raw = books.state(path).get(STATE_KEY)
    return raw if isinstance(raw, dict) else {}


def settings(path: Path) -> dict:
    raw = _saved(path)
    guide = raw.get("guide")
    return {"guide": guide if guide in GUIDES or guide == "none" else default_guide(path), "ref": str(raw.get("ref") or "")}


def set_settings(book_id: str, body: dict) -> dict:
    """The tool's choices: the guide (or none), the reference (Agent 6's picture, a spread, or none) — merged into what
    is saved under the state's lock, so two quick choices both stay."""
    path = books.book_path(book_id)
    changes = {}
    if "guide" in body:
        guide = str(body["guide"] or "")
        if guide not in GUIDES and guide != "none":
            raise ApiError("Невідома схема.")
        changes["guide"] = guide
    if "ref" in body:
        ref = str(body["ref"] or "")
        if ref not in ("", "none") and not (ref.startswith("spread") and ref[6:].isdigit()):
            raise ApiError("Референсом може бути тільки розворот книги.")
        changes["ref"] = ref

    def change(data):
        now = data.get(STATE_KEY)
        data[STATE_KEY] = {**(now if isinstance(now, dict) else {}), **changes}
    books.update_state(path, change)
    return settings(path)


def tool_state(path: Path, rows: list[dict], cover: dict) -> dict:
    """What the page needs: the guides, the book's choices, the spreads that can be the reference, and the prompt as
    «Генерувати» pastes it (the one shown and copied)."""
    st = settings(path)
    r = next((x for x in rows if x["key"] == "cover"), None)
    pasted = ""
    if r and r["prompt"]:
        referenced = bool(reference({"rows": rows, "cover": cover}, st))
        guide = st["guide"] if st["guide"] in GUIDES else None
        pasted = prompt_with_guide(r["prompt"], guide, referenced)
    return {"settings": st, "prompt": pasted,
            "guides": [{"name": n, "label": label, "src": f"/img/cover-guides/{n}.png"} for n, (label, _) in GUIDES.items()],
            "refs": [{"key": r["key"], "label": r["label"], "page": r["pictures"][0]}
                     for r in rows if r["kind"] == "spread" and r["pictures"]]}


def reference(detail: dict, st: dict) -> dict:
    """The reference: a spread the owner picked; «none»; else (by default) the picture Agent 6 named in the prompt and
    put into agent/ («Референс у буфер», 24.10.2026), if there is one."""
    ref = st["ref"]
    if ref.startswith("spread") and any(r["key"] == ref and r["pictures"] for r in detail["rows"]):
        return {"spread": ref}
    if ref != "none" and (detail["cover"].get("refs") or {}).get("cover"):
        return {"agent": detail["cover"]["refs"]["cover"]}
    return {}


# ---------------------------------------------------------------- the prompt and the clipboard

def prompt_with_guide(prompt: str, guide: str | None, referenced: bool = True) -> str:
    """Agent 6's prompt with the guide's words put in, right after the canvas (before the reference), and the reference
    named by its number among the pictures: Image 2 after the guide, Image 1 without one. No reference picture pasted:
    the prompt names none — else it would mean the guide."""
    try:
        obj = json.loads(prompt)
    except json.JSONDecodeError:
        return f"{prompt}\n\nlayout_guide: {GUIDES[guide][1]}" if guide else prompt
    if not referenced:
        obj = {k: v for k, v in obj.items() if k not in ("reference_image", "reference_rule")}
    else:  # a spread picked for a prompt that names none gets named too
        obj["reference_image"] = f"Image {2 if guide else 1} (the reference picture)"
    obj.pop("layout_guide", None)
    if not guide:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    anchor = next((k for k in ("canvas", "aspect_ratio", "task") if k in obj), None)
    out = {} if anchor else {"layout_guide": GUIDES[guide][1]}
    for k, v in obj.items():
        out[k] = v
        if k == anchor:
            out["layout_guide"] = GUIDES[guide][1]
    return json.dumps(out, indent=2, ensure_ascii=False)


def items(book_id: str, detail: dict) -> tuple[str, list[dict]]:
    """What the cover's «Генерувати» pastes, in order: the guide, the reference, the prompt with the guide's words."""
    path = books.book_path(book_id)
    r = next((x for x in detail["rows"] if x["key"] == "cover"), None)
    if not r or not r["prompt"]:
        raise ApiError("Обкладинка: промпту ще немає — його пише агент 6.")
    st = settings(path)
    pics: list[dict] = []
    guide = st["guide"] if st["guide"] in GUIDES else None
    if guide:
        pics.append({"kind": "image", "label": "схема", "path": str(GUIDE_DIR / f"{guide}.png")})
    ref = reference(detail, st)
    if ref.get("spread"):
        pics.append({"kind": "image", "label": "референс", "spread": ref["spread"]})
    elif ref.get("agent"):
        pics.append({"kind": "image", "label": "референс", "path": str(path / books.AGENT / ref["agent"])})
    referenced = bool(ref)
    return r["label"], pics + [{"kind": "text", "label": "промпт",
                                "text": prompt_with_guide(r["prompt"], guide, referenced)}]
