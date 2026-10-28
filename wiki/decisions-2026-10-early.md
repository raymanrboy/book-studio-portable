---
title: Decisions — 1–10 October 2026
type: decision
updated: 2026-10-28
code: []
---
# Decisions — 1–10 October 2026

Older decisions, moved out of [decisions.md](decisions.md) (the current ones). Same format; newest on top. A decision here may be superseded by a newer one there.

## 2026-10-09 — Etsy SEO: an agent's tool with long titles, eRank in the browser pane, unmeasured tags welcome

- **The owner:** "build an ultimate tool for my listings' SEO", used through Claude Code — a skill in Book Studio
  (`/etsy-seo`), not a part of the interface. Its data and rules live in `seo/`; the old `seo-intelligence` stays an archive.
- **Long titles only** (110–140 characters, no tests of short ones): Etsy's own guidance (27 Apr 2026) asks for under 15
  words, but the owner sees short titles index worse and the niche's leaders all use long ones. The title is built of
  exact buyer phrases, nothing untrue or irrelevant in it.
- **eRank is read in the browser pane** where he is signed in; the agent may use the whole daily limit. Etsy is never
  opened (the security rule).
- **No eRank data ≠ a bad tag** ("books sell anyway; we may be the first with this product") — such exact tags are
  judged by their competition, up to 5 per listing.
- **The shop's own Etsy Stats are not collected for now** (2026-10-10: the owner sent the top search terms after all — they
  go in as screens, the strongest evidence). Details — [features/seo.md](features/seo.md).

## 2026-10-08 — A name finds a print order only within a month of the receipt

- **The owner**: a repeat buyer's new receipt was shown as a bundle with her old one and the cost split — "the orders are on very different days".
- **Decided**: matching by the recipient's name (not by number, not manual) takes only a print order made from 1 day before to 30 days after
  the receipt. Otherwise a new receipt takes the buyer's old order and the two split its cost. Not to be "fixed" back to match the old
  Profit Calculator (its name rule had no time limit); a sale whose print order is older than a month is linked by hand.

> What was decided, when, and why. Before "fixing" something odd in the code — check whether it's a
> deliberate choice by the owner. Newest decisions are at the top. An entry is a record of its day: where it says
> "not built yet", the feature page tells what exists now.

## 2026-10-08 — A Chrome extension fills the Canva template

- **The owner:** Canva could not be automated "the standard ways" — so a Chrome extension: drop the book in, the pictures lay
  themselves out by the template, the text too. He chose: the book is picked as its **folder** (not a list from Book Studio — works
  without the program running); the code lives **in this repository** (`canva-extension/`); a second run **skips what is done**;
  a **pages field** for a part of the book; the cover gets **only its picture** — the title he sets himself.
- **The text's look (the owner):** each text page gets the element «Yellow gradient sphere» and on top of it a new text box,
  **Schoolbell, 100 — 110 on pages 1 and 30 — line spacing 2.04** (the sizes and spacing added the same day; then: **page 1 gets only its picture**, no sphere or text) — he aligns both by hand and removes the template's old placeholders («той білий я потім приберу»).
  The text is `book-text.md` without the `## Spread NN — …` heading, `{Name}` / `{Gifter}` left for the order.
- **Why the editor and not an API:** the Canva Apps SDK / Connect API were not taken — the owner had tried "the standard ways";
  the extension does a person's clicks, found by Canva's accessibility labels, every step tried by hand on his template first.
- **The look:** the owner asked for it to be beautiful — the panel is Book Studio's light look with its icon, and shows the book
  the way it is printed (the cover, the spreads), each page lit by its state.
- Details — [Canva extension](features/canva-extension.md).

## 2026-10-07 — «Для відео» is the video category; the videos with people are gone

- **The owner:** refuse the videos where people hold the book; the auto-caught video category becomes «Для відео»
  (the closed book on a sofa, a counter, a table), and the five templates with people are removed. The same templates
  he will use in Google Flow, so the prompt says: the camera glides in on the book, a hand appears and takes it, the book
  is never opened or turned.
