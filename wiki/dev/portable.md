---
title: The portable copy
type: dev
updated: 2026-11-12
code:
  - app/studio/portable.py
  - app/tools/setup_portable.py
  - app/tools/make_colleague_copy.py
  - app/tools/make_shortcut.py
  - app/tests/test_portable.py
  - app/tests/test_etsy_rule.py
  - app/tests/test_portable_move.py
  - app/tests/test_setup_portable.py
  - portable/Start Book Studio.bat
  - portable/Start with console.bat
  - portable/Make desktop shortcut.bat
  - portable/ПРОЧИТАЙ.md
---
# The portable copy

> Book Studio in a folder that carries every program it needs, so it can go to another PC or a USB drive. The repository holds all of the program (code, wiki, launchers, notes); it does not hold what the program runs on (`runtime/`) or the owner's data. Build, behaviour, git and the colleague's copy are on this page.

## The folder
```
Book Studio Portable/        any name, any place
  Book Studio/               the repository (git clone; the clone's name must be Book Studio)
  runtime/                   python, Photoshop, Templates (read-only), Ollama (+models), Upscayl, ffmpeg, Installers
  Book Studio.lnk            made at the first start; the launchers and ПРОЧИТАЙ.md are then hidden
```
The owner sees only `Book Studio.lnk`, `Book Studio/` and `runtime/`. A link holds an absolute path, so after moving the folder it is made again with the hidden `Make desktop shortcut.bat` (`make_shortcut.py`, which also tidies the launchers).

## Build from a clone
1. `git clone https://github.com/raymanrboy/book-studio-portable "Book Studio"` into a new folder.
2. A system Python 3.14 (x64) is needed **only for this build**. From `Book Studio`: `python app/tools/setup_portable.py --python --shortcut`. It lays out the launchers and an empty `runtime/` (`runtime/README.txt` says what goes where), copies that Python into `runtime/python`, installs `app/requirements.txt` there (the one step that uses the internet) and makes the shortcut. Run again, it only refreshes the launchers and lists what `runtime/` still lacks.
3. Put into `runtime/` what the script cannot: `ffmpeg` (`ffmpeg.exe` anywhere inside `runtime/ffmpeg`), `Photoshop` and `Templates`, and optionally `Installers/vc_redist.x64.exe`.
4. First start with `Start Book Studio.bat`; afterwards the shortcut. A window lists what is missing and what to sign in to by hand. The text check and upscaling are installed from Settings → «Модулі» ([modules](../features/modules.md)).

