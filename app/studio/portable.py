"""The portable copy: where the programs Book Studio needs live when they travel with it.

The folder next to the repository (`<portable>/runtime/`) holds Photoshop, the mockup templates, Antigravity, Ollama,
Upscayl, ffmpeg and Python. When that folder is there (or `BOOKSTUDIO_PORTABLE` names the portable
root), `runtime()` finds each program in it; when it is not (the ordinary install), everything answers None and the
program looks where it always did.
"""
from __future__ import annotations

import os
import re
import shutil
import time
from pathlib import Path

from . import core

OLLAMA_PORT = 11435      # the portable copy's own Ollama listens here, apart from an Ollama of the PC (which has 11434)


def root() -> Path | None:
    """The portable root (the folder with `runtime/` in it), or None for the ordinary install."""
    env = os.environ.get("BOOKSTUDIO_PORTABLE")        # set but empty: «not portable» (the tests say so)
    if env == "":
        return None
    base = Path(env) if env else core.ROOT.parent.parent
    return base if (base / "runtime").is_dir() else None


def runtime(*parts: str) -> Path | None:
    """`runtime/<parts>` when it exists, else None."""
    base = root()
    if not base:
        return None
    path = base / "runtime" / Path(*parts)
    return path if path.exists() else None


def relocate(saved: str | Path | None) -> Path | None:
    """A path remembered in the settings, taken to where the copy is now when it points into a `runtime` folder of another
    place the copy was moved from (`E:\\old\\runtime\\Upscayl\\…` → this `runtime/Upscayl/…`). Any other path — and the ordinary
    install — comes back as it was."""
    if not saved:
        return None
    path = Path(saved)
    base = root()
    if base and "runtime" in path.parts:
        moved = base / "runtime" / Path(*path.parts[path.parts.index("runtime") + 1:])
        if moved.exists():
            return moved
    return path


def antigravity() -> Path | None:
    return runtime("Antigravity", "app", "Antigravity.exe")


def ollama_folder() -> Path | None:
    return runtime("Ollama")


def ollama_url() -> str | None:
    """The address of the copy's own Ollama (None for the ordinary install, which uses the setting)."""
    return f"http://127.0.0.1:{OLLAMA_PORT}" if root() else None


def upscayl_exe() -> Path | None:
    return runtime("Upscayl", "resources", "bin", "upscayl-bin.exe")


def ffmpeg() -> Path | None:
    base = runtime("ffmpeg")
    if not base:
        return None
    found = next(base.rglob("ffmpeg.exe"), None)
    return found


def antigravity_launch() -> tuple[list[str], dict[str, str]] | None:
    """How to start Antigravity so that everything of its own stays in the portable folder: its user-data folder by
    `--user-data-dir`, and a home folder of its own (`USERPROFILE`) holding `.gemini` — the agents' chats and settings."""
    exe = antigravity()
    base = runtime("Antigravity")
    if not (exe and base):
        return None
    home = base / "home"
    home.mkdir(exist_ok=True)
    data = base / "data" / "user-data"
    data.mkdir(parents=True, exist_ok=True)
    return [str(exe), f"--user-data-dir={data}"], {"USERPROFILE": str(home), "HOME": str(home)}


def env() -> dict[str, str]:
    """What a program started by Book Studio needs in its environment: ffmpeg and Ollama on PATH, Ollama's models
    in the portable folder. Empty for the ordinary install."""
    out: dict[str, str] = {}
    folders = [p.parent for p in (ffmpeg(),) if p]
    ollama = ollama_folder()
    if ollama:
        folders.append(ollama)
    if root():              # always: so that an Ollama the PC set up (its OLLAMA_MODELS, its port) is never used or written to
        out["OLLAMA_HOST"] = f"127.0.0.1:{OLLAMA_PORT}"
        out["OLLAMA_MODELS"] = str(root() / "runtime" / "Ollama" / "models")
    if folders:
        out["PATH"] = os.pathsep.join([str(f) for f in folders] + [os.environ.get("PATH", "")])
    return out


# ------------------------------------------------------------------------------------------ the start-up check

def _problem(what: str, fix: str, folder: str | None = None) -> dict:
    """`folder`: a program that belongs in `runtime/<folder>` and is not there — the report lists these together."""
    return {"what": what, "fix": fix, "folder": folder}


def check() -> list[dict]:
    """What the portable copy lacks on this PC — [{what, fix}], empty when all is in place (and for the ordinary
    install, which is not checked). Looks at files only: nothing is started, no key is read out."""
    if not root():
        return []
    problems = []
    for name, found, what in (
            ("Antigravity", antigravity(), "Antigravity (агенти книг)"),
            ("ffmpeg", ffmpeg(), "ffmpeg (відео для фото-макапів)")):
        if not found:
            problems.append(_problem(what, f"Покладіть його в теку runtime/{name}.", name))
    # Ollama (the text check) and Upscayl (upscaling) are optional modules (modules.py): not asked for here.
    from . import mockups
    places = mockups.places()
    if not mockups.find_photoshop(places["photoshop"]):
        problems.append(_problem("Photoshop (макапи)", "Покладіть портативний Photoshop у теку runtime/Photoshop.", "Photoshop"))
    if not (places["templates"].is_dir() and any(places["templates"].iterdir())):
        problems.append(_problem("трафарети макапів", "Покладіть їх у теку runtime/Templates.", "Templates"))
    problems += _keys_problem()
    return problems


