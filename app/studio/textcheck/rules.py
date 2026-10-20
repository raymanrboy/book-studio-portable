"""The program's own rules: what a page's copy and the model's verdict become in the card (findings, their
words, what is left out as punctuation), the whole book's rules, and the guard against another book's pages."""
from __future__ import annotations

import hashlib
import re
from collections import Counter

from .. import library, orders
from ..wording import META as _META, words
from .texts import COMMON, MATCH, _NAME_SLOT, _base_word, _distance, _plain, _same, diff, fill, signs_off, similarity


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
        vocab.update(p.casefold() for w in words(value) for p in w.split("-") if p)  # «Godparents-John»: the buyer's John
    return vocab


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


def _case_only(op: dict, names: set[str]) -> bool:
    """«love» for «Love», «Savior» for «savior»: the Canva template's capitals, not an order's mistake
    (25.09.2026 calibration). The child's name in small letters stays the program's own red rule."""
    return bool(op["expected"] and op["printed"] and op["expected"].casefold() == op["printed"].casefold()
                and not {w.casefold() for w in words(op["expected"])} & names)


def _buyer_intact(own: str | None, text: str) -> bool:
    """Every word of the buyer's own message is on the page, in its order — capitals and a one-letter slip
    the owner fixed aside; the template's lines around it («Dear Mia,», «With love,») do not count."""
    if not own:
        return False
    for op in diff(own, text):
        need, got = op["expected"].split(), op["printed"].split()
        if need and not (len(need) == len(got) and all(
                a.casefold() == b.casefold() or (len(a) >= 5 and _distance(a.casefold(), b.casefold()) <= 1)
                for a, b in zip(need, got))):
            return False
    return True


def _twice(text: str, own: str | None, gifter: str) -> list[str]:
    """The first or last page says a thing twice — the owner's merge of the buyer's message with the template
    (20.09.2026: «Dear Mia,» above the buyer's own «Dear Mia,»; their «Love, Anna & Mark» and the
    template's «With love, {Gifter}» both kept). Counted against what the buyer wrote: what they wrote twice
    themselves is theirs. Runs of everyday words alone («we love you») are left out."""
    printed = words(text)
    low = [w.casefold() for w in printed]
    fields = [[w.casefold() for w in words(v or "")] for v in (own, gifter)]

    def runs(ws: list[str], n: int) -> Counter:
        return Counter(tuple(ws[i:i + n]) for i in range(len(ws) - n + 1))

    out, told = [], []
    # «Від кого» signed twice, in whatever order: every one of its own words (two at least — «Your family» alone
    # meets the template's «God and your family») printed more often than the buyer's fields say it.
    names = {w for w in fields[1] if len(w) >= 3 and w not in COMMON and w not in _META}
    written = Counter(low)
    if len(names) >= 2 and all(written[w] > max(1, *(f.count(w) for f in fields)) for w in names):
        out.append("Підпис «від кого» двічі")
    allowed: Counter = Counter()
    for field in fields:
        for n in (2, 3, 4):
            allowed |= runs(field, n)  # the most times any one field says it
    for n in (4, 3, 2):
        for seq, times in runs(low, n).items():
            if (times <= max(1, allowed[seq]) or all(w in COMMON for w in seq) or set(seq) <= set(fields[1])
                    or any(set(seq) <= t for t in told)):  # the signature is the check above
                continue
            told.append(set(seq))
            at = next(i for i in range(len(low)) if tuple(low[i:i + n]) == seq)
            out.append(f"Двічі «{' '.join(printed[at:at + n])}»")
    return out


