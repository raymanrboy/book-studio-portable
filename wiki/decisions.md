---
title: Cross-cutting decisions
type: decision
updated: 2026-11-12
code: []
---
# Decisions

> Live choices that touch more than one area. A choice that belongs to one feature sits on that feature's page as a "Why" line. History lives in git.

## Services
- Every new book goes to Gelato; Printify is read-only from 2026-10-01 (`printify.readOnlyFrom`) — why: the owner's choice after Printify print faults ([Printify](integrations/printify.md)) (2026-09-29)
- A missing Printify token is normal and raises no warning — why: no order goes through it any more (2026-10-05)
- Gelato gets drafts only; the owner pays and places the order in Gelato — why: a wrong order costs real money ([Gelato](integrations/gelato.md)) (2026-09-17)
- Etsy stays read-only: no marking shipped, no draft listings from the program — why: the owner's choice; any change risks the shop (2026-10-14)
- A request that creates something (POST) is never retried blindly; an unknown result means "check the service" — why: a duplicate image, product or order costs money ([Server](architecture/server.md)) (2026-09-23)

## Data and safety
- Every write keeps the previous version (last 20), a daily snapshot is kept 14 days, the send journal is add-only, deletions go to the Recycle Bin or the «Скасувати» shelf — why: no single bad write may lose data ([Data safety](architecture/data-safety.md)) (2026-10-04)
- Logs are kept 7 days — why: the owner: collect them and clean weekly ([Runtime](architecture/runtime.md)) (2026-10-04)
- Preview and tests run only on made-up data and never touch the real data, clipboard, keyboard, Downloads or books — why: an audit found they could; a test once started Ollama ([Preview](dev/preview.md)) (2026-09-26)
- Only made-up buyer data goes into the repository and tests — why: a real address leaked once ([Testing](dev/testing.md)) (2026-09-17)
- The backup is the whole folder every 3 days into a password-protected 7-Zip on Google Drive, keys inside — why: a restore on any computer needs nothing else ([Backup](features/backup.md)) (2026-09-27)
- `vault.json` is locked to one Windows user (DPAPI), so a settings transfer carries the keys decrypted inside its password-protected file, never on disk in the clear; it carries no safety switches — why: a copy must not drop the owner's rules ([Settings](features/settings.md)) (2026-10-03)

## Privacy
- The text-check model runs on this PC only (Ollama on `127.0.0.1`) — why: children's names never leave the computer, and there are no limits ([Text check](features/text-check.md)) (2026-09-19)
- Pictures are made on websites with the owner's subscriptions, never through a paid image API — why: no cost per picture ([Workshop](features/workshop.md)) (2026-09-24)

## Interface
- The program is light only — why: the owner's theme ([Frontend](architecture/frontend.md)) (2026-09-30)
- Edge stays the window; no WebView2, Qt or Electron — why: same engine, nothing to gain ([Runtime](architecture/runtime.md)) (2026-10-05)
- The program is rebuilt as one native Rust program with its own window, in its own repository (`raymanrboy/book-studio-rust`, the folder `Book Studio Rust` beside this one, with its plan in `docs/migration.md`); this program stays in use and unchanged until each area passes its parity checks, on the same data in the same formats — why: the owner wants one fast standalone program, and a working shop must not stop (2026-11-12)
- A reversible action runs at once with an undo (a 2-minute shelf); a question is asked only for what cannot be taken back — why: an undo the program cannot keep is a lie ([UI principles](owner/ui-principles.md)) (2026-10-06)
- No Workshop IDE is started; «Відкрити агента» only copies the agent's words to the clipboard — why: the book agents are Claude Code skills ([Workshop](features/workshop.md)) (2026-10-16)

## Agents and process
- Claude Code only: one `CLAUDE.md`, area rules in `.claude/rules/`, book steps as skills plus the subagent `book-text-critic`, a hook `.claude/hooks/book_guard.py` for what must never be skipped; the owner's stops stay in the main conversation — why: a session carries only what its task needs, and a background agent cannot ask the owner (2026-11-11)
- Commit and push only when the owner asks, and then everything together — why: the owner's preference (2026-09-17)
- The wiki describes the present only; history is git — why: an agent must read little to answer ([Index](index.md)) (2026-11-12)
