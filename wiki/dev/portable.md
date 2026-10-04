---
title: The portable copy
type: dev
updated: 2026-10-04
code:
  - app/studio/portable.py
  - app/tests/test_portable.py
  - app/tests/test_etsy_rule.py
  - app/tests/test_portable_move.py
  - app/tools/make_colleague_copy.py
---
# The portable copy

> A copy of Book Studio that carries every program it needs, so the folder can go to another PC. This copy lives
> in `Book Studio Portable/`; the plan by stages is `ROADMAP.md` in this repository's root. The original install is untouched. The repository alone is enough
> to build such a folder: [building a portable folder](portable-setup.md).

## Layout

`Book Studio Portable/` → `Book Studio/` (this repository) and `runtime/`: `python`, `Photoshop`, `Templates`
(the mockup templates, read-only), `Antigravity` (`app`, `data/user-data`), `Ollama` (with `models`), `Upscayl`,
`ffmpeg`.

## How the program finds them (stage 1, 03.10.2026)

`studio/portable.py`: the portable root is the folder with `runtime/` next to the repository (or the environment
variable `BOOKSTUDIO_PORTABLE`; set but empty = «not portable», which the tests use). In it `runtime()`, `antigravity()`,
`upscayl_exe()`, `ffmpeg()`, `ollama_folder()` and `env()` (ffmpeg and Ollama on `PATH`, `OLLAMA_MODELS`).
Without `runtime/` they all answer None and every place looks where it always did.

- **Saved paths** (`relocate()`): a path in the settings that contains a `runtime` folder of another place the copy was moved
  from is taken into the current `runtime/`. In the portable copy the mockups' places are `runtime/Photoshop` and
  `runtime/Templates` first (`mockups._saved_or_runtime()`); no PC-specific path is left in the code (cleaned 2026-10-03).
- **Users:** `mockups.places()`, `workshop/books.antigravity()`, `textcheck/ollama._ollama_command()` and its start,
  `workshop/upscale._candidates()`, `photos.ffmpeg()`, `settings_api._open_in_profile()`, `workshop/books.open_agent()`.
- **Left as the owner set them:** the backup folder (`G:\My Drive\…`) and the mockups' last output folder — his own
  folders, not programs.

## Launch and the start-up check (stage 2, 03.10.2026)

