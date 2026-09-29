// The listing slides' editor (#/slides/<set | template>/<1–6>) — the owner's touches on a book's six slides, the way
// he asked on 29.09.2026: "like Canva — layers, moving, rotating, resizing", then «Зберегти картинки» bakes them.
// Moved in from the external Slide Editor the same day, in Book Studio's own look. A separate module, loaded only when
// opened (left out of the pages' warm-up in app.js) with its own styles (css/slides.css).
// Every change is saved at once with the version it was made on; what an agent changes in the files meanwhile shows
// up by itself (the signature is asked every 1.5 s) — the owner may work on the slides through an LLM too.
import {
  api, post, html, ic, ib, setHtml, on, toast, runJob, menu, confirmBox, segHtml, notFound, tellBusy,
} from '../lib.js';
import {
  ready, setAssets, drawScene, drawElement, boxOf, elTransform, TSHADOW,
} from '../slides/engine.js';

const CSS = '/css/slides.css';
const SIG_EVERY = 1500;
const SAVE_AFTER = 450;
const HISTORY = 200;

// what each kind is called and drawn as in the layers
const KIND = {
  book: ['Мокап', 'book'], image: ['Картинка', 'image'], text: ['Текст', 'elText'], sticker: ['Наліпка', 'elSticker'],
  ribbon: ['Стрічка', 'elRibbon'], heart: ['Серце', 'elHeart'], arrow: ['Стрілка', 'elArrow'], sparkle: ['Зірочка', 'elStar'],
  band: ['Смуга', 'elBand'], blob: ['Пляма', 'elBlob'], dashes: ['Пунктир', 'elDashes'], leaves: ['Тінь листя', 'elLeaves'],
  grain: ['Зерно паперу', 'elGrain'],
};

// ---------------------------------------------------------------- the properties, grouped (the owner's panel)
const num = (k, label, o = {}) => ({ k, label, kind: 'num', step: 1, ...o });
const range = (k, label, min, max, step, def) => ({ k, label, kind: 'range', min, max, step, def });
const color = (def = '#ffffff') => ({ k: 'color', label: 'Колір', kind: 'color', def });
const XYR = [num('x', 'X'), num('y', 'Y'), num('rot', 'Кут °', { step: 0.5, def: 0 })];
const W = num('w', 'Ширина'), H = num('h', 'Висота');
const OPACITY = range('opacity', 'Непрозорість', 0, 1, 0.01, 1);
const TSH = range('tshadow', 'Тінь тексту', 0, 1, 0.01, TSHADOW);
const SPEC = {
  book: [['Мокап', [{ k: 'slot', kind: 'bookSlot' }]], ['Положення', [...XYR, W]],
    ['Тінь', [range('bake', 'З Photoshop', 0, 1, 0.01, 0.6), range('shadow', 'Додаткова', 0, 1, 0.01, 0.18)]], ['Вигляд', [OPACITY]]],
  image: [['Картинка', [{ k: 'slot', kind: 'picSlot' }, num('rim', 'Біла кромка', { def: 0 }), num('bumps', 'Хвильок у рамці', { def: 10 })]],
    ['Положення', [...XYR, W, H]], ['Вигляд', [OPACITY]]],
  text: [['Текст', [{ k: 'text', kind: 'text' }, num('size', 'Розмір літер'), num('lh', 'Між рядками', { step: 0.01, def: 1.18 }),
    range('arc', 'Дуга °', -180, 180, 1, 0), { k: 'align', label: 'Вирівняти', kind: 'seg', def: 'left', options: [['left', 'Ліворуч'], ['center', 'Центр'], ['right', 'Праворуч']] }]],
  ['Положення', [...XYR, num('w', 'Ширина рамки')]], ['Вигляд', [color(), OPACITY]], ['Тінь', [TSH]]],
  sticker: [['Текст', [{ k: 'lines', kind: 'lines' }, range('pad', 'Поле навколо тексту', 0, 0.4, 0.01, 0.22)]],
    ['Положення', [...XYR, num('r', 'Радіус')]], ['Вигляд', [color('#e8c59d')]], ['Тінь', [TSH]]],
  ribbon: [['Текст', [{ k: 'lines', kind: 'lines' }, range('pad', 'Поле навколо тексту', 0, 0.4, 0.01, 0.16)]],
    ['Положення', [...XYR, W, H]], ['Вигляд', [color('#a2a066'), num('rim', 'Біла кромка', { def: 7 })]], ['Тінь', [TSH]]],
  arrow: [['Форма', [range('bow', 'Вигин', -0.5, 0.5, 0.01, 0), range('loop', 'Петля', 0, 0.4, 0.01, 0), range('loopAt', 'Де петля', 0, 1, 0.01, 0.45),
    { k: 'loopDir', label: 'Петля в бік', kind: 'seg', def: 1, options: [[1, 'Праворуч'], [-1, 'Ліворуч']] }, num('sw', 'Товщина лінії', { def: 7 })]],
  ['Положення', [...XYR, W, H]], ['Вигляд', [color('#6b3a3a')]], ['Тінь', [range('tshadow', 'Тінь', 0, 1, 0.01, 0.45)]]],
  heart: [['Положення', [...XYR, W, H]], ['Вигляд', [color('#e8c59d'), range('iconSize', 'Значок', 0, 1, 0.01, 0.4)]]],
  sparkle: [['Положення', [...XYR, num('size', 'Розмір')]], ['Вигляд', [color()]]],
  band: [['Положення', [...XYR, W, H]], ['Вигляд', [color('#a2a066'), num('seed', 'Візерунок краю', { def: 4 }), num('rim', 'Біла кромка', { def: 8 })]]],
  blob: [['Положення', [...XYR, W, H]], ['Вигляд', [color('#f6ecde'), num('seed', 'Форма', { def: 1 }), OPACITY]]],
  dashes: [['Положення', [...XYR, num('w', 'Довжина'), num('h', 'Товщина')]], ['Вигляд', [color(), num('count', 'Скільки рисок', { def: 11 }), num('dash', 'Довжина риски', { def: 62 })]]],
  leaves: [['Положення', [...XYR, W, H]], ['Вигляд', [range('opacity', 'Сила', 0, 1, 0.01, 1)]]],
  grain: [['Вигляд', [range('opacity', 'Сила', 0, 1, 0.01, 1)]]],
};
// the handles a kind has: the edges for the ones that stretch in one direction
const STRETCHES = ['band', 'blob', 'dashes', 'leaves', 'text', 'arrow', 'image', 'ribbon', 'heart'];

