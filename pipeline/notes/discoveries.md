# Production Discoveries

Insights from research, competitor analysis, and testing.
These are production-relevant findings — not business analytics (those stay in Obsidian).

---

## Visual Style

**Watercolor wins over 3D.** The market data is clear: 3D-rendered books signal "AI-generated"
and underperform. Soft watercolor / hand-painted style reads as warm and trustworthy.
LittleStoryBloom had beautiful 3D books and zero sales. Watercolor competitors dominate.

**Book 01 established the house style: simplified pastel watercolor.**
The God's Love bedtime book finally locked the visual direction we want to reuse as the default:
soft pastel watercolor, smooth cream paper washes, airy negative space, simple childlike shapes,
low-to-medium detail, and one tiny friendly focal creature per spread.

Reference output: the God's Love book's spreads 02, 05, 09, 13 (book 3 of the old pipeline).

Why it worked:
- It kept the Etsy/nursery feeling soft and trustworthy.
- It left real usable text space without looking like a blank white box.
- The single tiny focal creature made landscape pages feel alive without turning them into a busy adventure.
- Low detail density is better for upscaling and avoids noisy flowers/grass/fur.
- The style stayed childlike and non-realistic while still looking premium.

Default future prompt language should include: `simplified pastel watercolor`, `smooth cream paper
washes`, `large calm negative space`, `simple readable shapes`, `low-to-medium detail density`,
`one clear tiny focal character`, and negatives like `no hyper-detailed botanical texture`,
`no realistic fur`, `no busy grass noise`, `no overworked background`.

---

## Image prompts — what works

**Minimalist "reference-only" prompts failed.** Short prompts that just said "use the
reference as the only source of character identity, don't redesign" produced generic,
inconsistent babies — the model ignored the reference and generated from the scene words.
Two-pass "generate scene, then swap the baby" also failed (it kept the realistic baby's
structure). Abandoned both.

**The verbose master-scene prompt is the working solution.** A full premium-publishing
structure — single continuous 2:1 spread, explicit CHARACTER CONSISTENCY feature list,
VISUAL STYLE with negatives, TEXT SAFE AREA, lighting/depth/emotional/quality blocks — is
what holds consistency and reads as premium. This is now the **sacred template**: every
image prompt is built on it. See `playbook/master-prompt.md`.

Generate all spreads in ONE chat with `canonical.png` attached as reference.

---

## JSON prompting — DEFAULT for Nano Banana 2

**Structured JSON prompts beat prose for character consistency.** A/B test on book 01 (same
canonical, same scenes: meadow finale, first steps, newborn): the JSON versions held the
character's signature features (big round rosy cheeks, button nose, curl volume, eye shape)
markedly closer to `canonical.png`. Prose drifted toward a "generic cute baby". Composition and
text-safe area were handled well by both. → **JSON is the only output format** (Agent 5);
the prose template was retired as dead weight.

Why it works: discrete fields = "separation of concerns" → no concept-bleeding; the character
object stays an isolated, intact identity anchor instead of dissolving into a paragraph.

Watch-outs:
- **Verify `aspect_ratio` is honored.** In testing a 2:1 spread came out 1:1. If it slips,
  also state the ratio in the request text, not only in the JSON.
- Keep the schema FLAT (Google's own guide prefers narrative and doesn't endorse JSON; deep
  nesting can be ignored). Keep the load-bearing fields from `master-prompt.md`.

**JSON canonical = the archetype engine.** When the canonical character render is itself JSON,
changing ONLY a `swappable_attributes` block (hair / eyes / skin / onesie color / gender) returns
the SAME child with just that one change — face, pose, blush, and style stay locked. Tested with
4 variants (green/blue onesie, blonde, blue eyes, girl) off one base — all clearly the same baby.
This finally unlocks the **archetype library** (one base → many variants) and **order-time
personalization**: Tier H = img2img-edit the demo spreads, swapping ONLY the child into the
customer's archetype (keep composition + text side; the swapped JSON guides it); Tier S = name-only.
Hygiene: use the real color only (no leftover words like "sage" before "pink"); never tag a
changed attribute as "identical to canonical".

