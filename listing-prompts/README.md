# Listing Prompts — правила створення lifestyle-промптів

Цей файл описує стандарт підготовки JSON-промптів для рекламних lifestyle-зображень. Основний сценарій: готовий мокап уже має правильний ракурс, перспективу, масштаб, дизайн, освітлення та тіні, а генератор повинен змінити лише порожнє оточення і природно вписати мокап у задану естетику.

Поточний базовий напрям — тепла Scandinavian-boho nursery естетика: натуральне дерево, молочні й вівсяні тканини, приглушений sage, dusty blush, евкаліпт, сухі трави та мінімалістичні дитячі аксесуари.

## 1. Головний принцип

Сам мокап не потрібно описувати в generator-facing промпті.

Він повністю береться з прикріпленого вихідного зображення. Промпт не повинен вигадувати його форму, матеріал, дизайн, текст, пропорції, ракурс або колір. Замість опису використовується нейтральне позначення:

> `the protected primary element from the attached source image`

Дозволено описувати лише:

- нове оточення;
- матеріали поверхні;
- декорації;
- розташування декорацій;
- інтеграцію світла й тіней;
- перспективу нових предметів;
- негативні обмеження;
- фінальну перевірку.

## 2. Що завжди подається генератору

Кожен запуск повинен містити щонайменше два компоненти:

1. Вихідний мокап — обов'язкове перше вкладення.
2. JSON-промпт — інструкція з оформлення оточення.

Для точнішого стилю рекомендовано також додавати lifestyle-референси:

1. `Image 1` — вихідний мокап, який треба зберегти.
2. `Image 2` — основний стилістичний референс.
3. `Image 3` — додатковий референс матеріалів або реквізиту, якщо потрібен.
4. Після зображень — JSON-промпт.

Якщо інтерфейс дозволяє підписувати вкладення, потрібно явно вказувати:

- `PRIMARY SOURCE — preserve exactly`;
- `STYLE REFERENCE — environment only`.

Стилістичний референс ніколи не має права змінювати вихідний мокап. Він керує лише естетикою оточення.

## 3. Найкращий режим генерації

Для таких завдань слід використовувати image editing, inpainting або outpainting, а не чисту text-to-image генерацію.

Якщо генератор підтримує маски:

- весь мокап позначається як захищена область;
- редагувати дозволяється лише простір навколо нього;
- існуюча тінь використовується як геометричний орієнтир;
- за потреби тінь акуратно реконструюється на новому матеріалі поверхні.

Якщо масок немає, JSON повинен містити максимально жорсткий `protected_source_policy`. Проте абсолютна піксельна тотожність у такому режимі залежить від можливостей конкретного генератора.

## 4. Ієрархія джерел

У кожному промпті фіксується однакова ієрархія:

1. Вихідне зображення керує захищеним центральним елементом.
2. Вихідне зображення керує камерою, перспективою та світлом.
3. Референси керують лише оточенням, палітрою, матеріалами та декораціями.
4. Текстовий промпт уточнює розташування нових предметів.
5. За будь-якого конфлікту вихідне зображення має абсолютний пріоритет.

Це потрібно повторювати безпосередньо в JSON. Однієї короткої фрази `keep it unchanged` зазвичай недостатньо.

## 5. Незмінні частини JSON-структури

Кожен промпт повинен мати такі блоки:

| Блок | Функція |
| --- | --- |
| `prompt_name` | Унікальна назва варіанта. |
| `task` | Коротко визначає, що змінюється лише оточення. |
| `source_hierarchy` | Встановлює пріоритет вихідного зображення над референсами. |
| `protected_source_policy` | Детально фіксує все, що не можна змінювати. |
| `edit_scope` | Визначає дозволену для редагування область. |
| `environment` | Описує поверхню, стіни, тканини та атмосферу. |
| `decoration_layout` | Дає конкретні позиції декорацій. |
| `perspective_matching` | Узгоджує нові предмети з камерою вихідного зображення. |
| `lighting_integration` | Узгоджує нові предмети з наявним світлом і тінями. |
| `color_palette` | Обмежує кольори сцени. |
| `visual_style` | Фіксує фотографічну якість і візуальну ієрархію. |
| `negative_constraints` | Забороняє типові помилки генератора. |
| `final_validation` | Перевіряє результат перед завершенням генерації. |

