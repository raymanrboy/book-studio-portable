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
   - fix the content, the "Where in the code" section (file + function/constant names after the link),
     and the `code:` front matter;
   - set `updated:` to today's date.
3. In addition, if it applies:
   - a new file → a line in `wiki/code-map.md` and a path in the `code:` of the closest matching page;
   - a new/changed/removed `@route` → `wiki/architecture/api-routes.md` (method, pattern as in the code,
     escape `|`);
   - an owner decision or a meaningful technical choice → an entry at the top of `wiki/decisions.md`
     (date, decision, why);
   - a new term from the owner → `wiki/glossary.md`;
   - a new "for later" idea or open question → `wiki/plans/`;
   - a new page → a link in `wiki/index.md`.
4. An entry at the top of `wiki/log.md`: `## [YYYY-MM-DD] update | what changed` and 1–5 bullet points.
5. `python app/tools/wiki_check.py` — should say "Wiki is in order." Then run the tests
   (`cd app && python -m unittest discover -s tests`).
6. In the report to the owner — one line listing which wiki pages were updated.

Format and rules — `wiki/dev/wiki-rules.md`. Don't retell the code; write *what* and *why*, and where to
look.
