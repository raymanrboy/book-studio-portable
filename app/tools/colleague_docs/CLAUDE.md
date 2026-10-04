@AGENTS.md

# Addendum for Claude Code

- **Project skills** (`.claude/skills/`):
  - `/wiki-update` — bring the wiki up to date after code changes (run at the end of every task);
  - `/wiki-ingest` — add material from the user into the wiki (text, screenshot, document);
  - `/wiki-lint` — wiki health check.
  - `/listing-slides` — change, look at and bake the six Etsy listing slides through their files (when the user
    asks in words instead of the editor).
  - `book-studio-ui-logic` — the interface rules as a checklist; **apply it before writing any UI**.
- **Interface preview**: `preview_start("book-studio-dev")` (`.claude/launch.json`, port 47890,
  made-up data; every page — the Workshop and the Mockups with a pretend Photoshop too; set the **light** theme first).
  The hidden browser pane doesn't run `requestAnimationFrame` — check the DOM and swap rAF for `setTimeout`; after
  `resize_window`, set it back to `preset: "desktop"`; finish with `preview_stop`. Details — `wiki/dev/preview.md`.
  `launch.json` runs plain `python`; with the portable Python use `..\runtime\python\python.exe app/tools/dev_server.py --sample`.
- **Shells**: in Bash, prefer absolute paths (`cd` changes the session's working folder); Cyrillic in
  Python output needs `PYTHONIOENCODING=utf-8`; tests need `PYTHONDONTWRITEBYTECODE=1`.
- **Agent memory** — personal notes only; everything about the project lives in the wiki.