Порядок блоків бажано не змінювати. Це робить промпти передбачуваними, читабельними та зручними для подальшої автоматизації.

## 6. Логіка protected source

Блок `protected_source_policy` є найважливішим. Він завжди повинен забороняти:

- переміщення;
- масштабування;
- обертання;
- кадрування;
- виправлення перспективи;
- перемальовування ілюстрації;
- зміну кольорів;
- зміну або повторне створення тексту;
- зміну різкості;
- повторне освітлення;
- перекриття декораціями.

Також потрібно прямо вимагати повторного використання пікселів із вихідного зображення:

> `Reuse the protected primary element directly from the source pixels. Do not reconstruct, regenerate or reinterpret it.`

### Виняток для головного кадру лістингу

У `01-listing-cover-boho-flatlay.json` дозволено лише рівномірно масштабувати та переміщувати весь захищений центральний елемент як одну неподільну площину, щоб він займав 68–72% квадратного кадру. Цей виняток не дозволяє перемальовувати, деформувати, обрізати, перефарбовувати або повторно створювати його внутрішній дизайн і типографіку.

## 7. Логіка композиції

Декор не можна механічно копіювати з референсу. Його потрібно адаптувати до реального ракурсу мокапу.

### Низький або похилий ракурс

- Усі предмети розташовуються на тій самій фізичній площині.
- Вертикальні аксесуари мають відповідати висоті камери.
- Не можна перетворювати сцену на вид згори.
- Декор переважно ставиться по зовнішніх краях кадру.

### Вертикально розташований мокап

- Можна створити теплий nursery-куточок зі стіною та підлогою.
- Декорації розміщуються ліворуч і праворуч.
- Предмети не повинні виглядати приклеєними до вертикальної площини.

### Близький динамічний ракурс

- Використовується менше реквізиту.
- Великі світлі ділянки залишаються спокійними.
- Часткове кадрування реквізиту по краях допомагає натуральності.
- Центральний елемент завжди залишається найрізкішим і найконтрастнішим.

### Майже горизонтальний ракурс

- Найкраще працюють текстильні шари, дерев'яні іграшки та невеликі аксесуари.
- Нові предмети повинні повторювати перспективне скорочення вихідної поверхні.
- Тканина має природно реагувати на вагу предметів.

## 8. Правила бохо-декору

Базова палітра:

- warm ivory;
- oatmeal beige;
- soft taupe;
- dusty blush;
- muted sage;
- eucalyptus green;
- pale natural wood.

Рекомендовані матеріали:

- chunky knit;
- waffle-weave cotton;
- linen;
- boucle;
- matte mineral plaster;
- pale oak;
- untreated natural wood;
- dusty botanicals.

Рекомендований реквізит:

- дерев'яна пірамідка в приглушених пастельних кольорах;
- дерев'яне брязкальце або кільце;
- коротка низка дерев'яних намистин;
- дерев'яний місяць або зірка;
- текстильний кролик;
- в'язана шапочка;
- маленькі в'язані шкарпетки;
- евкаліпт;
- сухі трави;
- стримана dusty-blush стрічка.

В одному кадрі достатньо 3–6 типів реквізиту. Не потрібно використовувати весь список одночасно.

## 9. Як описувати розташування

Не слід писати лише `add boho decorations`. Для стабільного результату кожен предмет отримує конкретну зону:

- `upper_left`;
- `upper_right`;
- `left_edge`;
- `right_side`;
- `lower_left`;
- `lower_right`;
- `lower_center`.

Для кожного предмета бажано вказати:

- матеріал;
- колір;
- приблизний масштаб;
- чи може він частково виходити за межі кадру;
- чи має бути трохи далі від камери;
- на якій поверхні він лежить;
- що він не може торкатися захищеної області.

## 10. Перспектива та фізична правдоподібність

Нові предмети повинні автоматично успадковувати з вихідного зображення:

- висоту камери;
- кут огляду;
- характер об'єктива;
- напрямки перспективного скорочення;
- фізичну площину;
- глибину різкості.

Кожен предмет повинен мати:

- реалістичний масштаб;
- правильну точку контакту з поверхнею;
- природну вагу;
- локальне стиснення тканини;
- правильне перекриття інших декорацій;
- відсутність перетину із захищеною областю.

