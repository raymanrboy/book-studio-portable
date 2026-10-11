---
title: Working with the owner
type: owner
updated: 2026-10-11
code: []
---
# Working with the owner

> The owner isn't a programmer, and writes in Ukrainian (often quickly, with typos), sending screenshots
> and batches of notes. He values a result treated "as if it were for oneself": tidy, well thought out,
> nothing extra.

## Communication

- **Reply in Ukrainian**, in plain words, with no jargon or function names in explanations. A report
  should say what changed for him, what was checked, what wasn't, and what he needs to do (e.g. restart
  the program).
- Be honest about what couldn't be checked (real smoothness in a visible window, a real drag-and-drop
  from Explorer, live orders).
- Don't ask unnecessary questions: if the answer is obvious, just do it and say so briefly.

## Working modes

- **"Just analyze, don't change anything" / "discussion mode"** — analysis and conversation only, no
  file changes. The owner may add notes across several messages.
- **Start only on command**: "Розпочинай" (Start), "roby" (Do it), "приступай" (Get going), "плануй і
  приступай" (Plan it and get going).
- He likes to talk through big ideas **as a dialogue** (point by point) before anything gets built.
- Plans, agreements, and specs go **into the project's files** (now — into this wiki), not just into an
  agent's memory.
- "Try hard" means he expects a thorough check before the report.

## Mandatory rules

- Security — [security.md](../security.md) (Etsy: browse as a visitor, never sign in here — sign-in only from Kyiv; read-only; Printify/Gelato — only what's
  allowed; never touch keys).
- Commit and push only when asked — and then everything together, with no splitting by branch or "whose
  change it is" ([dev/setup.md](../dev/setup.md)). Explain git in plain words, with no jargon.
- After changes to the server side, remind him to restart Book Studio.
- Never cache anything "just in case": the Order Creator is empty every time (except for unfinished work
  on a new order — that's remembered until the order leaves "New"), orders refresh only on launch and by
  button ([decisions.md](../decisions.md)).

## About the owner

- Two computers: the Wrocław one (day-to-day work) and a remote Kyiv one (the Etsy shop, signing in to
  Etsy). **Book Studio only runs on the Wrocław one**; the owner never runs the program on the Kyiv PC at
  all (said on 2026-09-18) — only a browser with Etsy lives there.
- The shop: personalized children's books; printed through Printify (shop CozyCovenant) and Gelato.
- Older tools: Etsy Profit Calculator, Order Creator Printify, Etsy OS (a failed pipeline).
- Book templates live in Canva; some pages get upscaled in Upscayl; the library isn't fully filled in
  yet.
- **Programs only go on `D:\Programs\Regular`; drive C — kept minimal, never touched unless truly
  necessary** (2026-09-19). Program downloads and data also go on D. The owner changes Windows system
  settings (environment variables, etc.) himself, following an agent's instructions. Extra Python
  libraries an agent needs for research live in `D:\Programs\Regular\python-libs` (add via `PYTHONPATH`;
  it has `psd-tools` 1.19, as of 2026-09-19).
- **"Very important to keep drive C clean"** (2026-09-23): any temporary file that appears while a program
  of his runs must be removed when it's done. So Book Studio (with its Mockups) gives itself — and every
  program they start (the Edge window, the Windows dialogs, cloudflared, Photoshop) — a temp folder inside
  their data folder on D and empty it at start and at close ([runtime](../architecture/runtime.md#temporary-files-and-drive-c));
  the tests and the preview servers write to `.tmp\` in the repository, also on D. An agent's own scratch
  files on C go at the end of its task.
- **Photoshop CC 2019 (20.0.5), portable** — `D:\Programs\Portable\Photoshop_Portable` (the program itself:
  `Portable Adobe Photoshop\App\Photoshop\Photoshop.exe`); used for Etsy listing mockups, the templates
  are in `D:\Roman\Desktop\Трафарети мастхев` (read-only) — [mockups](../features/mockups.md#the-templates).
  `ffmpeg` is on PATH (2026-09-23).
- **About visuals he's "pixel-perfect"**: the cover sells, so he fits covers himself (2026-09-23).
  He doesn't want an agent watching videos frame by frame ("too slow and costly") — he writes a text
  description instead.
- On the Wrocław PC: an RTX 4070 SUPER (12 GB), 32 GB RAM; Ollama (`D:\Programs\Regular\Ollama`) with the
  `gemma4:12b-it-qat` model (the owner decided to drop Qwen, 2026-09-19); user variables `OLLAMA_MODELS`,
  `OLLAMA_NUM_PARALLEL=4` ([text check](../features/text-check.md#why-this-model-and-this-design)). Ollama is started from the Start
  menu.

## Related

- [Interface principles](ui-principles.md) · [Decisions](../decisions.md)
