# Media Presets - locked art-style library

The chosen medium fills the **`style{}` block** of every generated image prompt.
Pick ONE per project - always confirm with the user before Agent 2. Default =
**RW (rich watercolor)** - the current house style.

These blocks are **locked for reproducibility** - paste the chosen preset's `style{}` and append its
`negative+` to every prompt, verbatim. The character, scene, composition, zones, text-safe area,
and standard safety negatives stay identical across all media.

## Mandatory paint/detail floor for every preset

Every production style must carry enough painterly information to reproduce a premium reference-level
finish, not a generic "nice watercolor" shortcut. Keep these qualities in every `style{}` block:
- specific paint behavior: washes, opacity, pigment bloom, brush shape, blending, glow, or oil layers
- tactile surface: cream fiber texture, matte paper/canvas feel, visible handmade variation
- controlled line/detail: thin warm pencil or soft painted edges, readable focal props, no heavy outline
- detail floor: low-to-medium or richer detail where the style calls for it, but always with charming
  inspectable props, warm light, and a softly illustrated overlay area
- palette behavior: warm cream base, coherent accents, no random saturated color

Do not compress a chosen style to one sentence during prompt assembly. The long `style{}` is part of
the generation control surface.

Only these production styles are available:
- **RW** - Rich Watercolor (default/current house style)
- **W** - Pastel Watercolor
- **G** - Gouache
- **GW** - Glowing Watercolor
- **LO** - Luminous Oil
- **HR** - High-Fidelity Realism (scenic, nature & sacred keepsakes)

---

## W - Pastel Watercolor
`task` tag: `... in a simplified soft pastel watercolor nursery illustration style`
```json
"style": {
  "medium": "luxury hand-painted soft pastel watercolor children's illustration",
  "paint_quality": "transparent watercolor with delicate pigment blooms, feathered wash edges, subtle pooling, and hand-brushed variation",
  "washes": "soft pastel watercolor washes over warm cream fiber texture, smooth gradients, light honey-beige undertones, no flat digital fill",
  "linework": "delicate warm-brown pencil and fine ink accents, thin and soft; many edges implied by paint instead of outline",
  "forms": "clear simple silhouettes, rounded childlike forms, gentle toddler-safe proportions, soft toy-like props",
  "detail": "low-to-medium detail density with inspectable charming props, tiny floral or wood accents, and airy negative space",
  "texture": "visible matte watercolor paper grain, mottled wash texture, soft fiber speckle, handmade unevenness",
  "color": "warm cream, ivory, oatmeal beige, dusty sage, muted peach, butter yellow, soft sky blue; low saturation and harmonious",
  "light": "diffuse morning glow, soft window warmth, tiny golden specks only when the scene calls for them",
  "depth_feel": "soft atmospheric depth with foreground, midground, and background layers kept quiet and readable",
  "overlay_behavior": "calm illustrated overlay areas remain softly painted with low-contrast texture, never blank or unfinished",
  "mood": "cozy, warm, tender, premium, keepsake-safe",
  "finish": "matte watercolor paper, hand-painted, gentle and breathable"
}
```
`negative+`: `["3D render","vector","anime","photorealism","AI-art look","hyper-detailed botanical texture","realistic fur texture","busy grass noise","overworked background"]`

---

## G - Gouache
`task` tag: `... in opaque GOUACHE, vintage mid-century children's illustration (NOT watercolor)`
```json
"style": {
  "medium": "opaque gouache painting, mid-century children's illustration",
  "paint_quality": "matte opaque gouache with creamy pigment, visible brush shapes, soft scumbled edges, and layered hand-painted color",
  "paint": "rich opaque gouache, gentle visible strokes, creamy blended skies, warm dry-brush texture, soft painterly transitions",
  "linework": "soft painted edges with occasional thin warm pencil accents; minimal outline and no harsh black contour",
  "forms": "rounded friendly shapes, clean readable silhouettes, simplified vintage props with tactile painted volume",
  "detail": "medium detail with developed cozy environments, inspectable wood grain, fabric folds, small toys, plants, and warm lamps",
  "texture": "matte paper tooth under opaque paint, subtle brush ridges, hand-painted unevenness, no plastic smoothness",
  "color": "warm cream and honey base with muted teal, peach, sage, dusty coral, warm brown, and deep but soft twilight contrast",
  "light": "cozy amber glow balanced with cool blue-teal atmosphere, soft luminous reflections, no theatrical harshness",
  "depth_feel": "strong painterly atmospheric depth, clear foreground and midground, softened distance",
  "overlay_behavior": "calm illustrated overlay areas use creamy low-contrast paint and quiet texture, never flat or empty",
  "mood": "cozy, nostalgic, premium, handmade, softly cinematic",
  "finish": "matte opaque gouache on slightly textured paper"
}
```
`negative+`: `["transparent watercolor","watercolor wash look","3D render","vector","anime","photorealism","AI-art look","glossy AI render","harsh black outlines","flat","empty background","under-detailed","white border","paper margins","rounded frame","sticker outline","border around image","photo frame"]`

