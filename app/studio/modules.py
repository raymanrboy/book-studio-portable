"""Optional modules: the heavy parts that are not in the program until the user asks for them.

Two of them, the owner's idea (2026-10-03, «як апгрейди в іграх»): the **text check** (Ollama + a model, ≈ 9 GB) and **upscaling**
(Upscayl's engine and one model). By default the portable folder has neither; the interface offers them where they would be used
(the Workshop's upscale switch, the order card's proofing, Settings → «Модулі»), and the program installs them itself:

- **from the internet** — the official release files, downloaded into `data/tmp/modules/` with progress, checked, unpacked into
  `runtime/<folder>/` (no installer, no administrator's rights); the text check then pulls its model through Ollama's own API;
- **from a file** — a ZIP the user points to (a module package made on another PC), for a PC without the internet.

A module is *installed* when its files are in `runtime/` (an Ollama or Upscayl the PC already has also counts). Removing one deletes
its folder (the models of the text check included) — the user's books and settings are never touched.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import threading
import time
import urllib.request
import zipfile
from pathlib import Path

from . import core, desktop, portable
from .jobs import Job, JobError, jobs
from .server import ApiError, Request, route

CHUNK = 1 << 20
TIMEOUT = 30

# What each module is and where its files come from. `zips`: (url, size in MB, sha256 or None, folder inside runtime/ to unpack to).
MODULES: dict[str, dict] = {
    "textcheck": {
        "title": "Розумна вичитка тексту",
        "about": "Місцева модель читає сторінки замовлення й звіряє їх із паспортом книги. Працює без інтернету, на відеокарті цього ПК.",
        "size": "≈ 9 ГБ",
        "folder": "Ollama",
        "needs": "Потрібна відеокарта. Перше завантаження — довге.",
    },
    "upscale": {
        "title": "Апскейл картинок ×2",
        "about": "Збільшує картинки Майстерні рушієм Upscayl (одна модель). Працює на відеокарті цього ПК.",
        "size": "≈ 40 МБ",
        "folder": "Upscayl",
        "needs": "Потрібна відеокарта з підтримкою Vulkan.",
    },
}

_lock = threading.Lock()


# ---------------------------------------------------------------- what is installed

def runtime_dir() -> Path | None:
    base = portable.root()
    return base / "runtime" if base else None


def installed(module_id: str) -> bool:
    if module_id == "textcheck" and portable.root():      # the portable copy: its own Ollama with its own model, nothing else counts
        folder = portable.ollama_folder()
        return bool(folder and (folder / "ollama.exe").is_file()) and _model_present()
    if module_id == "textcheck":
        from .textcheck import ollama
        state = ollama.status()
        if state["running"]:
            return bool(state["installed"])          # an Ollama that answers with the model counts, this PC's own too
        return bool(ollama._ollama_command()) and _model_present()
    if module_id == "upscale":
        from .workshop import upscale
        return upscale.available()
    return False


def _model_present() -> bool:
    """The model's manifest is on disk (when Ollama is the one in `runtime/`; a system Ollama is trusted to have it)."""
    from .textcheck import ollama
    models = (portable.ollama_folder() / "models") if portable.ollama_folder() else None
    if not models:
        return True
    model = ollama._settings()["model"]
    name, _, tag = model.partition(":")
    return any((models / "manifests").glob(f"*/*/{name}/{tag or 'latest'}"))


def listing() -> list[dict]:
    out = []
    for module_id, m in MODULES.items():
        running = _running_job(module_id)
        out.append({"id": module_id, "title": m["title"], "about": m["about"], "size": m["size"], "needs": m["needs"],
                    "installed": installed(module_id), "jobId": running.id if running else None,
                    "canInstall": runtime_dir() is not None})
    return out


def _running_job(module_id: str) -> Job | None:
    job = jobs.running(f"module-{module_id}")
    return job if job and job.status == "running" else None


# ---------------------------------------------------------------- getting the files

