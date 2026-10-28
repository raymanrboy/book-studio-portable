"""The book check: deterministic pre-flight checks for a Workshop book's folder («Промпти · GO» on its strip).

The old pipeline's tools/validate-book.py (its rules unchanged); it reads the book's `agent/` folder, where the
agents write every file. The Workshop calls run(); the book agents run the same rules through pipeline/check_book.py.

Catches MECHANICAL errors for free, BEFORE spending image-generation tokens. Subjective quality
(rhyme quality, scene repetition, "finale lands") stays with the LLM gate and `knowledge/
repetition-gate.md` - this script only checks what code can verify deterministically.

Usage (from the pipeline's folder):
    python check_book.py "books/40.some-book"

Exit code = number of FAIL findings (0 = clean). WARN never fails the build; it flags things for a
human/LLM glance.

PLUGGABLE: every rule is a function `rule_xxx(ctx) -> list[Finding]`, registered in RULES. To add a
rule, write the function and append its name to RULES. Nothing else to wire. A Finding is
(level, message); level is "PASS" | "WARN" | "FAIL".
"""
import json
import os
import re
import sys

Finding = tuple  # (level, message)

SENSITIVE = ("fair", "white", "light", "dark", "pale", "fairest")
ABC_LETTERS = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")

PROMPT_FILE_PREFIXES = (
    "spread-prompts-json",
    "endpage-prompts-json",
    "cover-prompts-json",
    "abc-prompts-json",
)

PROMPT_LEAKAGE_PATTERNS = (
    (re.compile(r"%"), "percent sign"),
    (re.compile(r"\bLEFT\s*\d+", re.IGNORECASE), "left layout measurement"),
    (re.compile(r"\bRIGHT\s*\d+", re.IGNORECASE), "right layout measurement"),
    (re.compile(r"\bMIDDLE\s*\d+", re.IGNORECASE), "middle layout measurement"),
    (re.compile(r"\bSTORY\s*\d+\s*/\s*TRANSITION\s*\d+\s*/\s*TEXT\s*\d+", re.IGNORECASE),
     "story/transition/text ratio label"),
    (re.compile(r"\bcharacter_position\b", re.IGNORECASE), "schematic character_position field"),
)

GENERATION_TRIGGER_PATTERNS = (
    (re.compile(r"\bbook\b", re.IGNORECASE), "book trigger"),
    (re.compile(r"\bstorybook\b", re.IGNORECASE), "storybook trigger"),
    (re.compile(r"\bpage\b", re.IGNORECASE), "page trigger"),
    (re.compile(r"\bpages\b", re.IGNORECASE), "pages trigger"),
    (re.compile(r"\bspread\b", re.IGNORECASE), "spread trigger"),
    (re.compile(r"\bcover\b", re.IGNORECASE), "cover trigger"),
    (re.compile(r"\bfront\b", re.IGNORECASE), "front trigger"),
    (re.compile(r"\bback\b", re.IGNORECASE), "back trigger"),
    (re.compile(r"\bspine\b", re.IGNORECASE), "spine trigger"),
    (re.compile(r"\bfold\b", re.IGNORECASE), "fold trigger"),
    (re.compile(r"\bseam\b", re.IGNORECASE), "seam trigger"),
    (re.compile(r"\bgutter\b", re.IGNORECASE), "gutter trigger"),
    (re.compile(r"\bdivider\b", re.IGNORECASE), "divider trigger"),
    (re.compile(r"\bdiptych\b", re.IGNORECASE), "diptych trigger"),
    (re.compile(r"\btwo-panel\b", re.IGNORECASE), "two-panel trigger"),
    (re.compile(r"\bsplit\b", re.IGNORECASE), "split trigger"),
    (re.compile(r"\bhalves\b", re.IGNORECASE), "halves trigger"),
    (re.compile(r"\bhalf\b", re.IGNORECASE), "half trigger"),
    (re.compile(r"\bsliced\b", re.IGNORECASE), "sliced trigger"),
    (re.compile(r"\bmockup\b", re.IGNORECASE), "mockup trigger"),
    (re.compile(r"\bproduct\b", re.IGNORECASE), "product trigger"),
    (re.compile(r"\bphysical\b", re.IGNORECASE), "physical-object trigger"),
    (re.compile(r"\bhardcover\b", re.IGNORECASE), "hardcover trigger"),
    (re.compile(r"\bpaper stack\b", re.IGNORECASE), "paper-stack trigger"),
    (re.compile(r"\bpage edges?\b", re.IGNORECASE), "page-edge trigger"),
    (re.compile(r"\bprinted\b", re.IGNORECASE), "printed-object trigger"),
)


