"""Makes a clean copy of the portable Book Studio to hand to someone else (a colleague).

    python app/tools/make_colleague_copy.py "D:\\Desktop\\Book Studio Colleague"  [--without-photoshop] [--without-templates] [--with-ollama] [--with-upscayl] [--dry-run]

What goes: the program (only what git knows — tracked files and new ones that are not ignored), `app/bin` (7-Zip,
cloudflared), `runtime/` (Python, ffmpeg, Ollama with its model, Upscayl, Antigravity's program), the launchers.
What never goes: `app/data` (orders, customers, the vault with the keys), `.secrets.txt`, the Workshop's books, `examples/`,
the git history (a fresh repository is made), the owner's raw wiki sources, Antigravity's user-data and home (his Google
login and chats), the Edge profile. Photoshop and the mockup templates go in (the owner, 2026-10-03: the colleague bought the
mockups too, and it is not commercial use) unless left out with `--without-photoshop` / `--without-templates`.
Ollama (the text check) and Upscayl (upscaling) are optional modules the program offers to install itself, so they are left out
unless `--with-ollama` / `--with-upscayl`. Python goes in with only the packages the program needs, ffmpeg with only `ffmpeg.exe`.
Photoshop goes in a stock state (his temp files, logs and preferences left out). The copy starts with the owner's two personal rules switched off (Etsy opens from any PC; Printify is not read-only) and the
light theme.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # …/Book Studio (the repository)
PORTABLE = ROOT.parent
sys.path.insert(0, str(ROOT / "app"))

KEEP_OUT_PREFIXES = ("wiki/raw/", "app/tools/colleague_docs/", "ROADMAP.md", "portable/ПРОЧИТАЙ.md")   # the owner's own words and plan; the colleague's docs are put in below
# Personal names in the docs (his GitHub account, his Windows profile) — said neutrally in the copy.
# The names are written in pieces: this file is copied into the colleague's copy too, and must not carry them itself.
_ACCOUNT, _PROFILE, _MAIL = "ray" + "manrboy", "Ro" + "man", "anna" + "miller764"
SCRUB = ((f"{_ACCOUNT}@gmail.com", "<email>"), (f"{_MAIL}@gmail.com", "<email>"),       # the e-mails before the account they contain
         (f"{_ACCOUNT}/book-studio", "<repository>"), (_ACCOUNT, "<github-account>"),
         ("C:\\Users\\" + _PROFILE + "\\", "C:\\Users\\<user>\\"), (f"/c/Users/{_PROFILE}/", "/c/Users/<user>/"),
         ("D:\\" + _PROFILE + "\\", "D:\\<user>\\"), (f"D:/{_PROFILE}/", "D:/<user>/"))
RAW_LINK = re.compile(r"\[([^\]]*)\]\((?:\.\./)*raw/[^)]*\)")
SETTINGS = {"security": {"etsyKyivOnly": False}, "printify": {"readOnlyFrom": None}, "ui": {"theme": "light"}}
README = """# Book Studio Portable

Усе потрібне лежить у цій папці — нічого встановлювати не треба.

**Перший запуск:** двічі клацни `Start Book Studio.bat`. Програма відкриється, а в цій теці з'явиться ярлик `Book Studio` (такий самий
і на робочому столі), і службові файли (`.bat` та цей текст) сховаються — у теці лишаться лише ярлик, `Book Studio` і `runtime`.
Далі запускай ярликом. Показати сховане: Провідник → Вигляд → Показати → Приховані елементи.
Якщо щось не відкривається і треба побачити помилку — `Start with console.bat` (сховане). Якщо теку перенесли, ярлик не відкриється:
запусти сховану `Make desktop shortcut.bat`.

**Перший запуск.** Програма сама покаже вікно: чого бракує і що зробити. Далі:
1. Налаштування → підключи свої ключі: Etsy, Printify, Gelato (вони шифруються під твій Windows-користувач).
2. Antigravity (агенти для нових книг) — увійди у свій обліковий запис Google.
3. Gelato і Canva відкриваються в Edge у власному профілі програми — увійди в них один раз.
4. Photoshop і трафарети мокапів уже лежать у `runtime\\Photoshop` і `runtime\\Templates` — програма знайде їх сама.

**З агентом (Claude Code, Antigravity, Codex…):** дай йому прочитати `Book Studio\\MANUAL.md` — інструкція, написана для ШІ: як
користуватись програмою, що де лежить, що робити, коли щось зламалось.