// «+» — a new element, in the slide's palette
const NEW = {
  text: () => ({ text: 'New text', w: 420, size: 44, color: '#ffffff', align: 'center' }),
  sparkle: () => ({ size: 22, color: '#ffffff' }),
  arrow: () => ({ w: 220, h: 120, w0: 220, h0: 120, pts: [[10, 110], [210, 12]], sw: 7, color: '#6b3a3a', bow: 0.2, loop: 0, solid: true }),
  sticker: () => ({ r: 110, color: '#e8c59d', lines: [{ t: 'new', k: 2 }, { t: 'sticker' }], tape: [0, -8] }),
  ribbon: () => ({ w: 170, h: 250, color: '#a2a066', lines: [{ t: 'new' }, { t: 'ribbon' }] }),
  heart: () => ({ w: 190, h: 180, color: '#e8c59d', icon: 'heart' }),
  band: () => ({ w: 1100, h: 150, color: '#a2a066', seed: 4 }),
  blob: () => ({ w: 380, h: 300, color: '#f6ecde', seed: 3 }),
  dashes: () => ({ w: 900, h: 12, color: '#ffffff', count: 11, dash: 62 }),
  book: () => ({ slot: 'open1:1', w: 600 }),
  image: () => ({ slot: 'page30', w: 300, h: 300, shape: 'scallop', rim: 10 }),
};
const ADD_ORDER = ['text', 'sticker', 'ribbon', 'arrow', 'sparkle', 'heart', 'band', 'blob', 'dashes', 'book', 'image'];

function ensureCss() {
  if (document.querySelector(`link[href="${CSS}"]`)) return Promise.resolve();
  return new Promise((resolve) => {
    const l = document.createElement('link');
    l.rel = 'stylesheet'; l.href = CSS;
    l.onload = l.onerror = () => resolve();
    document.head.appendChild(l);
  });
}

