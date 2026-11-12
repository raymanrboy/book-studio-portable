---
title: Workshop books 38–55
type: owner
updated: 2026-11-12
code: []
---
# Workshop books 38–55

> The books the owner picked for Christmas, family occasions, Valentine's Day, new babies and the faith line: each is a folder in `pipeline/books/` made by the `book` skill, shown in the [Workshop](../features/workshop.md). This page holds what a book is about, its characters, style and season; where a book stands is the Workshop's to say.

## Two kinds of books
- **Animal books (Tier S):** the characters are animals (or elves, a snowman); the child is the little animal of the book, and only `{Name}` is typed into the text, with no he/she, so one book fits boys and girls. No per-order picture is made. Books 38–40 and 42–55 are of this kind.
- **Child-hero books (Tier H):** the hero is a human child who must look like the buyer's child (book 41). The pipeline stops at its first hard stop until `agent/canonical.png` exists; the `book_guard.py` hook refuses the story, text and prompts before that (`DRAFT - NOT READY` files excepted).

Santa is never drawn with a face in books 38, 43, 44 and 45 (a far silhouette, a red mitten, a boot, a sack); in 41 he has a face from a written description.

## Styles
The style codes are the presets of [media-presets.md](../../pipeline/knowledge/media-presets.md); the long block is pasted verbatim into every prompt of a book.

| Code | Look |
|---|---|
| `CG` Cozy Glow | polished painting with golden light, dressed animals |
| `FG` Festive Gouache | bold gouache with crayon and dry-brush texture, gold stars, festive colour |
| `CP` Colored Pencil & Glowing Pastel | pencil and chalk on midnight paper, aurora and lanterns |
| `WP` Watercolor & Pencil Cottage | transparent watercolor over sepia pencil, muted cottage colours |
| `RW` Rich Watercolor | luminous watercolor; "stylized" books rewrite its `forms` line (simple rounded shapes, dot eyes, no fur strands) |

Book 48 changes one line of `FG` — `forms` describes dressed animals instead of children. Books 47–51 are the competitor-inspired family and holiday set; the style is copied, never a shop's characters, scenes or text (the poem "A Visit from St. Nicholas" is free; a shop's bear family or grandma-bear book is theirs). A close clone of one book invites an Etsy report.

## The books
| # | Title | Characters | Style | Season or occasion |
|---|---|---|---|---|
| 38 | {Name}'s Night Before Christmas | fox family in an old fir; the star stocking stands for {Name} | CG | Christmas |
| 39 | {Name}'s Christmas Eve Goodnight | a golden starlight visits woodland animals | CG | Christmas Eve, baby and toddler |
| 40 | {Name}'s Christmas with Grandma | the little bear and Grandma Bear (snowflake sweater, holly apron, no glasses) | CG | Christmas; Grandma, Grandpa, "Nana" listings |
| 41 | {Name}'s Night Before Christmas — the child, Santa and the reindeer | one human child (Tier H), boy/girl, skin and hair options | CG | Christmas |
| 42 | {Name} and the Christmas Snowman | a snowman and a robin | FG | Christmas |
| 43 | A Letter from Santa for {Name} | elves and reindeer; Santa's rhymed letter, never his face | CP | Christmas |
| 44 | {Name}'s Toy from Santa's Workshop | Pip the elf and a star-shaped music box | FG | Christmas |
| 45 | {Name}'s Wish Star and the Little Reindeer | a lost reindeer calf, a hare, a fox, an owl | CG | Christmas |
| 46 | Grandma & {Name}: Our Happy Days | the little bear and Grandma Bear, a day together | WP | any time; Grandma's birthday, Mother's Day |
| 47 | Daddy & {Name}: Our Camping Adventure | the little bunny and Daddy Bunny: backpack, fishing, canoe, stick fort, camping | CG | Father's Day, Dad's birthday, any time |
| 48 | Mommy & {Name}: Our First Christmas | the little otter and Mommy Otter: gingerbread fish, snow-otter in Mommy's scarf | FG | Christmas, a new mom's first |
| 49 | {Name} & Grandpa: Our Best Days | the same little bear and Grandpa Bear, a farm year spring to spring | WP | Grandpa's birthday, Father's Day, any time |
| 50 | {Name}, Our Little Valentine | the little hedgehog, Mommy and Daddy Hedgehog | CG | Valentine's Day, listed by mid-January |
| 51 | Welcome to the World, Little {Name} | a newborn fawn, Mama Deer, a bluebird; each woodland family brings a gift | RW stylized | new baby, baby shower, all year |
| 52 | Grandma's Christmas Prayer for {Name} | the little lamb, Grandma Sheep; Advent, a straw for each kind deed | WP | Christmas, a Christian gift from Grandma |
| 53 | Noah's Ark: God's Promise to {Name} | a little dove, pairs of animals | RW stylized | baptism, dedication, birthday, rainbow baby, all year |
| 54 | Mommy's Prayer for {Name} (Psalm 91:4) | the little chick, Mommy Hen | WP | baptism, dedication, Mother's Day, Christmas |
| 55 | Be Brave, {Name} (Joshua 1:9) | the little lion cub, Daddy Lion | RW stylized | baptism, Father's Day, Christmas, birthday |

## Rules inside single books
- **38:** no face of Santa is ever drawn. **40, 46, 49:** the child is the little bear; Grandma Bear has her own look so she is not a competitor's grandma. 49 is a whole farm year, so it does not repeat 46; the same bear makes the two a pair.
- **47:** a day of fishing and camping, not golf; bunnies, not foxes. **48:** the dedication is signed by the child to Mommy. **50:** the Valentine's theme sits on the cover.
- **51:** `RW` with stylized animals (a softer, more stylized look than the competitor's polished glow); glossy, airbrushed and fur-strand looks are in its negatives.
- **52:** Mary, Joseph and the Baby are never drawn: the stable shows only golden light from its doorway; no angels, no crosses. **53:** Noah is in the text only, never drawn; the storm stays calm and safe. **54:** no hawk or fox; every scare ends under the wing on the next spread. **55:** the cub has no mane (one book for boys and girls); no hunting, no fangs.
- Faith wording is ecumenical; the Bible references are in each book's `text-critic-report.md`.
- The casts hold together only by the written description in every prompt (Tier S): a drifting frame is regenerated, or the best frame is attached as a reference. The text is written and checked by agents; a native-English read is worth it before sale.

## One book, more listings
The word for the adult is plain text, so a Canva text swap makes another listing with the same pictures: Daddy → Papa / Dad (47), Mommy → Mama (48, 54), Grandpa → Papa / Grandad (49). Mommy → Grandma is not possible without new pictures, because the adult is drawn. 51 has no family word: one book for "new baby", "baby shower" and "baby's first Christmas" listings. A Christmas book can carry "Christmas gift" and "New Year" in the title and tags.

## Parked
An Easter book (bunnies at Grandma's and Grandpa's) sits in `pipeline/books/_later/easter-at-grandmas/`; a folder starting with `_` is hidden from the Workshop.

## Related
- [Ideas backlog](ideas.md) · [Workshop](../features/workshop.md) · [Cover](../features/cover.md) · [SEO](../features/seo.md)