# --------------------------------------------------------------------------------------
# Context: load the book's files once, parse what we can, never crash.
# --------------------------------------------------------------------------------------
def agent_dir(book_dir):
    """The folder the agents write into: `<book>/agent`; a folder without it is read as it is."""
    inner = os.path.join(book_dir, "agent")
    return inner if os.path.isdir(inner) else book_dir


class Ctx:
    def __init__(self, book_dir):
        self.dir = agent_dir(book_dir)
        self.book_text = self._read("book-text.md")
        self.blueprint = self._read("_work/story-blueprint.md") or self._read("story-blueprint.md")
        self.is_abc = self._is_abc_format()
        self.prompt_sets = self._load_prompt_sets()

    def _read(self, name):
        p = os.path.join(self.dir, name)
        try:
            with open(p, encoding="utf-8") as f:
                return f.read()
        except Exception:
            return None

    @staticmethod
    def _parse_json(raw):
        """Return prompt objects from fenced JSON block(s), or a raw JSON document."""
        if not raw:
            return None
        blobs = re.findall(r"```json\s*(.*?)```", raw, re.DOTALL) or [raw]
        out = []
        for blob in blobs:
            try:
                data = json.loads(blob)
            except Exception:
                return None
            if isinstance(data, dict):
                out.append(data)
            elif isinstance(data, list):
                out.extend(x for x in data if isinstance(x, dict))
        return out or None

    def _load_prompt_sets(self):
        """All generator-facing prompt JSON files -> [(filename, [prompt dicts] | None)]."""
        try:
            names = sorted(n for n in os.listdir(self.dir)
                           if n.endswith(".md") and n.startswith(PROMPT_FILE_PREFIXES))
        except Exception:
            names = []
        return [(n, self._parse_json(self._read(n))) for n in names]

    def _is_abc_format(self):
        blob = "\n".join(x for x in (self.book_text, self.blueprint) if x)
        return bool(re.search(r"Format:\s*ABC Square Exception|Formula:\s*F\b", blob, re.IGNORECASE))


def _spreads(book_text):
    """Split book-text into (heading, body-lines) sections for Spread NN / Afterword."""
    if not book_text:
        return []
    out, cur = [], None
    for line in book_text.splitlines():
        if re.match(r"^##\s+(Spread\s+\d+|Afterword)", line, re.IGNORECASE):
            cur = [line.strip(), []]
            out.append(cur)
        elif cur is not None:
            if line.strip() and not line.strip().startswith(("---", "- [", "## Self", "## ")):
                cur[1].append(line.rstrip())
    return out


def _abc_sections(book_text):
    """Split ABC text into Dedication (01/02), Afterword, and Letter A-Z sections."""
    if not book_text:
        return []
    out, cur = [], None
    for line in book_text.splitlines():
        if re.match(r"^##\s+(Dedication(\s+0?[12])?|Afterword|Letter\s+[A-Z]\b)", line, re.IGNORECASE):
            cur = [line.strip(), []]
            out.append(cur)
        elif cur is not None:
            stripped = line.strip()
            if not stripped or stripped.startswith(("---", "- [", "## Self", "## ")):
                continue
            if re.match(r"^(Large overlay|Overlay|Canva overlay):", stripped, re.IGNORECASE):
                continue
            cur[1].append(line.rstrip())
    return out


def _side(prompt):
    """Best-effort 'left'/'right' for a prompt's text-safe side; None if undetermined."""
    tsa = prompt.get("text_safe_area") or prompt.get("composition") or ""
    blob = json.dumps(tsa) if isinstance(tsa, (dict, list)) else str(tsa)
    blob = blob.lower()
    has_l, has_r = "left" in blob, "right" in blob
    if has_l and not has_r:
        return "L"
    if has_r and not has_l:
        return "R"
    return None


def _prompt_blob(prompt):
    return json.dumps(prompt, ensure_ascii=False)


def _is_spread_prompt_set(name):
    return name.startswith("spread-prompts-json")


