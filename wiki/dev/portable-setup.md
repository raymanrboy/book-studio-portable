---
title: Building a portable folder from the repository
type: dev
updated: 2026-10-04
code:
  - app/tools/setup_portable.py
  - app/tests/test_setup_portable.py
  - portable/Start Book Studio.bat
  - portable/Start with console.bat
  - portable/Make desktop shortcut.bat
  - portable/ПРОЧИТАЙ.md
  - ROADMAP.md
---
# Building a portable folder from the repository

> The repository (`raymanrboy/book-studio-portable`, the `Book Studio/` folder) holds **everything of the program**: the code, the
> wiki, the launchers (`portable/`), the plan (`ROADMAP.md`) and the notes for people and agents. It does not hold what the program
> *runs on* (`runtime/`: too big, and some of it is licensed) or the owner's data (`app/data`, the Workshop's books, the keys).
> With a clone and the steps below a working portable folder can be built on any Windows PC.

## The folder

```
Book Studio Portable/          (any name, any place — also a USB drive)
  Book Studio/                 ← this repository (git clone)
  runtime/                     ← the programs it runs on (below)
  Start Book Studio.bat        ← the launchers and ПРОЧИТАЙ.md, laid out from the repository's portable/
  Start with console.bat
  Make desktop shortcut.bat
  ПРОЧИТАЙ.md
```

## Steps

1. `git clone https://github.com/raymanrboy/book-studio-portable "Book Studio"` into a new folder (the folder's name is free,
   the clone's must be `Book Studio`).
2. Python 3.14 (x64) from python.org installed on this PC **only to start the build** (the portable folder carries its own).
   From the `Book Studio` folder: `python app/tools/setup_portable.py --python --shortcut`
   — it lays out the launchers and an empty `runtime/` (`runtime/README.txt` says what goes where), copies this Python into
   `runtime/python` and installs `app/requirements.txt` there (the one step that uses the internet: pip), makes the shortcut.
   Run again later: it only refreshes the launchers and says what `runtime/` still lacks.
3. Put into `runtime/` what the script cannot: **ffmpeg** (a Windows build, `ffmpeg.exe` anywhere inside `runtime/ffmpeg`),
   **Photoshop** and **Templates** (the owner's own portable Photoshop and the mockup templates), **Antigravity**
   (`runtime/Antigravity/app/Antigravity.exe`), and optionally `Installers/vc_redist.x64.exe`.
4. Start it (`Book Studio.lnk`). The window at the start lists what is still missing and what to log in to by hand.
   The text check and the upscaling are installed from Settings → «Модулі» (the program downloads and checks them itself).

## What does not come with a clone

| What | Why | How it is restored |
|---|---|---|
| `runtime/` | size, licences | steps 2–3; the program names what is missing |
| `app/data/` (orders, books, settings) | the owner's data | copy the folder, or start empty |
| The keys (`vault.json`) | encrypted by Windows for one Windows user (DPAPI) | enter them again, or Settings → «Перенесення налаштувань» / the backup ([settings transfer](../features/settings-transfer.md)) |
| `pipeline/books/` | gigabytes of pictures | in the backup |
| `app/bin/` (7-Zip, cloudflared) | downloaded helpers | `7za.exe` into `app/bin` (the backup and the settings file need it); cloudflared is fetched by the program for Gelato's temporary link |

## The plan and the launchers live in the repository

- `ROADMAP.md` (repository root) is the plan by stages and the list of what is not yet checked. Take one stage per session.
- `portable/` is the canonical copy of the launchers and of `ПРОЧИТАЙ.md`; the files in the portable root are copies made by
  `setup_portable.py` (a launcher is refreshed, `ПРОЧИТАЙ.md` is written only when missing). Change them here, then run the script.
- The colleague build ([the portable copy](portable.md)) takes the launchers from `portable/` and writes its own `ПРОЧИТАЙ.md`;
  `ROADMAP.md` stays out of it.

## Where in the code

- [app/tools/setup_portable.py](../../app/tools/setup_portable.py) — `layout()`, `copy_python()`, `install_packages()`, `missing()`, `main()`
- [app/tests/test_setup_portable.py](../../app/tests/test_setup_portable.py) — the layout, a second run, what is missing, the Python copy
- [portable/](../../portable/Start%20Book%20Studio.bat) — the launchers and the note for people
- [ROADMAP.md](../../ROADMAP.md) — the plan

## Related

- [The portable copy](portable.md) — how the program finds `runtime/`, the start-up check, the modules, the colleague build
- [Setup](setup.md) — Git and GitHub for this repository