---

## RW - Rich Watercolor (DEFAULT, current house style)
`task` tag: `... in a rich, warm watercolor nursery illustration style`
```json
"style": {
  "medium": "premium hand-painted soft watercolor children's illustration with rich colors",
  "paint_quality": "luminous watercolor with richer pigment load, warm blooms, soft pooling, layered transparent washes, and hand-brushed variation",
  "washes": "luminous watercolor washes, honey-gold gradients, smooth cream paper texture, warm pigment blooms, soft atmospheric transitions",
  "linework": "delicate soft pencil contours in warm brown, clean friendly shapes, expressive small details on faces and focal props",
  "forms": "chubby rounded silhouettes, friendly childlike proportions, plush toy softness, simple readable poses",
  "detail": "medium-high detail density with charming inspectable accents such as wildflowers, wood grain, water reflections, cozy shelves, starry skies, and tiny spark trails",
  "texture": "visible matte watercolor paper grain, pigment granulation, mottled wash edges, subtle fiber speckles",
  "color": "vibrant but soft pastel palette, warm honey-gold sunlight, rose pink, sage and rich grass green, soft coral sunset, deep twilight blue, warm wood brown",
  "light": "warm window glow, golden-hour softness, tiny magical specks, gentle halos around lamps or stars when appropriate",
  "depth_feel": "rich atmospheric depth, painterly layering, softly blurred distance, readable foreground props",
  "overlay_behavior": "calm illustrated overlay areas keep low-contrast wash texture, faint scenery, and gentle glow so they feel finished",
  "mood": "cozy, magical, celebratory, premium, full of love",
  "finish": "matte watercolor paper with a rich hand-painted look"
}
```
`negative+`: `["3D render","vector","anime","photorealism","AI-art look","glossy AI render","harsh black outlines","photographic realism","overly sharp digital detail","plastic texture","busy unreadable clutter"]`

---

## GW - Glowing Watercolor
`task` tag: `... in a rich glowing watercolor children's illustration style with volumetric light rays`
```json
"style": {
  "medium": "premium hand-painted luminous watercolor and soft gouache children's illustration",
  "paint_quality": "luminous watercolor over soft gouache accents, transparent blooms, creamy highlights, glowing pigment layers, and handmade brush variation",
  "washes": "radiant watercolor washes, soft gradient blending, visible fine paper texture, gentle pigment blooms, warm glaze buildup",
  "linework": "soft light-brown colored pencil contours, blended edges, delicate hand-drawn feel, fine accents around focal props",
  "forms": "chubby rounded silhouettes, cute expressive characters with warm eyes, rosy cheeks, and soft toy-like simplicity",
  "detail": "rich but controlled detail: stylized wildflowers, soft fur or fabric texture, tree leaves, gentle water ripples, cozy wood grain, sparkling golden dust",
  "texture": "matte watercolor paper with visible fiber, soft gouache opacity in highlights, delicate granulation",
  "color": "warm amber and golden-honey illumination, soft peach sunset tones, deep emerald green, rich wood brown, soft rose pink, deep twilight blue",
  "light": "magical warm glow, gentle luminous beams, soft halos, floating golden dust, no harsh spotlight contrast",
  "depth_feel": "warm atmospheric depth, glowing foreground accents, softened distance, clear focal hierarchy",
  "overlay_behavior": "calm illustrated overlay areas glow softly with low-contrast haze, faint texture, and minimal detail",
  "mood": "magical, spiritual, cozy, warm, premium, full of wonder and love",
  "finish": "matte textured watercolor paper with a rich glowing hand-painted finish"
}
```
`negative+`: `["3D render","vector","anime","photorealism","AI-art look","glossy AI render","harsh black outlines","plastic texture","flat","moody dark shadows","rough digital brushstrokes"]`