def _is_endpage_prompt_set(name):
    return name.startswith("endpage-prompts-json")


def _is_wraparound_prompt_set(name):
    return name.startswith("cover-prompts-json")


def _is_abc_prompt_set(name):
    return name.startswith("abc-prompts-json")


# Agent 6's two square prompts of «Два квадрати» (2026-10-24…27, taken out) — books written then keep them: 1:1, not
# the 2:1 contract (the Workshop's cover row ignores them).
SQUARE_COVER_IDS = ("title-square", "quiet-square")


def _is_square_cover(prompt):
    return str(prompt.get("id", "")) in SQUARE_COVER_IDS


def _expected_aspect(name, prompt=None):
    if _is_endpage_prompt_set(name) or _is_abc_prompt_set(name):
        return "1:1"
    if prompt is not None and _is_wraparound_prompt_set(name) and _is_square_cover(prompt):
        return "1:1"
    return "2:1"


# --------------------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------------------
def rule_text_structure(ctx):
    if ctx.book_text is None:
        return [("WARN", "book-text.md not found - skipping text structure")]
    t = ctx.book_text
    if ctx.is_abc:
        out = []
        # Support either two dedications (Dedication 01/02) OR Dedication + Afterword
        has_dedication_01 = bool(re.search(r"##\s+Dedication\s+0?1\b", t, re.IGNORECASE))
        has_dedication_02 = bool(re.search(r"##\s+Dedication\s+0?2\b", t, re.IGNORECASE))
        has_single_dedication = bool(re.search(r"##\s+Dedication\b(?!\s+0?2\b)", t, re.IGNORECASE))
        has_afterword = bool(re.search(r"##\s+Afterword\b", t, re.IGNORECASE))

        if not (has_dedication_01 or has_single_dedication):
            out.append(("FAIL", "book-text ABC: missing Dedication / Dedication 01"))
        if not (has_dedication_02 or has_afterword):
            out.append(("FAIL", "book-text ABC: missing Afterword / Dedication 02"))

        missing = [letter for letter in ABC_LETTERS
                   if not re.search(r"##\s+Letter\s+%s\b" % letter, t, re.IGNORECASE)]
        if missing:
            out.append(("FAIL", "book-text ABC: missing letters %s" % ", ".join(missing)))
        return out or [("PASS", "book-text ABC structure: Dedication + Letters A-Z + Afterword (or 2 Dedications) present")]
    out = []
    if not re.search(r"##\s+Spread\s+0?1\b.*[Dd]edication", t):
        out.append(("FAIL", "book-text: missing 'Spread 01 - Dedication'"))
    if not re.search(r"##\s+Spread\s+15\b", t):
        out.append(("FAIL", "book-text: missing 'Spread 15' (finale)"))
    if not re.search(r"##\s+Afterword", t, re.IGNORECASE):
        out.append(("FAIL", "book-text: missing 'Afterword' (separate square end image)"))
    if not re.search(r"^##\s+Cover\b", t, re.IGNORECASE | re.MULTILINE):
        out.append(("WARN", "book-text: no '## Cover' title - workshop.json will have no cover text"))
    return out or [("PASS", "book-text structure: Dedication + Spread 15 + Afterword present")]


def rule_blueprint_structure(ctx):
    if ctx.blueprint is None:
        return [("WARN", "story-blueprint.md not found - skipping blueprint structure")]
    if ctx.is_abc:
        out = []
        has_dedication_01 = bool(re.search(r"##\s+Dedication\s+0?1\b", ctx.blueprint, re.IGNORECASE))
        has_dedication_02 = bool(re.search(r"##\s+Dedication\s+0?2\b", ctx.blueprint, re.IGNORECASE))
        has_single_dedication = bool(re.search(r"##\s+Dedication\b(?!\s+0?2\b)", ctx.blueprint, re.IGNORECASE))
        has_afterword = bool(re.search(r"##\s+Afterword\b", ctx.blueprint, re.IGNORECASE))

        if not (has_dedication_01 or has_single_dedication):
            out.append(("FAIL", "blueprint ABC: missing Dedication / Dedication 01"))
        if not (has_dedication_02 or has_afterword):
            out.append(("FAIL", "blueprint ABC: missing Afterword / Dedication 02"))

        missing = [letter for letter in ABC_LETTERS
                   if not re.search(r"##\s+Letter\s+%s\b" % letter, ctx.blueprint, re.IGNORECASE)]
        if missing:
            out.append(("FAIL", "blueprint ABC: missing letters %s" % ", ".join(missing)))
        return out or [("PASS", "blueprint ABC structure present")]
    out = []
    if not re.search(r"##\s+Spread\s+0?1\b", ctx.blueprint):
        out.append(("FAIL", "blueprint: missing Spread 01"))
    if not re.search(r"##\s+Afterword", ctx.blueprint, re.IGNORECASE):
        out.append(("WARN", "blueprint: no Afterword entry (separate square end image)"))
    return out or [("PASS", "blueprint structure present")]


