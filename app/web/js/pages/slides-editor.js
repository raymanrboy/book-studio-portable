// The listing slides' editor (#/slides/<set | template>/<1–7>; 7 — the hero's looks, only for a book that has them) — the owner's touches on a book's six slides, the way
// he asked on 29.09.2026: "like Canva — layers, moving, rotating, resizing", then «Зберегти картинки» bakes them.
// Moved in from the external Slide Editor the same day, in Book Studio's own look. A separate module, loaded only when
// opened (left out of the pages' warm-up in app.js) with its own styles (css/slides.css).
// Every change is saved at once with the version it was made on; what an agent changes in the files meanwhile shows
// up by itself (the signature is asked every 1.5 s) — the owner may work on the slides through an LLM too.
import {
  api, post, html, ic, ib, setHtml, on, toast, runJob, menu, modal, confirmBox, segHtml, notFound, tellBusy, attr, reducedMotion,
} from '../lib.js';
import { store } from '../info.js';
import {
  ready, setAssets, drawScene, drawElement, boxOf, elTransform, TSHADOW, isHero,
} from '../slides/engine.js';

// Where the owner came into the editor from, and how each slide looked when this editing session began (2026-09-30): the
// way back leads there (the browser's history holds every slide he flipped through), and «Скинути» returns to that start —
// a session lives only while he stays in the editor, so a slide is never reset to a default from months ago.
let origin = '';
const sessions = new Map();