**Що де лежить:** `Book Studio\\` — програма та її вікі; `runtime\\` — Python, ffmpeg, Ollama, Upscayl, Antigravity.
Твої дані (замовлення, книги, ключі) з'являться в `Book Studio\\app\\data` і нікуди не відправляються.
"""


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                         capture_output=True, check=True).stdout.decode("utf-8")
    deleted = set(subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z", "--deleted"], capture_output=True,
                                 check=True).stdout.decode("utf-8").split("\0"))
    return [f for f in out.split("\0") if f and f not in deleted and not f.startswith(KEEP_OUT_PREFIXES)
            and (ROOT / f).is_file()]


def neutral_docs(repo: Path) -> None:
    """The rules for agents, written for the colleague: his own AGENTS.md / CLAUDE.md / working-with-the-owner page (templates in
    `app/tools/colleague_docs/`), and the owner's personal rules cut out of `wiki/security.md`."""
    src = ROOT / "app" / "tools" / "colleague_docs"
    for f in src.rglob("*.md"):
        out = repo / f.relative_to(src)
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, out)
    sec = repo / "wiki" / "security.md"
    if not sec.is_file():
        return
    text = sec.read_text(encoding="utf-8")

    def between(start: str, end: str, new: str) -> None:
        nonlocal text
        a = text.index(start)
        text = text[:a] + new + text[text.index(end, a):]

    between("1. *(A setting since", "2. **Etsy — read-only.**",
            "1. **Etsy** is signed in to from the computer where the program runs. The first owner's own rule «only from one\n"
            "   computer» is the setting `security.etsyKyivOnly`; it is switched off in this copy.\n")
    between("3. **Printify is read-only since", "4. **Gelato**",
            "3. **Printify** allows only image uploads, an unpublished product, and \"On hold\" orders (only after confirming manual\n"
            "   approval); the code keeps those rails. **Never**: sending to production, cancelling, Express, publishing, or\n"
            "   changing/deleting products. **The Master product is never changed.** (The first owner made it read-only from\n"
            "   2026-10-01: `printify.readOnlyFrom`; it is off in this copy.)\n")
    text = text.replace(", and only in the main account; the old account (kept after the\n   move to the owner's own one) is only read.", ".")
    between("`app/data/vault.json` is an encrypted store.", "7. **Never permanently delete",
            "`app/data/vault.json` is an encrypted store. A plain-text credentials file in the repo root, if one ever appears, is\n"
            "   ignored by git: never read, print, commit, change, or delete it unless the owner directly asks for exactly that.\n"
            "   Never ask the owner to paste keys into chat.\n")
    text = text.replace("**The mockup templates `D:\\Roman\\Desktop\\Трафарети мастхев` — read-only** (the owner's rule,\n    2026-09-23:",
                        "**The mockup templates (`runtime\\Templates`) — read-only** (the first owner's rule,\n    2026-09-23:")
    sec.write_text(text, encoding="utf-8")


def without_roadmap(repo: Path) -> None:
    """The owner's plan is not in the copy: the pages and the README that point at it lose those lines."""
    nl = chr(10)
    edits = {
        "wiki/dev/portable-setup.md": (
            (f"  - ROADMAP.md{nl}", ""),
            ("the launchers (`portable/`), the plan (`ROADMAP.md`) and the notes", "the launchers (`portable/`) and the notes"),
            (f"- `ROADMAP.md` (repository root) is the plan by stages and the list of what is not yet checked. Take one stage per session.{nl}", ""),
            (f"`ПРОЧИТАЙ.md`;{nl}  `ROADMAP.md` stays out of it.{nl}", f"`ПРОЧИТАЙ.md`.{nl}"),
            (f"- [ROADMAP.md](../../ROADMAP.md) — the plan{nl}", "")),
        "wiki/dev/portable.md": ((" the plan by stages is `ROADMAP.md` in this repository's root.", ""),),
        "README.md": (("; the plan — [ROADMAP.md](ROADMAP.md)", ""),),
    }
    for name, pairs in edits.items():
        page = repo / name
        if not page.is_file():
            continue
        text = page.read_text(encoding="utf-8")
        for old, new in pairs:
            text = text.replace(old, new)
        page.write_text(text, encoding="utf-8")


def scrub(repo: Path) -> int:
    """Takes the owner's personal names out of the copied documents; returns how many files changed."""
    changed = 0
    for p in repo.rglob("*.md"):
        if ".git" in p.parts:
            continue
        text = p.read_text(encoding="utf-8")
        new = RAW_LINK.sub(r"\1", text)             # links to the owner's raw sources, which are not in the copy
        for old, neutral in SCRUB:
            new = new.replace(old, neutral)
        if new != text:
            p.write_text(new, encoding="utf-8")
            changed += 1
    return changed