def rule_name_frequency(ctx):
    if ctx.is_abc:
        sections = _abc_sections(ctx.book_text)
        letters = [s for s in sections if re.match(r"##\s+Letter\s+[A-Z]\b", s[0], re.IGNORECASE)]
        if not letters:
            return [("WARN", "no ABC letter sections parsed - skipping {Name} check")]
        with_name = sum(1 for _, body in letters if any("{Name}" in ln for ln in body))
        line_initial = any(ln.lstrip().startswith("{Name}") for _, body in letters for ln in body)
        out = []
        if with_name < len(letters):
            out.append(("WARN", "{Name} in %d/%d ABC letter sections - strongest version uses every letter" %
                        (with_name, len(letters))))
        else:
            out.append(("PASS", "{Name} frequency ok (%d/%d ABC letter sections)" %
                        (with_name, len(letters))))
        out.append(("PASS" if line_initial else "WARN",
                    "line-initial {Name} present" if line_initial else "no line-initial {Name} found"))
        return out
    spreads = _spreads(ctx.book_text)
    if not spreads:
        return [("WARN", "no spreads parsed - skipping {Name} check")]
    story = [s for s in spreads if s[0].lower().startswith("## spread")]
    n = len(story)
    with_name = sum(1 for _, body in story if any("{Name}" in ln for ln in body))
    line_initial = any(
        ln.lstrip().startswith("{Name}") for _, body in story for ln in body
    )
    out = []
    if with_name == 0:
        out.append(("FAIL", "{Name} never appears in any spread"))
    elif n and with_name < n / 3:
        out.append(("WARN", "{Name} in %d/%d spreads - aim for >= 1 per 3" % (with_name, n)))
    else:
        out.append(("PASS", "{Name} frequency ok (%d/%d spreads)" % (with_name, n)))
    out.append(("PASS" if line_initial else "WARN",
                "line-initial {Name} present" if line_initial else "no line-initial {Name} found"))
    return out


def rule_sensitive_words(ctx):
    if ctx.book_text is None:
        return []
    hits = []
    sections = _abc_sections(ctx.book_text) if ctx.is_abc else _spreads(ctx.book_text)
    for _, body in sections:
        for ln in body:
            for w in SENSITIVE:
                if re.search(r"\b%s\b" % w, ln, re.IGNORECASE):
                    hits.append("%s -> \"%s\"" % (w, ln.strip()))
    if hits:
        return [("WARN", "sensitive word for human review (ok only for scenery): " + h) for h in hits]
    return [("PASS", "no sensitive appearance-words found")]


def rule_lines_per_spread(ctx):
    out = []
    if ctx.is_abc:
        for head, body in _abc_sections(ctx.book_text):
            if not re.match(r"##\s+Letter\s+[A-Z]\b", head, re.IGNORECASE):
                continue
            if len(body) > 4:
                out.append(("WARN", "%s has %d text lines (>4)" % (head, len(body))))
        return out or [("PASS", "<= 4 lines per ABC letter section")]
    for head, body in _spreads(ctx.book_text):
        if not head.lower().startswith("## spread"):
            continue
        if re.search(r"0?1\b", head) and "dedication" in head.lower():
            continue
        if len(body) > 8:
            out.append(("WARN", "%s has %d text lines (>8; standard is 6 short lines)" % (head, len(body))))
    return out or [("PASS", "<= 8 lines per story spread (standard: 6 short lines)")]


def rule_json_parses(ctx):
    if not ctx.prompt_sets:
        return [("WARN", "no generator-facing prompt JSON found - skipping prompt checks")]
    out = []
    for name, prompts in ctx.prompt_sets:
        if prompts is None:
            out.append(("FAIL", "%s: JSON did not parse" % name))
        else:
            out.append(("PASS", "%s: parsed (%d prompts)" % (name, len(prompts))))
    return out


