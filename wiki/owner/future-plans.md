---
title: Future plans
type: owner
updated: 2026-11-12
code: []
---
# Future plans

> The owner's plans for when he has time. Not in the colleague's copy.

## Linux (a possible move from Windows)
Book Studio stays a program on the PC, not a server. The order: it works on both Windows and Linux (Windows not broken), then Linux from a stick or a separate disk for a week on real orders, only then goodbye to Windows. Etsy opens only on the Kyiv PC; a new system there may make Etsy ask to confirm the sign-in, so not before sales days.
- Keys: `vault.py` encrypts with Windows (DPAPI); on Linux the system password store, the keys moved once through the password-protected backup.
- Windows-only places: `clipboard.py`, `desktop.py` (Recycle Bin, Downloads, windows, Edge), `backup.py` (the disk label), `portable.py` (the Visual C++ check), `make_shortcut.py` (`.lnk`), the `.bat` launchers.
- `runtime/`: Ollama, ffmpeg and Upscayl have Linux builds; Photoshop does not (the program draws the mockups itself).

## Syncing the library
To be designed, independent of the system from the start: paths relative to the library folder (never `D:\…`), care with names that differ only in letter case, files compared by content, not by change time.

## Related
- [Portable copy](../dev/portable.md) · [Limits](../dev/limits.md)
