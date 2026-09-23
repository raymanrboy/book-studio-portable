---
name: wiki-ingest
description: Add knowledge from the Book Studio owner (text, screenshots, documents, explanations of the business or plans) into the project wiki. Use when the owner shares information meant for the wiki.
---

# Add the owner's knowledge to the wiki

1. **Save the source**, if it's a file or a long piece of text: `wiki/raw/YYYY-MM-DD-what-its-about.ext`
   (no keys, passwords, or real buyer data). Files in `raw/` are never modified afterward.
2. **Read it** carefully. Look over any screenshots. Check it against what's already in the wiki
   (`wiki/index.md`) and in the code.
3. **Discuss it with the owner** briefly, in Ukrainian: the main points, what's new, where it
   contradicts the wiki or the code, what's unclear. If the owner only asked to have the information
   taken in, don't start any code changes.
4. **Spread it across pages** (often 5–15):
   - facts about the business and process → `overview.md`, `flows/`, `rules/`, `integrations/`;
   - preferences about how to work and how things should look → `owner/`;
   - decisions → `decisions.md` (date, decision, why);
   - ideas for later → `plans/roadmap.md`; unresolved questions → `plans/open-questions.md`;
   - new terms → `glossary.md`.
   Don't silently overwrite a contradiction with what's already there: update the page and note what
   changed and from which source.
5. New pages go into `wiki/index.md`; `updated:` in the front matter — today's date.
6. An entry at the top of `wiki/log.md`: `## [YYYY-MM-DD] ingest | source name` + which pages changed.
7. `python app/tools/wiki_check.py` — no errors.
8. Briefly tell the owner what was recorded where.
