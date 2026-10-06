// A book in the Workshop — the book console moved in (26.09.2026). On top, the book's path: Формула → Герой → Історія →
// Текст → Промпти · GO → Картинки n/16 → Обкладинка → Canva → Мокапи → Фото n/7 → Бібліотека, each step ticked by the files that
// exist (the agents write them in Antigravity), a click shows the step's file or work in the panel under it. Below, the
// book's rows — page 1, spreads 2–3 … 28–29, page 30 — each its prompt, its 2:1 frame and its text, and the cover last,
// in two stages. «Генерувати» puts a row's prompt into the clipboard; the picture the owner downloads from Gemini lands
// in its row, cut and flipped, and the next prompt is already in the clipboard. The page redraws in place whenever a
// file changes (workshop-live.js, patch()): what stayed, stays — pictures, scroll, an opened prompt.
import {
  api, post, html, ic, ib, raw, setHtml, on, toast, menu, confirmBox, upload, copyText, fadeImages, highlightTokens,
  plural, patch, syncSeg, runJob, topLayer, notFound, remember, media, attr, reducedMotion,
} from '../lib.js';
import { openLightbox } from '../lightbox.js';
import { openAddBook } from '../add-book.js';
import { offerModule } from '../modules-ui.js';
import { picture, checkWord, ERRORS, STATE_TEXT } from '../workshop-bits.js';
import { pathStep } from '../path.js';
import { watch, refresh, act, startGen, startPhoto, genAction, paintGenBar, genState, waitingFor } from '../workshop-live.js';
import { rowTemplates, waitChip, chipFill, slot } from './workshop-rows.js';

const IMG_RE = /\.(png|jpe?g|webp)$/i;
const VIDEO_RE = /\.(mp4|mov|webm)$/i;
// Who writes a step's file — said where the file isn't there yet.
const WHO = {
  formula: 'Агент 0 записує формулу книги й Tier (з героєм чи без) у formula.md.',
  hero: 'Агент 1 пише промпт героя (canonical-prompt.md) і картку героя; героя згенеруйте кнопкою вище — він стане canonical.png.',
  story: 'Агент 2 пише історію книги — story-blueprint.md.',
  text: 'Агенти 3 і 4 пишуть і шліфують текст — book-text.md.',
  prompts: 'Агент 5 пише промпти розворотів (spread-prompts-json.md) і сторінок 1 та 30 (endpage-prompts-json.md).',
};
const MANUAL = { canva: 'Книгу зверстано в Canva', mockups: 'Мокапи для лістингу зроблено' };
const shortLabel = (r) => r.label.replace(/^\D+/, '').replace(/ ·.*$/, ''); // «Розворот 4–5» → «4–5»

// What the page remembers about each book until a restart: the step open in the panel, the file shown for a step,
// the hero variant's tab, the prompts shown whole, the cover's stage picked by hand, the template's lines.
const memory = new Map();