def rule_prompt_asset_counts(ctx):
    if not ctx.prompt_sets:
        return []
    counts = {name: len(prompts) for name, prompts in ctx.prompt_sets if prompts is not None}
    out = []
    spread_files = [n for n in counts if _is_spread_prompt_set(n)]
    endpage_files = [n for n in counts if _is_endpage_prompt_set(n)]
    abc_files = [n for n in counts if _is_abc_prompt_set(n)]
    if ctx.is_abc:
        if not abc_files:
            out.append(("FAIL", "missing abc-prompts-json*.md with 28 square prompts"))
        for name in abc_files:
            if counts[name] != 28:
                out.append(("FAIL", "%s: expected 28 ABC square prompts, found %d" %
                            (name, counts[name])))
            else:
                out.append(("PASS", "%s: 28 ABC square prompts" % name))
        if spread_files:
            out.append(("WARN", "ABC format also has story panorama prompt file(s): %s" %
                        ", ".join(spread_files)))
        return out
    for name in spread_files:
        if counts[name] != 14:
            out.append(("FAIL", "%s: expected 14 story panorama prompts, found %d" %
                        (name, counts[name])))
        else:
            out.append(("PASS", "%s: 14 story panorama prompts" % name))
    if spread_files and not endpage_files:
        out.append(("FAIL", "missing endpage-prompts-json*.md with 2 square end-image prompts"))
    for name in endpage_files:
        if counts[name] != 2:
            out.append(("FAIL", "%s: expected 2 square end-image prompts, found %d" %
                        (name, counts[name])))
        else:
            out.append(("PASS", "%s: 2 square end-image prompts" % name))
    return out


def rule_json_aspect(ctx):
    out = []
    for name, prompts in ctx.prompt_sets:
        if not prompts:
            continue
        bad = [(i + 1, _expected_aspect(name, p)) for i, p in enumerate(prompts)
               if str(p.get("aspect_ratio", "")).strip() != _expected_aspect(name, p)]
        if bad:
            for expected in sorted({e for _, e in bad}):
                out.append(("FAIL", "%s: missing aspect_ratio '%s' at #%s" %
                            (name, expected, ", ".join(str(i) for i, e in bad if e == expected))))
        else:
            out.append(("PASS", "%s: every prompt declares %s" % (name, " / ".join(sorted({_expected_aspect(name, p) for p in prompts})))))
    return out


def rule_json_negatives(ctx):
    out = []
    for name, prompts in ctx.prompt_sets:
        if not prompts:
            continue
        file_out = []
        for i, p in enumerate(prompts):
            neg = " ".join(p.get("negative", [])).lower() if isinstance(p.get("negative"), list) else str(p.get("negative", "")).lower()
            if _is_abc_prompt_set(name):
                if "words" not in neg and "visible words" not in neg:
                    file_out.append(("WARN", "%s prompt #%d negative[] missing word guard" % (name, i + 1)))
            elif "text" not in neg:
                file_out.append(("WARN", "%s prompt #%d negative[] missing 'text'" % (name, i + 1)))
        guard = "word guard" if _is_abc_prompt_set(name) else "text guard"
        out.extend(file_out or [("PASS", "%s: negatives include %s" % (name, guard))])
    return out


def rule_no_empty_reference_fields(ctx):
    out = []
    for name, prompts in ctx.prompt_sets:
        if not prompts:
            continue
        findings = []
        for i, p in enumerate(prompts):
            if "reference_image" in p and p.get("reference_image") is None:
                findings.append("%s prompt #%d has reference_image:null; omit the key when no reference is used" %
                                (name, i + 1))
            ref_rule = str(p.get("reference_rule", ""))
            if re.search(r"\bno (image )?reference( image)? (is )?attached\b|\bno image reference\b",
                         ref_rule, re.IGNORECASE):
                findings.append("%s prompt #%d has filler reference_rule text; omit reference fields when no reference is used" %
                                (name, i + 1))
        if findings:
            out.extend(("FAIL", f) for f in findings)
        else:
            out.append(("PASS", "%s: no empty/null reference fields" % name))
    return out


