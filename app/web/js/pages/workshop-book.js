// A book in the Workshop — the book console moved in (26.09.2026). On top, the book's path: Формула → Герой → Історія →
// Текст → Промпти · GO → Картинки n/16 → Обкладинка → Canva → Мокапи → Бібліотека, each step ticked by the files that
// exist (the agents write them in Antigravity), a click shows the step's file or work in the panel under it. Below, the
// book's rows — page 1, spreads 2–3 … 28–29, page 30 — each its prompt, its 2:1 frame and its text, and the cover last,
// in two stages. «Генерувати» puts a row's prompt into the clipboard; the picture the owner downloads from Gemini lands
// in its row, cut and flipped, and the next prompt is already in the clipboard. The page redraws in place whenever a
// file changes (workshop-live.js, patch()): what stayed, stays — pictures, scroll, an opened prompt.
import {
  api, post, html, ic, ib, raw, setHtml, on, toast, menu, confirmBox, upload, copyText, fadeImages, highlightTokens,
  plural, patch, syncSeg, runJob, topLayer, notFound,
} from '../lib.js';
import { openLightbox } from '../lightbox.js';
import { openAddBook } from '../add-book.js';
import { picture, checkWord, ERRORS, STATE_TEXT } from '../workshop-bits.js';
import { watch, refresh, act, startGen, genAction, genBar, genState, waitingFor } from '../workshop-live.js';

