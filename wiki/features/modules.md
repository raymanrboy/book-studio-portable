---
title: Optional modules
type: feature
updated: 2026-10-04
code:
  - app/studio/modules.py
  - app/web/js/modules-ui.js
  - app/tests/test_modules.py
---
# Optional modules

> The heavy parts that are **not in the program** until the user asks: the **text check** (Ollama + a model, ≈ 9 GB) and **upscaling**
> (Upscayl's engine + one model, ≈ 40 MB). The interface offers them where they would be used and the program installs them itself.
> The owner's idea, 2026-10-03: «як апгрейди в іграх — по дефолту їх немає, але інтерфейс пропонує встановити».

## Where they are offered

- **Settings → «Модулі»** (the old address `#/settings/textcheck` leads here): each module with its size, a ✓ when installed, «Встановити» / the folder icon
  («з файлу», no internet) / a bin icon (remove).
- **Workshop**: the «Апскейл ×2» switch is off with a quiet button «Встановити апскейл» beside it (`install-module` in `workshop-book.js`);
  after the install the book's data is fetched again and the switch works.
- **Order card, step «Вичитка»**: when the module is missing the badge says «Вичитка не встановлена» with a download icon; after the
  install the check starts by itself (`start.module` from `POST /api/orders/<id>/textcheck`; `warm` stays quiet).
- All three ask first (`offerModule()`: what it is, the size, «Потрібна відеокарта»), then show a progress window (`installModule()`).

## The text check's own settings live here

The «Перевірка тексту» block is no longer a card of its own (2026-10-03, the owner: it is a module's setting, so it belongs under «Модулі»). Under the
installed «Розумна вичитка тексту» row: the switch «Перевіряти текст сторінок у картці замовлення», the quick-scan switch (`prescan`), the model
(«Обрати модель», «Перевірити зв'язок») and, when Ollama is not running, «Запустити». The row's mark shows whether the check works. Without the
module there are no settings, only «Встановити». Code: `textcheckSettings()` and `redrawModules()` in `settings.js`; the old address is mapped in `mount()`.

## What the install does (`modules.py`)

- **Where it goes:** `runtime/<folder>/` of the portable copy only (`runtime_dir()`); no installer, no administrator's rights.
  *Installed* = its files are there, or an Ollama that answers with the model / an Upscayl the PC already has.
- **From the internet:** the official release files pinned to a version, downloaded as `.part` into `data/tmp/modules/` with progress, checked
  against SHA-256, unpacked (a path out of the folder is refused). **Text check:** Ollama v0.35.1 `ollama-windows-amd64.zip` (1.47 GB; NVIDIA
  libraries inside, hash from the project's `sha256sum.txt`) + the AMD add-on `…-rocm.zip` (256 MB) only when the PC has an AMD card; then the
  model `gemma4:12b-it-qat` (7.2 GB) through Ollama's own API (`/api/pull`, with progress) into `runtime/Ollama/models`. **Upscale:**
  `upscayl-bin.exe` from `upscayl/upscayl-ncnn` release 20251207-174704 (2.4 MB; Upscayl publishes no hash, so the one computed on the checked
  download is pinned) + `upscayl-standard-4x.bin/.param` from the `upscayl/upscayl` repository (33 MB; the `.bin` is byte-identical to the one the
  owner's Upscayl has). Checked 2026-10-03: the upscale install was run for real (download → hash → unpack → engine found) and the engine
  upscaled a test picture ×2 on the GPU; the Ollama download was not run (≈ 8.7 GB) — its URLs and hashes were read from the release.
- **From a file:** a ZIP the user points to (`POST /api/modules/<id>/install-from-file`, the Windows dialog) laid out as `Ollama/…` or `Upscayl/…`
  — for a PC without the internet.
- **Isolated from the PC (portable copy).** The copy's Ollama listens on its **own port 11435** (`portable.OLLAMA_PORT`; `OLLAMA_HOST`) and its
  `OLLAMA_MODELS` is always `runtime/Ollama/models` (set before the folder even exists), so an Ollama the PC has — its port 11434, its models folder,
  its `OLLAMA_MODELS` — is never used or written to; it is started as `runtime/Ollama/ollama.exe serve` (the zip has no tray app). Upscale looks
  only at `runtime/Upscayl` (`upscale._candidates()`). A module is *installed* only when its files are in `runtime/` (for the text check also the
  model's manifest). Checked 2026-10-03 on the owner's real `runtime/Ollama`: it starts on 11435 and sees `gemma4:12b-it-qat` there while his
  system Ollama keeps running untouched.
- **Remove:** first closes what runs from the folder (`_stop_processes()`), then deletes the module's folder (the Ollama model included) after a confirmation; books and settings are never touched. A running
  Ollama holds its files: the message says to close it.
- Licences: both projects are AGPL-3.0 (downloaded, run unmodified as separate programs; nothing is redistributed by Book Studio).

## Routes

`GET /api/modules` · `POST /api/modules/<id>/install` · `…/install-from-file` · `…/remove` — see [api-routes](../architecture/api-routes.md).
The start-up check no longer asks for Ollama or Upscayl ([the portable copy](../dev/portable.md)); the colleague copy leaves both out.

## Where in the code

- [modules.py](../../app/studio/modules.py): `MODULES`, `installed()`, `listing()`, `download()`, `unpack()`, `_install_textcheck()`, `_install_upscale()`,
  `start_install()`, `remove()`, the sources `OLLAMA_ZIPS` / `UPSCAYL_ENGINE` / `UPSCAYL_MODEL`.
- [modules-ui.js](../../app/web/js/modules-ui.js): `offerModule()`, `installModule()`.
- [settings.js](../../app/web/js/pages/settings.js): the Settings block `modulesCard()`.
- Tests: [test_modules.py](../../app/tests/test_modules.py) (installs from `file://` sources, a wrong hash, a package that climbs out, removal).

## Safer installs (2026-10-04)

- Ollama's unpacking is marked by `runtime/Ollama/.installing`; a cut-short one is redone from the start (also when the AMD add-on failed). The Upscayl engine appears whole or not at all (`.part` → `upscayl-bin.exe`); `upscale.engine()` needs both `.param` and `.bin` of the model.
- A module ZIP must hold only its own folder (`Ollama/` or `Upscayl/`): it cannot replace `python/` or `Photoshop/`. A package can come only from the Windows dialog (`install-from-file`); the plain `install` route takes no path.