- **Launchers in the root** (kept in the repository's `portable/` and laid out by `setup_portable.py`; ASCII names — `cmd` does not read Cyrillic): `Start Book Studio.bat` (runtime Python,
  no window), `Start with console.bat` (errors stay on screen), `Make desktop shortcut.bat` (→ `tools/make_shortcut.py`;
  in the portable copy the shortcut is named «Book Studio Portable», the original's is left alone).
- **`portable.startup_report()`**, called by `Book Studio.pyw` before the server starts, shows one window: what is missing
  (`check()` — every program in `runtime/`, each with «what to do») and, once per computer (`first_run_notes()`,
  remembered in `data/portable-state.json`), what to log in to by hand: Antigravity's Google account, Gelato/Canva in Edge's own profile of the copy. Nothing is started and no key is read out.
- **The keys do not travel.** `vault.json` is encrypted by Windows for the one Windows user (DPAPI, `vault.py`); on another
  PC or user the keys do not open. `check()` says so (`_keys_problem()`); the way back is Settings (enter the keys again)
  or `app/tools/restore_keys.py` from the password-protected backup. Open question for the owner — a vault that opens
  with a password on any PC (ROADMAP, stage 2).
- Checked 03.10.2026: the program starts on `runtime/python` alone, with an empty environment (no Python, ffmpeg or Ollama
  on `PATH`), on made-up data.

## Antigravity, the browser and the rules file (stage 3, 03.10.2026)

- **Antigravity 2 is a plain Electron app** (no `data/` portable mode like VS Code). `portable.antigravity_launch()` starts it
  with `--user-data-dir=runtime/Antigravity/data/user-data` and a home of its own: `USERPROFILE`/`HOME` =
  `runtime/Antigravity/home`, where the agents' `.gemini` (chats, settings, its browser profile — 840 MB, a copy of the
  owner's) lives. So it does not read or write the PC's `%APPDATA%\Antigravity` or `~\.gemini`.
- **Gelato and Canva links open in Edge** (every Windows has it) with a profile of its own, `work-browser` in the data folder
  (`settings_api._open_in_profile()`), instead of Cent Browser's «Work»: a browser's saved logins are encrypted for the
  Windows user and would not travel anyway, so the 5 GB browser copy was dropped. Log in to Gelato and Canva once per PC.
  The original install still uses Cent.
- **`pipeline/AGENTS.md` is the only entry point** for book agents (the owner: «щоб будь-який агент міг юзати»); `GEMINI.md`
  is gone from the copy and the Workshop's words name `AGENTS.md`. The owner's global Antigravity rules (`~/.gemini/GEMINI.md`:
  answer in Ukrainian, no jargon, check yourself) came along inside the copied `home/.gemini`.

## The copy as a project (stage 5, 03.10.2026)

- **No git remote** (`origin` removed from this copy's `.git`): it cannot be pushed to the owner's GitHub by mistake. Local
  history only; commit when the owner asks. Everything from stages 1–5 is still uncommitted.
- `AGENTS.md` §0 tells an agent where it is; `ПРОЧИТАЙ.md` in the portable root tells the owner how to start and what to do on a
  new PC. The interface preview (`.claude/launch.json`) still runs plain `python` — on a PC without Python use
  `..\runtime\python\python.exe app/tools/dev_server.py --sample`.
- `Трафарети мастхев (копія)/` — the original's spare copy of the templates (1.5 GB, never used by the program) — was **removed from the portable
  copy on 2026-10-03** (to the Recycle Bin; every file matched `runtime/Templates`): the templates live in `runtime/Templates` there.

## A copy for someone else (stage 7, 03.10.2026)

The portable folder holds the owner's data, keys and accounts, so it is not handed over as it is. `python app/tools/make_colleague_copy.py
"<new folder>"` ([make_colleague_copy.py](../../app/tools/make_colleague_copy.py)) makes a **clean copy**:

- **In:** the program (only what git knows — tracked and new-but-not-ignored files), `app/bin` (7-Zip, cloudflared), `runtime/`
  (Python, ffmpeg, Ollama with its model, Upscayl, Antigravity's program), the launchers, a `ПРОЧИТАЙ.md` for the new user, a fresh git
  repository with one neutral commit (no history, no remote).
- **Photoshop** goes in a **stock** state: his temp files, logs and preferences left out, the portable build's own `DefaultData`
  put over the preferences (`copy_photoshop()`) — not run-tested.
- **Optional modules left out:** `runtime/Ollama` and `runtime/Upscayl` (the program offers to install them: [modules](../features/modules.md));
  Python carries only the packages `app/requirements.txt` needs (`copy_python()`), ffmpeg only `ffmpeg.exe`.
- **Out:** `app/data` (orders, customers, the vault), `.secrets.txt`, the Workshop's books, `examples/`, `wiki/raw/` (the owner's own
  words), Antigravity's user-data and home (his Google login and chats). Photoshop and the templates **are in** (the owner, 2026-10-03: the colleague bought the mockups too, and it is not
  commercial use); `--without-photoshop` / `--without-templates` leave them out.
  The owner keeps working in the portable copy and does not port the two switches to the original (2026-10-03).
- **Scrubbed:** his GitHub account, e-mail and Windows profile name in the documents (`scrub()`).
- **Starts with two personal rules off and the light theme** (seeded `settings.json`): `security.etsyKyivOnly: false`,
  `printify.readOnlyFrom: null`, `ui.theme: light`.
- **Its own rules for agents:** `AGENTS.md`, `CLAUDE.md` and `wiki/owner/working-with-owner.md` are written for the colleague (templates in
  `app/tools/colleague_docs/`, put in by `neutral_docs()`), `wiki/security.md` has the owner's personal rules cut out, links to the
  removed `wiki/raw/` are turned into plain text. The copy passes its own tests (501) and wiki check with its own Python.

Those two are the owner's own rules turned into settings (`core.etsy_kyiv_only()`, `printify.read_only_from()`): by default as before
— Etsy opens only from the Kyiv PC, Printify is read-only from 2026-10-01 — and the Settings page, the sign-in dialog and the
first-run note follow the setting. The colleague (an owner of a similar business, with his own Etsy shop, Printify and Gelato)
signs in to Etsy straight from his PC.

## Independent of the place (2026-10-03)

The owner's wish: the program is put somewhere and works in its own folders, depending as little as possible on paths and on moves between
computers and folders.

- **Everything it needs is in the folder** — Python, ffmpeg, Ollama and its models, Upscayl, Antigravity (with its own user-data and home),
  Photoshop, the templates, 7-Zip, cloudflared; its own temp files (`data/tmp/system`) and the Edge profile (`data/work-browser`).
  `runtime/` programs are found first; the system's are only a fallback.
- **Paths kept inside the data follow the folder** (`portable.rebase_paths()`, called by `main()`): the few absolute paths in `app/data/*.json`
  that point into the repository (`…\pipeline\books`, `…\app\data`, `…\wiki`) are rewritten to where the repository is now — when it differs
  from the place remembered in `portable-state.json` (`repo`). The old files go to `app/data/rebase-backup/<time>/`; logs, caches and the vault
  are not touched. Folders outside the program (his mockups' output folder, Downloads, Google Drive) are his own and stay as set.
- **What only Windows can have** (`portable.prerequisites()`): the **Microsoft Visual C++ 2015–2022 runtime (x64)** that Photoshop, Upscayl and
  Antigravity lean on (they do not carry it; Python and Ollama do). When it is missing, `Book Studio.pyw` asks «Встановити зараз — тихо?» and
  `portable.install()` runs it quietly in a visible console, Windows asking for the administrator's permission: the installer in
  `runtime/Installers/vc_redist.x64.exe` (Microsoft's, 14.44.35211, downloaded 2026-10-03 with the owner's permission, signature checked) (`/install /quiet /norestart`, works offline) or else `winget` (the owner's Windows 10 LTSC has no
  winget). With neither, the window prints the exact command and the link (`https://aka.ms/vs/17/release/vc_redist.x64.exe`).
  Microsoft Edge (the app window; the default browser is the fallback) and Google Drive for desktop (the backup) are left to the PC.

## The first-run windows (2026-10-03)

`Book Studio.pyw` shows one Windows message box before the server starts. Checked on the screen with an empty `runtime/`: a list «Немає в
теці runtime» (each program with its folder), one line «Скопіюйте ці теки…», then «Перший запуск на цьому комп'ютері — зробіть вручну» (Antigravity's
Google login, Gelato/Canva in Edge, and the Kyiv note only when that rule is on). Keys that do not open get their own paragraph with the
way out. Nothing shows when everything is in place and the computer was seen before.

## The manual for an agent

[MANUAL.md](../../MANUAL.md) at the repository root (proofread against the running program on 2026-10-03, every label and step) is a user manual written for an LLM (the person and their agent): what the
program is, the folder, the first-start checklist, the screens, every workflow (order → print, a new book, mockups and slides,
profit, backup and settings export), the rules, where things are, troubleshooting, what an agent may do, a glossary. It is neutral
(no personal rules), so it goes into the colleague copy as it is. Keep it in step with the program: when a screen or a step changes,
change it there.

## Not yet (see the ROADMAP)

The real Antigravity and Photoshop checks by the owner, the test on another PC, syncing settings between the two programs; the two
switches are in the portable copy only (not in the original).

## What the owner sees in the folder (2026-10-03)

Only `Book Studio.lnk`, `Book Studio/` and `runtime/`. The `.bat` files, `ROADMAP.md` and `ПРОЧИТАЙ.md` carry the Hidden attribute. `tools/make_shortcut.py` writes the link into the portable root and onto the desktop; a link holds an absolute path, so after moving the folder it is made again with the hidden `Make desktop shortcut.bat`.