const IMG_RE = /\.(png|jpe?g|webp)$/i;
const CUT = { sides: 'обрізано з боків', 'top-bottom': 'обрізано зверху й знизу' };
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
const waitChip = (text) => html`<span class="chip chip-accent"><span class="ws-pulse"></span>${text}</span>`;

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
    notFound(view, { back: '#/workshop', backLabel: 'До Майстерні', icon: 'workshop', title: 'Книгу не знайдено', text: err.message });
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

  setHtml(view, html`
    <div class="page-head ws-head" id="ws-head"></div>
    <div class="ws-genbar-slot" id="ws-gen"></div>
    <div class="ws-strip" id="ws-strip" role="tablist" aria-label="Шлях книги"></div>
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
          ${ib('folderOpen', 'Папка книги', 'data-act="open" data-what="folder"')}
          ${ib('images', 'Сторінки — нарізані 1–30 і Cover.png, набір для Canva', 'data-act="open" data-what="pictures"')}
          ${ib('original', 'Оригінали — картинки, як їх віддав генератор', 'data-act="open" data-what="originals"')}
          ${ib('more', 'Ще', 'data-act="more"')}</div>
        ${passed ? html`<button class="btn" data-act="to-library" data-tip="Книга вже в бібліотеці замовлень — відкрити її там">${ic('checkCircle')}У бібліотеці</button>`
          : html`<button class="btn ${ready() ? 'btn-primary' : ''}" data-act="to-library">${ic('shelf')}Передати в бібліотеку</button>`}
      </div>`],
    ];
  }

  // ---------------------------------------------------------------- the path strip
  function stepHtml(s, i) {
    const prev = b.steps[i - 1];
    const dot = s.key === 'hero' && s.thumb ? html`<span class="ws-dot photo"><img alt="" src="${pic('agent', s.thumb, 96)}"></span>`
      : html`<span class="ws-dot">${s.state === 'done' ? ic('check') : s.state === 'skip' ? ic('minus') : i + 1}</span>`;
    let count = s.key === 'pictures' ? html`<span class="ws-step-count num">${s.count}/${s.total}</span>` : '';
    let tip = `${s.label}: ${STATE_TEXT[s.state]}`;
    if (s.check) {
      count = html`<span class="ws-step-count ${s.check.go ? 'go' : 'nogo'}">${checkWord(s.check)}</span>`;
      tip += ` · перевірка: ${checkWord(s.check)}`;
    }
    if (s.manual) tip += ' · позначається вручну';
    const cls = [s.state, s.next && 'next', prev && ['done', 'skip'].includes(prev.state) && 'after-done',
      mem.step === s.key && 'sel', s.check && !s.check.go && 'nogo'].filter(Boolean).join(' ');
    return html`<button class="ws-step ${cls}" data-act="step" data-step="${s.key}" role="tab" aria-selected="${mem.step === s.key}" data-tip="${tip}">
      ${dot}<span class="ws-step-label">${s.label}</span>${count}</button>`;
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
      <div class="ws-mini-art ${r.kind === 'single' ? 'single' : ''}">${r.pictures.map((p) => html`<img data-fade alt="" src="${pic('pictures', p, 240)}">`)}</div>
      <div class="ws-mini-label num">${shortLabel(r)}</div></button>`)}</div>`;
  }

  async function panelBody(s, file) {
    if (s.manual) {
      return html`<div class="ws-manual"><div>${MANUAL[s.key]} поза Book Studio? Позначте крок, коли зроблено.</div>
        <div class="row-wrap">${s.key === 'mockups' ? html`<a class="btn" href="#/mockups">${ic('mockup')}Відкрити Мокапи</a>` : ''}
        <button class="btn ${s.state === 'done' ? '' : 'btn-primary'}" data-act="mark" data-step="${s.key}">${s.state === 'done' ? 'Зняти позначку' : html`${ic('check')}Зроблено`}</button></div></div>`;
    }
    if (s.key === 'library') {
      return b.library
        ? html`<div class="ws-manual"><div>Книга в бібліотеці замовлень${b.library.listingId ? html` · лістинг <span class="num">#${b.library.listingId}</span>` : ''}: замовлення знаходять її за лістингом. Папка книги тут лишилась як була — оригінали, варіанти героя.</div>
          <button class="btn" data-act="to-library">${ic('shelf')}Відкрити в бібліотеці</button></div>`
        : html`<div class="ws-manual">${missingSummary()}<button class="btn ${ready() ? 'btn-primary' : ''}" data-act="to-library">${ic('shelf')}Передати в бібліотеку</button></div>`;
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
    if (!s) { panel.hidden = true; patch(panel, []); return; }
    const files = panelFiles(s);
    const file = files.find((f) => f.name === mem.tabs.get(s.key)) || files.find((f) => f.exists) || files[0];
    let body;
    try { body = await panelBody(s, file); } catch (err) { body = html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`; }
    if (my !== panelSeq) return; // a newer draw is on its way
    const tabIcon = (f) => (f.kind === 'image' ? 'image' : f.kind === 'check' ? (b.check?.go ? 'checkCircle' : 'alertCircle') : /prompt/.test(f.name) ? 'prompt' : 'text');
    const tabs = files.length > 1 && s.state !== 'skip' ? html`<div class="seg ws-tabs"><span class="seg-pill"></span>${files.map((f) => html`<button type="button"
      class="${f === file ? 'active' : ''} ${f.exists ? '' : 'missing'} ${f.kind === 'check' ? (b.check.go ? 'go' : 'nogo') : ''}" data-act="tab" data-file="${f.name}"
      data-tip="${f.kind === 'check' ? 'Перевірка промптів (GO)' : f.exists ? f.name : `${f.name} — ще немає`}">${ic(tabIcon(f), 'icon-s')}${f.label || f.name}</button>`)}</div>` : '';
    let state = s.key === 'pictures' ? `${s.count} з ${s.total}` : STATE_TEXT[s.state];
    if (s.check) state += s.check.go ? ' · GO' : ' · перевірка не пройдена';
    const canOpen = file?.exists && file.area === 'agent';
    panel.hidden = false;
    const drawn = patch(panel, [
      ['head', html`<div class="ws-panel-head">
        <div class="ws-panel-title">${s.label}</div><div class="ws-panel-state ${s.state}">${state}</div>
        <div class="ws-panel-tools">${tabs}${canOpen ? ib('fileOpen', 'Відкрити файл у Windows', `data-act="open" data-what="agent" data-name="${file.name}"`) : ''}${ib('x', 'Згорнути', 'data-act="fold"')}</div></div>`],
      ['body', html`<div class="ws-panel-body">${body}</div>`],
    ]);
    drawn.forEach(fadeImages);
    panel.querySelectorAll('.seg').forEach(syncSeg);
  }

  // ---------------------------------------------------------------- the rows
  const saveBtn = (area, name, variant, tip) => html`<button type="button" class="ws-save" data-act="save" data-area="${area}" data-name="${name}" data-variant="${variant || ''}" aria-label="${tip}" data-tip="${tip}">${ic('download')}</button>`;
  const waitCover = (text) => html`<div class="ws-wait"><span class="ws-pulse"></span>${text}</div>`;
  const busyCover = (key) => (uploading.has(key) ? html`<div class="busy-overlay"><div class="ws-up"><i data-up="${key}"></i></div></div>` : '');

  function marks(r) {
    const m = r.marks || {};
    const chips = [];
    if (m.mirrored) chips.push(html`<span class="chip ws-mark">${ic('mirror', 'icon-s')}віддзеркалено</span>`);
    if (m.cut) chips.push(html`<span class="chip chip-amber ws-mark" data-tip="${m.source ? `Картинка ${m.source[0]}×${m.source[1]}` : ''}">${ic('alert', 'icon-s')}${CUT[m.cut] || m.cut}</span>`);
    return chips.length ? html`<div class="ws-marks">${chips}</div>` : '';
  }

  function placeholder(r, variant, half = null) {
    const what = r.kind === 'spread' ? 'розворот 2:1' : 'сторінку';
    return html`<button type="button" class="ws-ph" data-act="pick" data-key="${r.key}" data-variant="${variant}">
      ${half === null ? html`<span class="ws-half num">${r.pages[0]}</span><span class="ws-half num">${r.pages[1]}</span>` : html`<span class="ws-half ws-one num">${half}</span>`}
      <span class="ws-ph-text"><span class="drop-ico">${ic('upload')}</span><b>Перетягніть ${what}</b><span>або клацніть, щоб обрати файл</span>
        ${r.kind === 'spread' && r.mirrored ? html`<span class="ws-will-flip">${ic('mirror', 'icon-s')}віддзеркалиться</span>` : ''}</span></button>`;
  }

  function frame(r, variant = '') {
    const waiting = waitingFor(id, r.key, variant) ? waitCover('Чекаю картинку з «Завантажень»…') : '';
    const drop = (inside) => html`<div class="ws-drop" data-drop="${r.key}" data-variant="${variant}">${inside}${busyCover(r.key)}${waiting}</div>`;
    if (!r.pictures.length) {
      if (r.kind === 'spread') return html`<div class="ws-frame">${drop(placeholder(r, variant))}</div>`;
      const page = drop(placeholder(r, variant, r.pages[0]));
      const endpaper = html`<div class="ws-endpaper"><span>форзац</span></div>`;
      return html`<div class="ws-frame ws-single">${r.key === 'page1' ? html`${endpaper}${page}` : html`${page}${endpaper}`}</div>`;
    }
    const page = (name, i) => html`<div class="ws-page">
      <img data-fade alt="${r.label}" src="${pic('pictures', name, 900, variant)}" data-act="zoom" data-key="${r.key}" data-part="${i}">
      ${saveBtn('pictures', name, variant, `Зберегти сторінку ${name.replace(/\.\w+$/, '')} як…`)}</div>`;
    const tools = html`<div class="img-actions">
      ${variant ? '' : ib('expand', 'Переглянути', `data-act="zoom" data-key="${r.key}"`, { cls: 'sm' })}
      ${r.kind === 'spread' ? ib('mirror', r.marks?.mirrored ? 'Віддзеркалено — клацніть, щоб повернути' : 'Віддзеркалити розворот', `data-act="flip" data-key="${r.key}" data-variant="${variant}"`, { cls: `sm ${r.marks?.mirrored ? 'on' : ''}` }) : ''}
      ${variant ? '' : ib('copy', r.kind === 'spread' ? 'Копіювати розворот як картинку (як його зробив Gemini) — наприклад, агенту 6 як найкращий кадр' : 'Копіювати сторінку як картинку', `data-act="copy-picture" data-key="${r.key}"`, { cls: 'sm' })}
      ${r.original && !variant ? ib('imageDown', 'Зберегти оригінал як…', `data-act="save" data-area="originals" data-name="${r.original}" data-variant=""`, { cls: 'sm' }) : ''}
      ${ib('upload', 'Замінити файлом', `data-act="pick" data-key="${r.key}" data-variant="${variant}"`, { cls: 'sm' })}
      ${ib('trash', 'Прибрати картинку', `data-act="remove" data-key="${r.key}" data-variant="${variant}"`, { cls: 'sm danger' })}</div>`;
    if (r.kind === 'spread') {
      return html`<div class="ws-frame">${drop(html`<div class="ws-art ws-pairart">${r.pictures.map(page)}<div class="gutter"></div>${marks(r)}${tools}</div>`)}</div>`;
    }
    const art = drop(html`<div class="ws-art">${page(r.pictures[0], 0)}${marks(r)}${tools}</div>`);
    const endpaper = html`<div class="ws-endpaper"><span>форзац</span></div>`;
    return html`<div class="ws-frame ws-single">${r.key === 'page1' ? html`${endpaper}${art}` : html`${art}${endpaper}`}</div>`;
  }

  function genButton(r, variant = '', label = '') {
    if (!r.prompt) return '';
    if (waitingFor(id, r.key, variant)) return waitChip('чекаю картинку');
    const again = r.pictures.length > 0;
    return html`<button class="btn btn-sm ${again ? '' : 'btn-primary'}" data-act="gen" data-key="${r.key}" data-variant="${variant}"
      data-tip="${again ? 'Згенерувати ще раз — нова картинка замінить цю (стара піде в .replaced)' : 'Промпт — у буфер; Майстерня чекає картинку з «Завантажень»'}">${ic(again ? 'regenerate' : 'generate')}${label || (again ? 'Ще раз' : 'Генерувати')}</button>`;
  }

  function promptBlock(r, variant = '', title = 'Промпт') {
    const key = `${variant}/${r.key}`;
    const long = r.prompt.split('\n').length > 7;
    const open = mem.open.has(key);
    return html`<div class="ws-block ws-prompt">
      <div class="ws-block-head"><span class="eyebrow">${title}</span><span class="spacer"></span>
        ${r.prompt ? ib('copy', 'Скопіювати промпт', `data-act="copy" data-what="prompt" data-key="${r.key}" data-variant="${variant}"`, { cls: 'sm' }) : ''}</div>
      ${r.prompt ? html`<pre class="ws-body ws-mono ${long && !open ? 'clamp' : ''}">${r.prompt}</pre>
        ${long ? html`<button class="ws-more" data-act="whole-prompt" data-key="${key}">${open ? 'Згорнути' : 'Показати весь промпт'}</button>` : ''}`
        : html`<div class="ws-body empty-text">${r.key === 'cover' ? 'Промпту ще немає — його напише агент 6, коли розвороти будуть готові.' : 'Промпту ще немає — його напише агент.'}</div>`}
    </div>`;
  }

  function textBlock(r) {
    return html`<div class="ws-block ws-text">
      <div class="ws-block-head"><span class="eyebrow">${r.key === 'cover' ? 'Назва на обкладинці' : 'Текст'}</span><span class="spacer"></span>
        ${r.text ? ib('copy', 'Скопіювати текст', `data-act="copy" data-what="text" data-key="${r.key}" data-variant=""`, { cls: 'sm' }) : ''}</div>
      ${r.text ? html`<div class="ws-body">${highlightTokens(r.text)}</div>` : html`<div class="ws-body empty-text">Тексту ще немає.</div>`}
    </div>`;
  }

  function rowCard(r, variant = '') {
    return html`<section class="ws-row ${waitingFor(id, r.key, variant) ? 'waiting' : ''}" id="row-${r.key}">
      <div class="ws-row-head"><span class="ws-row-label">${r.label}</span><span class="ws-row-act">${genButton(r, variant)}</span></div>
      ${promptBlock(r, variant, variant ? 'Промпт заміни героя' : 'Промпт')}
      ${frame(r, variant)}
      ${variant ? '' : textBlock(r)}
    </section>`;
  }

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
          <span class="spacer"></span>
          ${c.final ? '' : html`<button class="btn btn-sm btn-ghost" data-act="no-margins" data-tip="Взяти обкладинку як є, без полів — вона стане Cover.png">Без полів</button>`}
          ${w2 ? waitChip('чекаю обкладинку з полями')
            : html`<button class="btn btn-sm ${c.final ? '' : 'btn-primary'}" data-act="gen" data-key="cover-wrap" data-variant="" data-tip="У буфер: обкладинка з полями, потім (Далі / F8) промпт аутпейнту">${ic(c.final ? 'regenerate' : 'generate')}${c.final ? 'Ще раз' : 'Генерувати поля'}</button>`}
        </div>
        <div class="ws-drop" data-drop="cover-wrap" data-variant="">
          <div class="ws-art ws-wide ${c.final ? '' : 'margins'}"${ratio(c.final && !c.skipped ? tpx : c.final ? c.artMarks.source : [cw, ch])}>${shown}${lines}
            ${c.final ? html`<div class="img-actions">${ib('copy', 'Копіювати готову обкладинку як картинку', 'data-act="copy-picture" data-key="cover"', { cls: 'sm' })}
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
          ${v.hero ? html`<div class="ws-art"><img data-fade alt="Герой варіанта ${v.name}" src="${pic('agent', v.hero, 600, v.name)}"></div>`
            : html`<button type="button" class="ws-ph" data-act="pick" data-key="hero" data-variant="${v.name}"><span class="ws-ph-text"><span class="drop-ico">${ic('hero')}</span><b>Героя ще немає</b><span>згенеруйте або перетягніть</span></span></button>`}
          ${busyCover('hero')}</div>
        <div class="ws-block ws-prompt grow"><div class="ws-block-head"><span class="eyebrow">Промпт героя (правка canonical.png)</span></div>
          ${v.heroPrompt ? html`<pre class="ws-body ws-mono clamp">${v.heroPrompt}</pre>` : html`<div class="ws-body empty-text">hero-prompt.md ще немає — його напише агент.</div>`}</div>
      </div></section>`;
  }

  // ---------------------------------------------------------------- painting
  function paintRows() {
    const v = mem.variant ? b.variants.find((x) => x.name === mem.variant) : null;
    if (mem.variant && !v) mem.variant = '';
    const rows = inner();
    const done = rows.filter((r) => r.pictures.length).length;
    const busy = genState()?.active?.book === id;
    const left = v ? v.rows.some((r) => r.prompt && !r.pictures.length) : rows.some((r) => r.prompt && !r.pictures.length);
    const heroThumb = step('hero').thumb;
    patch($('#ws-rows-head'), [['head', html`<div class="ws-rows-head-in">
      <h2 class="section-title">Сторінки книги</h2>
      ${v ? html`<span class="num" data-tip="Розвороти варіанта з картинками">${v.done}/${v.rows.length}</span>`
        : html`<span class="num" data-tip="Картинки ${done} з ${rows.length} · промпти ${b.counts.prompts}/17 · тексти ${b.counts.texts}/17">${done}/${rows.length}</span>
          <span class="ws-meter"><i style="transform:scaleX(${done / rows.length})"></i></span>`}
      <span class="spacer"></span>
      ${heroThumb && !v ? html`<button class="btn btn-sm" data-act="copy-hero" data-tip="Героя (canonical.png) — у буфер, щоб вставити в новий чат Gemini першим">${ic('hero')}Героя в буфер</button>` : ''}
      ${!busy && left ? html`<button class="btn btn-primary" data-act="series" data-tip="${v ? 'Усі розвороти варіанта без картинок — по черзі' : 'Розвороти 2–3 … 28–29, потім сторінки 1 і 30 — ті, що без картинок; після кожної картинки наступний промпт уже в буфері'}">${ic('generate')}${v ? 'Генерувати варіант' : done ? 'Генерувати решту' : 'Генерувати всю книгу'}</button>` : ''}
    </div>`]]);
    patch($('#ws-vtabs'), b.variants.length ? [['tabs', html`<div class="seg ws-vtabs"><span class="seg-pill"></span>
      <button type="button" class="${v ? '' : 'active'}" data-act="variant" data-variant="">Основна</button>
      ${b.variants.map((x) => html`<button type="button" class="${v === x ? 'active' : ''}" data-act="variant" data-variant="${x.name}">${x.name}<span class="seg-count">${x.done}/${x.rows.length}</span></button>`)}</div>`]] : []);
    patch($('#ws-notes'), !v && b.notes.length ? [['notes', html`<div class="notice notice-warn">${ic('alert')}<div>${raw(b.notes.map((n) => html`${n}`).join('<br>'))}</div></div>`]] : []);
    const cards = v
      ? [[`${v.name}|hero`, variantHero(v)], ...(v.rows.length ? v.rows.map((r) => [`${v.name}|${r.key}`, rowCard(r, v.name)])
        : [[`${v.name}|none`, html`<div class="ws-missing">У цьому варіанті ще немає промптів заміни (2.json … 15.json) — їх пише агент.</div>`]])]
      : [...rows.map((r) => [r.key, rowCard(r)]), ['cover', coverCard()]];
    const drawn = patch($('#ws-rows'), cards);
    drawn.forEach(fadeImages);
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
    if (bar) bar.style.transform = `scaleX(${uploading.get(key) || 0})`;
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
    const bar = genBar(id);
    patch($('#ws-gen'), bar ? [['bar', bar]] : []);
    paintRows();
    paintPanel();
    followWaiting();
    refreshViewer();
  }

  /** When the next row starts waiting and the one before was on screen, the page goes on to it — the owner sees where
   *  the next picture will land. */
  function followWaiting() {
    const a = genState()?.active;
    const key = a && a.book === id ? `${a.variant || ''}/${a.key.startsWith('cover') ? 'cover' : a.key}` : '';
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
      if (err.status === 404) { toast('Книги більше немає в Майстерні', 'info'); location.hash = '#/workshop'; }
      return;
    }
    draw();
  });
  draw();

  // ---------------------------------------------------------------- the viewer
  function viewerItems() {
    const items = [];
    const push = (key, area, name, title, sub, text) => items.push({
      key, src: pic(area, name, 1400), full: pic(area, name, 2600), title, sub, text,
      onOriginal: () => post('/api/workshop/open', { book: id, what: area, name }).catch((err) => toast(err.message, 'error')),
    });
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
  async function uploadTo(key, variant, file) {
    if (!IMG_RE.test(file.name)) { toast(`«${file.name}» — не картинка (PNG, JPG, WEBP)`, 'error'); return; }
    if (uploading.has(key)) { toast('Попередня картинка ще вантажиться', 'info'); return; }
    uploading.set(key, 0);
    paintRows();
    try {
      const q = new URLSearchParams({ key, name: file.name, ...(variant ? { variant } : {}) });
      const res = await upload(url(`/place?${q}`), file, (p) => { uploading.set(key, p); paintProgress(key); });
      toast(res.note || 'Готово', res.cut ? 'info' : 'success', res.cut ? 4000 : 2600);
    } catch (err) { toast(err.message, 'error'); }
    uploading.delete(key);
    paintRows();
    refresh();
  }

  async function removePicture(btn, key, variant) {
    const title = key === 'cover' ? 'Прибрати обкладинку разом з її полями?' : key === 'cover-wrap' ? 'Прибрати поля обкладинки?' : 'Прибрати картинку з цього рядка?';
    const text = `${key === 'cover-wrap' ? 'Сама обкладинка лишиться. ' : ''}Нічого не зникає назавжди — файли підуть у папку .replaced книги.`;
    if (!await confirmBox({ title, text, confirm: 'Прибрати', danger: true })) return;
    act(btn, () => post(url('/remove'), { key, variant }));
  }

  // ---------------------------------------------------------------- the library
  function missingSummary() {
    const noPicture = inner().filter((r) => !r.pictures.length).map((r) => shortLabel(r));
    if (!b.cover.final) noPicture.unshift('обкладинка');
    const noText = b.rows.filter((r) => !r.text).map((r) => (r.kind === 'cover' ? 'обкладинка' : shortLabel(r)));
    const gaps = [noPicture.length && `картинок — ${noPicture.join(', ')}`, noText.length && `текстів — ${noText.join(', ')}`].filter(Boolean);
    return gaps.length
      ? html`<div class="notice notice-warn">${ic('alert')}<div>Бракує ${gaps.join('; ')}. У бібліотеці їх можна докласти пізніше.</div></div>`
      : html`<div class="notice notice-success">${ic('checkCircle')}<div>Усі картинки й тексти на місці.</div></div>`;
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

  async function deleteBook(btn) {
    const name = `${b.number != null ? `№${b.number} ` : ''}${b.title}`;
    const ok = await confirmBox({
      title: `Видалити книгу «${name}»?`,
      text: 'Книга зникне з Майстерні, а її папка з усіма файлами — тексти й промпти агентів, сторінки, оригінали, обкладинка — піде в Кошик Windows. Звідти її ще можна відновити, поки Кошик не очищено.',
      confirm: 'Видалити книгу', danger: true,
    });
    if (!ok) return;
    const res = await act(btn, () => api(url(), { method: 'DELETE' }), `Книгу «${name}» видалено — папка в Кошику Windows`);
    if (res) { memory.delete(id); location.hash = '#/workshop'; }
  }

  // ---------------------------------------------------------------- events
  const rowOf = (key, variant) => (variant ? b.variants.find((x) => x.name === variant)?.rows : b.rows)?.find((r) => r.key === key)
    || (key === 'cover-wrap' ? { key, label: 'Поля обкладинки', prompt: b.cover.outpaint } : null);
  const offs = [on(view, 'click', '[data-act]', (e, t) => {
    const a = t.dataset.act;
    const { key = '', variant = '' } = t.dataset;
    if (a === 'back') { location.hash = '#/workshop'; return; }
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
    if (a === 'goto') {
      const el = view.querySelector(`#row-${t.dataset.row}`);
      if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'start' }); el.classList.remove('flash'); void el.offsetWidth; el.classList.add('flash'); }
      return;
    }
    if (a === 'gen') { startGen(t, { book: id, key, variant: key.startsWith('cover') ? '' : variant }); return; }
    if (a === 'series') { startGen(t, { book: id, variant: mem.variant, series: true }); return; }
    if (a === 'copy-hero') { act(t, () => post(url('/copy-hero'), { variant }), 'Герой у буфері як картинка — вставте в чат'); return; }
    if (a === 'copy-picture') { act(t, () => post(url('/copy-picture'), { key }), 'Картинка в буфері — вставте куди треба'); return; }
    if (a === 'save') { act(t, () => post(url('/save-as'), { area: t.dataset.area, name: t.dataset.name, variant }), (r) => (r.saved ? `Збережено: ${r.name}` : null)); return; }
    if (a === 'flip') { act(t, () => post(url('/flip'), { key, variant }), (r) => (r.mirrored ? 'Віддзеркалено' : 'Повернуто, як було')); return; }
    if (a === 'remove') { removePicture(t, key, variant); return; }
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
  const mark = (target) => {
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
    const dropped = [...e.dataTransfer.files].filter((f) => IMG_RE.test(f.name));
    if (!target) { toast('Перетягніть картинку на її рамку', 'info'); return; }
    if (dropped.length !== 1) { toast(dropped.length ? 'Одна картинка — в одну рамку' : 'Це не картинка (PNG, JPG, WEBP)', 'error'); return; }
    uploadTo(target.dataset.drop, target.dataset.variant || '', dropped[0]);
  };
  view.addEventListener('dragover', onOver);
  view.addEventListener('dragleave', onLeave);
  view.addEventListener('drop', onDrop);

  const onKey = (e) => {
    // defaultPrevented: the Esc a dialog took to close itself (it is already on its way out of the top layer).
    if (e.defaultPrevented || topLayer() || document.querySelector('.menu') || e.ctrlKey || e.altKey || e.metaKey) return;
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName || '')) return;
    if (e.key === 'Escape') { location.hash = '#/workshop'; return; }
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
