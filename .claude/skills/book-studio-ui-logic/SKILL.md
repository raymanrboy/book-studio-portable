---
name: book-studio-ui-logic
description: The owner's interface logic for Book Studio — use before adding, moving or labelling ANY control, caption, tab, chip, button, icon or screen in app/web, and when reviewing one. Show don't tell (icons over words), a label must do what it says, nothing redundant, the real state not the rule's guess, one loud button per screen, light theme first. Born from the owner's corrections of 2026-09-30.
---

# Book Studio — interface logic

The owner is not a designer and cannot always say *why* something is wrong — he feels it ("глупості", "бред",
"не інтуїтивно"). These are the rules behind those feelings, each with the case that taught it. Apply them **before**
writing UI, not after he finds the problem. They sit on top of the general skills (`product-design`, `uxcraft`,
`laws-of-ux`, `ux-heuristics`, `impeccable`); when they disagree, these win — they are his.

## 1. Show, don't tell
The interface **shows** with icons, position, colour and state; it **tells** with words only when nothing else can.
- Navigation and filters are icons (+ a count); the word lives in the tooltip (`data-tip`) and appears as text only on the
  *chosen* one (`segHtml(..., {compact: true})`). The page's own title already says where he is, so a rail label is noise.
- A path or status is a row of pictures (`pathHtml` with `icon`), not sentences. Never a sentence that explains what the
  picture already shows.
- Before adding a caption ask: could an icon + tooltip, a colour, a position or a state carry this? If yes, no caption.
- *Taught by:* the rail labels, the queue's tab words, «Далі: Canva» on rows, «Оновити» — "стало більше написів".

## 2. A label must do what it says
A control named with a verb performs that verb. If the click only **opens the details**, it is not named after the action.
- «Позначте в Etsy» on a row promised an action but just opened the order — and everything needed (the copyable tracking
  chips) was already in the row. That is *worse than nothing*: it teaches the owner that labels lie.
- If the action can be done right where the eye is, put the action there (copy on click); if it cannot, say nothing and let
  the row be a row.

## 3. Nothing redundant
Every element must earn its place by telling something the screen does not already tell.
- Two ways to the same thing, a sentence repeating a chip, a label beside an icon that means the same → delete one.
- Before adding, list what already shows this fact on the screen. Subtract first (the subtraction test of
  `cognitive-load-audit`).

## 4. Show the real state, not the rule's guess
A chip, badge or sentence that states a fact must read it from the **fact** (`o.provider`, the printer's status, the file
check), never from a rule that predicts it (`plan().provider`). A prediction is shown only before the fact exists, and
looks like a suggestion.
- *Taught by:* a Gelato order whose card said «Printify · 24 стор.» (2026-09-30) — the printer rule's answer shown after the
  order had been placed somewhere else.
- When writing a chip: name the field it reads; if a rule feeds it, what happens after the order exists?

## 5. One loud button per screen
The accent colour is the **next step**. Two accent buttons read as two next steps (the Workshop's «Папка книги» was loud
beside «Передати в бібліотеку»). Everything else is quiet: a bordered button, or an icon with a tooltip. Orange/cyan never
paints a *number* (the average margin) — the ink means "you can act here".

## 6. Places, objects, tools
- A **place** (rail): where things live — Замовлення, Книги, Прибуток. An **object** (an order, a book) has one home and its
  path on top; its next step is the loudest thing. A **tool** works alone *and* inside its object (opened from the object's
  step it carries the object, goes back to it, keeps its place lit — `navFor()`).
- Search is the **last** of the list (an action, not a place).
- Never two routes to the same page; the old address leads to the new one (`ALIASES`).

## 7. A button never ignores a press
No silent grey buttons: stay pressable, say what is missing, light the field (`markMissing()`).

## 8. The LIGHT theme is the main one
Design, screenshot and judge **light first**, then dark. Contrast, inks, surfaces, shadows, icon weight — all checked in
light. (Set it on the preview server: `post('/api/settings/ui', {theme: 'light'})`.)

## 9. Before you finish a UI change — the check
1. Who clicks this, what do they expect, what really happens? (Rule 2)
2. What already says this on the screen? (Rule 3) Where does the data come from — fact or rule? (Rule 4)
3. Can it be an icon? (Rule 1) How many captions did I add? How many can go?
4. One loud button? (Rule 5) Light theme screenshot, then dark, three widths (≥1280, 961–1279, ≤960).
5. The wiki: `wiki/owner/ui-principles.md` and the page of the feature, `decisions.md` if it revises a choice.