export async function mount(view, [whereParam, nParam]) {
  const where = whereParam === 'template' ? 'template' : whereParam;
  const n = Math.min(6, Math.max(1, +nParam || 1));
  const slide = `slide${n}`;
  const q = (path) => `${path}?w=${encodeURIComponent(where)}&s=${slide}`;
  let info = null, scene = null, version = '', assets = null;
  try {
    [, info, { scene, version }, assets] = await Promise.all([
      ensureCss(), api(`/api/slides/state?w=${encodeURIComponent(where)}`), api(q('/api/slides/scene')),
      api(`/api/slides/assets?w=${encodeURIComponent(where)}`), ready()]);
  } catch (err) {
    notFound(view, { back: '#/mockups', backLabel: 'До мокапів', icon: 'images', title: 'Слайди не відкрились', text: err.message });
    return null;
  }
  setAssets(assets);
  view.classList.add('se-view');
  const isSet = where !== 'template';
  const st = { sel: -1, past: [], future: [], saving: null, dirty: false, sig: info.sig, drag: null, live: null, S: 1, baking: null };
  let gone = false, sigTimer = 0, saveTimer = 0;
  const offs = [];
  const $ = (s) => view.querySelector(s);
  const snapshot = () => JSON.stringify(scene);
  const items = () => scene.items;
  const cur = () => items()[st.sel];

  // ---------------------------------------------------------------- the page
  setHtml(view, html`<div class="se">
    <header class="se-bar">
      <a class="back-link" href="#/mockups" aria-label="До мокапів" data-tip="До мокапів">${ic('arrowLeft', 'icon-s')}</a>
      <div class="se-title">
        <h1 class="page-title">Слайди</h1>
        <div class="page-sub truncate">${info.name}${isSet ? '' : ' · кожна нова книга починається з нього'}</div>
      </div>
      ${segHtml(info.slides.map((s, i) => ({ value: s.id, label: String(i + 1), tip: `${i + 1} · ${s.title}` })), slide, { accent: true, name: 'slide' })}
      <span class="grow"></span>
      <div class="tools">
        ${ib('undo', 'Назад', 'data-act="undo"', { kbd: 'Ctrl+Z' })}${ib('redo', 'Вперед', 'data-act="redo"', { kbd: 'Ctrl+Y' })}
        <span class="sep"></span>
        ${ib('restore', isSet ? 'Скинути слайд — як у шаблоні' : 'Скинути слайд — як був намальований спершу', 'data-act="reset"')}
        ${isSet ? ib('template', 'Зробити шаблоном — так цей слайд виглядатиме в кожній новій книзі', 'data-act="to-template"') : ''}
      </div>
      <span class="se-saved" id="se-saved"></span>
      ${isSet ? html`<button type="button" class="btn btn-primary" data-act="bake">${ic('download', 'icon-s')}Зберегти картинки</button>` : ''}
    </header>
    <div class="se-body">
      <aside class="card se-panel se-layers">
        <div class="se-panel-head"><span class="eyebrow grow">Шари</span>${ib('plus', 'Додати елемент', 'data-act="add"', { cls: 'sm' })}</div>
        <div class="se-list" id="se-layers"></div>
      </aside>
      <main class="se-canvas" id="se-canvas">
        <div class="se-wrap" id="se-wrap"><div class="se-stage" id="se-stage"></div><div class="se-over" id="se-over"></div></div>
        <div class="se-hint faint">Тягніть — рухати · кружечок — повертати (Shift — 15°) · кути — розмір · стрілки — 1 px (Shift — 10) · Delete — прибрати</div>
      </main>
      <aside class="card se-panel se-props" id="se-props"></aside>
    </div>
  </div>`);
  const stage = $('#se-stage'), over = $('#se-over'), wrap = $('#se-wrap');

  // ---------------------------------------------------------------- drawing
  function fit() {
    const box = $('#se-canvas')?.getBoundingClientRect();
    if (!box) return;
    st.S = Math.max(0.2, Math.min((box.width - 36) / 1000, (box.height - 48) / 1000));
    wrap.style.width = wrap.style.height = `${1000 * st.S}px`;
    stage.style.transform = over.style.transform = `scale(${st.S})`;
    drawSel();
  }
  const ro = new ResizeObserver(fit);
  ro.observe($('#se-canvas'));

  function redrawAll() { drawScene(scene, stage, 'se'); markLocks(); drawLayers(); drawSel(); drawProps(); }
  function redrawOne(i) {
    const old = stage.querySelector(`.el[data-idx="${i}"]`);
    if (!old) { redrawAll(); return; }
    old.replaceWith(drawElement(items()[i], i, 'se'));
    markLocks(); drawSel();
  }
  function place(i) {   // move / turn / mirror only: no drawing again
    const e = items()[i], el = stage.querySelector(`.el[data-idx="${i}"]`);
    if (!el) return;
    el.style.left = `${e.x}px`; el.style.top = `${e.y}px`; el.style.transform = elTransform(e);
    drawSel();
  }
  function markLocks() {
    items().forEach((e, i) => {
      const el = stage.querySelector(`.el[data-idx="${i}"]`);
      if (el && (e.locked || e.type === 'leaves' || e.type === 'grain')) el.dataset.lock = '1';
    });
  }

  // ---------------------------------------------------------------- the layers (the top one is in front)
  function drawLayers() {
    const list = $('#se-layers');
    setHtml(list, [...items().keys()].reverse().map((i) => {
      const e = items()[i];
      const [kind, glyph] = KIND[e.type] || [e.type, 'image'];
      return html`<div class="se-layer ${i === st.sel ? 'sel' : ''} ${e.hidden ? 'off' : ''}" data-i="${i}" draggable="true" role="button" tabindex="0">
        <span class="se-kind" data-tip="${kind}">${ic(glyph, 'icon-s')}</span>
        <span class="grow truncate">${e.name || kind}</span>
        ${ib(e.locked ? 'lock' : 'unlock', e.locked ? 'Закріплено — не рухається мишкою' : 'Закріпити', `data-act="lock" data-i="${i}"`, { cls: `xs se-lock ${e.locked ? 'on' : ''}` })}
        ${ib(e.hidden ? 'eyeOff' : 'eye', e.hidden ? 'Показати' : 'Сховати', `data-act="eye" data-i="${i}"`, { cls: `xs se-eye ${e.hidden ? 'on' : ''}` })}
      </div>`;
    }));
    list.querySelector('.se-layer.sel')?.scrollIntoView({ block: 'nearest' });
  }

  // ---------------------------------------------------------------- the selection and its handles
  function drawSel() {
    over.replaceChildren();
    const e = cur();
    if (!e || e.hidden) return;
    const [w, h] = boxOf(e), S = st.S, hs = 12 / S;
    const b = document.createElement('div');
    b.className = 'se-selbox';
    Object.assign(b.style, { left: `${e.x - w / 2}px`, top: `${e.y - h / 2}px`, width: `${w}px`, height: `${h}px`,
      transform: `rotate(${e.rot || 0}deg)`, outlineWidth: `${1.5 / S}px` });
    const handle = (cls, x, y, cursor) => {
      const d = document.createElement('div');
      d.className = `se-h h-${cls}`;
      d.dataset.h = cls;
      Object.assign(d.style, { width: `${hs}px`, height: `${hs}px`, left: `${x - hs / 2}px`, top: `${y - hs / 2}px`, cursor, borderWidth: `${1.5 / S}px` });
      b.appendChild(d);
    };
    if (e.type !== 'grain') {
      ['nw', 'ne', 'sw', 'se'].forEach((c) => handle(c, c[1] === 'w' ? 0 : w, c[0] === 'n' ? 0 : h, c === 'nw' || c === 'se' ? 'nwse-resize' : 'nesw-resize'));
      if (STRETCHES.includes(e.type)) {
        handle('e', w, h / 2, 'ew-resize'); handle('w', 0, h / 2, 'ew-resize');
        handle('n', w / 2, 0, 'ns-resize'); handle('s', w / 2, h, 'ns-resize');
      }
      const stem = document.createElement('div');
      stem.className = 'se-stem';
      Object.assign(stem.style, { top: `${-28 / S}px`, height: `${28 / S}px`, width: `${1.5 / S}px` });
      b.appendChild(stem);
      handle('rot', w / 2, -28 / S, 'grab');
    }
    over.appendChild(b);
  }
  function select(i) { st.sel = i; drawLayers(); drawSel(); drawProps(); }

  // ---------------------------------------------------------------- the properties
  const val = (e, f) => e[f.k] ?? f.def ?? '';
  const fmt = (v) => (typeof v === 'number' ? +v.toFixed(2) : v);
  function palette() {
    const seen = new Set(['#ffffff']);
    items().forEach((e) => { for (const k of ['color', 'textColor']) if (/^#[0-9a-f]{6}$/i.test(e[k] || '')) seen.add(e[k].toLowerCase()); });
    return [...seen].slice(0, 12);
  }
  function fieldHtml(e, f) {
    const v = val(e, f);
    if (f.kind === 'num') {
      return html`<label class="se-f"><span>${f.label}</span><input class="input num" type="number" step="${f.step}" data-k="${f.k}" data-kind="num" value="${v === '' ? '' : fmt(+v)}"></label>`;
    }
    if (f.kind === 'range') {
      return html`<label class="se-f se-wide se-range"><span>${f.label}</span>
        <input type="range" min="${f.min}" max="${f.max}" step="${f.step}" data-k="${f.k}" data-kind="range" value="${v}">
        <input class="input num" type="number" min="${f.min}" max="${f.max}" step="${f.step}" data-k="${f.k}" data-kind="num" value="${fmt(+v)}"></label>`;
    }
    if (f.kind === 'color') {
      return html`<div class="se-f se-wide"><span>${f.label}</span><div class="se-swatches">
        ${palette().map((c) => html`<button type="button" class="se-sw ${String(v).toLowerCase() === c ? 'on' : ''}" style="--c:${c}" data-act="swatch" data-c="${c}" aria-label="${c}" data-tip="${c}"></button>`)}
        <label class="se-sw se-pick" data-tip="Інший колір" style="--c:${v}"><input type="color" data-k="${f.k}" data-kind="color" value="${v}"></label>
      </div></div>`;
    }
    if (f.kind === 'seg') {
      return html`<div class="se-f se-wide"><span>${f.label}</span>${segHtml(f.options.map(([value, label]) => ({ value: String(value), label })), String(v), { name: `f-${f.k}` })}</div>`;
    }
    if (f.kind === 'text') {
      return html`<label class="se-f se-wide"><span>Текст · Enter — новий рядок · {pages} і {poems} — числа книги</span>
        <textarea class="textarea" rows="4" data-k="text" data-kind="text" spellcheck="false">${e.text}</textarea></label>`;
    }
    if (f.kind === 'lines') {
      return html`<label class="se-f se-wide"><span>Рядки · кожен окремо, текст сам стає рівно</span>
        <textarea class="textarea" rows="${Math.max(3, e.lines.length)}" data-kind="lines" spellcheck="false">${e.lines.map((l) => l.t).join('\n')}</textarea></label>`;
    }
    if (f.kind === 'bookSlot' || f.kind === 'picSlot') {
      const want = f.kind === 'bookSlot' ? 'book' : 'picture';
      const has = (s) => (want === 'book' ? assets.books[s] : assets.pictures[s]);
      return html`<div class="se-f se-wide"><span>${want === 'book' ? 'Який мокап' : 'Яка картинка'}</span>
        <select class="select" data-k="slot" data-kind="slot">${info.slots.filter((s) => s.kind === want).map((s) => html`<option value="${s.slot}" ${s.slot === e.slot ? 'selected' : ''}>${s.label}${has(s.slot) ? `  ·  ${has(s.slot).source || ''}` : '  ·  немає'}</option>`)}</select>
        ${want === 'picture' && isSet ? html`<button type="button" class="btn btn-sm btn-ghost se-repick" data-act="pick-picture" data-slot="${e.slot}">${ic('folderPick', 'icon-s')}Інша картинка…</button>` : ''}
      </div>`;
    }
    return '';
  }

  function drawProps() {
    const box = $('#se-props');
    const e = cur();
    if (!e) { setHtml(box, slideProps()); return; }
    const [kind] = KIND[e.type] || [e.type];
    setHtml(box, html`
      <div class="se-panel-head"><span class="eyebrow grow">${kind}</span>
        ${ib('mirror', 'Віддзеркалити зліва направо', 'data-act="flipX"', { cls: `sm ${e.flipX ? 'on' : ''}` })}
        ${ib('mirrorV', 'Віддзеркалити догори дригом', 'data-act="flipY"', { cls: `sm ${e.flipY ? 'on' : ''}` })}
        ${ib('copy', 'Копія', 'data-act="dup"', { cls: 'sm', kbd: 'Ctrl+D' })}
        ${ib('trash', 'Прибрати зі слайда', 'data-act="del"', { cls: 'sm', kbd: 'Delete' })}</div>
      <div class="se-scroll">
        <label class="se-f se-wide"><span>Назва</span><input class="input" data-k="name" data-kind="name" value="${e.name || ''}" spellcheck="false"></label>
        ${(SPEC[e.type] || []).map(([title, fields]) => html`<section class="se-group"><h4>${title}</h4><div class="se-grid">${fields.map((f) => fieldHtml(e, f))}</div></section>`)}
      </div>`);
  }

  // Nothing selected: the slide itself — its background and (a book's slides) the book's numbers.
  function slideProps() {
    return html`<div class="se-panel-head"><span class="eyebrow grow">Слайд ${n}</span></div>
      <div class="se-scroll">
        <section class="se-group"><h4>Тло</h4><div class="se-grid">
          <div class="se-f se-wide"><span>Колір тла</span><div class="se-swatches">
            ${palette().map((c) => html`<button type="button" class="se-sw ${String(scene.bg).toLowerCase() === c ? 'on' : ''}" style="--c:${c}" data-act="bg" data-c="${c}" aria-label="${c}" data-tip="${c}"></button>`)}
            <label class="se-sw se-pick" data-tip="Інший колір" style="--c:${scene.bg}"><input type="color" data-kind="bg" value="${/^#[0-9a-f]{6}$/i.test(scene.bg) ? scene.bg : '#eedec7'}"></label>
          </div></div>
        </div></section>
        ${isSet ? html`<section class="se-group"><h4>Числа книги</h4><div class="se-grid">
          <label class="se-f"><span>Сторінок · {pages}</span><input class="input num" type="number" min="1" max="999" data-kind="number" data-k="pages" value="${info.numbers.pages}"></label>
          <label class="se-f"><span>Віршів · {poems}</span><input class="input num" type="number" min="1" max="999" data-kind="number" data-k="poems" value="${info.numbers.poems}"></label>
        </div></section>` : ''}
        <p class="se-empty">Клацніть елемент на слайді або в шарах.</p>
      </div>`;
  }

  // ---------------------------------------------------------------- history and saving
  function commit(before) {
    if (before === snapshot()) return;
    st.past.push(before);
    if (st.past.length > HISTORY) st.past.shift();
    st.future = [];
    save();
  }
  function paintSaved(state, text) {
    const chip = $('#se-saved');
    if (!chip) return;
    chip.className = `se-saved ${state}`;
    setHtml(chip, state === 'busy' ? html`<span class="spinner"></span>${text}` : state === 'bad' ? html`${ic('alertCircle', 'icon-s')}${text}` : html`${ic('check', 'icon-s')}${text}`);
  }
  function save() {
    st.dirty = true;
    clearTimeout(saveTimer);
    saveTimer = setTimeout(flush, SAVE_AFTER);
  }
  async function flush() {
    clearTimeout(saveTimer);
    if (!st.dirty) return st.saving;
    if (st.saving) { await st.saving.catch(() => {}); return flush(); }
    st.dirty = false;
    const body = { w: where, s: slide, scene: JSON.parse(snapshot()), base: version };
    st.saving = post('/api/slides/scene', body).then((r) => {
      version = r.version;
      if (!gone) paintSaved('ok', 'Збережено');
    }).catch((err) => {
      if (gone) return;
      if (err.status === 409 && err.data?.scene) {   // changed on disk meanwhile (an agent): its version wins
        takeTheirs(err.data.scene, err.data.version, 'Слайд тим часом змінили — показано новий; ваша остання зміна не збереглась');
      } else {
        st.dirty = true;
        paintSaved('bad', 'Не збереглось');
        toast(err.message, 'error');
      }
    }).finally(() => { st.saving = null; });
    return st.saving;
  }
  function takeTheirs(theirs, v, text) {
    st.past.push(snapshot());
    st.future = [];
    scene = theirs;
    version = v;
    if (st.sel >= items().length) st.sel = -1;
    redrawAll();
    paintSaved('ok', 'Оновлено');
    toast(text, 'info', 3200);
  }
  function undo() {
    if (!st.past.length) return;
    st.future.push(snapshot());
    scene = JSON.parse(st.past.pop());
    if (st.sel >= items().length) st.sel = -1;
    redrawAll(); save();
  }
  function redo() {
    if (!st.future.length) return;
    st.past.push(snapshot());
    scene = JSON.parse(st.future.pop());
    if (st.sel >= items().length) st.sel = -1;
    redrawAll(); save();
  }

  // ---------------------------------------------------------------- what the agent changed shows up by itself
  async function watch() {
    clearTimeout(sigTimer);
    if (gone) return;
    if (view.isConnected && document.visibilityState === 'visible' && !st.drag && !st.live) {
      try {
        const { sig } = await api(`/api/slides/sig?w=${encodeURIComponent(where)}`);
        if (sig !== st.sig && !gone) {
          st.sig = sig;
          const [{ scene: theirs, version: v }, a, i] = await Promise.all([api(q('/api/slides/scene')),
            api(`/api/slides/assets?w=${encodeURIComponent(where)}`), api(`/api/slides/state?w=${encodeURIComponent(where)}`)]);
          if (gone) return;
          const assetsChanged = JSON.stringify(a) !== JSON.stringify(assets);
          assets = a; info = i; setAssets(a);
          if (v !== version && !st.dirty && !st.saving) takeTheirs(theirs, v, 'Слайд змінено ззовні — показано новий');
          else if (assetsChanged) { redrawAll(); }
        }
      } catch { /* the program is restarting: asked again next time */ }
    }
    sigTimer = setTimeout(watch, SIG_EVERY);
  }

  // ---------------------------------------------------------------- mouse: move, turn, resize
  const toStage = (ev) => { const r = wrap.getBoundingClientRect(); return [(ev.clientX - r.left) / st.S, (ev.clientY - r.top) / st.S]; };
  offs.push(on(wrap, 'pointerdown', '*', (ev) => {
    if (ev.button !== 0) return;
    const hEl = ev.target.closest('.se-h');
    const [px, py] = toStage(ev);
    if (hEl && cur()) {
      st.drag = { mode: hEl.dataset.h, px, py, e0: JSON.parse(JSON.stringify(cur())), before: snapshot() };
    } else {
      const el = ev.target.closest('#se-stage .el');
      if (!el) { if (st.sel >= 0) select(-1); return; }
      const i = +el.dataset.idx;
      if (i !== st.sel) select(i);
      st.drag = { mode: 'move', px, py, e0: JSON.parse(JSON.stringify(items()[i])), before: snapshot() };
    }
    wrap.setPointerCapture(ev.pointerId);
    ev.preventDefault();
  }));
  const onMove = (ev) => {
    const d = st.drag;
    if (!d) return;
    const e = cur(), e0 = d.e0;
    const [px, py] = toStage(ev);
    if (d.mode === 'move') {
      e.x = Math.round((e0.x + px - d.px) * 10) / 10; e.y = Math.round((e0.y + py - d.py) * 10) / 10;
      place(st.sel); return;
    }
    if (d.mode === 'rot') {
      let a = Math.atan2(py - e0.y, px - e0.x) * 180 / Math.PI + 90;
      a = ev.shiftKey ? Math.round(a / 15) * 15 : Math.round(a * 10) / 10;
      if (a > 180) a -= 360;
      e.rot = a; place(st.sel); return;
    }
    // resize: in the element's own (turned) axes
    const rad = (e0.rot || 0) * Math.PI / 180, cos = Math.cos(-rad), sin = Math.sin(-rad);
    const local = (x, y) => [(x - e0.x) * cos - (y - e0.y) * sin, (x - e0.x) * sin + (y - e0.y) * cos];
    const [lx0, ly0] = local(d.px, d.py);
    const [lx, ly] = local(px, py);
    const m = d.mode;
    if (m.length === 2) {           // a corner keeps the proportions
      const k = Math.max(0.05, Math.hypot(lx, ly) / Math.hypot(lx0, ly0));
      for (const key of ['w', 'h', 'r', 'size']) if (e0[key] != null) e[key] = Math.round(e0[key] * k * 10) / 10;
      if (e0.sw != null && e.type === 'arrow') e.sw = Math.round(e0.sw * k * 10) / 10;
    } else if (m === 'e' || m === 'w') e.w = Math.max(10, Math.round(e0.w * Math.abs(lx) / Math.max(1, Math.abs(lx0))));
    else if (e0.h != null) e.h = Math.max(4, Math.round(e0.h * Math.abs(ly) / Math.max(1, Math.abs(ly0))));
    redrawOne(st.sel);
  };
  const onUp = () => {
    if (!st.drag) return;
    const before = st.drag.before;
    st.drag = null;
    commit(before);
    drawProps();
  };
  wrap.addEventListener('pointermove', onMove);
  wrap.addEventListener('pointerup', onUp);
  wrap.addEventListener('pointercancel', onUp);

  // ---------------------------------------------------------------- the panels' events
  function change(fn, { redraw = true, props = false } = {}) {
    const before = snapshot();
    fn();
    if (redraw === 'place') place(st.sel); else if (redraw) redrawOne(st.sel);
    if (props) drawProps();
    commit(before);
  }
  function duplicate() {
    const e = cur();
    if (!e) return;
    const before = snapshot();
    const c = JSON.parse(JSON.stringify(e));
    c.x += 20; c.y += 20; c.name = `${e.name || KIND[e.type][0]} (копія)`; c.uid = Date.now() % 100000;
    items().splice(st.sel + 1, 0, c);
    st.sel += 1;
    redrawAll(); commit(before);
  }
  function remove() {
    if (!cur()) return;
    const before = snapshot();
    items().splice(st.sel, 1);
    st.sel = -1;
    redrawAll(); commit(before);
    toast('Прибрано — Ctrl+Z поверне', 'info', 1800);
  }
  function add(type) {
    const before = snapshot();
    const [kind] = KIND[type];
    const count = items().filter((e) => e.type === type).length + 1;
    const e = { type, name: `${kind} ${count}`, x: 500, y: 500, rot: 0, uid: Date.now() % 100000, ...NEW[type]() };
    const at = st.sel >= 0 ? st.sel + 1 : items().length;
    items().splice(at, 0, e);
    st.sel = at;
    redrawAll(); commit(before);
  }

  offs.push(on(view, 'click', '[data-act], .se-layer', async (ev, t) => {
    const a = t.dataset.act;
    if (!a && t.classList.contains('se-layer')) { select(+t.dataset.i); return; }
    ev.stopPropagation();
    if (a === 'undo') undo();
    else if (a === 'redo') redo();
    else if (a === 'lock' || a === 'eye') {
      const i = +t.dataset.i, e = items()[i], before = snapshot();
      if (a === 'lock') e.locked = !e.locked; else e.hidden = !e.hidden;
      redrawAll(); commit(before);
    } else if (a === 'add') {
      menu(t, ADD_ORDER.map((type) => ({ label: KIND[type][0], icon: KIND[type][1], onClick: () => add(type) })));
    } else if (a === 'flipX' || a === 'flipY') {
      change(() => { cur()[a] = !cur()[a]; }, { redraw: 'place', props: true });
    } else if (a === 'dup') duplicate();
    else if (a === 'del') remove();
    else if (a === 'swatch') {
      change(() => { cur().color = t.dataset.c; }, { props: true });
    } else if (a === 'bg') {
      const before = snapshot();
      scene.bg = t.dataset.c;
      stage.style.background = scene.bg;
      drawProps(); commit(before);
    } else if (a === 'pick-picture') pickPicture(t.dataset.slot);
    else if (a === 'reset') {
      const ok = await confirmBox({ title: 'Скинути слайд?', text: isSet ? 'Слайд стане таким, як у шаблоні. Ctrl+Z поверне.' : 'Шаблон цього слайда стане таким, як був намальований спершу. Ctrl+Z поверне.', confirm: 'Скинути' });
      if (!ok || gone) return;
      await flush();
      try {
        const r = await post('/api/slides/reset', { w: where, s: slide });
        st.past.push(snapshot()); st.future = [];
        scene = r.scene; version = r.version; st.sel = -1;
        redrawAll(); paintSaved('ok', 'Скинуто');
      } catch (err) { toast(err.message, 'error'); }
    } else if (a === 'to-template') {
      const ok = await confirmBox({ title: 'Зробити шаблоном?', text: `Слайд ${n} у кожній наступній книзі буде саме таким. Слайди вже зроблених книг не зміняться.`, confirm: 'Зробити шаблоном' });
      if (!ok || gone) return;
      await flush();
      try { await post('/api/slides/to-template', { w: where, s: slide }); toast(`Слайд ${n} тепер — шаблон для нових книг`, 'success'); }
      catch (err) { toast(err.message, 'error'); }
    } else if (a === 'bake') bake();
  }));

  // a segmented switch: another slide, or a field's choice
  offs.push(on(view, 'click', '.seg button', (ev, b) => {
    const seg = b.closest('.seg'), name = seg.dataset.seg;
    if (name === 'slide') { if (b.dataset.value !== slide) { flush(); location.hash = `#/slides/${where}/${b.dataset.value.replace('slide', '')}`; } return; }
    const k = name.replace(/^f-/, ''), f = (SPEC[cur()?.type] || []).flatMap(([, fs]) => fs).find((x) => x.k === k);
    if (!f) return;
    const raw_ = f.options.find(([v]) => String(v) === b.dataset.value)?.[0];
    change(() => { cur()[k] = raw_; }, { props: true });
  }));

  // fields: numbers and texts on change (one step of history), sliders and colours live
  offs.push(on(view, 'input', '#se-props [data-kind]', (ev, t) => {
    const kind = t.dataset.kind, e = cur();
    if (kind === 'range' || kind === 'color') {
      if (!st.live) st.live = snapshot();
      const v = kind === 'range' ? +t.value : t.value;
      if (e) {
        e[t.dataset.k] = v;
        redrawOne(st.sel);
      } else if (kind === 'color') { scene.bg = v; stage.style.background = v; }
      const twin = t.parentElement.querySelector(`input[data-kind="num"][data-k="${t.dataset.k}"]`);
      if (twin) twin.value = +(+v).toFixed(2);
      if (kind === 'color') t.closest('.se-pick')?.style.setProperty('--c', v);
    }
  }));
  offs.push(on(view, 'change', '#se-props [data-kind]', (ev, t) => {
    const kind = t.dataset.kind, e = cur();
    if (kind === 'range' || kind === 'color') {
      const before = st.live || snapshot();
      st.live = null;
      commit(before);
      drawProps();
      return;
    }
    if (kind === 'bg') { const before = snapshot(); scene.bg = t.value; stage.style.background = t.value; commit(before); drawProps(); return; }
    if (kind === 'number') { setNumber(t.dataset.k, +t.value); return; }
    if (!e) return;
    if (kind === 'name') { change(() => { e.name = t.value.trim(); }, { redraw: false }); drawLayers(); return; }
    if (kind === 'num') {
      if (t.value === '') return;
      change(() => { e[t.dataset.k] = +t.value; }, { redraw: ['x', 'y', 'rot'].includes(t.dataset.k) ? 'place' : true });
      const twin = t.parentElement.querySelector('input[type="range"]');
      if (twin) twin.value = t.value;
      return;
    }
    if (kind === 'text') { change(() => { e.text = t.value; }); drawSel(); return; }
    if (kind === 'lines') {
      change(() => {
        e.lines = t.value.split('\n').map((s) => s.trim()).filter(Boolean).map((s, i) => ({ ...(e.lines[i] || {}), t: s }));
      });
      return;
    }
    if (kind === 'slot') { change(() => { e.slot = t.value; }); drawSel(); }
  }));

  async function setNumber(k, value) {
    if (!(value > 0 && value < 1000)) { toast('Число має бути від 1 до 999', 'error'); drawProps(); return; }
    try {
      const r = await post('/api/slides/numbers', { w: where, [k]: Math.round(value) });
      info.numbers = r.numbers;
      assets = { ...assets, numbers: r.numbers };
      setAssets(assets);
      redrawAll();
    } catch (err) { toast(err.message, 'error'); }
  }

  async function pickPicture(slot) {
    try {
      const r = await post('/api/slides/picture', { w: where, slot });
      if (!r.picked || gone) return;
      assets = await api(`/api/slides/assets?w=${encodeURIComponent(where)}`);
      setAssets(assets);
      redrawAll();
      toast('Картинку замінено', 'success');
    } catch (err) { toast(err.message, 'error'); }
  }

  // «Зберегти картинки» — the six baked again into the book's folder (the Mockups' card shows the new ones)
  async function bake() {
    if (st.baking) return;
    await flush();
    const btn = $('[data-act="bake"]');
    st.baking = true;
    if (btn) btn.disabled = true;
    paintSaved('busy', 'Малюю…');
    tellBusy({ mockups: true });
    try {
      const res = await runJob(post('/api/slides/bake', { w: where }), (job) => { if (!gone) paintSaved('busy', job.step || 'Малюю…'); }, 500, () => !gone);
      if (gone) return;
      paintSaved('ok', `Збережено ${res.pictures.length} картинок`);
      toast(`Картинки збережено · ${res.pictures.length} — у папці книги, поверх попередніх`, 'success', 3600);
    } catch (err) {
      if (!gone) { paintSaved('bad', 'Не вдалося'); toast(err.message, 'error'); }
    } finally {
      tellBusy({ mockups: false });
      st.baking = null;
      if (btn) btn.disabled = false;
    }
  }

  // ---------------------------------------------------------------- dragging layers into another order
  let dragFrom = null;
  offs.push(on(view, 'dragstart', '.se-layer', (ev, t) => { dragFrom = +t.dataset.i; ev.dataTransfer.effectAllowed = 'move'; ev.dataTransfer.setData('application/x-se-layer', t.dataset.i); t.classList.add('dragging'); }));
  offs.push(on(view, 'dragend', '.se-layer', (ev, t) => { t.classList.remove('dragging'); view.querySelectorAll('.drop-above,.drop-below').forEach((x) => x.classList.remove('drop-above', 'drop-below')); dragFrom = null; }));
  offs.push(on(view, 'dragover', '.se-layer', (ev, t) => {
    if (dragFrom === null) return;
    ev.preventDefault();
    const r = t.getBoundingClientRect(), above = ev.clientY < r.top + r.height / 2;
    view.querySelectorAll('.drop-above,.drop-below').forEach((x) => x.classList.remove('drop-above', 'drop-below'));
    t.classList.add(above ? 'drop-above' : 'drop-below');
  }));
  offs.push(on(view, 'drop', '.se-layer', (ev, t) => {
    if (dragFrom === null) return;
    ev.preventDefault();
    const r = t.getBoundingClientRect(), above = ev.clientY < r.top + r.height / 2;
    const target = +t.dataset.i;
    // the list shows the top first: "above" a row means in front of it — a higher index
    let to = above ? target + 1 : target;
    const from = dragFrom;
    if (from < to) to -= 1;
    if (to === from) return;
    const before = snapshot();
    const selected = cur();
    const [moved] = items().splice(from, 1);
    items().splice(to, 0, moved);
    st.sel = selected ? items().indexOf(selected) : -1;
    redrawAll(); commit(before);
  }));

  // ---------------------------------------------------------------- keys
  const onKey = (ev) => {
    if (!view.isConnected || document.querySelector('.modal-root, .lightbox, .menu')) return;
    if (/^(INPUT|TEXTAREA|SELECT)$/.test(ev.target.tagName)) return;
    const k = ev.key.toLowerCase();
    if (ev.ctrlKey && k === 'z') { ev.preventDefault(); if (ev.shiftKey) redo(); else undo(); return; }
    if (ev.ctrlKey && k === 'y') { ev.preventDefault(); redo(); return; }
    if (ev.ctrlKey && k === 'd') { ev.preventDefault(); duplicate(); return; }
    if (ev.altKey || ev.ctrlKey) return;
    const e = cur();
    if (!e) return;
    if (ev.key === 'Delete' || ev.key === 'Backspace') { ev.preventDefault(); remove(); return; }
    if (ev.key === 'Escape') { ev.preventDefault(); select(-1); return; }
    const step = ev.shiftKey ? 10 : 1;
    const mv = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }[ev.key];
    if (mv) { ev.preventDefault(); change(() => { e.x += mv[0]; e.y += mv[1]; }, { redraw: 'place', props: true }); return; }
    if (ev.key === '[' || ev.key === ']') {
      change(() => { e.rot = Math.round(((e.rot || 0) + (ev.key === ']' ? 1 : -1) * (ev.shiftKey ? 5 : 0.5)) * 10) / 10; }, { redraw: 'place', props: true });
    }
  };
  document.addEventListener('keydown', onKey);
  // back from another window (the agent's): asked at once, not in 1.5 s
  const onVisible = () => { if (document.visibilityState === 'visible') watch(); };
  document.addEventListener('visibilitychange', onVisible);

  redrawAll();
  fit();
  paintSaved('ok', version ? 'Збережено' : isSet ? 'Як у шаблоні' : 'Як намальовано спершу');
  sigTimer = setTimeout(watch, SIG_EVERY);

  return {
    shown() { fit(); },
    unmount() {
      if (st.dirty) flush();   // a change made a moment ago still goes to disk
      gone = true;
      clearTimeout(sigTimer); clearTimeout(saveTimer);
      ro.disconnect();
      document.removeEventListener('keydown', onKey);
      document.removeEventListener('visibilitychange', onVisible);
      wrap.removeEventListener('pointermove', onMove);
      wrap.removeEventListener('pointerup', onUp);
      wrap.removeEventListener('pointercancel', onUp);
      offs.forEach((off) => off());
    },
  };
}