PY_DROP = ("Lib/test", "Lib/idlelib", "Lib/turtledemo", "Doc")      # Python's own tests, IDLE, demos, docs
NEEDED_SCRIPT = (
    "import importlib.metadata as md, json, re, sys\n"
    "norm = lambda n: re.sub(r'[-_.]+', '-', n).lower()\n"
    "stack, seen, files = [norm(n) for n in sys.argv[1:]], set(), set()\n"
    "while stack:\n"
    "    n = stack.pop()\n"
    "    if n in seen:\n"
    "        continue\n"
    "    try:\n"
    "        d = md.distribution(n)\n"
    "    except md.PackageNotFoundError:\n"
    "        continue\n"
    "    seen.add(n)\n"
    "    for f in d.files or []:\n"
    "        if not str(f).startswith('..'):\n"
    "            files.add(str(f).replace('\\\\', '/'))\n"
    "    for r in d.requires or []:\n"
    "        if 'extra ==' not in r:\n"
    "            stack.append(norm(re.split(r'[ ;<>=!~\\[(]', r)[0]))\n"
    "print(json.dumps({'dists': sorted(seen), 'files': sorted(files)}))\n")


def needed_packages(python: Path, requirements: Path) -> tuple[list[str], set[str]]:
    """The packages the program imports (its requirements.txt) with everything they need, and the files of them, relative to site-packages."""
    names = [re.split(r"[<>=!~ ;\[]", line.strip())[0] for line in requirements.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.lstrip().startswith("#")]
    out = subprocess.run([str(python), "-c", NEEDED_SCRIPT, *names, "pip"], capture_output=True, check=True).stdout
    data = json.loads(out)
    return data["dists"], set(data["files"])


def copy_python(src: Path, dst: Path, dry: bool) -> tuple[int, list[str]]:
    """Python as the program needs it: the interpreter and its library, and in site-packages only the program's packages (and what they
    need) — not the rest of the owner's general-purpose Python (data libraries, other projects')."""
    dists, keep = needed_packages(src / "python.exe", ROOT / "app" / "requirements.txt")
    n = 0
    for p in src.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(src).as_posix()
        if any(rel == d or rel.startswith(d + "/") for d in PY_DROP) or "__pycache__" in rel:
            continue
        if rel.startswith("Lib/site-packages/"):
            inner = rel[len("Lib/site-packages/"):]
            if inner not in keep:
                continue
        n += 1
        if not dry:
            out = dst / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, out)
    return n, dists


def copy_ffmpeg(src: Path, dst: Path, dry: bool) -> int:
    """ffmpeg.exe alone (the program never calls ffplay or ffprobe) with its licence files."""
    n = 0
    for p in src.rglob("*"):
        if p.is_file() and (p.name.lower() == "ffmpeg.exe" or p.name.upper().startswith(("LICENSE", "README"))):
            n += 1
            if not dry:
                out = dst / p.relative_to(src)
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, out)
    return n


PS_SKIP_DATA = ("Temp",)                                    # Photoshop's scratch folder (his temp files)
PS_LOG_NAMES = ("PSErrorLog.txt",)


def copy_photoshop(src: Path, dst: Path, dry: bool) -> int:
    """Photoshop without his traces: no scratch folder, no logs or error logs, and his preferences / recent lists replaced by the
    ones the portable build ships (`App/DefaultData`) — a stock Photoshop with the same launcher and settings."""
    n = 0
    for p in src.rglob("*"):
        if not p.is_file():
            continue
        parts = p.relative_to(src).parts                       # ('Portable Adobe Photoshop', 'Data', 'Temp', …)
        low = [x.lower() for x in parts]
        if len(parts) > 2 and parts[1] == "Data" and parts[2] in PS_SKIP_DATA:
            continue
        if "logs" in low or p.suffix.lower() == ".log" or p.name in PS_LOG_NAMES or p.name.startswith("sniffer-out"):
            continue
        n += 1
        if not dry:
            out = dst / p.relative_to(src)
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, out)
    seed = src / "Portable Adobe Photoshop" / "App" / "DefaultData"
    if seed.is_dir() and not dry:
        for p in seed.rglob("*"):
            if p.is_file():
                out = dst / "Portable Adobe Photoshop" / "Data" / p.relative_to(seed)
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, out)
    return n


