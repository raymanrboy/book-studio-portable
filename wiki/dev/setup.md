---
title: Setup, launch, GitHub
type: dev
updated: 2026-09-24
code:
  - app/tools/make_shortcut.py
  - app/requirements.txt
---
# Setup, launch, GitHub

## What's needed

- Windows 10/11, Microsoft Edge (or Chrome).
- Python 3.11+ (on the Wrocław PC — 3.14, `C:\Users\Roman\AppData\Local\Programs\Python\Python314`).
- Packages: `python -m pip install -r app/requirements.txt` (Pillow, img2pdf, cryptography).
- `app/bin/cloudflared.exe` — for Gelato's temporary links; **not in git**, on a new PC it has to be put
  there by hand (the official Cloudflare release).

## Launch

- The **Book Studio** shortcut on the desktop. The [Mockups](../features/mockups.md) live inside it since
  2026-09-24 (the Listings mode; they need Photoshop CC 2019 and the templates folder) — the old **Мокапи**
  shortcut points at a removed file, the owner deletes it. No shortcut, or the program was moved —
  `python app/tools/make_shortcut.py`.
- Won't start — `app/Запуск з консоллю.bat` (Run with console) will show the error; also
  `app/data/logs/startup-error.txt`.
- In detail — [architecture/runtime.md](../architecture/runtime.md).

## Another computer

- Code — from GitHub (see below). Data — copy `app/data`.
- Keys in `vault.json` are DPAPI-encrypted for one specific Windows user: they won't decrypt on another
  PC → enter the keys again in Settings, connect Etsy with an "access link".
- **After the 2026-09-17 move** (the code moved into `app/`): in the old copy of the project, move
  `data/` and `bin/` into `app/` and recreate the shortcut.

## GitHub

- The private repository **raymanrboy/book-studio**, branch `main`, remote `origin`.
- The GitHub CLI on the Wrocław PC was unpacked without an installer and **is not on PATH**:
  `C:\Users\Roman\AppData\Local\Programs\GitHubCLI\bin\gh.exe` (sign-in — `raymanrboy`).
- Git isn't configured globally for gh; push from Git Bash:
  ```
  git -c credential.helper= -c "credential.helper=!'/c/Users/Roman/AppData/Local/Programs/GitHubCLI/bin/gh.exe' auth git-credential" push
  ```
  (without this, a Git Credential Manager window opens).
- Commit and push — **only when the owner asks.** Commit messages — in English.
- **When he asks — commit everything in the working folder together** (including other sessions'
  changes), without splitting into "mine / someone else's": it's simpler for the owner, and the version
  history is all in git either way (his request, 2026-09-17). Before committing, only check that no keys
  or real customer data get in.
- `app/data/`, `app/bin/`, `__pycache__`, `.obsidian/`, and local Claude Code settings never go into the
  repository.

## Obsidian (optional)

The wiki is plain Markdown files. Opening the `wiki` folder as an Obsidian vault makes the links between
pages and the graph work; Obsidian doesn't open links to code (`../app/...`) — those are for agents.

## Where in the code

- [app/tools/make_shortcut.py](../../app/tools/make_shortcut.py) — `main()`
- [app/studio/desktop.py](../../app/studio/desktop.py) — `find_browser()`
- [app/studio/tunnel.py](../../app/studio/tunnel.py) — `CLOUDFLARED`

## Related

- [Launch](../architecture/runtime.md) · [Tests](testing.md) · [Data](../architecture/data.md)
