---
name: wiki-ingest
description: Add knowledge from the Book Studio owner (text, screenshots, documents, explanations of the business or plans) into the project wiki. Use when the owner shares information meant for the wiki.
---

# Add the owner's knowledge to the wiki

1. **Read it** carefully, screenshots too. Check it against what's already in the wiki (`wiki/index.md`)
   and in the code. The source itself is not stored in the wiki; a picture that a skill or the pipeline
   must keep using goes next to that skill or into `pipeline/knowledge/refs/`.
2. **Discuss it with the owner** briefly, in Ukrainian: the main points, what's new, where it
   contradicts the wiki or the code, what's unclear. If the owner only asked to have the information
   taken in, don't start any code changes.
3. **Put the facts where they belong**, rewriting the sentences they change (present tense, no history):
   - business, process, services → `flows/`, `rules/`, `integrations/`;
   - how he works, how things should look, books and ideas → `owner/`;
   - a choice with its reason → a "Why" line on its page, or `decisions.md` if it crosses areas;
   - limits → `dev/limits.md`; new terms → `glossary.md`.
4. A new page → one line in `wiki/index.md`; `updated:` — today's date.
5. `python app/tools/wiki_check.py` — no errors.
6. Briefly tell the owner what was recorded where.