def copy_tree(src: Path, dst: Path, dry: bool) -> int:
    n = 0
    for p in src.rglob("*"):
        if p.is_file():
            n += 1
            if not dry:
                out = dst / p.relative_to(src)
                out.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, out)
    return n


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target")
    ap.add_argument("--without-photoshop", action="store_true")
    ap.add_argument("--without-templates", action="store_true")
    ap.add_argument("--with-ollama", action="store_true")
    ap.add_argument("--with-upscayl", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    target = Path(args.target).resolve()
    if target.exists() and any(target.iterdir()):
        print(f"Папка {target} не порожня — оберіть нову.")
        return 2
    if target == PORTABLE or PORTABLE in target.parents or target in PORTABLE.parents:
        print("Копія має лежати окремо від портативної папки.")
        return 2
    dry = args.dry_run
    runtime = PORTABLE / "runtime"
    if not runtime.is_dir():
        print("Не знайдено runtime — це не портативна версія.")
        return 2

    files = tracked_files()
    print(f"Програма: {len(files)} файлів (лише те, що знає git; без даних, ключів, книг, історії).")
    if not dry:
        for rel in files:
            out = target / "Book Studio" / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, out)
    n = copy_tree(ROOT / "app" / "bin", target / "Book Studio" / "app" / "bin", dry) if (ROOT / "app" / "bin").is_dir() else 0
    print(f"app/bin: {n} файлів")

    skipped = []
    for part in sorted(p for p in runtime.iterdir() if p.is_dir()):
        name = part.name
        if (name == "Photoshop" and args.without_photoshop or name == "Templates" and args.without_templates
                or name == "Ollama" and not args.with_ollama or name == "Upscayl" and not args.with_upscayl):
            skipped.append(name)
            continue
        if name == "Antigravity":
            n = copy_tree(part / "app", target / "runtime" / "Antigravity" / "app", dry)
            print(f"runtime/Antigravity: програма ({n} файлів), без входу й чатів")
            continue
        if name == "python":
            n, dists = copy_python(part, target / "runtime" / name, dry)
            print(f"runtime/python: {n} файлів, лише потрібні пакунки ({', '.join(dists)})")
            continue
        if name == "ffmpeg":
            n = copy_ffmpeg(part, target / "runtime" / name, dry)
            print(f"runtime/ffmpeg: {n} файлів (лише ffmpeg.exe)")
            continue
        if name == "Photoshop":
            n = copy_photoshop(part, target / "runtime" / name, dry)
            print(f"runtime/{name}: {n} файлів (без його тимчасових файлів, журналів і налаштувань — стандартні)")
            continue
        n = copy_tree(part, target / "runtime" / name, dry)
        print(f"runtime/{name}: {n} файлів")
    for name in skipped:
        print(f"runtime/{name}: НЕ копіюється ({'додатковий модуль — програма запропонує встановити сама' if name in ('Ollama', 'Upscayl') else 'за ключем --without-' + name.lower()})")
    for name in skipped:                                         # left out: an empty place for him to fill
        if not dry and name not in ("Ollama", "Upscayl"):
            (target / "runtime" / name).mkdir(parents=True, exist_ok=True)

    if not dry:
        for bat in (ROOT / "portable").glob("*.bat"):          # the launchers as the repository keeps them
            shutil.copy2(bat, target / bat.name)
            subprocess.run(["attrib", "-h", str(target / bat.name)], check=False)     # the colleague sees them (the owner hides his)
        (target / "ПРОЧИТАЙ.md").write_text(README, encoding="utf-8")
        (target / "Book Studio" / "portable").mkdir(parents=True, exist_ok=True)
        (target / "Book Studio" / "portable" / "ПРОЧИТАЙ.md").write_text(README, encoding="utf-8")   # setup_portable.py lays it out from here
        data = target / "Book Studio" / "app" / "data"
        data.mkdir(parents=True, exist_ok=True)
        (data / "settings.json").write_text(json.dumps(SETTINGS, indent=2), encoding="utf-8")
        repo = target / "Book Studio"
        neutral_docs(repo)
        without_roadmap(repo)
        print(f"Особисті імена прибрано з {scrub(repo)} документів; правила для агентів написано для колеги")
        subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
        subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=Book Studio", "-c", "user.email=noreply@localhost",
                        "commit", "-q", "-m", "Book Studio"], check=True)
        print(f"\nГотово: {target}")
    else:
        print("\n(dry-run: нічого не записано)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