def rule_reference_images_exist(ctx):
    out = []
    for name, prompts in ctx.prompt_sets:
        if not prompts:
            continue
        findings = []
        for i, p in enumerate(prompts):
            ref = p.get("reference_image")
            refs = ref if isinstance(ref, list) else [ref]
            for item in refs:
                if not item:
                    continue
                if re.search(r"^[a-z]+://", str(item), re.IGNORECASE):
                    continue
                ref_path = os.path.normpath(os.path.join(ctx.dir, str(item)))
                book_root = os.path.abspath(ctx.dir)
                abs_ref_path = os.path.abspath(ref_path)
                if not (abs_ref_path == book_root or abs_ref_path.startswith(book_root + os.sep)):
                    findings.append("%s prompt #%d reference_image points outside the book folder: %s" %
                                    (name, i + 1, item))
                elif not os.path.isfile(abs_ref_path):
                    findings.append("%s prompt #%d reference_image not found: %s" %
                                    (name, i + 1, item))
        if findings:
            out.extend(("FAIL", f) for f in findings)
        else:
            out.append(("PASS", "%s: every local reference_image exists" % name))
    return out


def rule_prompt_no_layout_leakage(ctx):
    out = []
    for name, prompts in ctx.prompt_sets:
        if not prompts:
            continue
        findings = []
        for i, p in enumerate(prompts):
            blob = _prompt_blob(p)
            for pattern, label in PROMPT_LEAKAGE_PATTERNS:
                if pattern.search(blob):
                    findings.append("%s prompt #%d contains %s" % (name, i + 1, label))
        if findings:
            out.extend(("FAIL", f) for f in findings)
        else:
            out.append(("PASS", "%s: no drawable layout measurements/labels found" % name))
    return out


def rule_prompt_no_generation_triggers(ctx):
    out = []
    for name, prompts in ctx.prompt_sets:
        if not prompts:
            continue
        findings = []
        for i, p in enumerate(prompts):
            blob = _prompt_blob(p)
            for pattern, label in GENERATION_TRIGGER_PATTERNS:
                if pattern.search(blob):
                    findings.append("%s prompt #%d contains %s" % (name, i + 1, label))
        if findings:
            out.extend(("FAIL", f) for f in findings)
        else:
            out.append(("PASS", "%s: no physical-layout generation triggers found" % name))
    return out


def rule_text_side_right(ctx):
    out = []
    for name, prompts in ctx.prompt_sets:
        if not prompts or not _is_spread_prompt_set(name):
            continue
        sides = [_side(p) for p in prompts]
        left = sum(1 for s in sides if s == "L")
        known = [s for s in sides if s]
        if not known:
            out.append(("WARN", "%s: could not determine text-safe side" % name))
        elif left:
            out.append(("FAIL", "%s: text-safe side must be RIGHT on every spread; %d are LEFT" % (name, left)))
        else:
            out.append(("PASS", "%s: text-safe side is RIGHT on all spreads" % name))
    return out


def rule_wraparound_image_contract(ctx):
    out = []
    for name, prompts in ctx.prompt_sets:
        if not prompts or not _is_wraparound_prompt_set(name):
            continue
        findings = []
        for i, p in enumerate(prompts):
            if _is_square_cover(p):
                continue  # «Два квадрати»: a square, its own composition
            blob = _prompt_blob(p).lower()
            if "2:1" not in blob:
                findings.append("%s prompt #%d does not describe a 2:1 image" % (name, i + 1))
            if "continuous" not in blob and "uninterrupted" not in blob:
                findings.append("%s prompt #%d missing continuous/uninterrupted image language" %
                                (name, i + 1))
            if "right" not in blob:
                findings.append("%s prompt #%d missing right-area focal composition" %
                                (name, i + 1))
            if "left" not in blob:
                findings.append("%s prompt #%d missing left-area quiet continuation" %
                                (name, i + 1))
            if "upper right" not in blob and "top right" not in blob:
                findings.append("%s prompt #%d missing upper-right calm overlay area" %
                                (name, i + 1))
            if "typography" not in blob and "overlay" not in blob:
                findings.append("%s prompt #%d missing later typography/overlay space" %
                                (name, i + 1))
        if findings:
            out.extend(("FAIL", f) for f in findings)
        else:
            out.append(("PASS", "%s: wraparound image composition contract present" % name))
    return out