- **One step** (the one that worked with Omni): template → Cover 1 → the prompt, the generator swaps the book and animates.
  The JSON «swap the book» prompt stays in `PROMPTS["video"]` as a two-step fallback (a photo first, then Flow's first
  frame) if the cover comes out spoiled. **The trim stays** — 2 s at first, cut down to **0.5 s** the same day (the owner).
- The file is `etsy/video-video.mp4` (still the second in the listing); old `video-hands.mp4` are left alone, the owner
  replaces them himself. The folder `photo-mockups/hands` went to the Recycle Bin (his originals are untouched).
- **The video prompt never names opening** (the same day, after the generators opened and leafed through the book): no
  "open / page / flip / turn" at all, the book is "closed, stiff covers, one rigid board", the right hand grips **the
  corner**, a tilt is given in degrees (about 10°), and every second has its motion — the hand carries the book out at the end.
  [Photo mockups](features/photo-mockups.md).

## 2026-10-06 — What not to build next (the owner's answer to «what else could be better»)

- **Not wanted:** order deadlines / Windows notifications, sales analytics «what to make next», a morning summary on the start
  screen, a smarter search (the owner says he does not use search at all).
- **Not now:** the program rendering the personalised pages itself instead of Canva — too much work, and the owner wants to keep
  control; the cover stays in Canva in any case.
- **Liked, then done the same day** ("Все що придумав — роби"): «Скасувати» instead of a question for a Workshop book and a photo
  template — they wait 2 min on the program's shelf (`aside.py`) before the Recycle Bin, so the undo is real (the 2026-09-30 rule «an
  undo the program cannot keep is a lie» still holds: the shelf is what keeps it). Still asking, on purpose: removing a Workshop book's
  Etsy photo (its scenes are rebuilt), keys and Etsy sign-out, a module, re-making slides, putting a scheme over six slides, the send.
- **Search removed from the code** (the owner: "can be removed completely"): Ctrl+K, the magnifier and `palette.js`. The pages' own
  filters stay — they were not asked about.
