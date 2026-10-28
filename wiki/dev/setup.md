---
title: Setup, launch, GitHub
type: dev
updated: 2026-10-28
code:
  - app/tools/make_shortcut.py
  - app/requirements.txt
---
# Setup, launch, GitHub

## What's needed

- Windows 10/11, Microsoft Edge (or Chrome).
- Python 3.11+ (on the Wrocław PC — 3.14, `C:\Users\Roman\AppData\Local\Programs\Python\Python314`).
- Packages: `python -m pip install -r app/requirements.txt` (Pillow, img2pdf, pikepdf, cryptography, psd-tools, numpy).
- `app/bin/cloudflared.exe` — for Gelato's temporary links; **not in git**, on a new PC it has to be put
  there by hand (the official Cloudflare release).
- **ffmpeg** — cuts the start off the [photo mockups](../features/photo-mockups.md)' Omni video; on the Wrocław PC
  installed for Windows (on PATH), else `app/bin/ffmpeg.exe`.

## Launch

- The **Book Studio** shortcut on the desktop. The [Mockups](../features/mockups.md) live inside it (they need
  Photoshop CC 2019 and the templates folder). No shortcut, or the program was moved —
  `python app/tools/make_shortcut.py`.
- Won't start — `app/Запуск з консоллю.bat` (Run with console) will show the error; also
  `app/data/logs/startup-error.txt`.
- In detail — [architecture/runtime.md](../architecture/runtime.md).

## Another computer

- Code — from GitHub (see below). Data — copy `app/data`.
- Keys in `vault.json` are DPAPI-encrypted for one specific Windows user: they won't decrypt on another
  PC → enter the keys again in Settings, connect Etsy with an "access link".

## GitHub

- The private repository of **this (portable) copy**: **raymanrboy/book-studio-portable**, branch `main`, remote `origin`. (The ordinary Book Studio has its own, `raymanrboy/book-studio` — never push this copy there.)
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
  history is all in git either way (his request). Before committing, only check that no keys
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

## The portable copy

In `Book Studio Portable/` the program is `Book Studio/` and everything it runs on is `runtime/` (Python, Photoshop, the mockup
templates, ffmpeg, Antigravity, the optional modules). Start it with the `Book Studio` shortcut; the Python for commands is
`../runtime/python/python.exe`. Its GitHub repository is `raymanrboy/book-studio-portable` (private); no system Python is needed. Details — [portable](portable.md).
