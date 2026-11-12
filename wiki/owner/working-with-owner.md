---
title: Working with the owner
type: owner
updated: 2026-11-12
code: []
---
# Working with the owner

> What `CLAUDE.md` does not say: how the owner works, where his computers and programs are. Language, report shape, modes ("just analyse", "роби") and the commit rule live in `CLAUDE.md`.

## How he works
- He is not a programmer; he writes quickly, with typos, and sends screenshots and batches of notes. He wants a result made "as if for oneself": tidy, thought through, nothing extra.
- Say plainly what could not be checked: real smoothness in a visible window, a real drag from Explorer, live orders, the real Photoshop.
- Do not ask what is obvious: do it and say so in a line.
- Nothing is cached "just in case": forms open empty, orders refresh only on launch and by button ([interface principles](ui-principles.md#specific-requirements)).
- He is exact about pictures: the cover sells, so he fits covers himself (the mockups' crop window). He does not want an agent watching a video frame by frame; he writes a text description instead.

## His computers
- **Wrocław** is the work PC; Book Studio runs only here. **Kyiv** is a remote PC with the Etsy shop: only a browser with Etsy lives there, and Etsy is signed in only from it ([security](../security.md)).
- Programs live in `D:\Programs\Regular` (Ollama and others) and `D:\Programs\Portable` (portable Photoshop, 7-Zip). Drive C is kept clean: nothing is installed there and no temp file is left. Book Studio and every program it starts keep their temp files on D and empty them at start and close ([runtime](../architecture/runtime.md)); an agent's own scratch files on C go at the end of its task.
- Windows system settings (environment variables) are changed by him, following an agent's exact steps.
- Extra Python libraries an agent needs for research live in `D:\Programs\Regular\python-libs` (add with `PYTHONPATH`; it has `psd-tools`).
- **Photoshop CC 2019, portable:** `D:\Programs\Portable\Photoshop_Portable`; the templates are in `D:\Roman\Desktop\Трафарети мастхев` (read-only) — [mockups](../features/mockups-engine.md#templates). `ffmpeg` is on `PATH`.
- Hardware: RTX 4070 SUPER (12 GB), 32 GB RAM. The text check model is `gemma4:12b-it-qat` ([text check](../features/text-check.md)); user variables `OLLAMA_MODELS` and `OLLAMA_NUM_PARALLEL=4`.

## Related
- [Interface principles](ui-principles.md) · [Security](../security.md) · [Decisions](../decisions.md)
