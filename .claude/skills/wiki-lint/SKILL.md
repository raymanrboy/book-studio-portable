---
name: wiki-lint
description: Health-check the Book Studio wiki against the code and itself - contradictions, stale claims, gaps, orphan pages. Use when the owner asks to review the wiki or periodically before large tasks.
---

# Wiki health review

1. `python app/tools/wiki_check.py` and `--map` — mechanical problems (links, functions, routes,
   uncovered files). Fix them.
2. Read the pages in turn, together with the code they link to. Look for:
   - claims the code no longer backs up (numbers, names, behavior, "since …" dates);
   - contradictions between pages (e.g. `rules/` versus `features/`);
   - concepts mentioned in several places with no page of their own;
   - pages with no inbound links other than from `index.md`;
   - places where the description just retells the code instead of explaining *what* and *why*;
   - forward-looking text ("later", "planned", "not built", "open question") — the wiki describes the program as it is now;
     limits go to `dev/limits.md`.
3. Fix what's obvious; put anything debatable in a list of questions for the owner (in the report).
4. Suggest 1–3 new questions or sources the wiki is missing.
5. An entry at the top of `wiki/log.md`: `## [YYYY-MM-DD] lint | summary`.
6. `python app/tools/wiki_check.py` and the tests — no errors.
