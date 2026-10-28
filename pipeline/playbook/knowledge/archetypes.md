# Archetype Library — swappable_attributes presets

One canonical JSON base → swap `swappable_attributes` → a consistent variant (same face, pose,
blush, style). These 12 presets are the starter library (5 girls, 7 boys) with diverse skin tones
incl. Asian and dark-skinned. Drop a block into `swappable_attributes` in the canonical prompt
(`agents/1-character.md` / a book's `canonical-prompt.md`), generate at 3:4, save the result as
that archetype's canonical reference.

Rules: **girl → mandatory long eyelashes and/or a bow**; real color only; skin tone carries a
heritage hint where it helps the model render features respectfully.

---

## Girls

G4 (olive / Mediterranean) and G6 (South Asian) were removed by the owner on 2026-10-27 — he does not use them. The
other numbers stay as they are on purpose: a number means the same child in every book (book 41's variants are G1, G2, G3, G5, G7).

### G1 — Blonde
```json
"swappable_attributes": { "gender_presentation": "girl", "hair_color": "golden-blonde curls", "eye_color": "blue", "clothing_color": "blush pink", "skin_tone": "soft warm light", "girl_marker": "small bow + long eyelashes" }
```
### G2 — Brunette
```json
"swappable_attributes": { "gender_presentation": "girl", "hair_color": "dark-brown curls", "eye_color": "dark brown", "clothing_color": "lavender", "skin_tone": "warm light", "girl_marker": "small bow + long eyelashes" }
```
### G3 — East Asian
```json
"swappable_attributes": { "gender_presentation": "girl", "hair_color": "straight black hair in a short rounded bowl-cut bob", "eye_color": "dark brown", "clothing_color": "coral", "skin_tone": "warm golden, East Asian features", "girl_marker": "small bow + long eyelashes" }
```
### G5 — Black / deep skin
```json
"swappable_attributes": { "gender_presentation": "girl", "hair_color": "dark coily black hair in two small puff buns", "eye_color": "dark brown", "clothing_color": "teal", "skin_tone": "deep brown", "girl_marker": "bows on the buns + long eyelashes" }
```
### G7 — Redhead
```json
"swappable_attributes": { "gender_presentation": "girl", "hair_color": "auburn-ginger curls", "eye_color": "green", "clothing_color": "soft mint", "skin_tone": "soft warm light with light freckles across the nose", "girl_marker": "small bow + long eyelashes" }
```

---

## Boys

### B1 — Brunette (base)
```json
"swappable_attributes": { "gender_presentation": "boy", "hair_color": "dark-brown curls", "eye_color": "dark brown", "clothing_color": "sage green", "skin_tone": "warm light", "girl_marker": "n/a" }
```
### B2 — Sandy blond
```json
"swappable_attributes": { "gender_presentation": "boy", "hair_color": "light sandy-blond curls", "eye_color": "blue", "clothing_color": "powder blue", "skin_tone": "soft warm light", "girl_marker": "n/a" }
```
### B3 — East Asian
```json
"swappable_attributes": { "gender_presentation": "boy", "hair_color": "straight black hair", "eye_color": "dark brown", "clothing_color": "soft grey", "skin_tone": "warm golden, East Asian features", "girl_marker": "n/a" }
```
### B4 — Olive / Mediterranean
```json
"swappable_attributes": { "gender_presentation": "boy", "hair_color": "dark wavy hair", "eye_color": "brown", "clothing_color": "terracotta", "skin_tone": "warm tan olive", "girl_marker": "n/a" }
```
### B5 — Black / deep skin
```json
"swappable_attributes": { "gender_presentation": "boy", "hair_color": "short coily black hair", "eye_color": "dark brown", "clothing_color": "mustard ochre", "skin_tone": "deep brown", "girl_marker": "n/a" }
```
### B6 — South Asian
```json
"swappable_attributes": { "gender_presentation": "boy", "hair_color": "black hair", "eye_color": "dark brown", "clothing_color": "soft green", "skin_tone": "warm brown, South Asian features", "girl_marker": "n/a" }
```
### B7 — Redhead
```json
"swappable_attributes": { "gender_presentation": "boy", "hair_color": "copper-ginger curls", "eye_color": "green", "clothing_color": "rust orange", "skin_tone": "soft warm light with light freckles across the nose", "girl_marker": "n/a" }
```

---

## Coverage
12 archetypes (5 girls + 7 boys; G4 and G6 removed 2026-10-27).
Skin tones: light ×3, light-with-freckles ×2, golden/East Asian ×2, olive ×1 (B4), warm brown/South Asian ×1 (B6), deep brown ×2.
Hair: blonde, brown, black (straight/curly/coily), wavy, auburn/copper ginger. Eyes: blue, brown, green, dark brown.
Genders: 5 girls (all with eyelashes/bow marker), 7 boys.
Order-time: **Tier S** — name-only ({Name} in text / Canva), no regeneration. **Tier H** —
img2img-edit the demo spreads swapping ONLY the child into the customer's archetype (keep
composition + `text_safe_area.side`), guided by the swapped-attributes JSON. These 12 presets are
the starting palette; the listing shows one demo archetype.