def _keys_problem() -> list[dict]:
    """The keys are locked to the Windows user who saved them (DPAPI): on another PC or user they do not open."""
    from .vault import vault
    stored = [n for n in vault._load() if vault._load().get(n)]
    if stored and not any(vault.get(n) for n in stored):
        return [_problem("Ключі (Etsy, Printify, Gelato) не відкриваються на цьому комп'ютері: Windows захищає їх "
                         "для того користувача, що їх зберіг.",
                         "Відкрийте «Налаштування» й введіть ключі знову, або відновіть їх із резервної копії "
                         "(app/tools/restore_keys.py).")]
    return []


def first_run_notes() -> list[str]:
    """Things to do by hand once on a PC the copy has not run on before (a login cannot travel in a folder). Said once
    per computer: the name is remembered in `portable-state.json` in the data folder."""
    if not root():
        return []
    state_path = core.data_path("portable-state.json")
    state = core.read_json(state_path, {}) or {}
    me = os.environ.get("COMPUTERNAME", "")
    seen = list(state.get("computers") or ([state["computer"]] if state.get("computer") else []))     # a stick used on PC A, B, A: A is known
    if me in seen:
        return []
    core.write_json(state_path, {**state, "computer": me, "computers": [*seen, me][-20:]})
    return ["Antigravity: увійдіть у свій обліковий запис Google (вхід не переноситься між комп'ютерами).",
            "Edge: Gelato і Canva відкриються у власному профілі програми — увійдіть у них один раз.",
            *(["Etsy відкривайте лише на київському ПК."] if core.etsy_kyiv_only() else [])]


def startup_report() -> tuple[str, bool] | None:
    """The words for the window at start — (text, is_a_problem) — or None when there is nothing to say."""
    if not root():
        return None
    blocks = []
    problems = check()
    missing = [p for p in problems if p["folder"]]
    if missing:
        blocks.append("Немає в теці runtime:\n" + "\n".join(f"  •  {p['what']}  →  runtime/{p['folder']}" for p in missing)
                      + "\n\nСкопіюйте ці теки з комп'ютера, де вони є, — далі програма знайде їх сама.")
    for p in problems:
        if not p["folder"]:
            blocks.append(f"{p['what']}\n{p['fix']}")
    notes = first_run_notes()
    if notes:
        blocks.append("Перший запуск на цьому комп'ютері — зробіть вручну:\n" + "\n".join(f"  •  {n}" for n in notes))
    return ("\n\n".join(blocks), bool(problems)) if blocks else None


# ---------------------------------------------------------------- the folder moved: paths inside the data follow it

_SKIP_DATA = ("logs", "tmp", "cache", "window-profile", "work-browser", "import-backup", "rebase-backup", "recycle-bin", "history", "merge-backup")
_REPO_PATH = re.compile(r'([A-Za-z]:(?:\\\\[^"\\]+)+?)(?=\\\\(?:pipeline\\\\books|app\\\\data|wiki)\\\\)')   # inside JSON text


def _state_path() -> Path:
    return core.data_path("portable-state.json")


def _data_json():
    """The data's JSON files, the skipped folders never walked (the caches and browser profiles are ~90% of the files, 04.10.2026)."""
    for top, dirs, files in os.walk(core.DATA_DIR):
        if Path(top) == core.DATA_DIR:
            dirs[:] = [d for d in dirs if d not in _SKIP_DATA]
        yield from (Path(top) / f for f in files if f.lower().endswith(".json") and not f.startswith("vault"))


def rebase_paths() -> int:
    """The program lives in whatever folder it was put in; the few absolute paths it keeps in its JSON files (a slides set's
    folders, …) point into the repository folder (`…\\\\pipeline\\\\books`, `…\\\\app\\\\data`). When the repository is not where they
    say — the copy was moved, or the data came from another install — they are rewritten to where it is now. The files as they were
    go to `app/data/rebase-backup/<time>/` first. Runs when the repository folder differs from the one remembered in
    `portable-state.json` (and the first time). Returns how many files changed."""
    if not root():
        return 0
    here = str(core.ROOT.parent)
    state = core.read_json(_state_path(), {}) or {}
    if str(state.get("repo", "")).lower() == here.lower():
        return 0
    new = here.replace("\\", "\\\\")
    stamp, changed = time.strftime("%Y%m%d-%H%M%S"), 0
    for path in _data_json():
        rel = path.relative_to(core.DATA_DIR)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        old = {m for m in _REPO_PATH.findall(text) if m.lower() != new.lower()}
        if not old:
            continue
        fixed = text
        for prefix in sorted(old, key=len, reverse=True):
            fixed = fixed.replace(prefix + "\\\\", new + "\\\\")
        if fixed != text:
            save = core.data_path("rebase-backup", stamp, *rel.parts)
            save.parent.mkdir(parents=True, exist_ok=True)
            save.write_text(text, encoding="utf-8")
            path.write_text(fixed, encoding="utf-8")
            changed += 1
    core.write_json(_state_path(), {**state, "repo": here})
    if changed:
        core.log.info("Paths in %d data files follow the folder to %s", changed, here)
    return changed