## 11. Світло і тіні

Нову схему освітлення вигадувати не можна. Вона визначається вихідним мокапом.

Промпт повинен вимагати:

- аналізувати напрямок наявного світла;
- не змінювати освітлення захищеного елемента;
- зберігати напрямок, довжину, щільність і м'якість його тіні;
- природно реконструювати цю тінь на новій тканині або підлозі;
- створювати для реквізиту тіні від того самого джерела;
- додавати лише делікатне відбите світло від нового оточення.

Якщо головна тінь і тіні реквізиту дивляться в різні боки, результат вважається непридатним.

## 12. Візуальна ієрархія

Захищений елемент завжди повинен бути:

- найбільшим;
- найрізкішим;
- найважливішим;
- повністю видимим;
- вільним від перекриттів;
- контрастнішим за крайові декорації.

Декор створює атмосферу, але не стає другим головним об'єктом. Найвіддаленіші предмети можуть бути лише трохи м'якшими; сильне розмиття виглядає штучно.

## 13. Обов'язкові негативні обмеження

Кожен промпт повинен забороняти:

- зміни всередині захищеної області;
- повторне створення ілюстрації;
- зміну типографіки;
- додавання нового читабельного тексту;
- неправильну перспективу;
- предмети, що висять у повітрі;
- неправильний масштаб;
- дубльований реквізит;
- суперечливі напрямки тіней;
- жорсткий спалах;
- пластикові матеріали;
- штучні тканинні текстури;
- надмірне розмиття;
- перевантажену композицію;
- сильний жовтий або коричневий відтінок;
- водяні знаки, логотипи та елементи інтерфейсу.

## 14. Універсальний JSON-шаблон

Нижче наведена базова структура. Текст у квадратних дужках замінюється відповідно до конкретного мокапу та композиції.

```json
{
  "prompt_name": "[unique_scene_name]",
  "task": "Replace only the empty surroundings with [desired environment]. Keep the protected primary element from the attached source completely unchanged.",
  "source_hierarchy": {
    "primary_source": "The attached source exclusively controls the protected element, its placement, dimensions, perspective, artwork, focus and illumination.",
    "style_references": "The supplied references control only the surroundings, materials, decorative objects, palette and atmosphere.",
    "absolute_priority": "Preservation of the protected source region overrides every other instruction."
  },
  "protected_source_policy": {
    "instruction": "Reuse the protected primary element directly from the source pixels. Do not reconstruct, regenerate or reinterpret it.",
    "preserve_exactly": [
      "original position",
      "original dimensions and proportions",
      "original rotation and perspective",
      "all artwork and typography",
      "original colors and tonal values",
      "surface texture",
      "highlights and shading",
      "sharpness and focus"
    ],
    "prohibited_operations": [
      "Do not redraw the protected element",
      "Do not move, rotate, resize or crop it",
      "Do not change its perspective",
      "Do not modify or recreate existing text",
      "Do not recolor or relight it",
      "Do not place decorations over it"
    ]
  },
  "edit_scope": {
    "editable_region": "Only the existing surroundings outside the protected source region.",
    "objective": "[specific visual objective]",
    "canvas": "Preserve the exact original aspect ratio, resolution and framing."
  },
  "environment": {
    "surface": "[surface and textile description]",
    "surroundings": "[wall or surrounding description if applicable]",
    "materials": "[material behavior and texture]",
    "atmosphere": "[desired emotional atmosphere]"
  },
  "decoration_layout": {
    "upper_left": "[object or intentionally empty]",
    "upper_right": "[object or intentionally empty]",
    "lower_left": "[object or intentionally empty]",
    "lower_right": "[object or intentionally empty]",
    "distribution": "Use restrained asymmetrical balance and generous breathing room.",
    "density": "Use only a small curated selection of decorations."
  },
  "perspective_matching": {
    "instruction": "Infer the exact camera height, viewing direction, lens behavior and physical plane from the attached source.",
    "prop_alignment": "All added objects must follow the same perspective and spatial orientation.",
    "scale": "Use believable real-world proportions.",
    "surface_contact": "Every object must show realistic weight, contact and material compression.",
    "protected_margin": "No new object may touch or enter the protected source region.",
    "depth_of_field": "Keep the protected element perfectly sharp and apply only subtle softness to distant decorations."
  },
  "lighting_integration": {
    "instruction": "Continue the exact lighting already present in the source without changing illumination on the protected element.",
    "direction": "Match the existing light and cast-shadow direction.",
    "shadow_preservation": "Preserve the original shadow geometry, density and softness and reconstruct it naturally on the new materials.",
    "new_object_shadows": "Generate physically consistent shadows for all added objects using the same light source.",
    "white_balance": "Warm neutral daylight without a strong yellow tint.",
    "contrast": "Soft editorial contrast with detailed highlights and natural shadows."
  },
  "color_palette": [
    "warm ivory",
    "oatmeal beige",
    "soft taupe",
    "dusty blush",
    "muted sage",
    "pale natural wood"
  ],
  "visual_style": {
    "medium": "High-end realistic nursery lifestyle photography",
    "mood": "[desired mood]",
    "focal_hierarchy": "The protected source element remains the largest, sharpest and most visually dominant feature.",
    "integration_standard": "The result must look like one authentic photograph with no visible compositing."
  },
  "negative_constraints": [
    "No changes inside the protected source region",
    "No regenerated artwork",
    "No altered typography",
    "No new readable text",
    "No movement, resizing or perspective correction",
    "No decorations touching the protected element",
    "No incorrect perspective",
    "No floating objects",
    "No mismatched scale",
    "No duplicated props",
    "No conflicting shadow directions",
    "No hard flash",
    "No synthetic-looking materials",
    "No excessive blur",
    "No clutter",
    "No watermarks, logos or interface elements"
  ],
  "final_validation": [
    "The protected element is identical to the attached source.",
    "Its original position, scale and perspective remain unchanged.",
    "All original artwork and typography remain intact.",
    "The original lighting and shadow logic remain consistent.",
    "All added objects follow the source camera geometry.",
    "Every decoration has believable surface contact and matching shadows.",
    "The completed scene looks naturally photographed as one image."
  ]
}
```