def page_issues(target: dict, answer: dict, pers: dict, vocab: set[str], others: set[str]) -> list[dict]:
    """What is wrong on one page: the program's rules, the word-by-word comparison, the model's verdict.
    Red — certain; amber — worth a look (the model saw something the comparison did not, or the other way)."""
    text, verdict = answer.get("transcript") or "", answer.get("verdict")
    problems = [str(p).strip() for p in answer.get("problems") or [] if str(p).strip()]
    expected, mode = target.get("expected"), target["mode"]
    printed = words(text)
    names = {t.casefold() for t in words(pers["child"])}
    # The page's own words are no misspelt name — but the child's name filled into it is still the name: «olivia»
    # in small letters stays the red rule (it used to fall to the comparison's amber — 25.09.2026).
    page_vocab = vocab | ({w.casefold() for w in words(expected or "")} - names)
    out, covered = [], set()
    for f in findings(printed, pers["child"], page_vocab, others):
        sure = f["kind"] in ("placeholder", "case", "name") or expected is not None
        out.append(_issue(target, "error" if sure else "warn", FINDING_TEXT[f["kind"]].format(**f), kind="rule"))
        covered.add(f["printed"])
    if expected is not None and mode == "personal":
        expected = _own_greeting(_without_wish(expected, text, pers["gifter"]), text, pers["gifter"])
    ops = None
    if expected is not None:
        ops = [op for op in diff(expected, text) if not set(op["printed"].split()) & covered and not _case_only(op, names)]
        changed = sum(len(op["expected"].split()) + len(op["printed"].split()) for op in ops)
        heavy = len(ops) > 6 or changed > 16  # another text altogether: one line, not a word-by-word list
        if heavy:
            level = "error" if verdict == "error" and mode == "strict" else "warn"
            out.append({**_issue(target, level, "Текст сторінки інший, ніж у паспорті книги", kind="diff"), "whole": True})
        for op in ops if not heavy else []:
            if mode == "strict":
                level = "error" if verdict == "error" else "warn"
            else:  # the first and last page: the owner may shape them; a lost name is still certain
                level = "error" if {w.casefold() for w in words(op["expected"])} & names else "warn"
            out.append(_issue(target, level, _say_op(op, others), kind="diff"))
    elif target["page"] in (1, target["count"]):
        if not printed:
            out.append(_issue(target, "warn", "На сторінці немає тексту"))
        out += [_issue(target, "warn", said, kind="rule") for said in _twice(text, target.get("own"), pers["gifter"])[:2]]
    if verdict == "error" and problems:
        if out:
            out[0]["note"] = " ".join(problems[:3])
        else:  # the model saw what the words alone do not show — a word cut off at the edge, say
            flagged = answer.get("only_punctuation") is True
            # Every word the page must carry is in the model's own copy (or every word of the buyer's message):
            # its «a line is missing» contradicts that copy (Rocco, 06.10.2026: the lines the owner may drop).
            intact = _buyer_intact(target.get("own"), text) or ops == []
            out += [_issue(target, "warn", p, kind="model") for p in problems[:3]
                    if not _only_punctuation(p, flagged) and not _NO_PROBLEM.search(p)
                    and not _name_part(p, pers["child"])
                    and not (_LINES.search(p) and not _LINES_SUBSTANCE.search(p))
                    and not (intact and _CLAIM.search(p) and not _SEEN.search(p))]
    return out


def _changed(expected: str, text: str) -> int:
    return sum(len(op["expected"].split()) + len(op["printed"].split()) for op in diff(expected, text))


def _without_wish(expected: str, text: str, gifter: str) -> str:
    """«Congratulations on your Baptism!» right above a buyer's whole signed message («God bless you… Love, Pop-pop
    and Nonna»): the owner drops the template's last wish then (06.10.2026). The page is compared with the text
    without it only when that fits the page better — a kept line is never «extra»."""
    if not signs_off(gifter) or len(words(gifter)) < 8 or (at := expected.rfind(gifter)) <= 0:
        return expected
    paragraphs = re.split(r"\n[ \t]*\n", expected[:at].rstrip())
    if len(paragraphs) < 2 or len(words(paragraphs[-1])) > 8:
        return expected
    shorter = "\n\n".join(paragraphs[:-1]) + "\n\n" + expected[at:]
    return shorter if _changed(shorter, text) < _changed(expected, text) else expected


def _love_line(line: str) -> bool:
    """«With love,», «Love you always,»: a short line of love ending with a comma, every word an everyday one (a typo
    in it — «Love you alwys,» — is still compared)."""
    said = [w.casefold() for w in words(line)]
    return line.endswith(",") and 1 <= len(said) <= 4 and "love" in said and all(w in COMMON for w in said)


