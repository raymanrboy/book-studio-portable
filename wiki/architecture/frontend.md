---
title: Інтерфейс — будова і спільні помічники
type: architecture
updated: 2026-09-17
code:
  - app/web/index.html
  - app/web/js/app.js
  - app/web/js/lib.js
  - app/web/js/icons.js
  - app/web/js/handoff.js
  - app/web/js/lightbox.js
  - app/web/css/app.css
---
# Інтерфейс

> Одна HTML-сторінка без збірки: модулі ES з `app/web/js`, стилі в одному `app.css`.
> Сторінки перемикаються за `#хешем`, кожна — окремий модуль із `mount()`.

## Оболонка і маршрутизація — `app.js`

- **Бокова панель** (`NAV`): Замовлення `#/orders` (Alt+1), Бібліотека `#/library` (Alt+2),
  Order Creator `#/creator` (Alt+3), Налаштування `#/settings` (Alt+4). Стартова — `HOME = '#/orders'`.
  Внизу — меню теми (темна / світла / як у Windows, «мінімум анімацій»). Крапка на Налаштуваннях —
  коли якомусь сервісу бракує ключа чи входу.
- **Маршрути** (`ROUTES`): `#/orders[/<номер чека>]` → `pages/orders.js`, `#/library` → `library.js`,
  `#/book/<id>` → `book.js`, `#/creator` → `creator.js`, `#/settings[/<розділ>]` → `settings.js`.
  Сторінки **Прибуток немає в маршрутах** — вона прихована до 1 жовтня ([features/profit.md](../features/profit.md)).
- **Контракт сторінки**: `export async function mount(view, params)` будує вміст у переданому
  елементі й повертає `{ shown(), unmount() }` (обидва необов'язкові). `navigate()` будує нову
  сторінку поза екраном і міняє їх одним View Transition — без порожніх кадрів.
- `unmount()` мусить зняти всі слухачі (`on()` повертає функцію відписки) і таймери.
- `refreshInfo()` → `/api/app` (стан сервісів, кількість книг) для панелі та сторінок.

## Спільні помічники — `lib.js`

| Що | Функції |
|---|---|
| Безпечні шаблони | `` html`…` `` екранує все, крім `raw()`; `setHtml()`, `el()` |
| Кнопки-піктограми з підказкою | `ib(icon, tip, attrs, {cls, kbd})`; спільна підказка `showTip()` / `hideTip()` |
| Сервер | `api()` (токен, JSON, `ApiError`), `media()` (посилання з токеном), `upload()` (XHR з прогресом), `runJob()` |
| Зовнішні посилання | `openExternal()` — через сервер, у звичайному браузері (Etsy заблоковано) |
| Повідомлення | `toast()`, `modal()`, `confirmBox()`, `menu()` |
| Сегментований перемикач | `segHtml()`, `syncSeg()`, `setSeg()` |
| Формати | `money()`, `dateTime()`, `relTime()`, `bytes()`, `plural()`, `highlightTokens()` |
| Плавність | `fadeImages()` (декодування поза головним потоком), `slide()` (висота), `flip()` (переміщення карток), `perFrame()`, `keepFocus()`, `idle()`, `reducedMotion()` |

## Інші модулі

- `icons.js` — піктограми 24×24, обведення 1,6. **Одна піктограма — одне значення.**
  Є логотипи сервісів: `etsy`, `canva`, `printify`, `gelato`; `sendLog` — журнал відправок;
  `truck` — «друкарня відправила» (вкладка й чип трек-номера; з 17.09.2026 окремий малюнок, а не
  псевдонім коробки `package`, яка означає «відправлено в Etsy»).
- Чипи (`.chip`): текст чипа — одним шрифтом (`.chip .num` не перемикає шрифт), `.chip-mono` на 2 px
  нижче, щоб Consolas стояв на одній лінії з текстом інших чипів.
- `handoff.js` — `give(to, data)` / `take(to)`: одноразова передача між сторінками лише в пам'яті
  (картка замовлення → Order Creator).
- `order-bits.js` — спільне для Замовлень і Order Creator ([features/orders.md](../features/orders.md)).
- `lightbox.js` — `openLightbox(items, start)`; елемент: `src`, `full` (чіткіша версія при зумі),
  `title`, `sub`, `text` (клавіша T), `onOriginal`. Колесо, перетягування з інерцією, ← →, Esc.

## Візуальна система — `app.css` («Prepress»)

- Токени кольору на `:root` (світла тема «proofing booth») і `[data-theme="dark"]` («graphite»);
  тема ставиться до першого кадру скриптом в `index.html` (ключ `bs-theme` у localStorage).
- Шрифти: Bahnschrift — інтерфейс і заголовки, Segoe UI — текст, Sitka — тексти книг, Consolas — цифри/коди.
- Акцент — «process cyan»; кольори сервісів: `--printify` (салатовий), `--gelato` (синій),
  `--etsy`, `--canva`. Printify-режим Order Creator і картка друку Printify (`.tint-printify`)
  перефарбовують акцент у салатовий.
- Радіуси за роллю: папір гострий (`--r-art`), елементи керування м'які (`--r-ctl`).
- **60 кадрів/с**: анімуються лише `transform` і `opacity`, без розмиття; `data-motion="reduce"` і
  `prefers-reduced-motion` вимикають анімації.
- Групи класів: `.lib-toolbar` (панелі інструментів), `.ord-*` (замовлення), `.proof*`, `.strip*`
  (звірка), `.creator*`, `.spread-*` (Order Creator), `.book-*`, `.slot-*` (бібліотека),
  `.set-*` (налаштування), `.lightbox`, `.lb-*` (переглядач).
- Вимоги власника до вигляду — [owner/ui-principles.md](../owner/ui-principles.md).

## Де в коді

- [app/web/index.html](../../app/web/index.html) — токен `__STUDIO_TOKEN__`, тема до першого кадру
- [app/web/js/app.js](../../app/web/js/app.js) — `NAV`, `HOME`, `ROUTES`, `navigate()`, `buildSidebar()`, `applyTheme()`, `applyMotion()`, `refreshInfo()`, `openThemeMenu()`
- [app/web/js/lib.js](../../app/web/js/lib.js) — `html()`, `raw()`, `ib()`, `showTip()`, `api()`, `media()`, `upload()`, `runJob()`, `openExternal()`, `modal()`, `menu()`, `segHtml()`, `flip()`, `slide()`, `fadeImages()`
- [app/web/js/icons.js](../../app/web/js/icons.js) — `icon()`
- [app/web/js/handoff.js](../../app/web/js/handoff.js) — `give()`, `take()`
- [app/web/js/lightbox.js](../../app/web/js/lightbox.js) — `openLightbox()`, `TAU`, `MAX_ZOOM`
- [app/web/css/app.css](../../app/web/css/app.css) — токени кольорів на початку файлу

## Пов'язане

- [Карта коду](../code-map.md) · [Принципи інтерфейсу](../owner/ui-principles.md) · [Рецепти](../recipes.md)
