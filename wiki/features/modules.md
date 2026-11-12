---
title: Optional modules
type: feature
updated: 2026-11-12
code:
  - app/studio/modules.py
  - app/web/js/modules-ui.js
  - app/web/js/pages/settings.js
---
# Optional modules

> Heavy parts that are **not in the program** until the user asks: the **text check** (Ollama + a model; folder `Ollama`, several GB, needs a GPU) and **upscaling** (Upscayl's engine + one model; folder `Upscayl`, tens of MB, Vulkan GPU). The interface offers them where they would be used and the program installs them itself.

## Where they are offered
- **Settings → «Модулі»** (`#/settings/textcheck` also leads here): each module with its size, a ✓ when installed, «Встановити», a folder icon («з файлу», for a PC without internet) and a bin icon (remove).
- **Workshop:** the «Апскейл ×2» switch is off with a quiet «Встановити апскейл» beside it; after the install the book's data is fetched again ([Workshop](workshop.md)).
- **Order card, step «Вичитка»:** a missing module shows «Вичитка не встановлена» with a download icon; after the install the check starts by itself (`start.module` in the `textcheck` answer; `warm` stays quiet).
- All three ask first (`offerModule()`: what it is, size, «Потрібна відеокарта»), then show a progress window (`installModule()`).

## The text check's own settings
They live under the installed «Розумна вичитка тексту» row (`textcheckSettings()`, `redrawModules()` in `settings.js`); without the module there are none. The settings are `textcheck {enabled, prescan, model, url}`:
- «Перевіряти текст сторінок у картці замовлення» (`enabled`), the quick-scan switch (`prescan`), the model («Обрати модель»; default `gemma4:12b-it-qat`), «Перевірити зв'язок», and, when Ollama is not running, «Запустити» (starts the copy's own `runtime/Ollama/ollama.exe serve`). The row's mark shows whether the check works.
- What the switches do: [Text check](text-check.md).

## What the install does (`modules.py`)
- **Where it goes:** `runtime/<folder>/` of the portable copy only (`runtime_dir()`); no installer, no administrator rights. *Installed* = its files are there (for the text check also the model's manifest).
- **From the internet:** official release files pinned to a version (`OLLAMA_ZIPS`, `UPSCAYL_ENGINE`, `UPSCAYL_MODEL`), downloaded as `.part` into `data/tmp/modules/` with progress, checked against SHA-256, unpacked (a path out of the folder is refused). Text check: the Ollama Windows zip, the AMD add-on only when the PC has an AMD card (`_amd_card()`), then the model through Ollama's own API with progress into `runtime/Ollama/models`. Upscale: `upscayl-bin.exe` plus `upscayl-standard-4x.bin/.param`.
- **From a file:** a ZIP picked in the Windows dialog (`POST /api/modules/<id>/install-from-file`), laid out as `Ollama/…` or `Upscayl/…`. It may hold only its own folder, so it cannot replace `python/` or `Photoshop/`. The plain install route takes no path.
- **Whole or nothing:** Ollama's unpacking is marked by `runtime/Ollama/.installing` and a cut-short one is redone; the Upscayl engine appears whole or not at all (`.part` → `upscayl-bin.exe`); `upscale.engine()` needs both model files.
- **Isolated from the PC:** the copy's Ollama listens on its own port (`portable.OLLAMA_PORT`, 11435) and its models are always `runtime/Ollama/models`; a PC's own Ollama (port 11434, its models folder) is never used or written to. Upscale looks only at `runtime/Upscayl`.
- **Remove:** closes what runs from the folder (`_stop_processes()`), then deletes the module's folder, the Ollama model included, after a confirmation. Books and settings are never touched; a running Ollama holding files makes the message say to close it.
- Both projects are AGPL-3.0, downloaded and run unmodified as separate programs; Book Studio redistributes nothing.
- Routes: `GET /api/modules`, `POST /api/modules/<id>/install`, `…/install-from-file`, `…/remove`. The start-up check does not ask for them ([Portable copy](../dev/portable.md)); the colleague copy leaves both out unless made with `--with-ollama` / `--with-upscayl`.

## Why
- Heavy parts absent by default, offered when needed, like game upgrades.
- Everything stays inside the portable `runtime/`: no admin rights, no touching a PC's own programs.
- Install from file exists for PCs without internet and is restricted to the two module folders.

## Where in the code
- [app/studio/modules.py](../../app/studio/modules.py) — `MODULES`, `installed()`, `download()`, `unpack()`, `start_install()`, `remove()`
- [app/web/js/modules-ui.js](../../app/web/js/modules-ui.js) — `offerModule()`, `installModule()`
- [app/web/js/pages/settings.js](../../app/web/js/pages/settings.js) — `modulesCard()`, `textcheckSettings()`
- [app/tests/test_modules.py](../../app/tests/test_modules.py) — installs from `file://` sources, wrong hash, escaping package, removal

## Related
- [Settings](settings.md) · [Text check](text-check.md) · [Workshop](workshop.md) · [Portable copy](../dev/portable.md)