## 15. Фінальна перевірка перед використанням

Перед передачею промпту генератору потрібно відповісти `так` на всі питання:

- Чи прикріплено вихідний мокап першим?
- Чи чітко відокремлено вихідне зображення від стилістичних референсів?
- Чи відсутній опис зовнішності самого мокапу?
- Чи вимагається пряме повторне використання вихідних пікселів?
- Чи заборонені переміщення, масштабування та виправлення перспективи?
- Чи описані конкретні позиції декорацій?
- Чи декор адаптований до реального ракурсу?
- Чи всі предмети залишаються поза захищеною областю?
- Чи нові тіні узгоджені з наявним світлом?
- Чи збережено вихідний формат кадру?
- Чи композиція залишається стриманою?
- Чи є блок фінальної валідації?

## 16. Рекомендоване зберігання майбутніх промптів

Промпти для конкретного listing-набору можна додавати в цю папку за схемою:

```text
Listing prompts/
  README.md
  01-listing-cover-boho-flatlay.json
  02-upright-shelf-boho.json
  03-mother-baby-reading.json
  04-layered-textile-boho.json
```

`01-listing-cover-boho-flatlay.json` is the canonical golden-hour prompt for the primary Etsy listing image. Version 2 uses one attached source image, presents the protected square object at approximately 70% of a 1:1 frame, and generates a richly layered Scandinavian-boho environment with five distinct textile constructions, six to eight prop types, low upper-left sunlight and elongated lower-right shadows. No separate lifestyle reference is required.

`02-upright-shelf-boho.json` is the canonical universal prompt for the upright shelf scene. It accepts one source image with any artwork, locks that source's camera angle, perspective and light-shadow fingerprint, then constructs a richer Scandinavian-boho nursery environment around it.

`03-mother-baby-reading.json` is the canonical universal family-lifestyle prompt. It accepts one protected 2:1 artwork source, maps its two halves to a realistic open printed keepsake, and generates one new mother-and-infant casting for every run using a balanced, stereotype-free representation system for families living in the United States.

Назва файлу повинна відображати номер кадру та композиційний тип, а не ім'я дитини чи текст усередині мокапу. Це дозволяє повторно використовувати ті самі промпти для інших персоналізованих дизайнів.