---

## LO - Luminous Oil
`task` tag: `... in a rich glowing oil painting children's illustration style with volumetric light rays`
```json
"style": {
  "medium": "premium hand-painted luminous oil painting children's illustration",
  "paint_quality": "smooth luminous oil layers, creamy blended color, soft impasto hints only on focal accents, warm glaze depth, hand-painted brush variation",
  "paint": "smooth oil paint layers, creamy blended skies, soft edge transitions, subtle canvas texture, luminous glow",
  "linework": "soft painted edges, thin warm contours, delicate hand-painted feel, no harsh outlines",
  "forms": "chubby rounded silhouettes, cute expressive characters with warm eyes and rosy cheeks, simplified nursery-safe proportions",
  "detail": "simplified but inspectable gentle details: clean wildflowers, soft fabric folds, warm wood accents, tiny glowing dust, quiet background elements",
  "texture": "matte fine canvas texture, creamy brush softness, subtle paint-layer depth without realistic heaviness",
  "color": "warm amber and golden-honey illumination, soft peach sunset tones, deep emerald green, rich wood brown, soft rose pink, deep twilight blue",
  "light": "warm luminous glow, soft beams, gentle halos, ambient magic without harsh shadow",
  "depth_feel": "warm amber atmospheric depth, glowing foreground accents, softened distance, painterly dimensionality",
  "overlay_behavior": "calm illustrated overlay areas use smooth low-contrast glow and subtle canvas texture, never flat or empty",
  "mood": "magical, spiritual, cozy, warm, premium, full of wonder and love",
  "finish": "matte textured canvas with a rich glowing hand-painted oil finish"
}
```
`negative+`: `["transparent watercolor","watercolor washes","3D render","vector","anime","photorealism","AI-art look","glossy AI render","harsh black outlines","plastic texture","flat","moody dark shadows","rough digital brushstrokes","hyper-detailed textures","intricate micro-details","overworked rendering","photographic fur realism"]`

---

## HR - High-Fidelity Realism (Scenic & Sacred Keepsake)
`task` tag: `... in a high-fidelity painterly realism style in luminous watercolor and translucent gouache`
```json
"style": {
  "medium": "high-fidelity painterly realism illustration in luminous watercolor and translucent gouache",
  "paint_quality": "luminous watercolor washes with layered translucent gouache, fine brushwork, believable terrain scale, and natural atmospheric depth",
  "washes": "smooth luminous washes over warm cream watercolor paper, subtle pigment granulation, soft radiant glazing, natural light transitions",
  "linework": "fine delicate pencil and warm brush contours; subtle, natural, and integrated with the paint",
  "forms": "richly observed natural landscapes, authentic architectural elements, believable scale, organic textures, calm still-life arrangements",
  "detail": "high painterly detail density: convincing terrain, foliage, rock textures, gentle water reflections, soft clouds, and sparkling light",
  "texture": "visible matte fine-grain watercolor paper texture, delicate pigment granulation, tactile paint layers, no plastic smoothness",
  "color": "luminous natural palette: warm ivory, ochre, muted sage, soft dusty rose, celestial blue, warm honey light, rich earthy umber",
  "light": "convincing natural lighting: soft dawn glow, golden hour illumination, atmospheric mist, gentle moonlit reflections, volumetric warmth",
  "depth_feel": "strong atmospheric and spatial perspective: distinct readable foreground, detailed midground, softly blurred horizon",
  "overlay_behavior": "calm illustrated overlay areas remain softly painted with low-contrast sky/water/landscape washes, providing ample clean space for text",
  "mood": "serene, majestic, sacred, peaceful, timeless, premium keepsake",
  "finish": "matte high-resolution fine-art paper, richly observed and materially believable"
}
```
`negative+`: `["3D render","vector","anime","photorealism","AI-art look","glossy AI render","harsh black outlines","chibi","cartoon","oversaturated colors","flat digital fill","blurry details","plastic texture"]`

---

## How a new preset is added
Append a section with its `task` tag, full `style{}` block, and `negative+` list. Agent 5 reads the
chosen `Medium:` and drops that block in. Nothing else in the pipeline changes - the medium only
swaps `style{}` (+ medium negatives); everything else stays locked.
