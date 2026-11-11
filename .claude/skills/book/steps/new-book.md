# A new book, led step by step

For a drip-fed start («нова книга» with little detail). The owner is not a writer or designer: one question at a time,
plain warm Ukrainian, no jargon, no step or agent names. After each step show the result simply and ask «Все гаразд?
Йдемо далі?» — move on only on his yes. Always offer the easy path: «Немає? Нічого — запропоную сам».
If he gives everything at once, skip the questions he has answered: sum up (point 2 below) and go. (The points are
turns of the conversation; "step 0"… are the pipeline steps in SKILL.md.)

1. **Brief** — the occasion, and a competitor listing or his own idea. Do not ask the child's name — it is `{Name}`.
   → write `input.md`, run step 0 (formula and tier).
2. **Direction** — «Це формула [..], нагода [..], тон [..]». For an unusual format (an anthology with custom stories,
   ABC) ask 5–7 short questions about his vision first (theme, what to include or avoid, tone). Then the **medium**:
   show `python pipeline/scripts/preset.py --list` in plain words; it is locked for all frames.
3. **Hero (Tier H only)** — a reference photo, a description, or an archetype → step 1, the canonical prompt; he
   generates `canonical.png`. Wait (the Hero stop). Tier S skips this.
4. **Story** — wishes, important moments, who to mention → step 2; show the spread titles as a short outline.
5. **Text** → step 3 and the critic; show the text, say what the critic changed and why.
6. **Prompts** → step 5 → GO, and how to generate (in the step file).
7. **Cover** — after the pictures: «Готові робити обкладинку? Надішліть найкращі кадри з розворотів» → `book-cover`.

He can always go back a step; redo that one file and keep the rest.

## `input.md`

```
# Book Production Input — <number>.<slug>

- **Listing Title / Concept:** [the competitor's title or his idea]
- **Source:** [the competitor's listing link / shop, what we keep and what we make our own]
- **Occasion:** [..]
- **Target Audience:** [who buys, for whom, US English, read aloud]
- **Hero / Protagonist:** [Tier S: the animals and their fixed look | Tier H: the child and the character source]
- **Child Placeholder:** `{Name}`
- **Gifter Placeholder:** `{Gifter}`
- **Visual Medium / Style:** [preset code — name; any one-line change to it for this book]
- **Tone:** [..]
```
