---
paths:
  - "wiki/**"
---

# Writing the wiki

The full rules and operations: [wiki/dev/wiki-rules.md](../../wiki/dev/wiki-rules.md). The essentials:

- Every page starts with front matter (`title` in English, `type`, `updated`, `code:` — the files it describes), then
  `# Title` and a 1–3 sentence gist.
- A page says how things are **now**; history goes to `log.md`, the owner's reasons to `decisions.md` (with the date).
  Keep only the *why* of the present design when without it someone would "fix" it.
- One fact — one page; elsewhere a few words and a link.
- Code: a link to the file + function names (`name()`) and constants after it; no line numbers; no counts in prose.
- Links are plain relative Markdown; a path with spaces goes in angle brackets.
- `wiki/raw/` holds the owner's sources as they are — never change them.
- No keys, tokens, passwords or real customer data.
- `log.md`: `## [YYYY-MM-DD] kind | what happened`, newest on top. Every page is listed in `index.md`.
- `python app/tools/wiki_check.py` must pass (it also runs as a test).