- **The text check calibrated again** on 71 journaled checks (the owner: "more data has gathered") — see
  [text check](features/text-check.md#why-the-rules-are-what-they-are); the gemma4 loop is handled by keeping the whole transcript.
- **A robot clicks every page** before a change is called done (`tools/ui_smoke.py`, in the test run) — the owner asked what «automatic
  interface checks» are and said do it.

## 2026-10-06 — Progress only as far as it is known; motion on a 170–180 Hz screen

- **The owner** did not like step squares «filled to a half» and has a 170–180 Hz monitor: he wants more intermediate frames, nothing jumping.
- **Decision:** a measured progress fills in proportion, an unmeasured one is neutral (see [ui-principles](owner/ui-principles.md)); `patch()` morphs in place and
  `flip()` animates removals so state changes have frames; shared timing tokens; hidden toggles fade; the slide editor's drags are frame-synchronised.
  The Edge launch gets **no** frame-rate flags (they do not help a vsynced 170 Hz panel — they only tear). Five agents audited the areas in parallel, five implemented.
- **Not done:** `.ws-row` `content-visibility` (clips the waiting ring); the passport upload / export progress toast (needs new UI); the mockup/slides engine
  keeps `left/top` (a drag uses `translate`) so the baked slide output cannot change; server-side «unknown percent» flag for the Gelato/Printify milestone waits.

## 2026-10-05 — Speed audit: what runs only when it is needed, and what runs side by side

- **The owner** asked for a wide research of what could make the program faster, smaller and better, then said to do everything found.
  The measured findings: the code itself is quick (imports 0.26 s, 480 profit rows in 0.08 s) — the losses were elsewhere.
- **Decisions:** (1) the wiki check looks names up in a set of the code's words and never walks `data` (54 s → 2 s); (2) the text check's
  model is **not** read at every start — `warm()` does it when a card takes files (the earlier «prime» of 19.09 is gone); (3) Etsy,
  Printify and Gelato are read side by side in a sync; (4) Edge is told to leave components alone and its leftovers are removed from
  our two profiles when no window holds them; (5) the preview cache is capped at 800 MB (least recently used first); (6) the Workshop's
  and the slide editor's looking for changes slows to every 4 s after 30 quiet seconds; (7) scripts and styles are asked for by a
  versioned address and kept for good.
- **Not done, on purpose:** the 0.7 GB of identical files in the library and the Workshop were not turned into hard links (a page edited in
  place would change both copies — unlike the archive, which is never edited); folder previews keep `max-age=600` (some of their
  addresses carry no version, `immutable` would show a replaced page old); PNG pages are not recompressed (their hashes key the archive and
  Printify's upload cache). **Moving off Edge's `--app` window** (to WebView2, Qt or Electron) was weighed and rejected: same engine, a
  rewrite for no gain — the program never used WebView2.

## 2026-10-04 — The printer's history in the order card: asked for when the card opens, never in bulk

- **The owner** wanted what Gelato's dashboard shows (the status history) in the card's empty right-hand space — a square
  with a scroll — then: "forget what I said, do it as you think", and **"don't scan every order at launch and hide it
  everywhere — do it when I open an order, I can wait a couple of seconds."**
- **Decision:** a card «Історія» beside a placed Gelato order's data ([orders](features/orders.md)); the order is read from Gelato
  (one read-only `GET`) when its card opens, a skeleton meanwhile; nothing at launch, nothing for the queue. No always-open
  "expand" box: the column is free, so a click to open it would only cost.
- **Why not our own journal of status changes** (the alternative): it would have to watch every order at every sync — what the
  owner declined. So when Gelato's own log is empty, the card shows the few dates the order has and the tracking link.
- **Not known yet:** what Gelato's `eventLog` holds for a shipped order (the docs weren't readable, every draft had it empty);
  the card tries the likely field names and `gelato.log` records the real ones. The carrier's own scans (the USPS list in his
  screenshot) aren't in Gelato's API as far as found — the card links to the carrier's tracking page instead. Gelato's webhooks
  need a public address; the program has none.
- Built in the **portable** copy only (the owner, 2026-10-04: "будуй в портативній").

## 2026-10-02 — Listing slide 7: the hero's looks, each in its own frame, on its white background

- **The owner** asked for a new listing slide for the books with appearance variants, on the basis of slide 4 (his
  reference: «7 appearance options», a big G1, the others G2–G7 with their names). Then: "each must have its own place
  (a frame, a «зірочка») — I'll arrange them exactly later", and "it can stay with its white background, no cutting".
- Decided: slide 7 exists only for a Workshop book whose hero has **two looks or more** (`agent/variants/*/hero.png`);
  seven frames `hero:1…7` filled by the looks' numbers, the name from the folder («B2_blond» → «B2»); an empty frame shows
  only in the editor. The big one is a whole-body card, the six — scalloped frames with the head and shoulders. Old
  schemes get slide 7 recoloured from their own slide 4. In `etsy/` it is `15 Listing 7.png` — **last in the numbering**; the owner
  puts it into the listing himself. The texts are defaults he rewrites in the editor.

## 2026-10-03 — The portable Book Studio is back, in its own folder

- **The owner** took the portable copy up again: a folder `Book Studio Portable` on the Desktop with everything inside (Photoshop,
  templates, Python, Antigravity, Ollama, Upscayl, ffmpeg, Cent Browser); keys copied as they are; stage by stage, one stage
  per session (`ROADMAP.md` in its root). The original stays as it is. See [the portable copy](dev/portable.md).

## 2026-10-03 — Text check and upscaling are optional modules

