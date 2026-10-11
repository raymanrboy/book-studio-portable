# seo/ — the shop's Etsy SEO studio

Used by the agent through the `/etsy-seo` skill (`.claude/skills/etsy-seo/SKILL.md`): a book's long title,
13 tags and description, from the book's files, this keyword database and live eRank numbers.

```
seo.py                    the database and the checks (run with ../runtime/python/python.exe)
knowledge/rules.md        what is known about Etsy search and eRank, with evidence levels and sources
knowledge/erank-browser.md  how the agent reads eRank in the browser pane (pages, costs, JS snippets)
knowledge/description-template.md   the owner's description, with the parts that change per book
knowledge/blocklist.tsv   phrases never to use, with the reason
data/                     local only (not in git): seo.sqlite, inbox/ (eRank JSON), work/ (candidate lists)
```

Nothing here talks to Etsy. eRank is read only in the browser pane where the owner is signed in.
The old `Etsy-Book-Pipeline/seo-intelligence` is an archive: its competitor listings were copied in once
(`import-legacy`, 2026-10-09).