| Not in a clone | Why | How it comes back |
|---|---|---|
| `runtime/` | size, licences | steps 2–3; the program names what is missing |
| `app/data/` | the owner's data | copy the folder, or start empty |
| Keys (`vault.json`) | encrypted by Windows for one Windows user (DPAPI, `vault.py`) | enter them again; Settings → «Перенесення налаштувань»; the backup; `app/tools/restore_keys.py` ([settings](../features/settings.md)) |
| `pipeline/books/` | gigabytes of pictures | the backup |
| `app/bin/` | helpers | `7za.exe` (backup, settings file) and `cloudflared.exe` (Gelato's temporary link) are put there **by hand**; the program never downloads them |

`portable/` in the repository is the canonical copy of the launchers and `ПРОЧИТАЙ.md`: change them there, then run the script (a launcher is refreshed, `ПРОЧИТАЙ.md` only when missing). Launcher names are ASCII because `cmd` does not read Cyrillic.

## How the program finds `runtime/`
- The portable root is the folder with `runtime/` next to the repository, or the variable `BOOKSTUDIO_PORTABLE` (set but empty = "not portable", which the tests use). `portable.runtime()`, `upscayl_exe()`, `ffmpeg()`, `ollama_folder()` and `env()` (ffmpeg and Ollama on `PATH`, `OLLAMA_MODELS`, `OLLAMA_HOST`) answer from it; without `runtime/` they answer `None` and every place looks where it always did. `runtime/` programs come first, the system's are a fallback.
- The portable Ollama listens on `OLLAMA_PORT` (11435), apart from an Ollama of the PC, with its models in `runtime/Ollama/models`.
- **Saved paths:** a settings path that contains a `runtime` folder of the place the copy came from is taken into the current `runtime/` (`relocate()`). Users: `mockups.places()`, `textcheck/ollama._ollama_command()`, `workshop/upscale._candidates()`, `photos.ffmpeg()`, `settings_api._open_in_profile()`, `workshop/books.open_agent()`. The backup folder and the mockups' output folder are the owner's own and stay as set.
- **Paths inside the data follow the folder:** `rebase_paths()` (called by `main()`) rewrites the few absolute paths in `app/data/*.json` that point into the repository (`pipeline\books`, `app\data`, `wiki`) when the repository is not where `portable-state.json` (`repo`) remembers. The old files go to `app/data/rebase-backup/<time>/`; logs, caches and the vault are not touched.
- **Windows-only prerequisite** (`prerequisites()`): the Microsoft Visual C++ 2015–2022 x64 runtime, which Photoshop and Upscayl lean on. When it is missing, `Book Studio.pyw` asks «Встановити зараз — тихо?» and `install()` runs `runtime/Installers/vc_redist.x64.exe` quietly (signature checked, Windows asks for administrator permission), else `winget`; with neither the window prints the command and `VCREDIST_URL`. Edge (the app window) and Google Drive for desktop (the backup) are left to the PC.

## Start-up check
`startup_report()`, called by `Book Studio.pyw` before the server starts, shows one Windows message box: what is missing in `runtime/` (`check()`, each item with what to do) and, once per computer (`first_run_notes()`, remembered in `data/portable-state.json`), what to sign in to by hand — Gelato and Canva in Edge's own profile of the copy. Keys that do not open get their own paragraph (`_keys_problem()`). Nothing is started and no key is read out. Nothing shows when everything is in place on a known computer.

## The browser
Gelato and Canva links open in Edge with a profile of its own, `work-browser` in the data folder (`settings_api._open_in_profile()`): saved logins are encrypted per Windows user and would not travel anyway. Sign in once per PC. Edge starts with `--restore-last-session`, because it drops session cookies on exit otherwise; a running Edge just adds the tab. **The Canva extension is loaded into this profile once by hand** (`edge://extensions` → developer mode → load unpacked → `Book Studio\canva-extension`); Edge 155 ignores `--load-extension`.

## Git
- The repository is private: `raymanrboy/book-studio-portable`, remote `origin`. The owner's own work goes to branch `BookStudio-R`; `main` is the colleague's line, and nothing is merged into it or pushed to it without asking which changes go there. The original install has its own repository, `raymanrboy/book-studio`: never push this copy there.
- Commit and push **only when the owner asks**, then everything in the working folder together, without splitting by session or branch; messages in English. Before committing, check that no keys or real customer data get in. `app/data/`, `app/bin/`, `__pycache__`, `.obsidian/` and local Claude Code settings never go into git.
- The GitHub CLI is not on `PATH`: `C:\Users\Roman\AppData\Local\Programs\GitHubCLI\bin\gh.exe` (signed in as `raymanrboy`). Git is not configured globally for it, so push from Git Bash with:
  ```
  git -c credential.helper= -c "credential.helper=!'/c/Users/Roman/AppData/Local/Programs/GitHubCLI/bin/gh.exe' auth git-credential" push
  ```
  (without this a Git Credential Manager window opens).

## A copy for a colleague
The portable folder holds the owner's data, keys and accounts, so a colleague gets a **clean copy**: `python app/tools/make_colleague_copy.py "<new folder>"` ([make_colleague_copy.py](../../app/tools/make_colleague_copy.py)).
- **In:** the program (only what git knows), `app/bin`, `runtime/` (Python with only the packages `app/requirements.txt` needs — `copy_python()`; `ffmpeg.exe` alone; Photoshop in a stock state — `copy_photoshop()`; the templates), the launchers, a `ПРОЧИТАЙ.md` for the new user, a fresh repository with one neutral commit. `runtime/Ollama` and `runtime/Upscayl` are left out (the program offers them as modules) unless `--with-ollama` / `--with-upscayl`; `--without-photoshop` / `--without-templates` leave those out.
- **Out:** `app/data`, `.secrets.txt`, the Workshop's books, `examples/`, the owner's plans and sources, the personal rules cut out of [security](../security.md).
- **Scrubbed:** his GitHub account, e-mail and Windows profile name in the documents (`scrub()`); his own docs are replaced by neutral ones for the colleague (`neutral_docs()`, `without_owner_plans()`), including `AGENTS.md`.
- **Seeded settings** switch the owner's two personal rules off: `security.etsyKyivOnly: false` and `printify.readOnlyFrom: null` (the colleague signs in to Etsy from his own PC and can still send to Printify — [Printify](../integrations/printify.md)).
- The copy passes its own tests and wiki check with its own Python. [MANUAL.md](../../MANUAL.md) is neutral and goes in as it is; keep it in step with the program.

## Where in the code
- [app/studio/portable.py](../../app/studio/portable.py) — `runtime()`, `relocate()`, `check()`, `startup_report()`, `rebase_paths()`
- [app/tools/setup_portable.py](../../app/tools/setup_portable.py) — `layout()`, `copy_python()`, `install_packages()`, `missing()`
- [app/tools/make_colleague_copy.py](../../app/tools/make_colleague_copy.py) — `copy_python()`, `copy_photoshop()`, `scrub()`, `neutral_docs()`
- [app/tools/make_shortcut.py](../../app/tools/make_shortcut.py) — `tidy()`, `main()`

## Related
- [Runtime](../architecture/runtime.md) · [Settings](../features/settings.md) · [Backup](../features/backup.md) · [Preview](preview.md) · [Limits](limits.md)