- **The owner:** «давай зробимо ці штучки як модулі»: by default the program has neither Ollama (+ the model, ≈ 9 GB) nor Upscayl; the interface
  offers to install them where they would be used and the program installs them itself (quietly, from checked official files). A light PC
  (the colleague's) gets a program of ≈ 3 GB instead of 15. Also decided: Python is shipped with only the packages the program needs, ffmpeg
  with only `ffmpeg.exe`, Upscayl with its one model. See [optional modules](features/modules.md).

## 2026-10-03 — A copy for a colleague: the owner's rules become settings

- **The owner:** the program should be fit to hand to a colleague who owns a similar business (his own Etsy shop, Printify and Gelato; the
  Printify shop and defaults in the code are from his print shops the owner once worked on). The Kyiv option stays «only for me»; the
  colleague connects Etsy directly. Decided: `security.etsyKyivOnly` (default on) and `printify.readOnlyFrom` (default 2026-10-01,
  null = never) are settings; `make_colleague_copy.py` builds a copy without his data/keys/books/history with both switched off, **with**
  Photoshop and the mockup templates (the colleague paid for the mockups too; not commercial use).

## 2026-10-03 — Export/import of settings and keys, in both Book Studios

- **The owner:** a function in the ordinary and the portable program alike to move the settings and keys between computers/versions.
  Decided: only the settings, the keys and the slides' schemes (not books, orders or pictures); one 7-Zip file under the backup
  password, taken automatically. See [moving the settings](features/settings-transfer.md).

## 2026-10-03 — Edge instead of Cent Browser, and `AGENTS.md` only (the portable copy)

- **The owner:** the portable copy opens Gelato/Canva in the Edge that every Windows has, not in a carried Cent Browser;
  and the book pipeline's rules file is `AGENTS.md` alone, not a `GEMINI.md` twin, so any agent can use it. Antigravity's own
  data (`.gemini`) travels in the folder.

## 2026-10-03 — Keys in the portable copy: restored from the backup

- **The owner:** the keys do not travel in `vault.json` (Windows encrypts them for one user); on another PC they are brought back
  from the password-protected backup (`app/tools/restore_keys.py`), not by a new password vault. The start-up check says so.

## 2026-10-02 — The portable Book Studio is set aside

- **The owner:** «від портативки поки відмовися». The fully portable copy started on 2026-09-30 (its own folder on
  the Desktop, local git, no GitHub) is no longer there; the original `Book Studio` stays the only one. Not to be
  restarted without his word.

## 2026-10-01 (later) — a Gelato draft's card stays in the order card while its link lives

- **The owner**: the green card with all of a draft's details vanished once he left the Order Creator; he wants it to stay
  **while the temporary link lives**. He also wanted the yellow notice kept («Лиши»). Decided: the order card's print step
  shows the same card (`gelato-result.js`) until the link closes, then the short line. The button became «Замовлення в
  Gelato» (like «Замовлення в Printify»), one row with the copy and journal icons. The notice's text became true:
  Gelato fetches the files on its own within a minute (checked 17.09 and 30.09.2026), it does not wait for the draft to be
  opened. A first try with a small timer in the corner, without the yellow notice, was undone the same day: it was a
  misreading of a message typed without a Ukrainian keyboard.

## 2026-10-01 — Gelato and Canva open in the browser profile «Work»

- **The owner** asked that the «Gelato Dashboard» button open Gelato's orders list (`dashboard.gelato.com/orders/list`),
  not its home page, and that Gelato and Canva links open in one profile of his browser. The default browser on
  the Wrocław PC is Cent Browser (portable, Chromium); the profile he picked is «Work», which is the folder `Profile 6`.
- Decided: the settings' `browser` section (`exe`, `profile`, `hosts: gelato.com, canva.com`) is written once in
  `settings.json` and isn't shown in the interface, like other technical values. `_open_in_profile()` starts that
  browser with `--profile-directory`. If another site is opened, the section is empty, or the browser isn't found, the
  default browser opens the link as before. The Etsy block comes first and is unchanged.
