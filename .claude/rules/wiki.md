---
paths:
  - "wiki/**"
---

# Writing the wiki

The wiki says **what the program is now**, so an agent reads `wiki/index.md` and one or two pages, then the code. History
is git — there is no log, no archive of old decisions, no hand-kept code map or route table.

## A page

- Front matter: `title` (English), `type`, `updated` (date of the last substantive change), `code:` — the files the page
  describes (a folder ending in `/` covers every file inside). Then `# Title`, a 1–2 sentence gist, facts as bullets or
  small tables, `## Why` (only design guards someone would otherwise "fix", one line each), `## Where in the code`,
  `## Related`.
- **Present tense only.** No "since 12.10", "until …", "was … now", "old / new / legacy", "during the move", no
  "(the owner, date)" tags — `wiki_check.py` refuses dated history. When something changes, rewrite the sentence.
- **One fact — one page**; elsewhere a few words and a link.
- **At most 12 KB a page** (aim for 8); a bigger topic is split in two.
- Code: a link to the file, then the names (`name()`, `CONSTANT`) after it on the same line — each must be *defined* in
  that file (`Class.method()` in the class's file; another dotted `module.func()` only has to be called there). No line
  numbers, no counts in prose.
- File names Latin and hyphenated; links plain relative Markdown, a path with spaces in angle brackets.
- Every page is linked once from `index.md` (one line: what it is for).
- UTF-8 without BOM, LF line ends. No keys, tokens, passwords or real customer data.

## Where things go

- A choice that touches one feature → a "Why" line on that feature's page. A choice across areas → one line in
  `wiki/decisions.md` (`- decision — why: reason (YYYY-MM-DD)`); a superseded line is replaced, never kept.
- A word the owner uses → `wiki/glossary.md` (word → page). A known limit → `wiki/dev/limits.md`.
- A file or function → `python app/tools/wiki_check.py --map`; a route → `--routes` (printed from the code).
- A source the owner gives (text, screenshot): read it, talk the main points through with him, spread the facts over the
  pages; the source itself is not stored in the wiki.

## Checks

`python app/tools/wiki_check.py` (also a test) must pass: front matter, links, names, index, every code file covered,
page size, no history. It does not check that the prose is true — the `wiki-lint` skill does.