def _own_greeting(expected: str, text: str, gifter: str) -> str:
    """«Love you always,\nNanny» where the template says «With love,\n{Gifter}»: the owner's own words of love above
    a bare «from whom» (19.10.2026 calibration — three books of three, all marked «not a mistake»). Taken only when
    both lines are short lines of love standing right above the «from whom»."""
    at = expected.rfind(gifter) if gifter else -1
    head = expected[:at].rstrip(" \t")
    if at <= 0 or not head.endswith("\n"):
        return expected
    start = head[:-1].rfind("\n") + 1
    template = head[start:-1].strip()
    first = gifter.split("\n", 1)[0].strip()
    lines = [ln.strip() for ln in text.splitlines()]
    signed = re.compile(re.escape(first) + r"(?!\w)")  # the signature, not «Mommy» for «Mom» in the body
    above = next((lines[i - 1] for i in range(len(lines) - 1, 0, -1) if signed.match(lines[i])), "")
    if not (_love_line(template) and _love_line(above)):
        return expected
    return expected[:start] + above + "\n" + expected[at:]


# Where a line breaks is the owner's: «'Amen.' на окремому рядку», «у тому ж рядку», «додаткові порожні рядки»
# (06.10.2026 calibration — four of his «not a mistake» on one book). `_LINES` alone decides when the remark
# claims nothing else — «на новому рядку після імені Sophie» names the name only to say where.
_LINES = re.compile(r"окрем\w* рядк|нов\w* рядк|тому ж рядку|одному рядку|один рядок|порожн\w* рядк|абзац|перенос|"
                    r"line break", re.I)  # «записане в один рядок разом із…» — 19.10.2026
_LINES_SUBSTANCE = re.compile(r"обріз|обірв|зрізан|за кра|злит|злип|пропущ|відсутн|зайв|замість|повтор|двічі|дублю|не вистача|бракує|"
                              r"\{|cut|missing|repeat|extra", re.I)
_PUNCTUATION = re.compile(r"лапк|ком[аиуою]\b|крапк|пробіл|розділов|пунктуац|апостроф|тире|дефіс|перенес|"
                          r"нов\w* рядк|кінці рядк|окрем\w* рядк|одному рядку|тому ж рядку|порожн\w* рядк|"
                          r"двокрапк|знак оклику|велик\S* літер|мал\S* літер|регістр|"
                          r"quote|comma|punctuation|capital|uppercase|lowercase|line break", re.I)
_SUBSTANCE = re.compile(r"обріз|обірв|зрізан|за кра|злит|злип|між(?!\s+рядк)|разом|ім'я|імені|шаблон|плейсхолдер|\{|"
                        r"пропущ|відсутн\S* слов|зайв\S* слов|повтор|двічі|дублю|cut|missing word|repeat", re.I)
# «…помилки у словах немає. Перевірка показує повну відповідність», «Текст повністю збігається» — the model's
# verdict said error anyway.
_NO_PROBLEM = re.compile(r"помил\w*[^.]{0,30}\bнема|нема\w* помил|повн\w* відповідн|(?<!не )повністю збіга|"
                         r"збігається повністю", re.I)
# The model says a word is missing or changed; on a page where the program finds every word of the buyer's
# message, that is the model «correcting» it — a Bible verse quoted the buyer's way (25.09.2026).
_CLAIM = re.compile(r"пропущ|відсутн|замість|змін|замін|має бути|не вистача|missing|absent|instead", re.I)
# A name the model quotes: 'Ava' (not the apostrophe inside «Ім'я»).
_QUOTED = re.compile(r"(?:(?<=\s)|^|(?<=\())['‘\"«“]([^'’\"»”\n]{1,60})['’\"»”](?=[\s,.;:)!?]|$)")


def _name_part(problem: str, child: str) -> bool:
    """«Ім'я вказано як 'Ava', хоча в завданні 'Ava Rose'», «'Chloe Jane Robinson', хоча … 'Chloe'»: the page
    carries the child's name shorter or fuller than Etsy's field — the owner's choice, not a slip (06.10.2026)."""
    own = {w.casefold() for w in words(child)}
    quoted = [{w.casefold() for w in words(q)} for q in _QUOTED.findall(problem)]
    return bool(own) and any(a and b and a < b and (a <= own or own <= b) and (a & own)
                             for a in quoted for b in quoted)
_SEEN = re.compile(r"повтор|двічі|обріз|обірв|за кра", re.I)  # what only the eye can tell stays


