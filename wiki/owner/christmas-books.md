---
title: Five Christmas books and the two styles to copy
type: owner
updated: 2026-10-11
code: []
---
# Five Christmas books and the two styles to copy

> From the [ideas backlog](listing-ideas.md) the owner picked the Christmas season to focus on (2026-10-11): five books, and for them **the visual
> style of the two shops — TheChildhoodKeeper ("A") and LunaBooksUS ("B") — copied as exactly as possible**. The two styles are written as locked
> `style{}` presets for the book pipeline (`CG` and `FG` in
> [media-presets.md](../../pipeline/playbook/knowledge/media-presets.md)), so every picture of a book gets the same long description.

## The five books

Christmas demand on Etsy builds from now; the aim is to have the first listings up in about two weeks. "Tier" is the pipeline's: **S** = animals, only
the name is typed into the text (no per-order generation); **H** = a child character that must look like the buyer's child.

| # | Book | Style | Tier | Listings it gives | Seen at |
|---|---|---|---|---|---|
| 1 | **The Night Before Christmas, the (Family)'s** — the old poem retold for a family; woodland animals; the names are on the stockings | A | S | 3 (one child · brothers and sisters · the whole family) | L: [pages](../raw/2026-10-11-lunabooksus-book-pages/night-before-christmas-family/01.jpg) |
| 2 | **First Christmas as Mom / Dad / Grandma / Grandpa / Aunt / Uncle** — the child tells the adult about the first Christmas together | B | H | 6 (one interior, six covers) | L: [pages](../raw/2026-10-11-lunabooksus-book-pages/first-christmas-as-mom/01.jpg) |
| 3 | **Goodnight, Christmas Eve** — woodland animals settle down to wait for Santa; the child is the little (Name)-cub | A | S | 2 | T: [woodland goodnight](../raw/2026-10-11-thechildhoodkeeper-book-pages/woodland-bedtime-foxes/01.jpg); L: [Goodnight Little Bear](../raw/2026-10-11-lunabooksus-book-pages/goodnight-little-bear/01.jpg) |
| 4 | **Christmas with Grandma** (and with Grandpa) — a bear grandma and grandchild bake, decorate, make a snowman, cocoa on the porch swing | A | S | 3 (Grandma · Grandpa · "Nana") | owner's [Grandma bears](../raw/2026-10-11-grandma-bear-listing/1.webp); L: [Christmas as Grandma](../raw/2026-10-11-lunabooksus-book-pages/family-dad-rainbow-template/01.jpg) |
| 5 | **Where's (Name)? Christmas Search & Find** — five snowy worlds with things to find | B | H | 2 | L: [search & find](../raw/2026-10-11-lunabooksus-book-pages/search-and-find-toddler/01.jpg) |

Why these: all five are dated to Christmas, none is in the owner's shop (his "Baby's First Christmas" and "Nativity" stay), 1–4 are cheap in art
(one interior gives several listings; 1, 3, 4 are animals = Tier S), and between them they show both styles. **#5 is the riskiest**: a seek-and-find
needs a dense scene where the hidden things are really there, and a generator doesn't count; each scene would be checked by hand. If it proves too
much, swap it for a simpler "spot the star" book with three things to find per scene.

### The beats (the spreads, in short; the pipeline's agents write the text)

1. **Night Before Christmas:** the snowy forest house at dusk · stockings with names by the fire · tucked in, sugar plums · a clatter on the roof ·
   Santa and the sleigh · down the chimney · filling the stockings · a wink, up the chimney · Christmas morning.
2. **First Christmas as …:** the cookies in the oven window · the tree · wrapping gifts · Santa's lap (the beard) · opening the presents · candles in
   the evening · "your love is sweeter than any treat" · a hug. (The relation — Mommy / Daddy / Grandma … — is a placeholder in the text.)
3. **Goodnight, Christmas Eve:** a hedgehog under snowy pines · an owl and her owlet · a fox den · a deer by the frozen stream · lanterns and snow
   sparkles · the sleigh's bells far away · the (Name)-cub falls asleep · morning light.