## The center-fold / gutter line (2:1 spreads)

**Gemini may draw a vertical line when generator-visible text names publishing or multi-region
layout concepts.** Fix with positive image language only:
- Call it ONE wide panorama, a single continuous environment edge to edge.
- Do not repeat the unwanted concepts in `negative[]`; naming them can still prime their visual
  structure.
- Use one scene-wide continuity anchor — a horizon, runway, reflection, shoreline, cloud band,
  hill ridge, light path, or atmospheric wash — that travels through the full image.
- Keep strong vertical architecture and abrupt lighting changes away from the geometric middle.
This matters doubly because the Workshop slices the 2:1 into two squares exactly at the center
— a drawn line would ruin both halves.

## Text

**The word "fair" caused a 1-star review for a competitor.**
A page with a white doll and the text "...so sweet and fair. One day she'll grow as fair as her"
was read as racist by a buyer of a dark-skinned child's book.
"Fair" means both "beautiful" and "light-skinned" — never use it to describe a child's beauty,
skin, purity, goodness, or appearance.

Important nuance: this is **not** a global word ban. Words like `light`, `dark`, `white`, and
`pale` are normal and useful for scenery (`morning light`, `dark sky`, `white paper`, `pale
blue flowers`). The safety rule is about skin/appearance/purity/goodness contexts where a buyer
may read the line racially. Full context rule: `playbook/knowledge/text-rules.md`.

**Book 01 text polish: simple does not mean generic.**
The first God's Love bedtime book exposed the difference between "acceptable rhyme" and
publication-worthy read-aloud text. The winning lines were short, concrete, and emotionally
anchored:

```
God's love wakes the morning
with honey-colored light.
A little bee hums low and slow,
and everything feels right.
```

and:

```
Mountains stand with patient hearts,
steady, calm, and tall.
God's love is strong beneath your feet, {Name},
and holds you when you fall.
```

Why these worked:
- **Concrete image first.** Morning light, bee hum, mountains, feet, falling: the parent can
  instantly picture the page and read the line without decoding it.
- **One emotional verb per spread.** Wakes, returns, moves, holds, shelters, watches. The verb
  carries the theology more naturally than explaining the theology.
- **Rhyme is quiet, not showy.** `light/right`, `tall/fall`, `appear/near` are simple and stable;
  they do not twist the sentence to land.
- **{Name} belongs at the emotional hinge.** It worked best when placed where the promise turns
  toward the child: "beneath your feet, {Name}" / "God watches over you, {Name}".
- **Small sonic softness matters.** Phrases like "hums low and slow" read gently aloud and match
  bedtime pacing.

What failed before polish:
- Repeating the same nature family (flowers in too many spreads) made the book feel thin.
- Lines that were individually pretty but unrelated ("moonlight..." then "quiet rooms...") felt
  pasted together. Every stanza needs a bridge from image to promise.
- Some lines were technically grammatical but awkward in the mouth ("The fawn curls close...")
  and had to be simplified.
- Overusing sleep/rest/nest near the end flattened the bedtime arc; save sleep language for the
  final turn toward bed.
- Avoid weakening the strongest line only to insert `{Name}`. If a line is excellent, keep its
  structure and place `{Name}` at the natural emotional hinge.

**Formula B / bedtime sequencing lesson.**
Nature-metaphor books need a clear invisible progression, especially bedtime books. A random
set of pretty nature images causes repetition. A morning-to-night arc fixes this:
morning garden → shore/breeze/rain → mountains/afternoon shade → sunset home → dusk fireflies →
night deer/moonlit pond → sleep/finale. The reader feels the day closing, even without a plot.

---

## Market

**"Daddy and Me / Mommy and Me"** had explosive sales at a store just 1 month old.
High signal — worth creating dedicated Formula A (modified) listings early.

**Personalization is the #1 purchase driver**, even above visual quality.
A well-personalized listing with mediocre art outperforms a gorgeous book without personalization.

**SEO/tags matter more than catalog size.**
LittleStoriesBooks: 166 sales in month 1 with 28 listings.
LittleStoryBloom: 0 sales with 10 listings and better art quality.
Difference: discoverability, not product quality.

