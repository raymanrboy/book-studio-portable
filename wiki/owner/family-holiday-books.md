---
title: Five family and holiday books (47–51)
type: owner
updated: 2026-11-01
code: []
---
# Five family and holiday books (47–51)

> The owner asked (2026-11-01) for five new Workshop books, each about a holiday or the child with Mom, Dad, Grandma
> or Grandpa, taken from the competitors' examples — and **with no human characters** ([decisions](../decisions.md)).
> All five are animal books, Tier S (no `canonical.png`, only `{Name}` is typed in), made by the book pipeline
> (`pipeline/AGENTS.md`) up to GO: formula, blueprint, text, the 14 + 2 prompts, the book check with 0 FAILs.

## The five books

| Workshop | Book | Who | Style | Occasion — when to list | Seen at |
|---|---|---|---|---|---|
| **47** | {Name} & Daddy: Our Big Adventure Day — a day of fishing, a canoe and camping | the little bunny and Daddy Bunny | CG | Father's Day, Dad's birthday, Christmas for Dad — any time | T: [Day with Daddy](../raw/2026-10-11-day-with-daddy-listing/2.png) (the owner: not golf — fishing, the forest) |
| **48** | Mommy & {Name}: Our First Christmas — a first Christmas season, snow to Christmas morning | the little otter and Mommy Otter | FG | Christmas, a new mom's first Christmas — **now** | L: [First Christmas as Mom](../raw/2026-10-11-lunabooksus-book-pages/first-christmas-as-mom/01.jpg) |
| **49** | {Name} & Grandpa: Our Best Days (the owner's title order) — a year on Grandpa's farm, spring to spring | the little bear (as in 46) and Grandpa Bear | WP | Grandpa's birthday, Father's Day, Christmas — any time | L: Grandpa line; the pair of our [46](book-ideas.md) |
| **50** | {Name}, Our Little Valentine — one Valentine's Day with Mommy and Daddy | the little hedgehog, Mommy and Daddy Hedgehog | CG | Valentine's Day — by mid-January | backlog row 36; L: "How Much I Love You" |
| **51** | Welcome to the World, Little {Name} — a newborn fawn, and every woodland family brings a gift | the little fawn, Mama Deer, a bluebird, one animal family per scene | RW | a new baby, baby shower, a baby's Christmas — **all year** | T: [Welcome to the World](../raw/2026-10-11-welcome-to-the-world-listing/2.png) |

The styles are the presets in `pipeline/playbook/knowledge/media-presets.md`. **48 changes one line of `FG`**: its `forms` describes
children, so in this book it describes dressed animals (the rest of the block is verbatim) — written in its `input.md`.
**51 is `RW` (Rich Watercolor) with stylized animals, not the competitor's `CG`**: the owner didn't like the polished glow, asked for a
softer watercolor and a more stylized art (it was `W` for a while), then for the same stylization with a bit more color. Its `forms` line is
the stylized one — simple rounded shapes, tiny dot eyes, no fur strands — and the cast descriptions have no "big glossy eyes"; glossy,
airbrushed and fur-strand looks are in its negatives.

**The owner's changes the same day:** 47 — bunnies instead of the competitor's foxes; 48 — otters instead of deer; 51 — the Easter book
("Easter is far, something more universal") swapped for **Welcome to the World**, the competitor's book the owner had marked as "the same
style and the same idea". The Easter book (bunnies at Grandma and Grandpa's, ready to GO) is parked in `pipeline/books/_later/easter-at-grandmas/`
— a folder starting with `_` is hidden from the Workshop; give it the next number and move it back into `books/` in early March.

## What makes each one ours, not a copy

- **47:** the competitor's foxes play golf, toss the kit up and make pancakes; ours are bunnies who pack a backpack, fish from a dock,
  paddle a canoe, build a stick fort, play leapfrog, camp and watch the sunrise.
- **48:** LunaBooksUS draws a human child and the cookies in an oven window; ours is an otter family: gingerbread fish, a snow-otter
  wearing Mommy's scarf, a tummy slide down the riverbank, holding paws at goodnight, the scarf around both at the end. The dedication is
  signed by the child to Mommy.
- **49:** a whole farm year instead of one day, so it doesn't repeat 46 (no birdhouse, seed row or berries); the same little bear and
  style make the two a pair ("Grandma & {Name}" and "Grandpa & {Name}").
- **50:** no competitor book behind it — the backlog's own seasonal idea in the shops' family-love format.
- **51:** the competitor's animals make the world ready (acorn lights) and gather round an empty glowing nest; ours draw the baby as a
  newborn fawn, and each family brings its own gift (a flower crown, a moss blanket, a dandelion pillow, a cradle, a song, berries, a dance,
  a lit path, a lullaby), all in the cradle at the end, and a new star appears. Both scenes of theirs are in the prompts' negatives.

## One book → more listings

The word for the adult is plain text, so a Canva text swap makes another listing with the same pictures: **Daddy → Papa / Dad** (47),
**Mommy → Mama** (48), **Grandpa → Papa / Grandad** (49). A Mommy → Grandma swap is not possible without new pictures: the adult is drawn.
51 has no family word: one book for "new baby", "baby shower", "baby's first Christmas" listings.

## Open points

1. Nothing is generated yet: per book, generate **one** frame first and compare it with the style's references.
2. The casts hold together only by the written description in every prompt (Tier S); 50 has three characters and 51 a new animal family
   per scene, so a drifting frame is regenerated or the best frame attached as a reference.
3. The text was written and checked by one agent (a script counted syllables) — worth a native-English read.
4. No listing SEO yet (`/etsy-seo`). Cover prompts — Agent 6 after the pictures.

## 49 — the cover

The owner renamed it «{Name} & Grandpa: Our Best Days» (the name first) and picked three frames: spread 04 (the sailboat on the creek,
pages 6–7), spread 05 (the kite, 8–9), spread 08 (watermelon on the porch, 14–15). They are stacked into one reference
(`agent/ref_cover_hybrid-06-07-08-09-14-15.jpg`) and the scene blends them: on the right Grandpa on the creek bank with the little bear on
his knee flying the fish kite, the squirrel and the robin; on the left the kite in the sky, the porch with watermelon and geraniums, the
creek with the toy sailboat and the footbridge. Painted: «& / Grandpa / Our Best Days»; the name goes into the empty room above (the
tool's default guide «Ім'я, під ним назва»).

## 50 — the cover

The pictures of 50 are generated. The owner picked three frames — spread 02 (pancakes, pages 2–3), spread 09 (the kitchen dance,
16–17), spread 11 (the wish on the star, 20–21) — and asked that **the Valentine's theme be on the cover**. So the three are stacked
into one reference (`agent/ref_cover_hybrid-02-03-16-17-20-21.jpg`, for the characters and the look only) and the scene is new: the
three hedgehogs in one hug on rosy snow, the little one holding a big red heart balloon, paper hearts drifting; on the left the home in
the oak roots with a heart wreath, a heart garland, a sled with valentine cards and heart cookies. Painted: «Our Little / Valentine»; the
name goes into the empty room above it (the tool's default guide «Ім'я, під ним назва»).

## 51 — the cover

The pictures of 51 are all generated. Its cover prompt (`agent/cover-prompts-json.md`, 2026-11-01) uses **the owner's hybrid of two
frames** — spread 02 (pages 2–3, the dawn news) and spread 14 (pages 26–27, the moonlit goodnight): the cover tool takes one reference,
so the two are put one above the other into one picture, `agent/ref_cover_hybrid-02-03-26-27.jpg`, and the prompt says to blend the
dawn mood of one with the moonlit gathering of the other and not to copy either composition. The scene: Mama Deer curled in the
ferns with the awake fawn and the friends around them on the right, a peach-gold dawn sky melting into a moonlit twilight on the left
with the gift-filled cradle. Painted: «Welcome to the / World / Little»; the name goes into the empty room under it (the tool's
default guide «Назва, під нею ім'я»).

## Related

- [Listing ideas backlog](listing-ideas.md) · [Book ideas](book-ideas.md) · [Christmas books](christmas-books.md) · [Workshop](../features/workshop.md)