4. **Christmas with Grandma:** baking cookies · trimming the tree · wrapping · making a snowman · painting a card · hot cocoa on the porch swing under
   lights · carols by the fire · Christmas morning · goodnight on the swing.
5. **Search & Find:** Santa's workshop · a snowy village · the ice pond · the gingerbread town · the sky over the North Pole.

All five can carry "Christmas gift" and "New Year" in the listing title and tags — the owner's "New Year" is the same season, not a separate book.

## In the Workshop (2026-10-11)

The three animal books were taken through the pipeline's agents (0, 2, 3, 4, 5) at the owner's request and wait in the Workshop («Майстерня») as
**38** (Night Before Christmas), **39** (Goodnight, Christmas Eve) and **40** (Christmas with Grandma). For each: the formula, the story
(14 scenes), the text (6 rhymed lines per spread, a dedication and an afterword), the 14 panorama prompts and 2 square prompts are filled and the
book check says GO (0 FAIL, 0 WARN); the steps from «Картинки» on are still to do — **the pictures are the owner's to generate**. The style is
`CG` in all three.

- **38 — {Name}'s Night Before Christmas:** a fox family in a cottage in an old fir; the star stocking stands for {Name}; Santa is only a far silhouette,
  a red mitten, a boot and a sack — **no face is ever drawn**. One child's version; the family/siblings variants need only a rewritten text, the pictures stay.
- **39 — {Name}'s Christmas Eve Goodnight:** a little golden starlight visits a different woodland animal at every stop, then the sleigh bells, gifts at
  every door and a forest Christmas tree; {Name} is in the text only.
- **40 — {Name}'s Christmas with Grandma:** {Name} is the little bear (Formula C, the child as an animal, no he/she), Grandma Bear has her own look
  (a snowflake sweater and a holly apron, no glasses) so she is not TheChildhoodKeeper's grandma; the knitted scarf of Spread 07 pays off in 14.
- **Open points:** (1) the style was written from pictures — generate one frame per book style before the whole thing; (2) the two bears (and the fox
  family) hold together only by a fixed written description, so a drifting picture is regenerated or the best frame is attached as a reference; (3) the
  text was written and checked by one agent (syllables counted by a script, no second reader) — worth a native-English read; (4) no listing SEO yet
  (`/etsy-seo` when the owner asks).

## Style A — TheChildhoodKeeper (the cozy glow)

References: [foxes](../raw/2026-10-11-thechildhoodkeeper-book-pages/woodland-bedtime-foxes/02.jpg) ·
[cowboy](../raw/2026-10-11-thechildhoodkeeper-book-pages/cowboy-bedtime/03.jpg) ·
[fairy](../raw/2026-10-11-thechildhoodkeeper-book-pages/fairy-stardust/03.jpg) ·
[little ghost](../raw/2026-10-11-thechildhoodkeeper-book-pages/halloween-little-ghost/01.jpg) ·
[big sister](../raw/2026-10-11-thechildhoodkeeper-book-pages/twin-siblings/01.jpg) · the owner's own screenshots
([bears with grandma](../raw/2026-10-11-grandma-bear-listing/4.webp), [foxes](../raw/2026-10-11-day-with-daddy-listing/2.png)).

What makes it this style (read from the pictures):

- **Digital painting that imitates watercolour, gouache and colour pencil, very smooth and polished.** No outlines; shape comes from changes of
  colour. Fine pencil-like strokes only inside fur, hair, knitwear and leaves.
- **Light is the star:** warm golden-hour backlight, window glow, soft rays through trees, lanterns, floating sparkles and fireflies; twilight
  scenes in luminous violet-indigo. Never harsh.
- **Characters:** round, big head, large dark glossy eyes with one highlight, tiny nose, pink blush, a gentle smile. Animals wear human clothes
  (cardigan, scarf, floral apron, round glasses, a hat); the human child has pigtails and a knit or dungarees.
- **Colour:** warm amber, peach, dusty rose, lavender, sage and eucalyptus, chestnut brown, deep violet-blue; one saturated warm accent (the
  orange fox, red plaid) against soft surroundings.