export async function mount(view, [rawId]) {
  const id = decodeURIComponent(rawId);
  const url = (tail = '') => `/api/workshop/books/${encodeURIComponent(id)}${tail}`;
  let first;
  try {
    first = await api(url());
  } catch (err) {
    notFound(view, { back: '#/books/work', backLabel: 'До книг', icon: 'workshop', title: 'Книгу не знайдено', text: err.message });
    return null;
  }
  let b = first.book;
  if (!memory.has(id)) {
    memory.set(id, { step: (b.steps.find((s) => s.next) || b.steps[0]).key, tabs: new Map(), variant: '', open: new Set(), cover: 0, guides: true });
  }
  const mem = memory.get(id);
  const uploading = new Map(); // drop key → the share uploaded (0…1)
  let stepsSeen = null;         // the steps' states at the last draw: a step that has just become done pops
  let coverSeen = null;         // { art, stage } at the last draw: a new cover picture turns the card to its margins
  let coverSlide = '';          // the cover's pane glides this way once, at the next draw ('slide-next' / 'slide-back')
  const docs = new Map();       // a step's text by its file and version: an open step isn't fetched again on each change
  let waitSeen = '';            // the row waited for at the last draw: the page follows the queue
  let lb = null;
  const lbItems = [];
  let panelKey = null;          // the step + file shown in the panel: its content fades only when this changes, not on a live redraw
  let shownVariant;             // the tab shown at the last draw: a switch fades the rows
  const filled = new Map();     // row key → had a picture at the last draw: a picture that arrives into an empty frame fades in once

  setHtml(view, html`
    <div class="page-head ws-head" id="ws-head"></div>
    <div class="ws-genbar-slot" id="ws-gen"></div>
    <div class="ws-strip path-strip path-icons" id="ws-strip" style="--steps:11" role="tablist" aria-label="Шлях книги"></div>
    <div class="ws-panel" id="ws-panel" hidden></div>
    <div class="ws-col">
      <div class="ws-rows-head" id="ws-rows-head"></div>
      <div id="ws-vtabs"></div>
      <div id="ws-notes"></div>
      <div class="ws-rows" id="ws-rows"></div>
    </div>
    <input type="file" id="ws-file" accept=".png,.jpg,.jpeg,.webp" hidden>`);
  const $ = (s) => view.querySelector(s);
  const step = (key) => b.steps.find((s) => s.key === key);
  const pic = (area, name, w, variant) => picture(b, area, name, w, variant);
  const inner = () => b.rows.filter((r) => r.kind !== 'cover');
  const ready = () => step('pictures').state === 'done' && step('cover').state === 'done';

  // ---------------------------------------------------------------- the header
  function head() {
    const passed = b.library;
    return [
      ['back', html`<button class="back-link" data-act="back" aria-label="До Майстерні" data-tip="До Майстерні" data-kbd="Esc">${ic('arrowLeft')}</button>`],
      ['title', html`<div class="ws-head-title">
        <h1 class="page-title">${b.number != null ? html`<span class="ws-no num">№${b.number}</span>` : ''}${b.title}</h1>
        ${b.coverTitle ? html`<div class="page-sub serif">${highlightTokens(b.coverTitle)}</div>` : ''}</div>`],
      ...(b.tier ? [['tier', html`<span class="chip chip-accent ws-tier" data-tip="${b.tier === 'H' ? 'Tier H — герой-дитина на кожному розвороті' : 'Tier S — без постійного героя'}">Tier ${b.tier}</span>`]] : []),
      ['tools', html`<div class="page-actions">
        <div class="tools">
          ${ib('agent', 'Відкрити агента — Antigravity; у буфері «Продовжуємо книгу …» з повною адресою книги', 'data-act="agent"')}
          <span class="sep"></span>
          ${ib('images', 'Сторінки — нарізані 1–30 і Cover.png, набір для Canva', 'data-act="open" data-what="pictures"')}
          ${ib('original', 'Оригінали — картинки, як їх віддав генератор', 'data-act="open" data-what="originals"')}
          ${ib('folderOpen', 'Папка книги в Провіднику: сторінки, оригінали, мокапи, etsy', 'data-act="open" data-what="folder"')}
          ${ib('more', 'Ще', 'data-act="more"')}
          ${ready() && !passed ? '' : html`<span class="sep"></span>${passed
            ? ib('checkCircle', 'Книга вже в бібліотеці замовлень — відкрити її там', 'data-act="to-library"')
            : ib('shelf', 'Передати в бібліотеку замовлень — коли сторінки й обкладинка готові', 'data-act="to-library"')}`}</div>
        ${ready() && !passed ? html`<button class="btn btn-primary" data-act="to-library" data-tip="Книга готова — передати в бібліотеку замовлень">${ic('shelf')}Передати в бібліотеку</button>` : ''}
      </div>`],
    ];
  }

  // ---------------------------------------------------------------- the path strip
  // The path strip is the shared one (path.js): a picture per step, the word and the count in the tooltip.
  const STEP_ICON = { formula: 'sparkle', hero: 'hero', story: 'spread', text: 'text', prompts: 'prompt', pictures: 'images',
    cover: 'book', canva: 'canva', mockups: 'mockup', photos: 'camera', library: 'shelf' };
  function stepHtml(s, i) {
    let tip = `${s.label}: ${STATE_TEXT[s.state]}`;
    if (['pictures', 'photos'].includes(s.key)) tip += ` · ${s.count} з ${s.total}`;
    if (s.check) tip += ` · перевірка: ${checkWord(s.check)}`;
    if (s.key === 'photos') tip += '; категорії можна пропускати — тоді позначте вручну';
    else if (s.manual) tip += ' · позначається вручну';
    const steps = b.steps.map((x) => ({ ...x, icon: STEP_ICON[x.key] || 'sparkle' }));
    return pathStep({ ...steps[i], tip, nogo: !!(s.check && !s.check.go),
      thumb: s.key === 'hero' && s.thumb ? pic('agent', s.thumb, 96) : '' }, i, steps, { act: 'step', active: mem.step, tabs: true });
  }

  // ---------------------------------------------------------------- the step's panel
  function renderDoc(text) {
    // A light reading of Markdown: headings stand out, code blocks keep their lines, the rest as written.
    const out = [];
    let code = null;
    for (const line of text.replace(/\r/g, '').split('\n')) {
      if (line.trim().startsWith('```')) {
        if (code) { out.push(html`<pre>${code.join('\n')}</pre>`); code = null; } else code = [];
        continue;
      }
      if (code) { code.push(line); continue; }
      const h = line.match(/^(#{1,4})\s+(.*)$/);
      out.push(h ? html`<div class="h h${h[1].length}">${h[2]}</div>` : html`<div class="p">${line}</div>`);
    }
    if (code) out.push(html`<pre>${code.join('\n')}</pre>`);
    return html`<div class="ws-doc">${out}</div>`;
  }

  function checkBody(c) {
    // The book check (the old validator's rules): what fails, what to glance at, what passed.
    const list = (items, cls) => items.map((m) => html`<li class="${cls}">${m}</li>`);
    return html`${c.go
      ? html`<div class="notice notice-success ws-check-head">${ic('checkCircle')}<div><b>GO</b> — механічно готово: помилок немає${c.warns.length ? `, ${c.warns.length} ${plural(c.warns.length, ['попередження', 'попередження', 'попереджень'])} — глянути` : ''}.</div></div>`
      : html`<div class="notice notice-error ws-check-head">${ic('alertCircle')}<div><b>Не готово</b> — ${c.fails.length} ${plural(c.fails.length, ERRORS)}. Попросіть агента виправити їх до GO.</div></div>`}
      ${c.fails.length ? html`<div class="ws-check-group"><div class="eyebrow">Помилки</div><ul class="ws-check-list">${list(c.fails, 'fail')}</ul></div>` : ''}
      ${c.warns.length ? html`<div class="ws-check-group"><div class="eyebrow">Попередження</div><ul class="ws-check-list">${list(c.warns, 'warn')}</ul></div>` : ''}
      <div class="faint ws-check-foot">Пройдено перевірок: <span class="num">${c.passed}</span> · ті самі правила, що в <span class="mono">pipeline/check_book.py</span></div>`;
  }

  function heroActions(s) {
    const waiting = waitingFor(id, 'hero', null);
    return html`<div class="ws-hero-actions">
      ${waiting ? waitChip('чекаю героя з «Завантажень»')
        : b.heroPrompt ? html`<button class="btn btn-sm ${s.thumb ? '' : 'btn-primary'}" data-act="gen" data-key="hero" data-tip="Промпт героя — у буфер; завантажений герой стане canonical.png">${ic(s.thumb ? 'regenerate' : 'generate')}${s.thumb ? 'Згенерувати ще раз' : 'Генерувати героя'}</button>` : ''}
      ${s.thumb ? html`<button class="btn btn-sm" data-act="copy-hero" data-tip="canonical.png — у буфер, щоб вставити в новий чат">${ic('copy')}Героя в буфер</button>` : ''}
      <button class="btn btn-sm" data-act="pick" data-key="hero" data-variant="" data-tip="Покласти готову картинку як canonical.png">${ic('upload')}Обрати файл</button>
    </div>`;
  }

  function miniRows() {
    // The 16 rows as small frames: a filled one shows its pages; a click scrolls to the row.
    return html`<div class="ws-mini">${inner().map((r) => html`<button class="ws-mini-row ${r.pictures.length ? 'full' : ''}" data-act="goto" data-row="${r.key}" data-tip="${r.label} — показати рядок">
      <div class="ws-mini-art ${r.kind === 'single' ? 'single' : ''}">${r.pictures.map((p) => html`<img data-fade loading="lazy" decoding="async" alt="" src="${pic('pictures', p, 240)}">`)}</div>
      <div class="ws-mini-label num">${shortLabel(r)}</div></button>`)}</div>`;
  }

  // «Мокапи» (the owner, 29.09.2026): made from here they go into the book's folder «mockups», the step ticks itself; back
  // to them at any time — the folder, the Mockups for this book, its slides in the editor.
  function mockupsBody(s) {
    const made = s.mockups || s.slides;
    const what = [s.mockups ? `${s.mockups} ${plural(s.mockups, ['мокап', 'мокапи', 'мокапів'])}` : '',
      s.noBg ? `без фону — ${s.noBg}` : '', s.slides ? `${s.slides} ${plural(s.slides, ['слайд', 'слайди', 'слайдів'])} для лістингу` : '']
      .filter(Boolean).join(' · ');
    return html`<div class="ws-manual"><div>${made ? html`У папці книги: ${what}.` : s.state === 'done'
      ? 'Позначено: мокапи зроблено поза Book Studio.' : 'Мокапи ще не робились. Зроблені звідси, вони ляжуть у папку книги, а крок позначиться сам.'}</div>
      <div class="row-wrap">
        <button class="btn ${made || s.state === 'done' ? '' : 'btn-primary'}" data-act="to-mockups">${ic('mockup')}${made ? 'Редагувати мокапи' : 'Зробити мокапи'}</button>
        ${s.editable ? html`<button class="btn" data-act="to-slides">${ic('images')}Редагувати слайди</button>` : ''}
        ${made ? html`<button class="btn" data-act="open" data-what="mockups">${ic('folderOpen')}Відкрити папку мокапів</button>` : ''}
        ${s.slides ? html`<button class="btn" data-act="open" data-what="etsy">${ic('folderOpen')}Відкрити папку Etsy</button>` : ''}
        <button class="btn btn-ghost" data-act="mark" data-step="mockups">${s.state === 'done' ? 'Зняти позначку' : html`${ic('check')}Позначити зробленим`}</button>
      </div></div>`;
  }

  // «Фото» (the owner, 30.09.2026): a lifestyle photo per category with our book in it. A card per category (its photo,
  // or an empty frame); a click shows the category's templates, and a click on one puts it into the clipboard, then the
  // book's reference (Cover 1, Cover & Open 1 or the Canva cover — shown on top), then the prompt; the photo the owner
  // downloads lands in the book's etsy/ folder. A category may be skipped: the step is ticked by all seven, or by hand.
  // «Книга в руках у людини» is a video made in Gemini Omni: the same clipboard; the video is caught (its first 2 seconds
  // cut off by the server) and its card plays it.
  let photoTemplates = null, photoTemplatesAt = 0;
  async function templatesOf(key) {
    if (!photoTemplates || Date.now() - photoTemplatesAt > 8000) {
      photoTemplates = (await api('/api/photos')).categories;
      photoTemplatesAt = Date.now();
    }
    return photoTemplates.find((c) => c.key === key)?.templates || [];
  }

  async function photosBody(s) {
    const p = b.photos;
    if (!p.cards.some((c) => c.key === mem.photoCat)) mem.photoCat = (p.cards.find((c) => !c.photo) || p.cards[0]).key;
    const sel = p.cards.find((c) => c.key === mem.photoCat);
    const tpl = await templatesOf(sel.key);
    const a = genState()?.active;
    const busy = (key) => (uploading.has(key) ? html`<div class="busy-overlay"><div class="ws-up"><i data-up="${key}"></i></div></div>` : '');
    const refs = html`<div class="ph-refs">${p.refs.map((r) => {
      const art = r.name ? html`<img data-fade loading="lazy" decoding="async" alt="${r.label}" src="${pic('mockups', r.name, 240)}">` : ic(r.key === 'canva-cover' ? 'upload' : 'mockup');
      const inner = html`<span class="ph-ref-art">${art}</span><span class="ph-ref-text"><b>${r.label}</b><span>${r.name ? 'є в папці мокапів' : r.key === 'canva-cover' ? 'перетягніть сюди' : 'ще немає'}</span></span>`;
      const cls = `ph-ref ${r.name ? 'ok' : 'missing'} ${r.key === sel.ref ? 'used' : ''}`;
      return r.key === 'canva-cover'
        ? html`<div class="ws-drop ph-ref-drop" data-drop="canva-cover"><button type="button" class="${cls}" data-act="pick" data-key="canva-cover" data-variant="" data-tip="${r.name ? `${r.name} — перетягніть або оберіть інший файл, щоб замінити` : r.missing}">${inner}</button>${busy('canva-cover')}</div>`
        : html`<div class="${cls}" data-tip="${r.name || r.missing}">${inner}</div>`;
    })}</div>`;
    const cards = html`<div class="ph-cards">${p.cards.map((c) => {
      const waiting = waitingFor(id, `photo:${c.key}`, null);
      const art = c.omni
        ? html`<video muted loop autoplay playsinline preload="metadata" src="${pic('etsy', c.photo)}"></video>`
        : html`<img data-fade loading="lazy" decoding="async" alt="${c.label}" src="${pic('etsy', c.photo, 480)}">`;
      const look = c.omni
        ? ib('external', 'Відкрити відео', `data-act="photo-play" ${attr('data-name', c.photo)}`, { cls: 'sm' })
        : ib('expand', 'Переглянути', `data-act="photo-zoom" ${attr('data-cat', c.key)}`, { cls: 'sm' });
      return html`<div class="ph-card ${c.key === sel.key ? 'sel' : ''} ${c.photo ? 'full' : ''} ${waiting ? 'waiting' : ''}">
        <div class="ws-drop ph-card-drop" data-drop="photo:${c.key}" data-video="${c.omni ? '1' : ''}">
          ${c.photo ? html`<div class="ph-card-art" data-act="photo-cat" data-cat="${c.key}">${art}
              <div class="img-actions">${look}${ib('download', 'Зберегти як…', `data-act="save" data-area="etsy" ${attr('data-name', c.photo)}`, { cls: 'sm' })}${ib('trash', `Прибрати ${c.omni ? 'відео' : 'фото'} — у папку .replaced книги`, `data-act="photo-remove" ${attr('data-cat', c.key)}`, { cls: 'sm danger' })}</div></div>`
            : html`<button type="button" class="ph-card-ph" data-act="photo-cat" data-cat="${c.key}" aria-label="${c.label}">${ic(c.omni ? 'video' : 'camera')}</button>`}
          ${waiting ? html`<div class="ws-wait"><span class="ws-pulse"></span>${c.omni ? 'Чекаю відео…' : 'Чекаю фото…'}</div>` : ''}${busy(`photo:${c.key}`)}
        </div>
        <button type="button" class="ph-card-label" data-act="photo-cat" data-cat="${c.key}">${c.photo ? ic('checkCircle', 'icon-s') : ''}${c.label}</button>
      </div>`;
    })}</div>`;
    const ref = p.refs.find((r) => r.key === sel.ref);
    const nowTpl = (name) => a?.kind === 'photo' && a.book === id && a.category === sel.key && a.template === name;
    const pick = html`<div class="ph-pick">
      <div class="ph-pick-head"><b>${sel.label}</b><span class="ph-flow">фото ${ic('chevRight', 'icon-s')} ${ref.label} ${ic('chevRight', 'icon-s')} промпт</span>
        <span class="spacer"></span>${ib('prompt', 'Промпт цієї категорії — у буфер', `data-act="photo-prompt" ${attr('data-cat', sel.key)}`)}</div>
      ${ref.name ? '' : html`<div class="notice notice-warn">${ic('alert')}<div>${ref.missing}</div></div>`}
      ${sel.omni ? html`<div class="notice notice-info">${ic('video')}<div>Це відео для Gemini Omni: фото, ${ref.label} і промпт ідуть у буфер як завжди. Завантажене відео Book Studio зловить сам, обріже перші 2 секунди й покладе в папку Etsy книги.</div></div>` : ''}
      ${tpl.length ? html`<div class="ph-tiles sm">${tpl.map((t) => html`<div class="ph-tile ${t.name === sel.template ? 'used' : ''} ${nowTpl(t.name) ? 'now' : ''}" style="aspect-ratio:${t.size ? `${t.size[0]} / ${t.size[1]}` : '1 / 1'}">
          <button type="button" class="ph-shot" data-act="photo-start" data-cat="${sel.key}" data-name="${t.name}" data-tip="${`У буфер: це фото, далі Ctrl+V у Chrome — ${ref.label}, ще раз — промпт${t.name === sel.template ? ' · цю заготовку брали востаннє' : ''}`}">
            <img data-fade alt="${t.name}" src="${media(`/media/photos/${encodeURIComponent(sel.key)}/${encodeURIComponent(t.name)}`, { w: 360, v: t.v })}" loading="lazy"></button>
          ${t.name === sel.template ? html`<span class="ph-used">${ic('check')}</span>` : ''}</div>`)}</div>`
        : html`<div class="ws-missing">У цій категорії ще немає заготовок — додайте їх у «Фотомокапи».</div>`}
    </div>`;
    return html`${refs}${cards}${pick}
      <div class="row-wrap ph-foot">
        <button class="btn" data-act="open" data-what="etsy">${ic('folderOpen')}Відкрити папку Etsy</button>
        <a class="btn btn-ghost" href="#/photos">${ic('camera')}Усі заготовки</a>
        ${p.count === p.total ? '' : html`<button class="btn btn-ghost" data-act="mark" data-step="photos" data-tip="Категорії можна пропускати — позначте крок, коли фото досить">${s.state === 'done' ? 'Зняти позначку' : html`${ic('check')}Позначити зробленим`}</button>`}
      </div>`;
  }

  async function panelBody(s, file) {
    if (s.key === 'mockups') return mockupsBody(s);
    if (s.key === 'photos') return photosBody(s);
    if (s.manual) {
      return html`<div class="ws-manual"><div>${MANUAL[s.key]} поза Book Studio? Позначте крок, коли зроблено.</div>
        <div class="row-wrap">${s.key === 'mockups' ? html`<a class="btn" href="#/mockups">${ic('mockup')}Відкрити Мокапи</a>` : ''}
        <button class="btn ${s.state === 'done' ? '' : 'btn-primary'}" data-act="mark" data-step="${s.key}">${s.state === 'done' ? 'Зняти позначку' : html`${ic('check')}Зроблено`}</button></div></div>`;
    }
    if (s.key === 'library') {
      return b.library
        ? html`<div class="ws-manual"><div>Книга в бібліотеці замовлень${b.library.listingId ? html` · лістинг <span class="num">#${b.library.listingId}</span>` : ''}: замовлення знаходять її за лістингом. Обкладинку й сторінки бібліотека бере звідси: заміните тут — зміниться й там.</div>
          <button class="btn" data-act="to-library">${ic('shelf')}Відкрити в бібліотеці</button></div>`
        : html`<div class="ws-manual">${missingSummary()}<button class="btn" data-act="to-library">${ic('shelf')}Передати в бібліотеку</button></div>`;
    }
    if (s.key === 'pictures') {
      return html`${s.count ? '' : html`<div class="ws-missing">Картинок ще немає — натисніть «Генерувати всю книгу» над рядками.</div>`}${miniRows()}`;
    }
    if (s.state === 'skip') return html`<div class="ws-missing">Книга без постійного героя (Tier S) — цей крок не потрібен.</div>`;
    const hero = s.key === 'hero' ? heroActions(s) : '';
    if (s.key === 'cover' && !file) {
      return html`<div class="ws-missing">Обкладинка — остання картка внизу сторінки: два етапи, картинка й поля.</div><button class="btn btn-sm" data-act="goto" data-row="cover">Показати обкладинку</button>`;
    }
    if (!file) return html`${hero}<div class="ws-missing">${WHO[s.key] || ''}</div>`;
    if (!file.exists) return html`${hero}<div class="ws-missing"><div>Ще немає: <span class="mono">${file.name}</span></div><div>${WHO[s.key] || ''}</div></div>`;
    if (file.kind === 'check') return checkBody(b.check);
    if (file.kind === 'image') {
      return html`${hero}<div class="ws-shot"><img data-fade alt="${file.name}" src="${pic(file.area, file.name, 1400)}" data-act="zoom-one" data-area="${file.area}" data-name="${file.name}"></div>`;
    }
    const key = `${file.area}/${file.name}`, version = b.v?.[key] || '';
    if (docs.get(key)?.version !== version) {
      const { text } = await api(url(`/file?name=${encodeURIComponent(file.name)}`));
      docs.set(key, { version, text });
    }
    return html`${hero}${renderDoc(docs.get(key).text)}`;
  }

  function panelFiles(s) {
    if (s.key === 'cover' && !step('cover').files.some((f) => f.area === 'pictures')) return [];
    const files = s.manual || ['pictures', 'library'].includes(s.key) ? [] : [...s.files];
    if (s.key === 'prompts' && b.check) files.unshift({ name: '__check', label: 'Перевірка', kind: 'check', exists: true });
    return files;
  }

  let panelSeq = 0;
  async function paintPanel() {
    const panel = $('#ws-panel');
    const s = step(mem.step);
    const my = ++panelSeq;
    if (!s) { panel.hidden = true; panelKey = null; return; }   // closes by its height (css); the content stays until it has gone
    const files = panelFiles(s);
    const file = files.find((f) => f.name === mem.tabs.get(s.key)) || files.find((f) => f.exists) || files[0];
    let body;
    try { body = await panelBody(s, file); } catch (err) { body = html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`; }
    if (my !== panelSeq) return; // a newer draw is on its way
    const tabIcon = (f) => (f.kind === 'image' ? 'image' : f.kind === 'check' ? (b.check?.go ? 'checkCircle' : 'alertCircle') : /prompt/.test(f.name) ? 'prompt' : 'text');
    const tabs = files.length > 1 && s.state !== 'skip' ? html`<div class="seg ws-tabs"><span class="seg-pill"></span>${files.map((f) => html`<button type="button"
      class="${f === file ? 'active' : ''} ${f.exists ? '' : 'missing'} ${f.kind === 'check' ? (b.check.go ? 'go' : 'nogo') : ''}" data-act="tab" data-file="${f.name}"
      data-tip="${f.kind === 'check' ? 'Перевірка промптів (GO)' : f.exists ? f.name : `${f.name} — ще немає`}">${ic(tabIcon(f), 'icon-s')}${f.label || f.name}</button>`)}</div>` : '';
    let state = s.key === 'pictures' || (s.key === 'photos' && s.state !== 'done') ? `${s.count} з ${s.total}` : STATE_TEXT[s.state];
    if (s.check) state += s.check.go ? ' · GO' : ' · перевірка не пройдена';
    const canOpen = file?.exists && file.area === 'agent';
    const wasOpen = !panel.hidden;
    panel.hidden = false;
    const drawn = patch(panel, [
      ['head', html`<div class="ws-panel-head">
        <div class="ws-panel-title">${s.key === 'photos' ? html`${ic('camera', 'icon-s')}Фотомокапи` : s.label}</div><div class="ws-panel-state ${s.state}">${state}</div>
        <div class="ws-panel-tools">${tabs}${canOpen ? ib('fileOpen', 'Відкрити файл у Windows', `data-act="open" data-what="agent" ${attr('data-name', file.name)}`) : ''}${ib('x', 'Згорнути', 'data-act="fold"')}</div></div>`],
      ['body', html`<div class="ws-panel-body">${body}</div>`],
    ]);
    drawn.forEach(fadeImages);
    panel.querySelectorAll('.seg').forEach(syncSeg);
    const key = `${s.key}|${file?.name || ''}`;
    if (key !== panelKey && wasOpen && panelKey) appear(panel.querySelector('.ws-panel-body'), 220);
    panelKey = key;
  }

  // ---------------------------------------------------------------- the rows (workshop-rows.js)
  const { saveBtn, waitCover, busyCover, genButton, promptBlock, textBlock, rowCard, upChip, upBtn } = rowTemplates({ id, book: () => b, mem, uploading });

  // ---------------------------------------------------------------- the cover: ① the picture ② its margins
  function coverCard() {
    const r = b.rows.find((x) => x.key === 'cover');
    const c = b.cover;
    const artV = c.art ? b.v?.[`originals/${c.art}`] || c.art : '';
    if (coverSeen && artV && coverSeen.art !== artV) mem.cover = 0; // a new picture: on to its margins
    const stage = mem.cover || (c.final || c.art ? 2 : 1);
    coverSlide = coverSeen && coverSeen.stage !== stage ? (stage > coverSeen.stage ? 'slide-next' : 'slide-back') : '';
    coverSeen = { art: artV, stage };
    const w1 = waitingFor(id, 'cover', ''), w2 = waitingFor(id, 'cover-wrap', '');
    const stepBtn = (n, label, done, now) => html`<button type="button" class="ws-cv-step ${stage === n ? 'on' : ''} ${done ? 'done' : ''}" data-act="cover-stage" data-stage="${n}">
      <span class="ws-cv-no">${done ? ic('check') : n}</span>${label}${now ? html`<span class="ws-pulse"></span>` : ''}</button>`;
    const ratio = (s) => (s && s[0] && s[1] ? raw(` style="aspect-ratio:${s[0]} / ${s[1]}"`) : '');
    let pane;
    if (stage === 1) {
      const artFrame = c.art
        ? html`<div class="ws-drop" data-drop="cover" data-variant=""><div class="ws-art ws-wide"${ratio(c.artMarks.source)}>
            <img data-fade alt="Обкладинка" src="${pic('originals', c.art, 1400)}" data-act="zoom" data-key="cover-art">
            ${saveBtn('originals', c.art, '', 'Зберегти обкладинку як…')}
            ${c.artMarks.source ? html`<div class="ws-marks"><span class="chip ws-mark num">${c.artMarks.source[0]}×${c.artMarks.source[1]}</span></div>` : ''}
            <div class="img-actions">${ib('upload', 'Замінити файлом', 'data-act="pick" data-key="cover" data-variant=""', { cls: 'sm' })}${ib('trash', 'Прибрати обкладинку (і її поля)', 'data-act="remove" data-key="cover" data-variant=""', { cls: 'sm danger' })}</div>
          </div>${busyCover('cover')}${w1 ? waitCover('Чекаю обкладинку…') : ''}</div>`
        : html`<div class="ws-frame"><div class="ws-drop" data-drop="cover" data-variant=""><button type="button" class="ws-ph" data-act="pick" data-key="cover" data-variant="">
            <span class="ws-half">задня</span><span class="ws-half">передня</span>
            <span class="ws-ph-text"><span class="drop-ico">${ic('upload')}</span><b>Перетягніть обкладинку</b><span>або клацніть, щоб обрати файл</span></span></button>
            ${busyCover('cover')}${w1 ? waitCover('Чекаю обкладинку з «Завантажень»…') : ''}</div></div>`;
      pane = html`${promptBlock(r, '', 'Промпт обкладинки (агент 6)')}${artFrame}${textBlock(r)}
        ${c.art ? html`<div class="ws-cv-next"><button class="btn btn-primary" data-act="cover-stage" data-stage="2">Далі: поля${ic('chevRight')}</button></div>` : ''}`;
    } else {
      // The picture laid on the printer's template, white all round → the generator fills the margins → Cover.png at
      // the template's exact size. The template's lines can be shown over it.
      const lay = c.layout || {};
      const [cw, ch] = lay.size || [1, 1];
      const [ax, ay, aw, ah] = lay.art || [0, 0, cw, ch];
      const pct = (v, of) => `${((v / of) * 100).toFixed(3)}%`;
      const box = (g) => `left:${(g[0] * 100).toFixed(3)}%;top:${(g[1] * 100).toFixed(3)}%;width:${(g[2] * 100).toFixed(3)}%;height:${(g[3] * 100).toFixed(3)}%`;
      const G = c.guides;
      const lines = mem.guides && !c.skipped ? html`<div class="ws-tpl" aria-hidden="true">
          <span class="ws-tpl-trim" style="${box(G.trim)}"></span><span class="ws-tpl-spine" style="${box(G.spine)}"></span>
          <span class="ws-tpl-safe" style="${box(G.back)}"><em>задня</em></span><span class="ws-tpl-safe" style="${box(G.front)}"><em>передня</em></span></div>` : '';
      const tpx = c.template.px;
      const shown = c.final
        ? html`<img data-fade alt="Обкладинка з полями" src="${pic('pictures', c.final, 2600)}" data-act="zoom" data-key="cover">${saveBtn('pictures', c.final, '', 'Зберегти готову обкладинку як…')}`
        : c.expanded ? html`<img data-fade alt="Обкладинка з білими полями" src="${pic('originals', c.expanded, 2600)}"><span class="ws-cv-inner" style="left:${pct(ax, cw)};top:${pct(ay, ch)};width:${pct(aw, cw)};height:${pct(ah, ch)}"></span>` : '';
      pane = html`<div class="ws-cv-bar">
          <div class="tools">${ib('guides', mem.guides ? 'Сховати лінії шаблону друкарні' : 'Показати лінії шаблону друкарні: обріз, корінець, безпечні зони', 'data-act="guides"', { cls: mem.guides ? 'on' : '' })}</div>
          <span class="ws-cv-info num">${c.final ? (c.skipped ? 'без полів' : `${tpx[0]}×${tpx[1]} px · ${c.template.dpi} dpi`) : `поля за шаблоном · ${cw}×${ch} px`}</span>
          ${c.final ? upChip('cover-wrap', c.wrapMarks) : ''}
          <span class="spacer"></span>
          ${c.final ? '' : html`<button class="btn btn-sm btn-ghost" data-act="no-margins" data-tip="Взяти обкладинку як є, без полів — вона стане Cover.png">Без полів</button>`}
          ${w2 ? waitChip('чекаю обкладинку з полями')
            : html`<button class="btn btn-sm ${c.final ? '' : 'btn-primary'}" data-act="gen" data-key="cover-wrap" data-variant="" data-tip="У буфер: обкладинка з полями, потім промпт аутпейнту — Ctrl+V у Chrome сам перемикає">${ic(c.final ? 'regenerate' : 'generate')}${c.final ? 'Ще раз' : 'Генерувати поля'}</button>`}
        </div>
        <div class="ws-drop" data-drop="cover-wrap" data-variant="">
          <div class="ws-art ws-wide ${c.final ? '' : 'margins'}"${ratio(c.final && !c.skipped ? tpx : c.final ? c.artMarks.source : [cw, ch])}>${shown}${lines}
            ${c.final ? html`<div class="img-actions">${upBtn('cover-wrap', c.wrapMarks)}${ib('copy', 'Копіювати готову обкладинку як картинку', 'data-act="copy-picture" data-key="cover"', { cls: 'sm' })}
              ${ib('upload', 'Замінити файлом', 'data-act="pick" data-key="cover-wrap" data-variant=""', { cls: 'sm' })}
              ${ib('trash', 'Прибрати поля (сама обкладинка лишиться)', 'data-act="remove" data-key="cover-wrap" data-variant=""', { cls: 'sm danger' })}</div>` : ''}
          </div>${busyCover('cover-wrap')}${w2 ? waitCover('Чекаю обкладинку з полями…') : ''}</div>
        ${c.outpaint ? promptBlock({ key: 'cover-wrap', prompt: c.outpaint }, '', 'Промпт аутпейнту — заповнити тільки білі поля') : ''}`;
    }
    return html`<section class="ws-row ws-cover ${w1 || w2 ? 'waiting' : ''}" id="row-cover">
      <div class="ws-row-head"><span class="ws-row-label">Обкладинка</span>
        <span class="ws-cv-steps">${stepBtn(1, 'Картинка', !!c.art, w1)}<i class="ws-cv-line ${c.art ? 'on' : ''}"></i>${stepBtn(2, 'Поля', !!c.final, w2)}</span>
        <span class="ws-row-act">${stage === 1 ? genButton({ ...r, pictures: c.art ? [c.art] : [] }) : ''}</span></div>
      <div class="ws-cv-body"><div class="ws-cv-pane">${pane}</div></div>
    </section>`;
  }

  // ---------------------------------------------------------------- hero variants (only when the agent made one)
  function variantHero(v) {
    const waiting = waitingFor(id, 'hero', v.name);
    return html`<section class="ws-row ${waiting ? 'waiting' : ''}">
      <div class="ws-row-head"><span class="ws-row-label">Герой варіанта · ${v.name}</span><span class="ws-row-act">
        ${v.hero ? html`<button class="btn btn-sm" data-act="copy-hero" data-variant="${v.name}">${ic('copy')}Героя в буфер</button>` : ''}
        ${waiting ? waitChip('чекаю картинку')
          : v.heroPrompt ? html`<button class="btn btn-sm ${v.hero ? '' : 'btn-primary'}" data-act="gen" data-key="hero" data-variant="${v.name}">${ic(v.hero ? 'regenerate' : 'generate')}${v.hero ? 'Ще раз' : 'Генерувати'}</button>` : ''}</span></div>
      <div class="ws-vhero">
        <div class="ws-drop ws-hero-shot" data-drop="hero" data-variant="${v.name}">
          ${v.hero ? html`<div class="ws-art"><img data-fade loading="lazy" decoding="async" alt="Герой варіанта ${v.name}" src="${pic('agent', v.hero, 600, v.name)}"></div>`
            : html`<button type="button" class="ws-ph" data-act="pick" data-key="hero" data-variant="${v.name}"><span class="ws-ph-text"><span class="drop-ico">${ic('hero')}</span><b>Героя ще немає</b><span>згенеруйте або перетягніть</span></span></button>`}
          ${busyCover('hero')}</div>
        <div class="ws-block ws-prompt grow"><div class="ws-block-head"><span class="eyebrow">Промпт героя (правка canonical.png)</span></div>
          ${v.heroPrompt ? html`<pre class="ws-body ws-mono clamp">${v.heroPrompt}</pre>` : html`<div class="ws-body empty-text">hero-prompt.md ще немає — його напише агент.</div>`}</div>
      </div></section>`;
  }

  /** A variant's own cover (the owner, 27.09.2026): one frame, the finished wide cover at once — no stages, no
   *  prompt; «Генерувати» puts the base cover and the variant's hero in the clipboard and waits for the picture. */
  function variantCover(v) {
    const c = v.cover || {};
    const waiting = waitingFor(id, 'cover-wrap', v.name);
    const tpx = b.cover.template.px;
    const act = (k) => `data-key="cover-wrap" data-variant="${v.name}" ${k}`;
    const art = c.final
      ? html`<div class="ws-art ws-wide" style="aspect-ratio:${tpx[0]} / ${tpx[1]}">
          <img data-fade alt="Обкладинка ${v.name}" src="${pic('pictures', c.final, 2600, v.name)}" data-act="zoom" data-key="cover">
          ${saveBtn('pictures', c.final, v.name, `Зберегти обкладинку ${v.name} як…`)}
          <div class="ws-marks">${upChip(slot('cover-wrap', v.name), c.marks)}${c.marks?.cut ? html`<span class="chip ws-mark">обрізано під шаблон</span>` : ''}</div>
          <div class="img-actions">${upBtn(slot('cover-wrap', v.name), c.marks)}${ib('upload', 'Замінити файлом', act('data-act="pick"'), { cls: 'sm' })}${ib('trash', 'Прибрати обкладинку варіанта', act('data-act="remove"'), { cls: 'sm danger' })}</div></div>`
      : html`<button type="button" class="ws-ph" data-act="pick" ${raw(act(''))}>
          <span class="ws-half">задня</span><span class="ws-half">передня</span>
          <span class="ws-ph-text"><span class="drop-ico">${ic('upload')}</span><b>Перетягніть обкладинку ${v.name}</b><span>одразу розширену, з полями — або клацніть, щоб обрати файл</span></span></button>`;
    const drop = html`<div class="ws-drop" data-drop="cover-wrap" data-variant="${v.name}">${art}${busyCover('cover-wrap')}${waiting ? waitCover('Чекаю обкладинку з «Завантажень»…') : ''}</div>`;
    return html`<section class="ws-row ws-cover ${waiting ? 'waiting' : ''}" id="row-cover">
      <div class="ws-row-head"><span class="ws-row-label">Обкладинка · ${v.name}</span><span class="ws-row-act">
        ${waiting ? waitChip('чекаю обкладинку')
          : html`<button class="btn btn-sm ${c.final ? '' : 'btn-primary'}" data-act="gen" data-key="cover-wrap" data-variant="${v.name}" data-tip="У буфер: основна обкладинка і герой варіанта (що є); Майстерня чекає обкладинку з «Завантажень» — її зведе до шаблону друкарні">${ic(c.final ? 'regenerate' : 'generate')}${c.final ? 'Ще раз' : 'Генерувати'}</button>`}</span></div>
      ${c.final ? drop : html`<div class="ws-frame">${drop}</div>`}
    </section>`;
  }

  /** «Апскейл ×2» for the whole book (on by default; the owner, 27.09.2026) — and what's left to upscale. */
  function upSwitch(v) {
    const u = b.upscale;
    if (!u) return '';
    const tip = !u.available ? 'Апскейл — додатковий модуль: він ще не встановлений. Кнопка поруч встановить його (≈ 40 МБ)'
      : u.on ? `Кожна сторінка й обкладинка після того, як лягла в рядок, збільшується ×${u.scale} (Upscayl, ${u.model}) — у фоні, по одній. Вимкніть, щоб лишити книгу як є`
        : 'Апскейл вимкнено для цієї книги — сторінки лишаються такими, як їх зробив генератор';
    const busy = u.queue.length + (u.current ? 1 : 0);
    // What's left on this tab (the base book's rows, or this variant's): to upscale, and to cut again from an original
    // that is big already (upscaled by hand and put back into originals/).
    const mine = (s) => (v ? s.startsWith(`${v.name}/`) : !s.includes('/'));
    const free = u.todo.filter((k) => mine(k) && !u.queue.includes(k) && u.current?.key !== k);
    const recut = free.filter((k) => u.sides[k]?.recut);
    const left = free.filter((k) => !u.sides[k]?.recut);
    const keys = (list) => JSON.stringify(list);
    return html`<label class="ws-upscale ${u.available ? '' : 'off'}" data-tip="${tip}"><span class="switch"><input type="checkbox" data-act="upscale" ${u.on && u.available ? 'checked' : ''} ${u.available ? '' : 'disabled'} aria-label="Апскейл ×${u.scale}"></span>Апскейл ×${u.scale}</label>
      ${u.available ? '' : html`<button class="btn btn-sm" data-act="install-module" data-module="upscale" data-tip="Встановити модуль «Апскейл» (≈ 40 МБ) — тоді нові картинки збільшуватимуться самі">${ic('download', 'icon-s')}Встановити апскейл</button>`}
      ${u.on && busy ? html`<span class="chip chip-accent"><span class="ws-pulse"></span>апскейл · ще ${busy}</span>`
        : html`${u.on && u.available && left.length ? html`<button class="btn btn-sm" data-act="upscale-all" data-keys="${keys(left)}" data-tip="Сторінки цієї вкладки, які ще не апскейлені й не великі (від ${u.big} px) — у чергу">${ic('sparkle')}Апскейлити решту (${left.length})</button>` : ''}
          ${recut.length ? html`<button class="btn btn-sm" data-act="upscale-all" data-keys="${keys(recut)}" data-tip="Оригінали в папці вже великі (їх апскейлили окремо), а сторінки нарізані з маленьких — перерізати сторінки з великих, без Upscayl">${ic('images')}Перерізати з великих оригіналів (${recut.length})</button>` : ''}`}`;
  }

  /** «Підхопити з папки (N)»: pictures put into originals/ by hand with the right names (the owner, 27.09.2026 — "I
   *  put the spreads into the folder and the program doesn't pick them up"), taken the usual way on a press. */
  let adopting = null; // the variant ('' — the base book) and how far it is, while a pick-up goes on
  function adoptBtn(v) {
    const name = v ? v.name : '';
    if (adopting && adopting.variant === name) return html`<span class="chip chip-accent chip-prog"><span class="ws-pulse"></span>${adopting.text}${chipFill(adopting.p)}</span>`;
    const keys = b.leftBehind?.[name] || [];
    if (!keys.length) return '';
    const folder = v ? `originals\\variants\\${v.name}` : 'originals';
    return html`<button class="btn btn-sm" data-act="adopt" data-tip="${`У папці ${folder} є картинки з правильними назвами, для яких ще немає сторінок — розрізати, віддзеркалити й апскейлити їх, як перетягнуті`}">${ic('folderIn')}Підхопити з папки (${keys.length})</button>`;
  }

  async function adopt(btn) {
    if (adopting) return;
    const variant = mem.variant;
    adopting = { variant, text: 'Підхоплюю…' };
    paintRows();
    try {
      const res = await runJob(post(url('/adopt'), { variant }), (job) => {
        adopting.text = job.step || 'Підхоплюю…';
        adopting.p = job.percent / 100;
        paintRows();
      });
      const n = res.done.length;
      toast(`Підхоплено з папки: ${n}${res.failed.length ? ` · не вдалося: ${res.failed.join('; ')}` : ''}`, res.failed.length ? 'error' : 'success', 6000);
    } catch (err) { toast(err.message, 'error'); }
    adopting = null;
    paintRows();
    refresh();
  }

  // ---------------------------------------------------------------- painting
  function paintRows() {
    const v = mem.variant ? b.variants.find((x) => x.name === mem.variant) : null;
    if (mem.variant && !v) mem.variant = '';
    const rows = inner();
    const done = rows.filter((r) => r.pictures.length).length;
    const busy = genState()?.active?.book === id;
    // A variant's tab has no «Генерувати варіант» (the owner, 27.09.2026: "I do them one by one, it's handier").
    const left = !v && rows.some((r) => r.prompt && !r.pictures.length);
    const heroThumb = step('hero').thumb;
    patch($('#ws-rows-head'), [['head', html`<div class="ws-rows-head-in">
      <h2 class="section-title">Сторінки книги</h2>
      ${v ? html`<span class="num" data-tip="Розвороти варіанта з картинками">${v.done}/${v.rows.length}</span>`
        : html`<span class="num" data-tip="Картинки ${done} з ${rows.length} · промпти ${b.counts.prompts}/17 · тексти ${b.counts.texts}/17">${done}/${rows.length}</span>
          <span class="ws-meter"><i style="transform:scaleX(${done / rows.length})"></i></span>`}
      ${upSwitch(v)}
      <span class="spacer"></span>
      ${adoptBtn(v)}
      ${heroThumb && !v ? html`<button class="btn btn-sm" data-act="copy-hero" data-tip="Героя (canonical.png) — у буфер, щоб вставити в новий чат Gemini першим">${ic('hero')}Героя в буфер</button>` : ''}
      ${!busy && left ? html`<button class="btn btn-primary" data-act="series" data-tip="Розвороти 2–3 … 28–29, потім сторінки 1 і 30 — ті, що без картинок; після кожної картинки наступний промпт уже в буфері">${ic('generate')}${done ? 'Генерувати решту' : 'Генерувати всю книгу'}</button>` : ''}
    </div>`]]);
    patch($('#ws-vtabs'), b.variants.length ? [['tabs', html`<div class="seg ws-vtabs"><span class="seg-pill"></span>
      <button type="button" class="${v ? '' : 'active'}" data-act="variant" data-variant="">Основна</button>
      ${b.variants.map((x) => html`<button type="button" class="${v === x ? 'active' : ''}" data-act="variant" data-variant="${x.name}">${x.name}<span class="seg-count">${x.done}/${x.rows.length}</span></button>`)}</div>`]] : []);
    patch($('#ws-notes'), !v && b.notes.length ? [['notes', html`<div class="notice notice-warn">${ic('alert')}<div>${raw(b.notes.map((n) => html`${n}`).join('<br>'))}</div></div>`]] : []);
    const cards = v
      ? [[`${v.name}|hero`, variantHero(v)], ...(v.rows.length ? v.rows.map((r) => [`${v.name}|${r.key}`, rowCard(r, v.name)])
        : [[`${v.name}|none`, html`<div class="ws-missing">У цьому варіанті ще немає промптів заміни (2.json … 15.json) — їх пише агент.</div>`]]),
        [`${v.name}|cover`, variantCover(v)]]
      : [...rows.map((r) => [r.key, rowCard(r)]), ['cover', coverCard()]];
    const drawn = patch($('#ws-rows'), cards);
    drawn.forEach(fadeImages);
    if (shownVariant !== undefined && shownVariant !== mem.variant) appear($('#ws-rows'), 220);   // another tab: its rows come in
    shownVariant = mem.variant;
    for (const row of $('#ws-rows').children) {   // a picture that has just arrived into an empty frame fades in once
      const now = !!row.querySelector('.ws-art'), was = filled.get(row.dataset.key);
      if (was === false && now) row.querySelectorAll('.ws-art').forEach((a) => appear(a, 300));
      filled.set(row.dataset.key, now);
    }
    // One-shot animations go on after the redraw, not into the markup: written there, the next redraw found the markup
    // changed (the class gone) and drew the part once more, losing its hover and tip (26.09.2026).
    const body = coverSlide && $('#ws-rows .ws-cv-body');
    if (body) once(body, coverSlide);
    coverSlide = '';
    view.querySelectorAll('#ws-vtabs .seg').forEach(syncSeg);
    uploading.forEach((_, key) => paintProgress(key));
  }

  function paintProgress(key) {
    const bar = view.querySelector(`[data-up="${CSS.escape(key)}"]`);
    if (!bar) return;
    const p = uploading.get(key) || 0;
    // The upload's share is real; once it is all sent the server still cuts, flips and upscales for a time nobody can know — a neutral sweep, not a full-looking bar.
    bar.parentElement.classList.toggle('proc', p >= 1);
    bar.style.transform = p >= 1 ? '' : `scaleX(${p})`;
  }

  /** A node comes in once (opacity, a hair of scale) — for what arrives, not for what is redrawn. */
  function appear(node, ms = 260) {
    if (!node || reducedMotion()) return;
    node.animate([{ opacity: 0, transform: 'scale(.985)' }, { opacity: 1, transform: 'none' }], { duration: ms, easing: 'cubic-bezier(.2, .9, .25, 1)' });
  }

  /** A class that plays its animation once and goes. */
  function once(node, cls) {
    node.classList.remove(cls);
    void node.offsetWidth; // the same class again restarts the animation
    node.classList.add(cls);
    node.addEventListener('animationend', () => node.classList.remove(cls), { once: true });
  }

  function draw() {
    const drawn = [...patch($('#ws-head'), head()), ...patch($('#ws-strip'), b.steps.map((s, i) => [s.key, stepHtml(s, i)]))];
    drawn.forEach(fadeImages);
    for (const s of b.steps) {  // a step that has just become done pops
      if (stepsSeen && stepsSeen[s.key] !== 'done' && s.state === 'done') {
        const node = $(`#ws-strip [data-step="${s.key}"]`);
        if (node) once(node, 'just');
      }
    }
    stepsSeen = Object.fromEntries(b.steps.map((s) => [s.key, s.state]));
    paintGenBar($('#ws-gen'), id);
    paintRows();
    paintPanel();
    followWaiting();
    refreshViewer();
  }

  /** When the next row starts waiting and the one before was on screen, the page goes on to it — the owner sees where
   *  the next picture will land. */
  function followWaiting() {
    const a = genState()?.active;
    const key = a && a.book === id && a.kind !== 'photo' ? `${a.variant || ''}/${a.key.startsWith('cover') ? 'cover' : a.key}` : '';
    const before = waitSeen;
    waitSeen = key;
    if (!key || !before || key === before) return;
    const prev = view.querySelector(`#row-${before.split('/')[1]}`)?.getBoundingClientRect();
    const next = view.querySelector(`#row-${key.split('/')[1]}`);
    if (next && (!prev || (prev.bottom > 0 && prev.top < innerHeight))) next.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  // The generation's state first (the bar and the waiting rows are drawn from it), then the page.
  const unwatch = watch({ book: id, sig: first.sig, gen: first.gen }, async () => {
    try {
      b = (await api(url())).book;
    } catch (err) {
      if (err.status === 404) { toast('Книги більше немає в Майстерні', 'info'); location.hash = '#/books/work'; }
      return;
    }
    draw();
  });
  draw();

  // ---------------------------------------------------------------- the viewer
  /** The viewer's pictures: the base book's, or — on a hero variant's tab — the variant's own spreads and cover. */
  function viewerItems() {
    const items = [];
    const v = mem.variant ? b.variants.find((x) => x.name === mem.variant) : null;
    const variant = v ? v.name : '';
    const push = (key, area, name, title, sub, text) => items.push({
      key, src: pic(area, name, 1400, variant), full: pic(area, name, 2600, variant), title: v ? `${v.name} · ${title}` : title, sub, text,
      onOriginal: () => post('/api/workshop/open', { book: id, what: area, name, variant }).catch((err) => toast(err.message, 'error')),
    });
    if (v) {
      for (const r of v.rows) {
        const base = b.rows.find((x) => x.key === r.key);
        r.pictures.forEach((p, i) => push(`${r.key}:${i}`, 'pictures', p, `${r.label} · ${i ? 'права' : 'ліва'} сторінка ${r.pages[i]}`,
          `${p}${r.marks?.mirrored ? ' · віддзеркалено' : ''}`, base?.text || ''));
      }
      if (v.cover?.final) push('cover:0', 'pictures', v.cover.final, 'Обкладинка', 'за шаблоном друкарні', b.rows.find((r) => r.key === 'cover')?.text || '');
      return items;
    }
    for (const r of inner()) {
      const flipped = r.marks?.mirrored ? ' · віддзеркалено' : '';
      r.pictures.forEach((p, i) => push(`${r.key}:${i}`, 'pictures', p,
        r.pictures.length > 1 ? `${r.label} · ${i ? 'права' : 'ліва'} сторінка ${r.pages[i]}` : r.label, `${p}${flipped}`, r.text));
    }
    const c = b.cover;
    const text = b.rows.find((r) => r.key === 'cover')?.text || '';
    if (c.final) push('cover:0', 'pictures', c.final, 'Обкладинка', c.skipped ? 'без полів' : 'з полями, за шаблоном друкарні', text);
    if (c.art) push('cover-art:0', 'originals', c.art, 'Обкладинка · картинка', 'як її зробив генератор', text);
    return items;
  }
  function zoom(key) {
    lbItems.splice(0, lbItems.length, ...viewerItems());
    lb = openLightbox(lbItems, Math.max(0, lbItems.findIndex((it) => it.key === key)));
  }
  /** A picture replaced while the viewer is open: it shows the new one (only when a picture changed). */
  function refreshViewer() {
    if (!lb || !document.querySelector('.lightbox:not(.closing)')) { lb = null; return; }
    const items = viewerItems();
    if (items.map((it) => it.src).join() === lbItems.map((it) => it.src).join()) return;
    lbItems.splice(0, lbItems.length, ...items);
    if (lbItems.length) lb.refresh(Math.min(lb.index, lbItems.length - 1)); else lb.close();
  }

  // ---------------------------------------------------------------- pictures in, by hand
  let pickFor = null;
  const videoKey = (key) => !!b.photos?.cards.find((c) => `photo:${c.key}` === key)?.omni;
  async function uploadTo(key, variant, file) {
    if (videoKey(key) ? !VIDEO_RE.test(file.name) : !IMG_RE.test(file.name)) {
      toast(videoKey(key) ? `«${file.name}» — не відео (MP4, MOV, WEBM)` : `«${file.name}» — не картинка (PNG, JPG, WEBP)`, 'error');
      return;
    }
    if (uploading.has(key)) { toast('Попередня картинка ще вантажиться', 'info'); return; }
    uploading.set(key, 0);
    paintRows();
    paintPanel();
    try {
      const q = new URLSearchParams({ key, name: file.name, ...(variant ? { variant } : {}) });
      const res = await upload(url(`/place?${q}`), file, (p) => { uploading.set(key, p); paintProgress(key); });
      toast(res.note || 'Готово', res.cut ? 'info' : 'success', res.cut ? 4000 : 2600);
    } catch (err) { toast(err.message, 'error'); }
    uploading.delete(key);
    paintRows();
    paintPanel();  // a photo mockup's frame or the Canva cover is in the step's panel
    refresh();
  }

  // A removal acts at once and offers «Скасувати» (the owner's rule, 2026-09-30: a question only for what cannot be taken back):
  // the files wait in the book's .replaced and the server hands back what is needed to return them.
  async function removePicture(btn, key, variant) {
    const done = await act(btn, () => post(url('/remove'), { key, variant }));
    if (!done?.undo) return;
    const what = key === 'cover' ? 'Обкладинку прибрано' : key === 'cover-wrap' ? 'Поля обкладинки прибрано' : 'Картинку прибрано';
    toast(what, 'success', 9000, {
      undo: { label: 'Скасувати', run: async () => { await post(url('/restore'), { undo: done.undo }); toast('Повернуто', 'success', 2000); refresh(); } },
    });
  }

  // ---------------------------------------------------------------- the library
  function missingSummary() {
    const noPicture = inner().filter((r) => !r.pictures.length).map((r) => shortLabel(r));
    if (!b.cover.final) noPicture.unshift('обкладинка');
    const noText = b.rows.filter((r) => !r.text).map((r) => (r.kind === 'cover' ? 'обкладинка' : shortLabel(r)));
    const gaps = [noPicture.length && `картинок — ${noPicture.join(', ')}`, noText.length && `текстів — ${noText.join(', ')}`].filter(Boolean);
    const u = b.upscale;
    const upLabel = (s) => {
      const [variant, key] = s.includes('/') ? s.split('/') : ['', s];
      const what = key === 'cover-wrap' ? 'обкладинка' : shortLabel(b.rows.find((r) => r.key === key));
      return variant ? `${variant} ${what}` : what;
    };
    const small = u?.on ? u.todo.map(upLabel) : [];
    const notUp = small.length ? html`<div class="notice notice-warn">${ic('alert')}<div>Ще не апскейлені: ${small.join(', ')}${u.queue.length || u.current ? ' — апскейл іде, зачекайте трохи' : ''}.</div></div>` : '';
    return gaps.length
      ? html`<div class="notice notice-warn">${ic('alert')}<div>Бракує ${gaps.join('; ')}. У бібліотеці їх можна докласти пізніше.</div></div>${notUp}`
      : html`<div class="notice notice-success">${ic('checkCircle')}<div>Усі картинки й тексти на місці.</div></div>${notUp}`;
  }

  async function toLibrary() {
    if (b.library) { location.hash = `#/book/${b.library.id}`; return; }
    let existing;
    try { existing = (await api('/api/library/books')).books; } catch (err) { toast(err.message, 'error'); return; }
    openAddBook(existing, {
      summary: missingSummary(),
      send: (body, say) => runJob(post(url('/to-library'), body),
        (job) => say(`Передаю… ${Math.round(job.percent || 0)}%`)),
      done: (res) => {
        toast(`«${res.book.title}» — у бібліотеці замовлень${res.errors.length ? ` · не взято: ${res.errors.length}` : ''}`, res.errors.length ? 'info' : 'success', 6000);
        refresh();
      },
    });
  }

  // No question any more (06.10.2026): the folder waits a few minutes on the program's shelf before the Recycle Bin,
  // so «Скасувати» really brings the book back (studio/aside.py).
  async function deleteBook(btn) {
    const name = `${b.number != null ? `№${b.number} ` : ''}${b.title}`;
    const res = await act(btn, () => api(url(), { method: 'DELETE' }));
    if (!res) return;
    memory.delete(id);
    location.hash = '#/books/work';
    toast(`Книгу «${name}» видалено`, 'success', 9000, { undo: { run: async () => {
      await post('/api/aside/restore', { token: res.undo });
      toast(`«${name}» повернуто`, 'success', 2000);
      location.hash = `#/workshop/${encodeURIComponent(id)}`;
    } } });
  }

  // ---------------------------------------------------------------- events
  const rowOf = (key, variant) => (variant ? b.variants.find((x) => x.name === variant)?.rows : b.rows)?.find((r) => r.key === key)
    || (key === 'cover-wrap' ? { key, label: 'Поля обкладинки', prompt: b.cover.outpaint } : null);
  const offs = [on(view, 'click', '[data-act]', (e, t) => {
    const a = t.dataset.act;
    const { key = '', variant = '' } = t.dataset;
    if (a === 'back') { location.hash = '#/books/work'; return; }
    if (a === 'agent') { act(t, () => post('/api/workshop/agent', { book: id }), () => 'Antigravity відкривається · у буфері — ця книга з повною адресою; вставте в чат агента'); return; }
    if (a === 'open') { act(t, () => post('/api/workshop/open', { book: id, what: t.dataset.what, name: t.dataset.name || '' })); return; }
    if (a === 'more') {
      menu(t, [{ label: 'Видалити книгу…', icon: 'trash', danger: true, onClick: () => deleteBook(t) }]);
      return;
    }
    if (a === 'to-library') { toLibrary(); return; }
    if (a === 'step') { mem.step = mem.step === t.dataset.step ? null : t.dataset.step; draw(); return; }
    if (a === 'fold') { mem.step = null; draw(); return; }
    if (a === 'tab') { mem.tabs.set(mem.step, t.dataset.file); paintPanel(); return; }
    if (a === 'mark') { act(t, () => post(url('/mark'), { step: t.dataset.step, on: step(t.dataset.step).state !== 'done' })); return; }
    if (a === 'to-mockups') { remember('mk-for-book', { id }); location.hash = '#/mockups'; return; }
    if (a === 'to-slides') { location.hash = `#/slides/${encodeURIComponent(id)}/1`; return; }
    if (a === 'photo-cat') { mem.photoCat = t.dataset.cat; paintPanel(); return; }
    if (a === 'photo-start') { startPhoto(t, { book: id, category: t.dataset.cat, template: t.dataset.name }); return; }
    if (a === 'photo-prompt') { act(t, () => post('/api/photos/prompt', { category: t.dataset.cat }), 'Промпт у буфері'); return; }
    if (a === 'photo-remove') {
      confirmBox({ title: 'Прибрати фото?', text: 'Воно піде в папку .replaced книги — нічого не зникає назавжди.', confirm: 'Прибрати', danger: true })
        .then((ok) => ok && act(t, () => post(url('/photos/remove'), { category: t.dataset.cat })));
      return;
    }
    if (a === 'photo-play') { act(t, () => post('/api/workshop/open', { book: id, what: 'etsy', name: t.dataset.name })); return; }
    if (a === 'photo-zoom') {
      const shots = b.photos.cards.filter((c) => c.photo && !c.omni);
      openLightbox(shots.map((c) => ({ key: c.key, src: pic('etsy', c.photo, 1400), full: pic('etsy', c.photo, 2600), title: `Фото · ${c.label}`, sub: c.photo,
        onOriginal: () => post('/api/workshop/open', { book: id, what: 'etsy', name: c.photo }).catch((err) => toast(err.message, 'error')) })),
      Math.max(0, shots.findIndex((c) => c.key === t.dataset.cat)));
      return;
    }
    if (a === 'goto') {
      const el = view.querySelector(`#row-${t.dataset.row}`);
      if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'start' }); el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash'); }
      return;
    }
    if (a === 'gen') { startGen(t, { book: id, key, variant }); return; }
    if (a === 'series') { startGen(t, { book: id, variant: mem.variant, series: true }); return; }
    if (a === 'copy-hero') { act(t, () => post(url('/copy-hero'), { variant }), 'Герой у буфері як картинка — вставте в чат'); return; }
    if (a === 'copy-picture') { act(t, () => post(url('/copy-picture'), { key }), 'Картинка в буфері — вставте куди треба'); return; }
    if (a === 'save') { act(t, () => post(url('/save-as'), { area: t.dataset.area, name: t.dataset.name, variant }), (r) => (r.saved ? `Збережено: ${r.name}` : null)); return; }
    if (a === 'flip') { act(t, () => post(url('/flip'), { key, variant }), (r) => (r.mirrored ? 'Віддзеркалено' : 'Повернуто, як було')); return; }
    if (a === 'remove') { removePicture(t, key, variant); return; }
    if (a === 'install-module') { offerModule(t.dataset.module).then(async (ok) => { if (ok) { try { b = (await api(url())).book; draw(); } catch { /* the page's own watcher will catch up */ } } }); return; }
    if (a === 'upscale') {
      act(t, () => post(url('/upscale'), { on: t.checked }), t.checked ? 'Апскейл увімкнено — нові картинки збільшуватимуться ×2' : 'Апскейл вимкнено для цієї книги');
      return;
    }
    if (a === 'adopt') { adopt(t); return; }
    if (a === 'upscale-all') { act(t, () => post(url('/upscale/start'), { keys: JSON.parse(t.dataset.keys || '[]') }), (r) => `У черзі: ${r.queue.length + (r.current ? 1 : 0)}`); return; }
    if (a === 'upscale-row') { act(t, () => post(url('/upscale/start'), { key }), 'У черзі на апскейл'); return; }
    if (a === 'no-margins') { act(t, () => post(url('/no-margins'), {}), (r) => r.note); return; }
    if (a === 'pick') { pickFor = { key, variant }; $('#ws-file').click(); return; }
    if (a === 'zoom') { zoom(`${key}:${t.dataset.part || 0}`); return; }
    if (a === 'zoom-one') {
      const { area, name } = t.dataset;
      openLightbox([{ src: pic(area, name, 1400), full: pic(area, name, 2600), title: `${step(mem.step)?.label} · ${name}`, sub: b.title,
        onOriginal: () => post('/api/workshop/open', { book: id, what: area, name }).catch((err) => toast(err.message, 'error')) }]);
      return;
    }
    if (a === 'copy') {
      const r = rowOf(key, variant);
      if (r) copyText(t.dataset.what === 'prompt' ? r.prompt : r.text, t.dataset.what === 'prompt' ? `Промпт скопійовано (${r.label.toLowerCase()})` : 'Текст скопійовано');
      return;
    }
    if (a === 'whole-prompt') { if (mem.open.has(key)) mem.open.delete(key); else mem.open.add(key); paintRows(); return; }
    if (a === 'variant') { mem.variant = variant; paintRows(); return; }
    if (a === 'cover-stage') { mem.cover = Number(t.dataset.stage); paintRows(); return; }
    if (a === 'guides') { mem.guides = !mem.guides; paintRows(); }
  }), on(view, 'click', '[data-gen]', (e, t) => genAction(t, t.dataset.gen))];

  $('#ws-file').addEventListener('change', (e) => {
    const f = e.target.files[0];
    e.target.value = '';
    if (f && pickFor) uploadTo(pickFor.key, pickFor.variant, f);
  });

  // A picture dragged in from Explorer lands in the frame it is dropped on — one picture per frame.
  const files = (e) => [...(e.dataTransfer?.types || [])].includes('Files');
  let hotNow = null;
  const mark = (target) => {
    if (target === hotNow) return;   // dragover fires ~20 times a second: nothing to do while it is the same frame
    hotNow = target;
    view.querySelectorAll('.drop-hot').forEach((x) => x.classList.remove('drop-hot'));
    target?.classList.add('drop-hot');
  };
  const onOver = (e) => {
    if (!files(e)) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    mark(e.target.closest('[data-drop]'));
  };
  const onLeave = (e) => { if (!e.relatedTarget || !view.contains(e.relatedTarget)) mark(null); };
  const onDrop = (e) => {
    if (!files(e)) return;
    e.preventDefault();
    mark(null);
    const target = e.target.closest('[data-drop]');
    if (!target) { toast('Перетягніть картинку на її рамку', 'info'); return; }
    const video = target.dataset.video === '1';
    const dropped = [...e.dataTransfer.files].filter((f) => (video ? VIDEO_RE : IMG_RE).test(f.name));
    if (dropped.length !== 1) {
      toast(dropped.length ? `Один${video ? 'е відео' : 'а картинка'} — в одну рамку` : video ? 'Це не відео (MP4, MOV, WEBM)' : 'Це не картинка (PNG, JPG, WEBP)', 'error');
      return;
    }
    uploadTo(target.dataset.drop, target.dataset.variant || '', dropped[0]);
  };
  view.addEventListener('dragover', onOver);
  view.addEventListener('dragleave', onLeave);
  view.addEventListener('drop', onDrop);

  const onKey = (e) => {
    // defaultPrevented: the Esc a dialog took to close itself (it is already on its way out of the top layer).
    if (e.defaultPrevented || topLayer() || document.querySelector('.menu') || e.ctrlKey || e.altKey || e.metaKey) return;
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName || '')) return;
    if (e.key === 'Escape') { location.hash = '#/books/work'; return; }
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      const i = Math.max(0, b.steps.findIndex((s) => s.key === mem.step));
      const next = b.steps[Math.max(0, Math.min(b.steps.length - 1, i + (e.key === 'ArrowRight' ? 1 : -1)))];
      if (next && next.key !== mem.step) { e.preventDefault(); mem.step = next.key; draw(); }
    }
  };
  document.addEventListener('keydown', onKey);

  return {
    unmount() {
      unwatch();
      offs.forEach((off) => off());
      document.removeEventListener('keydown', onKey);
      lb?.close();
    },
  };
}
