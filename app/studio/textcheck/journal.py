"""The journal of every check (data/logs/checks/) and the owner's «це не помилка» marks in it."""
from __future__ import annotations

import re
import threading
import time

from .. import core


CHECKS = core.data_path("logs", "checks")
KEEP = 400


def _journal(receipt_id: str, result: dict, pers: dict, pick: int = 0, answers: dict | None = None,
             layout: dict | None = None) -> str | None:
    """Every check, with what the model read — to see later why something was (not) flagged. Local only.
    The book number is in the name: two books of one order can finish within the same second. Each page also
    keeps the model's own verdict, so a later calibration can replay what the program would show now
    (app/tools/textcheck_replay.py). Returns the file's name: the owner's «not a mistake» is written there."""
    pages = result.get("pages") or []
    if answers:
        pages = [{**p, "model": _raw(answers.get(i) or {})} for i, p in enumerate(pages)]
    try:
        CHECKS.mkdir(parents=True, exist_ok=True)
        path = CHECKS / f"{time.strftime('%Y-%m-%d_%H%M%S')}_{receipt_id}-{pick + 1}.json"
        core.write_json(path, {"receiptId": receipt_id, "book": pick + 1, "at": core.now_iso(),
                               "personalization": pers, **result, "pages": pages,
                               "layout": {k: (layout or {}).get(k) or [] for k in ("unmatched", "blank")}}, backup=False)
        for old in sorted(CHECKS.glob("*.json"))[:-KEEP]:
            old.unlink(missing_ok=True)
        return path.name
    except Exception:
        core.log.exception("Text check journal not written")
        return None


def _raw(answer: dict) -> dict:
    """The model's own verdict on a page, as it answered (before the program chose what to show)."""
    if answer.get("failed"):
        return {"failed": answer["failed"]}
    return {"verdict": answer.get("verdict"), "problems": list(answer.get("problems") or []),
            "onlyPunctuation": answer.get("only_punctuation")}


_JOURNAL_NAME = re.compile(r"\d{4}-\d{2}-\d{2}_\d{6}_\d{5,20}-\d{1,3}\.json")
_journal_lock = threading.Lock()


def mark(journal: str, issue_id: str) -> bool:
    """«Це не помилка»: the owner's own verdict goes into that check's journal, so the next calibration of what
    is shown is made on his answers rather than on guesses (25.09.2026). False when there is no such finding."""
    if not _JOURNAL_NAME.fullmatch(journal or "") or not re.fullmatch(r"[0-9a-f]{12}", issue_id or ""):
        return False
    path = CHECKS / journal
    with _journal_lock:
        data = core.read_json(path)
        issue = next((i for i in (data or {}).get("issues") or [] if i.get("id") == issue_id), None)
        if not issue:
            return False
        marks = data.setdefault("notMistakes", [])
        if not any(m.get("id") == issue_id for m in marks):
            marks.append({"id": issue_id, "text": issue.get("text"), "label": issue.get("label"), "at": core.now_iso()})
            core.write_json(path, data, backup=False)
    return True