def rule_square_endpage_contract(ctx):
    out = []
    for name, prompts in ctx.prompt_sets:
        if not prompts or not _is_endpage_prompt_set(name):
            continue
        findings = []
        for i, p in enumerate(prompts):
            blob = _prompt_blob(p).lower()
            if "1:1" not in blob and "square" not in blob:
                findings.append("%s prompt #%d does not describe a square image" % (name, i + 1))
            if "center" not in blob and "central" not in blob:
                findings.append("%s prompt #%d missing central calm overlay area" %
                                (name, i + 1))
            if "rounded" not in blob and "round" not in blob and "oval" not in blob:
                findings.append("%s prompt #%d missing rounded/oval central area language" %
                                (name, i + 1))
            if "corner" not in blob and "edge" not in blob:
                findings.append("%s prompt #%d missing decorative corner/edge detail language" %
                                (name, i + 1))
            if "overlay" not in blob and "typography" not in blob:
                findings.append("%s prompt #%d missing later overlay/typography space" %
                                (name, i + 1))
        if findings:
            out.extend(("FAIL", f) for f in findings)
        else:
            out.append(("PASS", "%s: square end-image composition contract present" % name))
    return out


def rule_abc_square_contract(ctx):
    out = []
    for name, prompts in ctx.prompt_sets:
        if not prompts or not _is_abc_prompt_set(name):
            continue
        findings = []
        for i, p in enumerate(prompts):
            blob = _prompt_blob(p).lower()
            prompt_id = str(p.get("id", ""))
            is_letter_image = bool(re.match(r"^[a-z]-", prompt_id))
            if "1:1" not in blob and "square" not in blob:
                findings.append("%s prompt #%d does not describe a square image" % (name, i + 1))
            if "overlay" not in blob:
                findings.append("%s prompt #%d missing later overlay space" % (name, i + 1))
            if not any(word in blob for word in ("upper", "left", "center", "central")):
                findings.append("%s prompt #%d missing calm placement language for later layout" %
                                (name, i + 1))
            if is_letter_image:
                if "exactly one large" not in blob and "single uppercase" not in blob:
                    findings.append("%s prompt #%d missing one-large-letter requirement" %
                                    (name, i + 1))
                if "no visible words" not in blob and "visible words" not in blob:
                    findings.append("%s prompt #%d missing visible-word guard language" %
                                    (name, i + 1))
            elif "no visible words" not in blob and "no visible text" not in blob:
                findings.append("%s prompt #%d missing visible-text/word guard language" % (name, i + 1))
        if findings:
            out.extend(("FAIL", f) for f in findings)
        else:
            out.append(("PASS", "%s: ABC square composition contract present" % name))
    return out


RULES = [
    rule_text_structure,
    rule_blueprint_structure,
    rule_name_frequency,
    rule_sensitive_words,
    rule_lines_per_spread,
    rule_json_parses,
    rule_prompt_asset_counts,
    rule_json_aspect,
    rule_json_negatives,
    rule_no_empty_reference_fields,
    rule_reference_images_exist,
    rule_prompt_no_layout_leakage,
    rule_prompt_no_generation_triggers,
    rule_text_side_right,
    rule_wraparound_image_contract,
    rule_square_endpage_contract,
    rule_abc_square_contract,
]


def run(book_dir):
    """Every rule's findings for a book folder: [(level, message)] — the Workshop shows them on its strip."""
    ctx = Ctx(book_dir)
    out = []
    for rule in RULES:
        try:
            out.extend(rule(ctx) or [])
        except Exception as exc:  # a rule bug must never block the report
            out.append(("WARN", "%s crashed: %s" % (rule.__name__, exc)))
    return out


def main(argv):
    if len(argv) < 2:
        print("usage: python check_book.py <book-folder>")
        return 2
    book_dir = argv[1]
    if not os.path.isdir(book_dir):
        print("not a folder: %s" % book_dir)
        return 2
    print("check_book: %s\n" % book_dir)
    fails = 0
    for level, msg in run(book_dir):
        print("  [%s] %s" % (level, msg))
        if level == "FAIL":
            fails += 1
    print("\n%s - %d FAIL(s)" % ("NOT READY" if fails else "MECHANICALLY READY", fails))
    return fails


if __name__ == "__main__":
    sys.exit(main(sys.argv))