def download(url: str, dest: Path, job: Job, step: str, sha256: str | None = None) -> None:
    """Streams a file to `dest` (as `.part`, renamed when whole), reporting the percent; checks the hash when it is known."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    digest = hashlib.sha256()
    request = urllib.request.Request(url, headers={"User-Agent": "BookStudio"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response, open(part, "wb") as out:
            total = int(response.headers.get("Content-Length") or 0)
            got = 0
            while chunk := response.read(CHUNK):
                out.write(chunk)
                digest.update(chunk)
                got += len(chunk)
                if total:
                    job.progress(step, 100 * got / total, f"{got >> 20} з {total >> 20} МБ")
    except OSError as err:
        part.unlink(missing_ok=True)
        raise JobError(f"Не вдалося завантажити {url.rsplit('/', 1)[-1]}: {err}") from err
    if sha256 and digest.hexdigest().lower() != sha256.lower():
        part.unlink(missing_ok=True)
        raise JobError("Завантажений файл не збігся з контрольною сумою — не встановлюю.")
    os.replace(part, dest)


def unpack(archive: Path, into: Path, job: Job | None = None, step: str = "Розпаковую…", only: str | None = None) -> int:
    """Unpacks a ZIP into `into`; refuses a name that would land outside it, and (with `only`) one outside the module's own
    folder — a package made by hand must not replace `python/` or `Photoshop/` in `runtime/`. Returns the file count."""
    into.mkdir(parents=True, exist_ok=True)
    root = into.resolve()
    with zipfile.ZipFile(archive) as z:
        names = z.infolist()
        if only and any(not info.filename.replace("\\", "/").startswith(only + "/") for info in names):
            raise JobError(f"У файлі модуля має бути лише тека «{only}» — не розпаковую.")
        for n, info in enumerate(names, 1):
            target = (into / info.filename).resolve()
            if root not in target.parents and target != root:
                raise JobError("У файлі модуля є небезпечний шлях — не розпаковую.")
            z.extract(info, into)
            if job and n % 50 == 0:
                job.progress(step, 100 * n / len(names))
    return len(names)


# ---------------------------------------------------------------- the install of each module

def _scratch() -> Path:
    path = core.data_path("tmp", "modules")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _install_textcheck(job: Job, package: Path | None) -> None:
    from .textcheck import ollama
    base = runtime_dir()
    folder = base / "Ollama"
    mark = folder / ".installing"                      # present while the unpacking is not finished: a cut-short one is redone
    if package:
        job.progress("Розпаковую модуль…", 0)
        unpack(package, base, only="Ollama")
    elif mark.exists() or not (folder / "ollama.exe").is_file():
        zips = OLLAMA_ZIPS + ([OLLAMA_ROCM] if _amd_card() else [])
        folder.mkdir(parents=True, exist_ok=True)
        mark.write_text("unpacking", encoding="utf-8")
        for n, (url, sha) in enumerate(zips, 1):
            archive = _scratch() / url.rsplit("/", 1)[-1]
            download(url, archive, job, f"Завантажую Ollama ({n} з {len(zips)})…", sha)
            unpack(archive, folder, job, "Розпаковую Ollama…")
            archive.unlink(missing_ok=True)
        mark.unlink(missing_ok=True)
    if not _model_present():
        job.progress("Запускаю Ollama…", 0)
        if not ollama.start_ollama(wait=60):
            raise JobError("Ollama не запустилась — модель не завантажити.")
        _pull_model(job, ollama._settings()["model"])
    job.progress("Готово", 100)


def _pull_model(job: Job, model: str) -> None:
    """The model through Ollama's own API (it keeps the files in `runtime/Ollama/models`), with progress."""
    from .textcheck import ollama
    body = json.dumps({"model": model, "stream": True}).encode("utf-8")
    request = urllib.request.Request(ollama._base() + "/api/pull",
                                     data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=600) as response:
            for line in response:
                if not line.strip():
                    continue
                data = json.loads(line)
                if data.get("error"):
                    raise JobError(f"Ollama: {data['error']}")
                total, done = data.get("total") or 0, data.get("completed") or 0
                step = f"Завантажую модель {model}…"
                job.progress(step, 100 * done / total if total else None,
                             f"{done >> 20} з {total >> 20} МБ" if total else str(data.get("status") or ""))
    except OSError as err:
        raise JobError(f"Модель не завантажилась: {err}") from err
    if not ollama._has(ollama.status()["models"], model):
        raise JobError("Модель не з'явилась в Ollama після завантаження.")


def _install_upscale(job: Job, package: Path | None) -> None:
    """The engine (`resources/bin/upscayl-bin.exe`) and the one model (`resources/models/`) — the layout `upscale.engine()` looks for."""
    base = runtime_dir()
    folder = base / "Upscayl"
    if package:
        job.progress("Розпаковую модуль…", 0)
        unpack(package, base, only="Upscayl")
    else:
        url, sha, exe = UPSCAYL_ENGINE
        archive = _scratch() / url.rsplit("/", 1)[-1]
        download(url, archive, job, "Завантажую рушій апскейлу (1 з 3)…", sha)
        (folder / "resources" / "bin").mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            inner = next((n for n in z.namelist() if n.endswith("/" + exe) or n == exe), None)
            if not inner:
                raise JobError("У файлі рушія немає upscayl-bin.exe.")
            part = folder / "resources" / "bin" / (exe + ".part")      # the engine appears whole or not at all
            with z.open(inner) as src, open(part, "wb") as out:
                shutil.copyfileobj(src, out)
            os.replace(part, folder / "resources" / "bin" / exe)
        archive.unlink(missing_ok=True)
        for n, (url, sha) in enumerate(UPSCAYL_MODEL, 2):
            dest = folder / "resources" / "models" / url.rsplit("/", 1)[-1]
            download(url, dest, job, f"Завантажую модель ({n} з 3)…", sha)
    from .workshop import upscale
    upscale._missing_until = 0.0        # look for the engine again at once
    if not upscale.available():
        raise JobError("Файли встановлено, але рушій апскейлу не знайдено.")
    job.progress("Готово", 100)


