---
name: wiki-lint
description: Health-check the Book Studio wiki against the code and itself - contradictions, stale claims, gaps, orphan pages. Use when the owner asks to review the wiki or periodically before large tasks.
---

# Wiki health review

1. `python app/tools/wiki_check.py` and `--map` — mechanical problems (links, names, uncovered files,
   page size, dated history). Fix them.
2. Read the pages in turn, together with the code they link to (for many pages, hand groups of pages to
   subagents and ask for findings only). Look for:
   - claims the code no longer backs up (numbers, names, behavior, paths);
   - contradictions between pages (e.g. `rules/` versus `features/`), the same fact told in two places;
   - history that slipped in ("old", "first design", "was … now") — rewrite to the present;
   - concepts mentioned in several places with no page of their own; pages nothing links to but `index.md`;
   - text that retells the code instead of explaining *what* and *why*;
   - forward-looking text ("later", "planned", "not built") — limits go to `dev/limits.md`, plans to `owner/`.
3. Fix what's obvious; put anything debatable in a list of questions for the owner (in the report).
4. `python app/tools/wiki_check.py` and the tests — no errors.