- **Layout of a spread:** one side is the picture, the other is a **soft colour wash taken from the picture's palette** (peach, lavender, sage,
  night indigo) with a few drifting leaves, petals, dandelion seeds or sparkles. The text is **bold rounded capitals** in near-black on light
  washes and white on night washes (or a script for the fairy tale), centred or left-aligned in short lines.
- The pipeline's own `GW` (Glowing Watercolor) is the nearest preset but is rougher and rawer; `CG` adds the smoothness, pencil fur and the dressed
  animals.

## Style B — LunaBooksUS (the bold festive gouache)

References: [cookies in the oven](../raw/2026-10-11-lunabooksus-book-pages/first-christmas-as-mom/01.jpg) ·
[the tree](../raw/2026-10-11-lunabooksus-book-pages/first-christmas-as-mom/03.jpg) ·
[Santa's lap](../raw/2026-10-11-lunabooksus-book-pages/first-christmas-as-mom/06-from-dad-listing-06.jpg) ·
[Santa on the roof](../raw/2026-10-11-lunabooksus-book-pages/night-before-christmas-family/01.jpg) ·
[the bears' stairs](../raw/2026-10-11-lunabooksus-book-pages/night-before-christmas-family/04.jpg) ·
[the flight over cities](../raw/2026-10-11-lunabooksus-book-pages/night-before-christmas-family/05-from-night-before-2-03.jpg) ·
[search & find](../raw/2026-10-11-lunabooksus-book-pages/search-and-find-toddler/03.jpg) (the shop's "not AI" art — we copy the look, not the claim).

What makes it this style:

- **Opaque gouache-like shapes with chalky crayon and dry-brush texture** — fir needles drawn as crayon strokes, snow and fur as rough
  brush; no black outlines, edges are separated by colour and a light rim. Often the picture sits in a **ragged painted vignette** on a pale
  ground.
- **Saturated festive colour:** fir green, cranberry red, mustard and gold, teal, violet, cream, peach, powder blue — on warm gradient backdrops
  (peach to butter yellow, blush pink, pale sky, deep indigo night) scattered with **gold four-point stars, moons and sparkles**.
- **Characters:** stylised, big round heads, **large oval black eyes with a white highlight, round pink cheeks, wide open smiling mouths**, small
  bodies; a diverse set of hair and skin tones; Santa with a long wavy white beard, glasses and fur trim.
- **Props are bold and patterned:** wrapped gifts (dots, waves, stripes), garlands with red berries and gold beads, string lights, stockings,
  wreaths with a red bow, a tray of cookies.
- **Light:** the glow of the oven, fireplace and candles, warm orange against cool blue-violet snow-night.
- **Layout:** a pale tinted text page with **small serif text** in short stanzas and stars or ornaments at the edges, facing a full picture; or a
  picture running across both sides.

## Copy the style, not the book

The style (medium, colours, light, proportions, layout) is free to follow. What we must not reproduce is a particular shop's **characters, scenes and
text**: the poem "A Visit from St. Nicholas" is old and free, but LunaBooksUS's bear family and TheChildhoodKeeper's grandma-bear book are theirs —
ours use their own animals, own scenes and own words. Close clones of a single book invite an Etsy report; an own book in the same style is safe.

## How to check that it is "almost ideal"

The presets were written from the pictures, not tested: no image has been generated yet. Before a whole book: generate **one** frame per style
(a Christmas tree scene with a child, or a woodland animal under snowy pines), put it next to the reference pictures above, and compare the ten
things listed under each style. What differs goes into the preset's `style{}` (the pipeline's rule: the long block is pasted verbatim, never
shortened). The generation is the owner's, in Nano Banana; the pipeline's GO/NO-GO step is the place for it.

## Where in the pipeline

- [media-presets.md](../../pipeline/playbook/knowledge/media-presets.md) — `CG` and `FG`, the blocks to paste into every prompt of a book.
- [visual-world-bible.md](../../pipeline/playbook/visual-world-bible.md) — the house style (soft pastel watercolour) that `CG` and `FG` leave: a book
  with one of them says so in its `input.md`, as book 28 does for its own style block.

## Related

- [Listing ideas backlog](listing-ideas.md) · [Book ideas](book-ideas.md) · [Workshop](../features/workshop.md)