def _only_punctuation(problem: str, flagged: bool = False) -> bool:
    """«Відсутні лапки», «пробіл після коми», «FIRST великими літерами»: the words compare equal, so this is
    the page's punctuation or lettering — the owner's to shape (a name in small letters the program catches
    itself). The model says so itself (only_punctuation), so its wording need not match the words below
    (22.09.2026 audit: another model or prompt would word it differently); without that answer the wording
    is read. A cut-off or stuck word is never just punctuation, whatever the flag says. Where a line breaks
    is the owner's to shape too («St.» at the end of a line, 25.09.2026); a line said twice is not."""
    if _SUBSTANCE.search(problem):
        return False
    return flagged or bool(_PUNCTUATION.search(problem))


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


def _ordered(issues: list[dict]) -> list[dict]:
    """Findings in reading order, the certain ones before the ones only worth a look."""
    rank = {"error": 0, "warn": 1}
    return sorted(issues, key=lambda x: (x["page"] if x["page"] else -1, rank.get(x["level"], 2)))


def _all_issues(targets: list, answers: dict, layout: dict, files: dict, pers: dict, count: int,
                rules: tuple, book_id: str | None = None) -> list[dict]:
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
    strange = _strange(issues, layout["unmatched"], count)
    if _wrong_book(strange, count):
        issues = _one_alarm(issues, strange, count, _like_book(targets, answers, strange, pers, book_id))
    return _ordered(issues)


# ---------------------------------------------------------------- another book's pages (a guard for the owner)
# 21.09.2026 the owner laid out a book from the Canva template of the order's other book; the check said so in
# eleven amber rows. He asked for a guard nobody can miss (25.09.2026): one alarm, a red banner in the card.
WRONG_BOOK = hashlib.sha1(b"wrong book").hexdigest()[:12]  # one per check: «not a mistake» outlives a re-check


def _strange(issues: list[dict], unmatched: list[int], count: int) -> set[int]:
    """Story pages unlike the book's passport: no text of it found there, or another text altogether."""
    return set(unmatched) | {i["page"] for i in issues if i.get("whole") and 1 < i["page"] < count}


def _wrong_book(strange: set[int], count: int) -> bool:
    """Half the story spreads or more: a drifted passport differs in a word or a line, not in whole pages."""
    return len(strange) >= max(3, len(range(2, count, 2)) // 2)


def _one_alarm(issues: list[dict], strange: set[int], count: int, like: dict | None = None) -> list[dict]:
    """The rows of those pages give way to one alarm (the program's own name rules stay: another child's name
    is still worth its row). `like` — the library book the pages seem to come from."""
    first = min(strange)
    alarm = {"id": WRONG_BOOK, "page": first, "file": f"{first}.png", "part": None, "label": "Уся книга",
             "level": "error", "kind": "book", "text": "Сторінки не з цієї книги",
             "note": f"{len(strange)} з {len(range(2, count, 2))} розворотів не схожі на тексти її паспорта",
             "pages": sorted(strange), "like": like}
    return [i for i in issues if i["page"] not in strange or i["kind"] == "rule"] + [alarm]


def _like_book(targets: list, answers: dict, strange: set[int], pers: dict, book_id: str | None) -> dict | None:
    """Which library book the strange pages come from, when most of them start like one of its texts."""
    read = [words(answers[i].get("transcript") or "")[:12] for i, t in enumerate(targets) if t["page"] in strange]
    read = [r for r in read if len(r) >= 3]
    best, hits = None, 0
    for book in library.all_books():
        texts = [words(fill(v, pers["child"], pers["gifter"]) or v) for k, v in (book.get("text") or {}).items()
                 if k.startswith("spread") and v]
        if book.get("id") == book_id or not texts:
            continue
        found = sum(1 for r in read if max(similarity(r, t) for t in texts) >= MATCH)
        if found > hits:
            best, hits = book, found
    return orders.book_brief(best) if best and hits >= max(2, len(read) // 2) else None


def _learnable(targets: list, issues: list) -> dict[int, str]:
    """Pages whose only fault is a difference from the library text can teach the passport (the owner decides):
    the library was written apart from the Canva template, and a template that differs would be red every time.
    Never from another book's pages: they would overwrite this book's passport with that book's texts."""
    if any(i["kind"] == "book" for i in issues):
        return {}
    kinds: dict[tuple, set] = {}
    for i in issues:
        kinds.setdefault((i["page"], i.get("part")), set()).add(i["kind"])
    out = {}
    for i, t in enumerate(targets):
        k = kinds.get((t["page"], t.get("part")), set())
        if t["mode"] == "strict" and t.get("key") and "diff" in k and "rule" not in k:
            out[i] = t["key"]
    return out


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
