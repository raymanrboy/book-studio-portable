---
title: Plans for later and what is still unchecked
type: owner
updated: 2026-11-11
code: []
---
# Plans for later and what is still unchecked

> The owner's plans for when he has time, and the few things the portable copy's stages left unchecked. Until
> 2026-11-11 they lived in `ROADMAP.md` (the portable copy's plan by stages — every stage done, the file retired).

## Linux support (a possible move from Windows)

The owner, 2026-10-29: Book Studio **stays a program on the PC**, not a server — the rented Kyiv server (1 vCPU, 2 GB
RAM, 30 GB SSD) is too weak for it and could only carry small background work (a new-order notice), which is a separate
thing. The order: first the program works on both Windows and Linux (Windows not broken) → Linux from a stick or a
separate disk, a week on real orders → only then goodbye to Windows.

- Keys: `studio/vault.py` encrypts with Windows (DPAPI) → on Linux the system password store; the keys move once through
  the password-protected backup.
- `studio/clipboard.py`, `studio/desktop.py` (the Recycle Bin, Downloads from the registry, windows, Edge → Chrome /
  Chromium), `studio/backup.py` (the disk label).
- `studio/portable.py` (the Visual C++ check is not needed on Linux), `tools/make_shortcut.py` (`.lnk` → `.desktop`),
  the `.bat` launchers → `.sh`.
- `runtime/`: Ollama, ffmpeg and Upscayl have Linux builds; **Photoshop does not** (the program draws the mockups itself
  now, so it is probably not needed).
- Etsy opens only on the Kyiv PC: a new system there may make Etsy ask to confirm the sign-in — not before sales days.
- Graphics: an NVIDIA card can stutter on Linux; AMD / Intel are usually smooth.

## Syncing the library

To be designed and made, from the start independent of the system: paths relative to the library folder (never
`D:\…`); careful with names that differ only in letter case (different files on Linux); compare files by content, not by
the time they changed.

## Still unchecked

- Python on a clean Windows without Visual C++ (the `vcruntime140*.dll` lie in `runtime/python`).
- A Gelato draft from this copy — after the keys are restored with `restore_keys.py` (no real writes without his leave).
- The settings import has no "show the difference before applying" (it overwrites and keeps the old ones in
  `import-backup`) — only if it is ever needed.
- The colleague's copy: the printers' defaults in the code (the Printify shop, the Master product) are history for the
  owner but the colleague's own; the owner's fallback paths `D:\Roman\Desktop\…` in `mockups.py` / `portable.py` (only
  fallbacks — `runtime/` comes first).

## Related

- [The portable copy](../dev/portable.md) · [Building a portable folder](../dev/portable-setup.md) · [Limits](../dev/limits.md)