const CSS = '/css/slides.css';
const SIG_EVERY = 1500, SIG_CALM = 4000, CALM_AFTER = 30000;   // asked less often once nothing has happened here for 30 s (05.10.2026)
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
  image: [['Картинка', [{ k: 'slot', kind: 'picSlot' },
    { k: 'shape', label: 'Рамка', kind: 'seg', def: 'rect', options: [['scallop', 'Зірочка'], ['rect', 'Прямокутна']] },
    num('rim', 'Біла кромка', { def: 0 }), num('bumps', 'Хвильок у рамці', { def: 10 }),
    range('zoom', 'Наблизити', 1, 3, 0.01, 1), range('fy', 'Що видно: верх → низ', 0, 1, 0.01, 0.5)]],
  ['Підпис', [{ k: 'labelText', kind: 'caption' }, { k: 'label', label: 'Де підпис', kind: 'seg', def: 'below', options: [['below', 'Під рамкою'], ['above', 'Над рамкою'], ['none', 'Без']] },
    num('labelSize', 'Розмір літер', { def: 46 }), num('labelGap', 'Відступ', { def: 14 }),
    { k: 'labelColor', label: 'Колір', kind: 'color', def: '#3b2a1e' }], (e) => isHero(e.slot)],
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
  const n = Math.min(7, Math.max(1, +nParam || 1));
  const slide = `slide${n}`;
  const q = (path) => `${path}?w=${encodeURIComponent(where)}&s=${slide}`;
  let info = null, scene = null, version = '', assets = null;
  try {
    [, info, { scene, version }, assets] = await Promise.all([
      ensureCss(), api(`/api/slides/state?w=${encodeURIComponent(where)}`), api(q('/api/slides/scene')),
      api(`/api/slides/assets?w=${encodeURIComponent(where)}`), ready()]);
  } catch (err) {
    notFound(view, { back: '#/tools', backLabel: 'До інструментів', icon: 'images', title: 'Слайди не відкрились', text: err.message });
    return null;
  }
  if (!info.slides.some((s) => s.id === slide)) {   // slide 7 of a book whose hero has no looks
    location.replace(`#/slides/${whereParam}/1`);
    return null;
  }
  setAssets(assets);
  view.classList.add('se-view');
  if (!String(store.here || '').startsWith('#/slides/')) origin = store.here || '';   // a scheme picked inside the editor keeps the way out
  if (!String(store.here || '').startsWith(`#/slides/${whereParam}/`)) sessions.delete(where);
  const session = sessions.get(where) || sessions.set(where, {}).get(where);
  if (!(slide in session)) session[slide] = JSON.stringify(scene);
  const isSet = where !== 'template' && !where.startsWith('scheme:');   // a book's slides; else a scheme edited on its own
  const st = { sel: -1, bg: false, past: [], future: [], saving: null, dirty: false, sig: info.sig, drag: null, live: null, S: 1,
    baking: null, others: [], pressed: null };
  let gone = false, sigTimer = 0, saveTimer = 0;
  const offs = [];
  const $ = (s) => view.querySelector(s);
  const snapshot = () => JSON.stringify(scene);
  const items = () => scene.items;
  const cur = () => items()[st.sel];
  // Every element stays put unless it is freed (the owner, 29.09.2026: "all elements locked against moving by default"):
  // a click selects it and its properties open; the lock in the layers lets the mouse move it. New ones come free.
  const isLocked = (e) => e.locked !== false;
  const THROUGH = ['leaves', 'grain'];   // over everything, never in the way of a click

  function schemeLabel() { return `Схема: ${info.scheme?.name || '—'}`; }

  // ---------------------------------------------------------------- the page
  setHtml(view, html`<div class="se">
    <header class="se-bar">
      <button type="button" class="back-link" data-act="back" aria-label="Назад" data-tip="Назад">${ic('arrowLeft', 'icon-s')}</button>
      <div class="se-title">
        <h1 class="page-title">Слайди</h1>
        <div class="page-sub truncate">${info.name}${isSet || info.scheme?.key !== info.defaultScheme ? '' : ' · з неї починається кожна нова книга'}</div>
      </div>
      ${segHtml(info.slides.map((s, i) => ({ value: s.id, label: String(i + 1), tip: `${i + 1} · ${s.title}` })), slide, { accent: true, name: 'slide' })}
      <span class="grow"></span>
      <div class="tools">
        ${ib('undo', 'Назад', 'data-act="undo"', { kbd: 'Ctrl+Z' })}${ib('redo', 'Вперед', 'data-act="redo"', { kbd: 'Ctrl+Y' })}
        <span class="sep"></span>
        ${ib('restore', 'Повернути слайд, як він був, коли ви відкрили редактор', 'data-act="reset"')}
      </div>
      <button type="button" class="btn se-scheme" data-act="scheme" id="se-scheme">${ic('template', 'icon-s')}<span class="truncate">${schemeLabel()}</span>${ic('chevDown', 'icon-s')}</button>
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
    if (st.drag) st.drag.rect = wrap.getBoundingClientRect();
    drawSel();
  }
  const ro = new ResizeObserver(fit);
  ro.observe($('#se-canvas'));

  function redrawAll() { drawScene(scene, stage, 'se'); markLocks(); drawLayers(); drawSel(); drawProps(); }
  function redrawOne(i) {
    const old = stage.querySelector(`.el[data-idx="${i}"]`);
    if (!old) { redrawAll(); return; }
    old.replaceWith(drawElement(items()[i], i, 'se'));
    markLocks(i); drawSel();
  }
  function place(i) {   // move / turn / mirror only: no drawing again
    const e = items()[i], el = stage.querySelector(`.el[data-idx="${i}"]`);
    if (!el) return;
    el.style.left = `${e.x}px`; el.style.top = `${e.y}px`; el.style.transform = elTransform(e);
    el.style.translate = '';   // a drag moves by `translate` (compositor); here the real position takes over
    drawSel();
  }
  function markLocks(only) {
    const mark = (e, i) => {
      const el = stage.querySelector(`.el[data-idx="${i}"]`);
      if (!el) return;
      if (THROUGH.includes(e.type)) el.dataset.lock = '1';
      else if (isLocked(e)) el.dataset.fixed = '1';
    };
    if (only != null) { if (items()[only]) mark(items()[only], only); return; }
    items().forEach(mark);
  }
  // A short fade over the stage when the whole slide changes at once (a scheme laid on, a reload from disk).
  function fadeStage() {
    if (reducedMotion()) return;
    stage.animate([{ opacity: 0.2 }, { opacity: 1 }], { duration: 220, easing: 'cubic-bezier(.2,.7,.2,1)' });
  }

  // ---------------------------------------------------------------- the layers (the top one is in front)
  function drawLayers() {
    const list = $('#se-layers');
    // A redraw replaces the rows: a press made from the keyboard (Enter on a layer, on its lock or eye) keeps the focus.
    const was = document.activeElement;
    const focusSel = was && list.contains(was)
      ? (was.classList.contains('se-layer') ? `.se-layer[data-i="${was.dataset.i}"]` : was.dataset.act ? `[data-act="${was.dataset.act}"][data-i="${was.dataset.i}"]` : '') : '';
    setHtml(list, [...items().keys()].reverse().map((i) => {
      const e = items()[i];
      const [kind, glyph] = KIND[e.type] || [e.type, 'image'];
      const locked = isLocked(e) && !THROUGH.includes(e.type);
      return html`<div class="se-layer ${i === st.sel ? 'sel' : ''} ${e.hidden ? 'off' : ''}" data-i="${i}" draggable="true" role="button" tabindex="0" data-press>
        <span class="se-kind" data-tip="${kind}">${ic(glyph, 'icon-s')}</span>
        <span class="grow truncate">${e.name || kind}</span>
        ${THROUGH.includes(e.type) ? '' : ib(locked ? 'lock' : 'unlock', locked ? 'Закріплено — зняти замок, щоб рухати мишкою' : 'Вільно рухається — закріпити', `data-act="lock" ${attr('data-i', i)}`, { cls: `xs se-lock ${locked ? '' : 'free'}` })}
        ${ib(e.hidden ? 'eyeOff' : 'eye', e.hidden ? 'Показати' : 'Сховати', `data-act="eye" ${attr('data-i', i)}`, { cls: `xs se-eye ${e.hidden ? 'on' : ''}` })}
      </div>`;
    }).concat([html`<div class="se-layer se-bg-row ${st.bg ? 'sel' : ''}" data-i="bg" role="button" tabindex="0" data-press>
        <span class="se-kind se-bg-chip" style="--c:${scene.bg}" data-tip="Тло"></span><span class="grow truncate">Тло</span></div>`]));
    list.querySelector('.se-layer.sel')?.scrollIntoView({ block: 'nearest' });
    if (focusSel) list.querySelector(focusSel)?.focus({ preventScroll: true });
  }

  // ---------------------------------------------------------------- the selection and its handles
  // One box with its handles lives while the same element stays selected (same kind, same lock): a drag only moves
  // them (no rebuilding per event); a new selection builds them once and they fade in.
  let selBox = null, selKey = '', selHs = [], selStem = null, selLay = '';
  function buildSel(e, locked) {
    over.replaceChildren();
    selHs = []; selStem = null; selLay = '';
    const b = document.createElement('div');
    b.className = `se-selbox ${locked ? 'fixed' : ''}`;
    const handle = (cls, fx, fy, cursor) => {
      const d = document.createElement('div');
      d.className = `se-h h-${cls}`;
      d.dataset.h = cls;
      d.style.cursor = cursor;
      b.appendChild(d);
      selHs.push({ d, fx, fy });
    };
    if (!locked && e.type !== 'grain') {
      [['nw', 0, 0], ['ne', 1, 0], ['sw', 0, 1], ['se', 1, 1]].forEach(([c, fx, fy]) => handle(c, fx, fy, c === 'nw' || c === 'se' ? 'nwse-resize' : 'nesw-resize'));
      if (STRETCHES.includes(e.type)) {
        handle('e', 1, 0.5, 'ew-resize'); handle('w', 0, 0.5, 'ew-resize');
        handle('n', 0.5, 0, 'ns-resize'); handle('s', 0.5, 1, 'ns-resize');
      }
      selStem = document.createElement('div');
      selStem.className = 'se-stem';
      b.appendChild(selStem);
      handle('rot', 0.5, null, 'grab');
    }
    over.appendChild(b);
    selBox = b;
  }
  function drawSel() {
    const e = cur();
    if (!e || e.hidden) { if (selBox) { over.replaceChildren(); selBox = null; selKey = ''; } return; }
    const locked = isLocked(e);
    const key = `${st.sel}|${e.type}|${locked}|${STRETCHES.includes(e.type)}`;
    if (!selBox || key !== selKey || !selBox.isConnected) { buildSel(e, locked); selKey = key; }
    const [w, h] = boxOf(e), S = st.S;
    Object.assign(selBox.style, { left: `${e.x - w / 2}px`, top: `${e.y - h / 2}px`, transform: `rotate(${e.rot || 0}deg)` });
    const lay = `${w}|${h}|${S}`;
    if (lay === selLay) return;   // only moved or turned: the rest of the box is as it was
    selLay = lay;
    const hs = 12 / S;
    Object.assign(selBox.style, { width: `${w}px`, height: `${h}px`, outlineWidth: `${1.5 / S}px` });
    for (const { d, fx, fy } of selHs) {
      const x = w * fx, y = fy === null ? -28 / S : h * fy;
      Object.assign(d.style, { width: `${hs}px`, height: `${hs}px`, left: `${x - hs / 2}px`, top: `${y - hs / 2}px`, borderWidth: `${1.5 / S}px` });
    }
    if (selStem) Object.assign(selStem.style, { top: `${-28 / S}px`, height: `${28 / S}px`, width: `${1.5 / S}px` });
  }
  function select(i) {
    st.bg = i === 'bg';
    st.sel = st.bg ? -1 : i;
    const list = $('#se-layers');
    const rows = list ? [...list.querySelectorAll('.se-layer')] : [];
    if (rows.length === items().length + 1) {   // the rows are there: only the mark moves, so its transition plays
      rows.forEach((r) => r.classList.toggle('sel', r.dataset.i === 'bg' ? st.bg : +r.dataset.i === st.sel));
      list.querySelector('.se-layer.sel')?.scrollIntoView({ block: 'nearest' });
    } else drawLayers();
    drawSel(); drawProps(true);
  }

  // ---------------------------------------------------------------- the properties
  const val = (e, f) => e[f.k] ?? f.def ?? '';
  const fmt = (v) => (typeof v === 'number' ? +v.toFixed(2) : v);
  const HEX = /^#[0-9a-f]{6}$/i;
  function coloursOf(sc) {
    const out = [];
    if (HEX.test(sc?.bg || '')) out.push(sc.bg.toLowerCase());
    (sc?.items || []).forEach((e) => { for (const k of ['color', 'textColor', 'labelColor']) if (HEX.test(e[k] || '')) out.push(e[k].toLowerCase()); });
    return out;
  }
  // [this slide's colours, the other five slides' ones not on this one]
  function palettes() {
    const mine = [...new Set(['#ffffff', ...coloursOf(scene)])];
    const others = [...new Set(st.others.flatMap(coloursOf))].filter((c) => !mine.includes(c));
    return [mine.slice(0, 14), others.slice(0, 14)];
  }
  function swatches(current, act, pick, key = 'color') {
    const [mine, others] = palettes();
    const sw = (c) => html`<button type="button" class="se-sw ${String(current).toLowerCase() === c ? 'on' : ''}" style="--c:${c}" data-act="${act}" data-k="${key}" data-c="${c}" aria-label="${c}" data-tip="${c}"></button>`;
    return html`<div class="se-swatches">${mine.map(sw)}${pick}</div>
      ${others.length ? html`<div class="se-swatches se-others"><span class="se-others-label">З інших слайдів</span>${others.map(sw)}</div>` : ''}`;
  }
  async function loadOthers() {
    const rest = info.slides.map((x) => x.id).filter((id) => id !== slide);
    try {
      const got = await Promise.all(rest.map((id) => api(`/api/slides/scene?w=${encodeURIComponent(where)}&s=${id}`)));
      if (gone) return;
      st.others = got.map((r) => r.scene);
      drawProps();
    } catch { /* only the suggestions: this slide's colours are there anyway */ }
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
      return html`<div class="se-f se-wide"><span>${f.label}</span>${swatches(v, 'swatch',
        html`<label class="se-sw se-pick" data-tip="Інший колір" style="--c:${v}"><input type="color" data-k="${f.k}" data-kind="color" value="${v}"></label>`, f.k)}</div>`;
    }
    if (f.kind === 'seg') {
      return html`<div class="se-f se-wide"><span>${f.label}</span>${segHtml(f.options.map(([value, label]) => ({ value: String(value), label })), String(v), { name: `f-${f.k}` })}</div>`;
    }
    if (f.kind === 'caption') {   // a look's caption: empty — its name (2026-10-02)
      const name = assets.pictures[e.slot]?.label || '';
      return html`<label class="se-f se-wide"><span>Підпис · порожньо — «${name || 'назва варіанта'}» · {name} — назва варіанта</span>
        <textarea class="textarea" rows="2" data-k="labelText" data-kind="caption" spellcheck="false" placeholder="${name}">${e.labelText || ''}</textarea></label>`;
    }
    if (f.kind === 'text') {
      return html`<label class="se-f se-wide"><span>Текст · Enter — новий рядок · {pages} і {poems} — числа книги, {looks} — скільки варіантів героя</span>
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
        <select class="select" data-k="slot" data-kind="slot">${info.slots.filter((s) => s.kind === want).map((s) => html`<option value="${s.slot}" ${s.slot === e.slot ? 'selected' : ''}>${s.label}${has(s.slot) ? '' : '  ·  немає'}</option>`)}</select>
        ${want === 'picture' && isSet && !isHero(e.slot) ? html`<button type="button" class="btn btn-sm btn-ghost se-repick" data-act="pick-picture" data-slot="${e.slot}">${ic('folderPick', 'icon-s')}Інша картинка…</button>` : ''}
      </div>`;
    }
    return '';
  }

  let propsRaf = 0;
  function queueProps() {   // several changes in one frame (a held arrow key) redraw the panel once
    if (propsRaf) return;
    propsRaf = requestAnimationFrame(() => { propsRaf = 0; if (!gone) drawProps(); });
  }
  function drawProps(fade = false) {
    if (propsRaf) { cancelAnimationFrame(propsRaf); propsRaf = 0; }
    const box = $('#se-props');
    if (fade && !reducedMotion()) box.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 160, easing: 'ease-out' });
    const e = cur();
    if (!e) { setHtml(box, slideProps()); return; }
    const [kind] = KIND[e.type] || [e.type];
    setHtml(box, html`
      <div class="se-panel-head"><span class="eyebrow grow">${kind}</span>
        ${THROUGH.includes(e.type) ? '' : ib(isLocked(e) ? 'lock' : 'unlock', isLocked(e) ? 'Закріплено — зняти замок, щоб рухати мишкою' : 'Вільно рухається — закріпити', `data-act="lock" ${attr('data-i', st.sel)}`, { cls: `sm ${isLocked(e) ? 'on' : ''}` })}
        ${ib('mirror', 'Віддзеркалити зліва направо', 'data-act="flipX"', { cls: `sm ${e.flipX ? 'on' : ''}` })}
        ${ib('mirrorV', 'Віддзеркалити догори дригом', 'data-act="flipY"', { cls: `sm ${e.flipY ? 'on' : ''}` })}
        ${ib('copy', 'Копія', 'data-act="dup"', { cls: 'sm', kbd: 'Ctrl+D' })}
        ${ib('trash', 'Прибрати зі слайда', 'data-act="del"', { cls: 'sm', kbd: 'Delete' })}</div>
      <div class="se-scroll">
        <label class="se-f se-wide"><span>Назва</span><input class="input" data-k="name" data-kind="name" value="${e.name || ''}" spellcheck="false"></label>
        ${(SPEC[e.type] || []).filter(([, , when]) => !when || when(e)).map(([title, fields]) => html`<section class="se-group"><h4>${title}</h4><div class="se-grid">${fields.map((f) => fieldHtml(e, f))}</div></section>`)}
      </div>`);
  }

  // Nothing selected: the slide itself — its background and (a book's slides) the book's numbers.
  function slideProps() {
    return html`<div class="se-panel-head"><span class="eyebrow grow">${st.bg ? 'Тло' : `Слайд ${n}`}</span></div>
      <div class="se-scroll">
        <section class="se-group"><h4>Тло</h4><div class="se-grid">
          <div class="se-f se-wide"><span>Колір тла</span>${swatches(scene.bg, 'bg',
            html`<label class="se-sw se-pick" data-tip="Інший колір" style="--c:${scene.bg}"><input type="color" data-kind="bg" value="${HEX.test(scene.bg) ? scene.bg : '#eedec7'}"></label>`)}</div>
        </div></section>
        ${isSet ? html`<section class="se-group"><h4>Числа книги</h4><div class="se-grid">
          <label class="se-f"><span>Сторінок · {pages}</span><input class="input num" type="number" min="1" max="999" data-kind="number" data-k="pages" value="${info.numbers.pages}"></label>
          <label class="se-f"><span>Віршів · {poems}</span><input class="input num" type="number" min="1" max="999" data-kind="number" data-k="poems" value="${info.numbers.poems}"></label>
        </div></section>` : ''}
        ${st.bg ? '' : html`<p class="se-empty">Клацніть елемент на слайді або в шарах.</p>`}
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
  // A real percent (the bake) fills a thin bar; none known (a save) — the neutral spinner, never a half-filled one.
  function paintSaved(state, text, pct = null) {
    const chip = $('#se-saved');
    if (!chip) return;
    const bar = chip.querySelector('.se-bake > i');
    if (state === 'busy' && pct != null && bar) {   // the same bar moves on: its fill glides
      bar.style.transform = `scaleX(${Math.max(0, Math.min(100, pct)) / 100})`;
      chip.querySelector('.se-saved-text').textContent = text;
      return;
    }
    chip.className = `se-saved ${state}`;
    const lead = state === 'busy' ? (pct != null ? html`<span class="progress progress-thin live se-bake"><i style="transform:scaleX(${Math.max(0, Math.min(100, pct)) / 100})"></i></span>` : html`<span class="spinner"></span>`)
      : state === 'bad' ? ic('alertCircle', 'icon-s') : ic('check', 'icon-s');
    setHtml(chip, html`${lead}<span class="se-saved-text">${text}</span>`);
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
      if (gone) { // the page is already left: the chip is gone, but a lost last change must still be said
        toast(err.status === 409 ? 'Останню зміну слайда не збережено: його тим часом змінили.' : `Останню зміну слайда не збережено: ${err.message}`, 'error');
        return;
      }
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
    redrawAll(); fadeStage();
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
  let lastActive = Date.now();
  const stir = () => { lastActive = Date.now(); };
  view.addEventListener('pointerdown', stir, true);
  view.addEventListener('keydown', stir, true);
  async function watch() {
    clearTimeout(sigTimer);
    if (gone) return;
    if (view.isConnected && document.visibilityState === 'visible' && !st.drag && !st.live) {
      try {
        const { sig } = await api(`/api/slides/sig?w=${encodeURIComponent(where)}`);
        if (sig !== st.sig && !gone) {
          const [{ scene: theirs, version: v }, a, i] = await Promise.all([api(q('/api/slides/scene')),
            api(`/api/slides/assets?w=${encodeURIComponent(where)}`), api(`/api/slides/state?w=${encodeURIComponent(where)}`)]);
          if (gone || st.drag) return;   // a hand is on the slide: asked again next time
          lastActive = Date.now();
          st.sig = sig; // remembered only once the three answers are in: a failed round asks again next time
          const assetsChanged = JSON.stringify(a) !== JSON.stringify(assets);
          assets = a; info = i; setAssets(a);
          if (v !== version && !st.dirty && !st.saving) takeTheirs(theirs, v, 'Слайд змінено ззовні — показано новий');
          else if (assetsChanged) { redrawAll(); }
          loadOthers();
        }
      } catch { /* the program is restarting: asked again next time */ }
    }
    sigTimer = setTimeout(watch, Date.now() - lastActive > CALM_AFTER ? SIG_CALM : SIG_EVERY);
  }

  // ---------------------------------------------------------------- mouse: move, turn, resize
  // A pointer move is only noted; the newest sample is applied once per frame (at 170 Hz events outrun frames), and the
  // last one at once on release. The slide's rectangle is measured on press, not on every event.
  const toStage = (ev, r) => [(ev.clientX - r.left) / st.S, (ev.clientY - r.top) / st.S];
  let dragRaf = 0, dragSample = null;
  offs.push(on(wrap, 'pointerdown', '*', (ev) => {
    if (ev.button !== 0) return;
    const hEl = ev.target.closest('.se-h');
    const rect = wrap.getBoundingClientRect();
    const [px, py] = toStage(ev, rect);
    if (hEl && cur()) {
      st.drag = { mode: hEl.dataset.h, px, py, rect, e0: JSON.parse(JSON.stringify(cur())), before: snapshot() };
    } else {
      const el = ev.target.closest('#se-stage .el');
      if (!el) { if (st.sel >= 0 || st.bg) select(-1); return; }
      const i = +el.dataset.idx;
      if (i !== st.sel) select(i);
      if (isLocked(items()[i])) { st.pressed = { x: ev.clientX, y: ev.clientY, told: false }; return; }
      st.drag = { mode: 'move', px, py, rect, e0: JSON.parse(JSON.stringify(items()[i])), before: snapshot() };
    }
    if (st.drag.mode === 'move' || st.drag.mode === 'rot') {   // its own layer while it travels
      st.drag.el = stage.querySelector(`.el[data-idx="${st.sel}"]`);
      if (st.drag.el) st.drag.el.style.willChange = 'transform';
    }
    wrap.setPointerCapture(ev.pointerId);
    ev.preventDefault();
  }));
  const lockedToast = () => toast('Закріплено — зніміть замок у шарах (або вгорі праворуч), щоб рухати мишкою', 'info', 2600);
  function applyDrag(sample) {
    const d = st.drag, e = cur();
    if (!d || !e) return;
    const e0 = d.e0;
    const [px, py] = toStage(sample, d.rect);
    if (d.mode === 'move') {
      e.x = Math.round((e0.x + px - d.px) * 10) / 10; e.y = Math.round((e0.y + py - d.py) * 10) / 10;
      // the element stays where it was drawn (left/top); only a compositor `translate` carries it
      if (d.el) d.el.style.translate = `${e.x - e0.x}px ${e.y - e0.y}px`; else place(st.sel);
      drawSel(); return;
    }
    if (d.mode === 'rot') {
      let a = Math.atan2(py - e0.y, px - e0.x) * 180 / Math.PI + 90;
      a = sample.shiftKey ? Math.round(a / 15) * 15 : Math.round(a * 10) / 10;
      if (a > 180) a -= 360;
      e.rot = a;
      if (d.el) { d.el.style.transform = elTransform(e); drawSel(); } else place(st.sel);
      return;
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
  }
  const onMove = (ev) => {
    const p0 = st.pressed;
    if (p0 && !p0.told && ev.buttons && Math.hypot(ev.clientX - p0.x, ev.clientY - p0.y) > 6) { p0.told = true; lockedToast(); }
    if (!st.drag) return;
    dragSample = { clientX: ev.clientX, clientY: ev.clientY, shiftKey: ev.shiftKey };
    if (!dragRaf) dragRaf = requestAnimationFrame(() => { dragRaf = 0; if (st.drag && dragSample) applyDrag(dragSample); });
  };
  const endDrag = () => {
    if (dragRaf) { cancelAnimationFrame(dragRaf); dragRaf = 0; }
    const d = st.drag;
    if (d?.el) d.el.style.willChange = '';
    return d;
  };
  const onUp = (ev) => {
    st.pressed = null;
    if (!st.drag) return;
    if (dragRaf) applyDrag({ clientX: ev.clientX, clientY: ev.clientY, shiftKey: ev.shiftKey });   // the frame not yet drawn
    const d = endDrag();
    dragSample = null;
    st.drag = null;
    if (d.mode === 'move' || d.mode === 'rot') place(st.sel);   // the real position replaces the carrying translate
    commit(d.before);
    drawProps();
  };
  const onCancel = () => {   // the system took the pointer: the element goes back as it was
    st.pressed = null;
    if (!st.drag) return;
    const d = endDrag();
    dragSample = null;
    st.drag = null;
    if (items()[st.sel]) { items()[st.sel] = d.e0; redrawOne(st.sel); }
    drawProps();
  };
  wrap.addEventListener('pointermove', onMove);
  wrap.addEventListener('pointerup', onUp);
  wrap.addEventListener('pointercancel', onCancel);

  // ---------------------------------------------------------------- the panels' events
  function change(fn, { redraw = true, props = false } = {}) {
    const before = snapshot();
    fn();
    if (redraw === 'place') place(st.sel); else if (redraw) redrawOne(st.sel);
    if (props) queueProps();
    commit(before);
  }
  function duplicate() {
    const e = cur();
    if (!e) return;
    const before = snapshot();
    const c = JSON.parse(JSON.stringify(e));
    c.x += 20; c.y += 20; c.name = `${e.name || KIND[e.type][0]} (копія)`; c.uid = Date.now() % 100000; c.locked = false;
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
    const e = { type, name: `${kind} ${count}`, x: 500, y: 500, rot: 0, uid: Date.now() % 100000, locked: false, ...NEW[type]() };
    const at = st.sel >= 0 ? st.sel + 1 : items().length;
    items().splice(at, 0, e);
    st.sel = at;
    redrawAll(); commit(before);
  }

  offs.push(on(view, 'click', '[data-act], .se-layer', async (ev, t) => {
    const a = t.dataset.act;
    if (!a && t.classList.contains('se-layer')) { select(t.dataset.i === 'bg' ? 'bg' : +t.dataset.i); return; }
    ev.stopPropagation();
    if (a === 'undo') undo();
    else if (a === 'redo') redo();
    else if (a === 'back') { flush(); location.hash = origin && !origin.startsWith('#/slides/') ? origin : '#/tools'; }
    else if (a === 'scheme') openSchemes(t);
    else if (a === 'lock' || a === 'eye') {
      const i = +t.dataset.i, e = items()[i], before = snapshot();
      if (a === 'lock') e.locked = !isLocked(e); else e.hidden = !e.hidden;
      redrawAll(); commit(before);
    } else if (a === 'add') {
      menu(t, ADD_ORDER.map((type) => ({ label: KIND[type][0], icon: KIND[type][1], onClick: () => add(type) })));
    } else if (a === 'flipX' || a === 'flipY') {
      change(() => { cur()[a] = !cur()[a]; }, { redraw: 'place', props: true });
    } else if (a === 'dup') duplicate();
    else if (a === 'del') remove();
    else if (a === 'swatch') {
      change(() => { cur()[t.dataset.k || 'color'] = t.dataset.c; }, { props: true });
    } else if (a === 'bg') {
      const before = snapshot();
      scene.bg = t.dataset.c;
      stage.style.background = scene.bg;
      drawProps(); drawLayers(); commit(before);
    } else if (a === 'pick-picture') pickPicture(t.dataset.slot);
    else if (a === 'reset') {
      // Back to how this slide was when the editor was opened; Ctrl+Z undoes it, so no question (and nothing older than the session).
      const start = session[slide];
      if (!start || start === snapshot()) { toast('З моменту відкриття редактора цей слайд не змінювали', 'info'); return; }
      st.past.push(snapshot()); st.future = [];
      scene = JSON.parse(start); st.sel = -1;
      redrawAll(); save(); paintSaved('ok', 'Повернуто');
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
  let liveRaf = 0;
  function queueRedraw() {   // a slider fires faster than frames: the element is drawn once per frame
    if (!liveRaf) liveRaf = requestAnimationFrame(() => { liveRaf = 0; if (!gone && cur()) redrawOne(st.sel); });
  }
  offs.push(on(view, 'input', '#se-props [data-kind]', (ev, t) => {
    const kind = t.dataset.kind, e = cur();
    if (kind === 'range' || kind === 'color') {
      if (!st.live) st.live = snapshot();
      const v = kind === 'range' ? +t.value : t.value;
      if (e) {
        e[t.dataset.k] = v;
        queueRedraw();
      } else if (kind === 'color') { scene.bg = v; stage.style.background = v; view.querySelector('.se-bg-chip')?.style.setProperty('--c', v); }
      const twin = t.parentElement.querySelector(`input[data-kind="num"][data-k="${t.dataset.k}"]`);
      if (twin) twin.value = +(+v).toFixed(2);
      if (kind === 'color') t.closest('.se-pick')?.style.setProperty('--c', v);
    }
  }));
  offs.push(on(view, 'change', '#se-props [data-kind]', (ev, t) => {
    const kind = t.dataset.kind, e = cur();
    if (kind === 'range' || kind === 'color') {
      if (liveRaf) { cancelAnimationFrame(liveRaf); liveRaf = 0; if (e) redrawOne(st.sel); }
      const before = st.live || snapshot();
      st.live = null;
      commit(before);
      drawProps();
      return;
    }
    if (kind === 'bg') { const before = snapshot(); scene.bg = t.value; stage.style.background = t.value; commit(before); drawProps(); drawLayers(); return; }
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
    if (kind === 'caption') { change(() => { if (t.value.trim()) e.labelText = t.value; else delete e.labelText; }); drawSel(); return; }
    if (kind === 'lines') {
      change(() => {
        e.lines = t.value.split('\n').map((s) => s.trim()).filter(Boolean).map((s, i) => ({ ...(e.lines[i] || {}), t: s }));
      });
      return;
    }
    if (kind === 'slot') { change(() => { e.slot = t.value; }, { props: true }); drawSel(); }
  }));

  // The schemes (the owner, 29.09.2026: "a colour scheme you can save while working in the editor… not only the
  // colours but the settings of the whole mockup"): Nature, Night, his own, and the other Workshop books' slides.
  async function openSchemes(anchor) {
    let r;
    try { r = await api(`/api/slides/presets?w=${encodeURIComponent(where)}`); } catch (err) { toast(err.message, 'error'); return; }
    if (gone) return;
    const schemes = r.presets.filter((x) => x.kind === 'scheme'), books = r.presets.filter((x) => x.kind === 'book');
    const current = schemes.find((x) => x.key === r.current);
    if (!isSet) {   // on its own: pick which scheme is edited here — Nature, Night, his own (2026-09-30)
      menu(anchor, [
        ...schemes.map((x) => ({ label: `${x.name}${x.default ? ' · для нових книг' : ''}`, icon: 'template', on: x.key === r.current,
          onClick: () => { flush(); location.hash = `#/slides/${x.default ? 'template' : `scheme:${x.key}`}/${n}`; } })),
        '-',
        { label: 'Зберегти ці слайди як схему…', icon: 'download', onClick: () => saveScheme(current, schemes) },
        ...(current && !current.default ? [{ label: `Нові книги — зі схеми «${current.name}»`, icon: 'check', onClick: () => makeDefault(current).then(() => { location.hash = `#/slides/template/${n}`; }) }] : []),
      ]);
      return;
    }
    menu(anchor, [
      ...schemes.map((x) => ({ label: `${x.name}${x.default ? ' · для нових книг' : ''}`, icon: 'template', on: x.key === r.current, onClick: () => applyScheme(x) })),
      ...(books.length ? ['-', ...books.map((x) => ({ label: x.name, icon: 'book', on: x.key === r.current, onClick: () => applyScheme(x) }))] : []),
      '-',
      { label: 'Зберегти ці слайди як схему…', icon: 'download', onClick: () => saveScheme(current, schemes) },
      ...(current && !current.default ? [{ label: `Нові книги — зі схеми «${current.name}»`, icon: 'check', onClick: () => makeDefault(current) }] : []),
    ]);
  }
  async function applyScheme(x) {
    const ok = await confirmBox({ title: `Накласти «${x.name}»?`, text: 'Усі шість слайдів цієї книги стануть як у ній — кольори, розташування, тексти. Мокапи й числа книги лишаться свої. Скасувати можна лише так: накласти іншу схему.', confirm: 'Накласти' });
    if (!ok || gone) return;
    await flush();
    try {
      await post('/api/slides/apply', { w: where, key: x.key });
      const [{ scene: fresh, version: v }, i] = await Promise.all([api(q('/api/slides/scene')), api(`/api/slides/state?w=${encodeURIComponent(where)}`)]);
      if (gone) return;
      info = i; scene = fresh; version = v; st.sel = -1; st.bg = false; st.past = []; st.future = [];
      const btn = $('#se-scheme .truncate');
      if (btn) btn.textContent = schemeLabel();
      redrawAll(); fadeStage(); loadOthers();
      paintSaved('ok', `Схема «${x.name}»`);
    } catch (err) { toast(err.message, 'error'); }
  }
  function saveScheme(current, schemes) {
    const m = modal({
      title: 'Зберегти як схему',
      sub: 'Усі шість слайдів — кольори, розташування, тіні, тексти. Та сама назва — та схема оновиться.',
      body: html`<div class="stack">
        <label class="field"><span class="field-label">Назва</span><input class="input" data-name value="${current?.name || ''}" placeholder="напр. Night" autofocus spellcheck="false"></label>
        ${schemes.length ? html`<div class="se-scheme-names">${schemes.map((x) => html`<button type="button" class="chip" data-use="${x.name}">${x.name}</button>`)}</div>` : ''}
        <label class="check"><input type="checkbox" data-default><span>Нові книги починаються з цієї схеми</span></label>
      </div>`,
      foot: html`<button class="btn btn-ghost" data-no>Скасувати</button><button class="btn btn-primary" data-yes>${ic('download', 'icon-s')}Зберегти</button>`,
    });
    const input = m.el.querySelector('[data-name]');
    m.el.querySelectorAll('[data-use]').forEach((b) => { b.onclick = () => { input.value = b.dataset.use; input.focus(); }; });
    m.foot.querySelector('[data-no]').onclick = () => m.close();
    const go = async () => {
      const name = input.value.trim();
      if (!name) { input.focus(); toast('Назвіть схему', 'info'); return; }
      await flush();
      try {
        const r = await post('/api/slides/save-scheme', { w: where, name, default: m.el.querySelector('[data-default]').checked });
        m.close();
        toast(`Схему «${r.name}» збережено`, 'success');
      } catch (err) { toast(err.message, 'error'); }
    };
    m.foot.querySelector('[data-yes]').onclick = go;
    input.addEventListener('keydown', (ev) => { if (ev.key === 'Enter') go(); });
  }
  async function makeDefault(x) {
    try { await post('/api/slides/default-scheme', { key: x.key }); toast(`Нові книги почнуться зі схеми «${x.name}»`, 'success'); }
    catch (err) { toast(err.message, 'error'); }
  }

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
    paintSaved('busy', 'Малюю…', 0);
    tellBusy({ mockups: true });
    try {
      const res = await runJob(post('/api/slides/bake', { w: where }), (job) => { if (!gone) paintSaved('busy', job.step || 'Малюю…', job.percent); }, 500, () => !gone);
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
    if (dragFrom === null || t.dataset.i === 'bg') return;
    ev.preventDefault();
    const r = t.getBoundingClientRect(), above = ev.clientY < r.top + r.height / 2;
    view.querySelectorAll('.drop-above,.drop-below').forEach((x) => x.classList.remove('drop-above', 'drop-below'));
    t.classList.add(above ? 'drop-above' : 'drop-below');
  }));
  offs.push(on(view, 'drop', '.se-layer', (ev, t) => {
    if (dragFrom === null || t.dataset.i === 'bg') return;
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
    if (ev.key === 'Escape' && st.bg) { ev.preventDefault(); select(-1); return; }
    if (!e) return;
    if (ev.key === 'Delete' || ev.key === 'Backspace') { ev.preventDefault(); remove(); return; }
    if (ev.key === 'Escape') { ev.preventDefault(); select(-1); return; }
    const step = ev.shiftKey ? 10 : 1;
    const mv = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }[ev.key];
    if ((mv || ev.key === '[' || ev.key === ']') && isLocked(e)) { ev.preventDefault(); lockedToast(); return; }
    if (mv) { ev.preventDefault(); change(() => { e.x += mv[0]; e.y += mv[1]; }, { redraw: 'place', props: true }); return; }
    if (ev.key === '[' || ev.key === ']') {
      change(() => { e.rot = Math.round(((e.rot || 0) + (ev.key === ']' ? 1 : -1) * (ev.shiftKey ? 5 : 0.5)) * 10) / 10; }, { redraw: 'place', props: true });
    }
  };
  document.addEventListener('keydown', onKey);
  // back from another window (the agent's): asked at once, not in 1.5 s
  const onVisible = () => { if (document.visibilityState === 'visible') { stir(); watch(); } };
  document.addEventListener('visibilitychange', onVisible);

  redrawAll();
  fit();
  loadOthers();
  paintSaved('ok', version ? 'Збережено' : isSet ? 'Як у схемі' : 'Як намальовано спершу');
  sigTimer = setTimeout(watch, SIG_EVERY);

  return {
    // A book's slides are that book's: the rail stays on «Книги»; a scheme or an older set is the tool's (2026-09-30).
    navFor: () => (/^\d{1,5}\./.test(whereParam) ? '#/books' : null),
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
      wrap.removeEventListener('pointercancel', onCancel);
      cancelAnimationFrame(dragRaf); cancelAnimationFrame(propsRaf); cancelAnimationFrame(liveRaf);
      offs.forEach((off) => off());
    },
  };
}
