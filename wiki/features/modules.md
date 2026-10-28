---
title: Optional modules
type: feature
updated: 2026-10-28
code:
  - app/studio/modules.py
  - app/web/js/modules-ui.js
  - app/tests/test_modules.py
---
# Optional modules

> The heavy parts that are **not in the program** until the user asks: the **text check** (Ollama + a model) and **upscaling**
> (Upscayl's engine + one model). The interface offers them where they would be used and the program installs them itself. The owner:
> like upgrades in games — absent by default, the interface offers to install.

## Where they are offered

- **Settings → «Модулі»** (`#/settings/textcheck` leads here): each module with its size, a ✓ when installed, «Встановити» / the folder icon
  («з файлу», no internet) / a bin icon (remove).
- **Workshop**: the «Апскейл ×2» switch is off with a quiet button «Встановити апскейл» beside it (`install-module` in `workshop-book.js`);
  after the install the book's data is fetched again and the switch works.
- **Order card, step «Вичитка»**: when the module is missing the badge says «Вичитка не встановлена» with a download icon; after the
  install the check starts by itself (`start.module` from `POST /api/orders/<id>/textcheck`; `warm` stays quiet).
- All three ask first (`offerModule()`: what it is, the size, «Потрібна відеокарта»), then show a progress window (`installModule()`).

## The text check's own settings live here

The text check is a module's setting, so it has no card of its own. Under the installed «Розумна вичитка тексту» row: the switch «Перевіряти
текст сторінок у картці замовлення», the quick-scan switch (`prescan`), the model («Обрати модель», «Перевірити зв'язок») and, when Ollama is
not running, «Запустити» (starts the copy's own `runtime/Ollama/ollama.exe serve`). The row's mark shows whether the check works. Without the
module there are no settings, only «Встановити». What the switches do — [text check](text-check.md). Code: `textcheckSettings()` and
`redrawModules()` in `settings.js`; the old address is mapped in `mount()`.

## What the install does (`modules.py`)

- **Where it goes:** `runtime/<folder>/` of the portable copy only (`runtime_dir()`); no installer, no administrator's rights.
  *Installed* = its files are there (for the text check also the model's manifest).
- **From the internet:** the official release files pinned to a version, downloaded as `.part` into `data/tmp/modules/` with progress, checked
  against SHA-256, unpacked (a path out of the folder is refused). **Text check:** Ollama `ollama-windows-amd64.zip` (NVIDIA libraries inside,
  hash from the project's `sha256sum.txt`) + the AMD add-on `…-rocm.zip` only when the PC has an AMD card; then the model
  `gemma4:12b-it-qat` through Ollama's own API (`/api/pull`, with progress) into `runtime/Ollama/models`. **Upscale:** `upscayl-bin.exe` from
  `upscayl/upscayl-ncnn` (Upscayl publishes no hash, so the one computed on a checked download is pinned) + `upscayl-standard-4x.bin/.param`
  from the `upscayl/upscayl` repository. Versions and hashes — `OLLAMA_ZIPS`, `UPSCAYL_ENGINE`, `UPSCAYL_MODEL`.
- **From a file:** a ZIP the user points to (`POST /api/modules/<id>/install-from-file`, the Windows dialog) laid out as `Ollama/…` or `Upscayl/…`
  — for a PC without the internet. It must hold only its own folder (`Ollama/` or `Upscayl/`): it cannot replace `python/` or `Photoshop/`.
  A package comes only from the Windows dialog; the plain `install` route takes no path.
- **Whole or not at all:** Ollama's unpacking is marked by `runtime/Ollama/.installing`; a cut-short one is redone from the start (also when
  the AMD add-on failed). The Upscayl engine appears whole or not at all (`.part` → `upscayl-bin.exe`); `upscale.engine()` needs both `.param`
  and `.bin` of the model.
- **Isolated from the PC (portable copy).** The copy's Ollama listens on its **own port** (`portable.OLLAMA_PORT`; `OLLAMA_HOST`) and its
  `OLLAMA_MODELS` is always `runtime/Ollama/models` (set before the folder even exists), so an Ollama the PC has — its default port, its models
  folder, its `OLLAMA_MODELS` — is never used or written to; it is started as `runtime/Ollama/ollama.exe serve` (the zip has no tray app).
  Upscale looks only at `runtime/Upscayl` (`upscale._candidates()`).
- **Remove:** first closes what runs from the folder (`_stop_processes()`), then deletes the module's folder (the Ollama model included) after a
  confirmation; books and settings are never touched. A running Ollama holds its files: the message says to close it.
- Licences: both projects are AGPL-3.0 (downloaded, run unmodified as separate programs; nothing is redistributed by Book Studio).

## Routes

`GET /api/modules` · `POST /api/modules/<id>/install` · `…/install-from-file` · `…/remove` — see [api-routes](../architecture/api-routes.md).
The start-up check does not ask for Ollama or Upscayl ([the portable copy](../dev/portable.md)); the colleague copy leaves both out.

## Where in the code

- [modules.py](../../app/studio/modules.py): `MODULES`, `installed()`, `listing()`, `download()`, `unpack()`, `_install_textcheck()`, `_install_upscale()`,
  `start_install()`, `remove()`, the sources `OLLAMA_ZIPS` / `UPSCAYL_ENGINE` / `UPSCAYL_MODEL`.
- [modules-ui.js](../../app/web/js/modules-ui.js): `offerModule()`, `installModule()`.
- [settings.js](../../app/web/js/pages/settings.js): the Settings block `modulesCard()`.
- Tests: [test_modules.py](../../app/tests/test_modules.py) (installs from `file://` sources, a wrong hash, a package that climbs out, removal).
