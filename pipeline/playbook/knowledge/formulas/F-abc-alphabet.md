# Formula F - ABC Alphabet Square Book

## Concept

A personalized alphabet keepsake built from standalone square illustrations: one opening dedication
image, one image for each letter A-Z, and one closing afterword image.

This is a format exception. It does not use the standard 14 panorama sequence or slicing workflow.

The emotional core: "Every letter becomes a tiny joyful moment for {Name}."

---

## Best For

- Personalized ABC books
- Alphabet train / animal alphabet listings
- First birthday alphabet keepsakes
- Toddler learning gifts where the child name is placed in the text

---

## Tier

Always default to Tier S unless the user explicitly asks for the same child to appear visually on
every letter image (Tier H). If Tier H is chosen, a canonical.png must be created in the book's `agent/` folder,
and character prompts must reference it for consistency.

No `canonical.png` is required. Consistency is carried by:
- one art medium
- repeated square composition
- the same typographic overlay system in Canva
- friendly animal/object motifs

---

## Structure

Internal production structure:

```
Dedication
Letter A
Letter B
...
Letter Z
Afterword
```

Generated image count: **28 square 1:1 illustrations**.

No 2:1 story panoramas. No slicing. No wraparound prompt is part of this formula unless the user
asks for a separate outer image later.

---

## Text Pattern

Each letter gets a short 1-2 couplet stanza:

```
{Name} and [animal/object] [simple action],
[warm sensory detail / tiny rhyme / playful sound].
```

Use `{Name}` often, preferably on every letter image for maximum personalization. Keep the text
short enough for large toddler-safe typography.

---

## Image Prompt Rule

ABC is the exception to the usual no-letter rule.

For each A-Z image, the generator should draw exactly one large readable uppercase Latin letter.
The letter is part of the art: oversized, hand-painted, dark muted navy/charcoal or a soft accent,
with the animal/object overlapping or interacting with it.

Canva still owns:
- child name
- stanza text
- dedication text

The generated art must not contain words, child names, stanza text, numbers, signs, labels, logos,
or extra alphabet characters.

---

## Visual Notes

Use soft watercolor, warm cream paper, simple rounded animal shapes, one dominant large letter, and
minimal tiny flowers/leaves/dots. Keep each square readable at thumbnail size.

Vary animals, objects, pose, and accent colors from letter to letter while preserving the same
overall nursery-watercolor style. Avoid heavy side decoration; the composition is letter + one
animal/object first.