# ---------------------------------------------------------------- what Windows itself must have

VCREDIST_URL = "https://aka.ms/vs/17/release/vc_redist.x64.exe"


def vcredist_present() -> bool:
    """The Microsoft Visual C++ 2015–2022 runtime (x64) that Photoshop, Upscayl and Antigravity lean on."""
    if os.name != "nt":
        return True
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64") as key:
            installed = winreg.QueryValueEx(key, "Installed")[0] == 1
            try:
                build = int(winreg.QueryValueEx(key, "Bld")[0])
            except (OSError, ValueError, TypeError):
                build = 0
            if installed and build >= 29000:            # 2019 or later: the one that has vcruntime140_1.dll (a 2015 one does not)
                return True
    except OSError:
        pass
    system = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
    return (system / "vcruntime140_1.dll").is_file() and (system / "msvcp140.dll").is_file()


def prerequisites() -> list[dict]:
    """What the program needs from Windows that cannot live in a folder, each with how to put it in quietly: an installer in
    `runtime/Installers/` (works without the internet) or `winget`. Only what a clean Windows may lack."""
    installer = runtime("Installers", "vc_redist.x64.exe")
    return [{"id": "vcredist", "label": "Microsoft Visual C++ 2015–2022 (x64)", "needed_by": "Photoshop, Upscayl, Antigravity",
             "present": vcredist_present(), "installer": str(installer) if installer else None,
             "winget": "Microsoft.VCRedist.2015+.x64", "url": VCREDIST_URL}]


def declined(item: dict) -> bool:
    """The owner said «ні» to installing this on this computer: it is not asked at every start (said again after the next move to a new PC)."""
    state = core.read_json(core.data_path("portable-state.json"), {}) or {}
    return os.environ.get("COMPUTERNAME", "") in (state.get("declined") or {}).get(item["id"], [])


def decline(item: dict) -> None:
    path = core.data_path("portable-state.json")
    state = core.read_json(path, {}) or {}
    declined_on = state.setdefault("declined", {}).setdefault(item["id"], [])
    me = os.environ.get("COMPUTERNAME", "")
    if me not in declined_on:
        declined_on.append(me)
    core.write_json(path, state)


def install_result(code: int | None) -> tuple[str, bool]:
    """What to tell after `install()`: (text, is_a_problem)."""
    if code in (0, 1638):
        return "Готово: системну програму встановлено (або вона вже була).", False
    if code in (3010, 1641):
        return "Встановлено, але Windows просить перезавантажити комп'ютер — зробіть це, коли зручно.", False
    if code is None:
        return "Немає чим встановити: завантажте її з сайту Microsoft і запустіть вручну.", True
    return f"Установка не завершилась (код {code}). Якщо ви відмовили у дозволі — нічого страшного: спробуйте ще раз або встановіть її самі.", True


def missing_prerequisites() -> list[dict]:
    return [p for p in prerequisites() if not p["present"]]


def install_command(item: dict) -> list[str] | None:
    """The quiet install of one prerequisite as a command — the bundled installer first, else winget, else None."""
    if item.get("installer"):
        return [item["installer"], "/install", "/quiet", "/norestart"]
    if shutil.which("winget"):
        return ["winget", "install", "--id", item["winget"], "-e", "--silent", "--accept-package-agreements",
                "--accept-source-agreements"]
    return None


def install(item: dict) -> int | None:
    """Runs the quiet install in a console the user can see, asking Windows for the administrator's permission (it shows its own
    prompt). Returns the exit code (0 or 3010 = done), or None when there is nothing to run it with."""
    command = install_command(item)
    if not command:
        return None
    import subprocess
    if command[0] == "winget":
        run = subprocess.run(command, creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
        return run.returncode
    args = ",".join("'" + a.replace("'", "''") + "'" for a in command[1:])
    script = (f"$p = Start-Process -FilePath '{command[0].replace(chr(39), chr(39) * 2)}' -ArgumentList {args} -Verb RunAs -Wait -PassThru; "
              "exit $p.ExitCode")
    run = subprocess.run(["powershell", "-NoProfile", "-Command", script],
                         creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
    return run.returncode
