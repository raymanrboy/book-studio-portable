"""Replays the text-check journal through the program's current rules: what the order card would show now for
every past check, next to what it showed then, and what the owner marked «це не помилка». For calibrating
what the check shows (wiki/features/text-check.md, «Calibration»). Reads app/data; changes nothing.

  python app/tools/textcheck_replay.py          checks whose findings would change, and the totals
  python app/tools/textcheck_replay.py --all    every check

The model is not asked again: its verdicts are the ones it gave then (older journals, before 25.09.2026, keep
only the verdicts it made the program show — its dropped remarks are lost). The expected texts are filled
again from today's passports, so a passport updated since counts. The «another order's child» rule is not
replayed (it needs the orders of that day).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from studio import library  # noqa: E402
from studio import textcheck as tc  # noqa: E402


def rebuild(journal: dict) -> tuple:
    """The check as the program had it at the end: its pages, the model's answers and which spreads matched."""
    pages = journal.get("pages") or []
    count = max((p["page"] for p in pages), default=0)
    pers = {"child": "", "gifter": "", "dedication": None, "closing": None, **(journal.get("personalization") or {})}
    if pers["dedication"]:  # the box read again by today's headings («close:», «Closing», a note before them)
        dedication, closing = tc.split_dedication(pers["dedication"])
        pers["dedication"], pers["closing"] = dedication, pers["closing"] or closing
    child = tc.printed_name(pers.get("child") or "")
    try:
        texts = library.load(journal["bookId"])["text"] if journal.get("bookId") else {}
    except Exception:
        texts = {}
    placed: dict[tuple, list] = {}
    for i in journal.get("issues") or []:
        placed.setdefault((i["page"], i.get("part")), []).append(i)
    targets, answers = [], {}
    for n, p in enumerate(pages):
        t = {k: p.get(k) for k in ("page", "part", "file", "label", "key", "mode", "expected")}
        t["count"] = count
        own = (pers.get("dedication") if p["page"] == 1 else pers.get("closing")) if p["page"] in (1, count) else None
        answers[n] = _answer(p, placed.get((p["page"], p.get("part")), []))
        if own and t["mode"] == "personal" and p.get("part") is None:
            # Today the buyer's own words are found where the passport text was asked for: the model was asked
            # another question then, so its remarks are left out (it is not asked again).
            t.update(mode="loose", key=None, expected=None)
            answers[n] = {**answers[n], "verdict": "ok", "problems": []}
        if t["mode"] == "loose" and p["page"] in (1, count):
            t["own"] = own
        if t["expected"] is not None and t["key"] and texts.get(t["key"]):
            t["expected"] = tc.fill(texts[t["key"]], child, pers.get("gifter") or "") or t["expected"]
        elif t["expected"] and child != pers.get("child"):
            t["expected"] = re.sub(rf"(?<!\w){re.escape(pers['child'])}(?!\w)", lambda m: child,
                                   t["expected"])  # the name read right since («ava» → «Ava», never «lava»)
        if t["expected"] != p.get("expected") and _same_words(t["expected"] or "", answers[n].get("transcript") or ""):
            answers[n].update(verdict="ok", problems=[])  # the model spoke of a text the page no longer has to be
        targets.append(t)
    layout = journal.get("layout") or {
        "unmatched": sorted({i["page"] for i in journal.get("issues") or [] if i.get("kind") == "unmatched"}),
        "blank": [list(map(int, re.findall(r"\d+", i["label"]))) for i in journal.get("issues") or []
                  if i["text"] == "На розвороті немає тексту"]}
    layout = {"mapping": {}, **layout}
    return targets, answers, layout, {p["page"]: Path(p["file"]) for p in pages}, {**pers, "child": child}, count


def _answer(page: dict, shown: list[dict]) -> dict:
    model = page.get("model")
    if model:
        if model.get("failed"):
            return {"failed": model["failed"]}
        return {"transcript": page.get("text") or "", "verdict": model.get("verdict"),
                "problems": model.get("problems") or [], "only_punctuation": model.get("onlyPunctuation")}
    # An older journal: the verdict is read back from what the program showed of it.
    failed = next((i for i in shown if i["text"].startswith("Сторінку не вдалося перевірити")), None)
    if failed:
        return {"failed": failed["text"]}
    problems = [i["note"] for i in shown if i.get("note")] + [i["text"] for i in shown if i.get("kind") == "model"]
    error = bool(problems) or any(i.get("kind") == "diff" and i["level"] == "error" and page["mode"] == "strict"
                                  for i in shown)
    return {"transcript": page.get("text") or "", "verdict": "error" if error else "ok", "problems": problems}


def _same_words(expected: str, printed: str) -> bool:
    return all(op["expected"].casefold() == op["printed"].casefold() for op in tc.diff(expected, printed))


def replay(journal: dict) -> list[dict]:
    """What the card would show for this check with today's rules."""
    targets, answers, layout, files, pers, count = rebuild(journal)
    rules = (tc._vocabulary(pers), set())
    return tc._all_issues(targets, answers, layout, files, pers, count, rules, journal.get("bookId"))


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    every = "--all" in argv
    total = {"checks": 0, "then": 0, "now": 0, "red then": 0, "red now": 0, "marked": 0, "marked still shown": 0}
    for path in sorted(tc.CHECKS.glob("*.json")):
        journal = json.loads(path.read_text(encoding="utf-8"))
        then, now = journal.get("issues") or [], replay(journal)
        marked = {m["id"] for m in journal.get("notMistakes") or []}
        total["checks"] += 1
        total["then"] += len(then)
        total["now"] += len(now)
        total["red then"] += sum(i["level"] == "error" for i in then)
        total["red now"] += sum(i["level"] == "error" for i in now)
        total["marked"] += len(marked)
        total["marked still shown"] += sum(i["id"] in marked for i in now)
        was = {(i["label"], i["text"]) for i in then}
        new = {(i["label"], i["text"]) for i in now}
        if not every and was == new:
            continue
        print(f"\n{path.name}  {journal['personalization'].get('child')!r}")
        for i in then:
            sign = "  " if (i["label"], i["text"]) in new else "- "
            print(f"  {sign}{_row(i, marked)}")
        for i in now:
            if (i["label"], i["text"]) not in was:
                print(f"  + {_row(i, marked)}")
    print("\n" + " · ".join(f"{k}: {v}" for k, v in total.items()))
    return 0


def _row(issue: dict, marked: set) -> str:
    flag = "  [owner: not a mistake]" if issue["id"] in marked else ""
    return f"[{issue['level']:5}] {issue['label']:12} {issue['text'][:140]}{flag}"


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
