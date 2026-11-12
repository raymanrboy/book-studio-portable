---
name: wiki-update
description: Bring the Book Studio wiki up to date after code changes. Use at the end of every task that changed files in app/, or when the wiki check or test_wiki fails.
---

# Update the wiki after code changes

1. Look at what changed: `python app/tools/wiki_check.py --changed` (from the repo root,
   `PYTHONIOENCODING=utf-8`). It lists the wiki pages that describe the changed files, and any files
   with no page describing them.
2. For each page in the list:
   - re-read it and the changed code;
   - **rewrite** what changed so the page says how things are now — never add "since …" or "was … now";
   - fix the "Where in the code" section (file + function/constant names after the link) and `code:`;
   - set `updated:` to today's date.
3. In addition, if it applies:
   - a new file → its path in the `code:` of the closest matching page;
   - a new or changed choice of the owner's → a "Why" line on its page, or one line in `wiki/decisions.md`
     if it crosses areas (replace a line it supersedes);
   - a new term from the owner → `wiki/glossary.md`; a new known limit → `wiki/dev/limits.md`;
   - a new page → one line in `wiki/index.md`. A page over 12 KB → split it.
   Routes and the code map are printed by `wiki_check.py --routes` / `--map`; nothing to write for them.
4. `python app/tools/wiki_check.py` — should say "Wiki is in order." Then run the tests
   (`cd app && python -m unittest discover -s tests`).
5. In the report to the owner — one line listing which wiki pages were updated.

Rules — `.claude/rules/wiki.md`. Don't retell the code; write *what* and *why*, and where to look.