# The official files, pinned to a release so what is downloaded is what was checked (2026-10-03; the hashes are the project's own
# `sha256sum.txt` for Ollama, and computed on the files downloaded from GitHub for Upscayl, whose releases publish none).
OLLAMA_RELEASE = "https://github.com/ollama/ollama/releases/download/v0.35.1/"
OLLAMA_ZIPS: list[tuple[str, str | None]] = [      # NVIDIA's libraries are in the base zip (the program is also fine on a CPU)
    (OLLAMA_RELEASE + "ollama-windows-amd64.zip", "dc50b9ca7f9023c86525012632cd1615b093d0407987444a7f62ecab617e8e93")]
OLLAMA_ROCM = (OLLAMA_RELEASE + "ollama-windows-amd64-rocm.zip",           # the AMD add-on, only for a PC with an AMD card
               "00e1d52a38479aa88954e01c969228fa98a07f433e639a6ba9fcd80b8d0993ca")
UPSCAYL_ENGINE = ("https://github.com/upscayl/upscayl-ncnn/releases/download/20251207-174704/"
                  "upscayl-bin-20251207-174704-windows.zip",
                  "1f0f65c5d2ade866555e2ac467d35952c35a47080a4060fe56a1ab028f67258a", "upscayl-bin.exe")
_RAW = "https://raw.githubusercontent.com/upscayl/upscayl/main/resources/models/"
UPSCAYL_MODEL = [(_RAW + "upscayl-standard-4x.param", "35330ececcea33b6c397a72548e788d5d53becee4734c50b7fada36e89f10a86"),
                 (_RAW + "upscayl-standard-4x.bin", "713ee713b0353afaa27976f0563a64a5043bd70b9bd8936c2e26e25ebcdbcddf")]


def _amd_card() -> bool:
    """Whether the PC has an AMD graphics card (then Ollama needs the ROCm add-on too)."""
    import subprocess
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "(Get-CimInstance Win32_VideoController).Name -join ';'"],
                             capture_output=True, text=True, timeout=20, creationflags=desktop.CREATE_NO_WINDOW).stdout
    except (OSError, subprocess.SubprocessError):
        return False
    return any(w in out.lower() for w in ("amd", "radeon"))


def start_install(module_id: str, package: str | None = None) -> Job:
    if module_id not in MODULES:
        raise ApiError("Такого модуля немає.", 404)
    if runtime_dir() is None:
        raise ApiError("Модулі встановлюються лише в портативну версію (поруч має бути тека runtime).")
    path = Path(package) if package else None
    if path and not path.is_file():
        raise ApiError("Файл модуля не знайдено.", 404)

    def work(job: Job):
        with _lock:
            (_install_textcheck if module_id == "textcheck" else _install_upscale)(job, path)
        return {"installed": installed(module_id)}

    return jobs.start(f"module-{module_id}", work, exclusive=f"module-{module_id}")


def _stop_processes(folder: Path) -> None:
    """Closes what runs from the module's folder (its Ollama), so that the folder can go."""
    import subprocess
    script = ("Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and $_.ExecutablePath.StartsWith('"
              + str(folder).replace("'", "''") + "\\', 'OrdinalIgnoreCase') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }")
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, timeout=30,
                       creationflags=desktop.CREATE_NO_WINDOW)
    except (OSError, subprocess.SubprocessError):
        return
    time.sleep(1)


def remove(module_id: str) -> None:
    """Deletes the module's folder under `runtime/` (not a system Ollama or Upscayl)."""
    if module_id not in MODULES:
        raise ApiError("Такого модуля немає.", 404)
    base = runtime_dir()
    folder = base / MODULES[module_id]["folder"] if base else None
    if not folder or not folder.exists():
        raise ApiError("Модуль не в теці runtime — нічого видаляти.")
    _stop_processes(folder)
    try:
        shutil.rmtree(folder)
    except PermissionError as err:
        raise ApiError("Не вдалося видалити: програма модуля ще працює. Закрийте її (Ollama — у треї) і спробуйте знову.") from err
    if module_id == "upscale":
        from .workshop import upscale
        upscale._missing_until = 0.0
    core.log.info("Module %s removed from %s", module_id, folder)


# ---------------------------------------------------------------- routes

@route("GET", "/api/modules")
def _list(req: Request):
    return {"modules": listing(), "portable": runtime_dir() is not None}


@route("POST", r"/api/modules/(\w+)/install")
def _install(req: Request):
    return {"jobId": start_install(req.groups[0], None).id}      # a file package comes only from the Windows dialog (install-from-file)


@route("POST", r"/api/modules/(\w+)/install-from-file")
def _install_from_file(req: Request):
    """A module package (a ZIP made on another PC) picked in the Windows dialog, for a PC without the internet."""
    if core.SANDBOX:
        raise ApiError("Це тестовий сервер на вигаданих даних.")
    path = desktop.pick_zip("Файл модуля (ZIP)", str(Path.home() / "Desktop"))
    if not path:
        return {"cancelled": True}
    return {"jobId": start_install(req.groups[0], path).id}


@route("POST", r"/api/modules/(\w+)/remove")
def _remove(req: Request):
    remove(req.groups[0])
    return {"modules": listing()}
