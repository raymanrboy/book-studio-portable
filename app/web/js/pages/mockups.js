// Listing mockups: the demo book's Canva ZIP comes in, the presentable spreads are picked, and one Photoshop
// script fills the owner's templates — pages, back cover and spine everywhere; the front cover he fits himself in
// the three templates left open, and «Зберегти відкриті» saves those too (wiki/features/mockups.md).
// Laid out like Book Studio's Order Creator: numbered steps on the left, the book's structure on the right — the
// demo book comes in there (a drop or a click; its own step «Демо-книга з Canva» doubled it and went, 29.09.2026).
// A page of the Listings mode (#/mockups; until 24.09.2026 a window of its own). It is kept when the owner steps
// away (keep()): the book, the picks and a run going on in Photoshop wait for him; a small dot on the rail says a
// run is on, and a notice says when it ends.
import {
  api, post, html, ic, ib, setHtml, el, on, media, toast, runJob, fadeImages, plural, modal, confirmBox, remembered,
  remember, setProgress, patch, tellBusy, backToTools,
} from '../lib.js';
import { openLightbox } from '../lightbox.js';
import { store } from '../info.js';
import { receiveDrop, dropLabel, wireFolderDrop } from '../drop.js';
import { take } from '../handoff.js';
import { PICTURES, runView, rowsHtml, resultCard, turnCard, finishedCard } from './mockups-run.js';
import { slidesStep } from './mockups-slides.js';

const THUMB_H = 360;          // a spread tile (two 180-px pages side by side)
const SLOT_H = 120;           // a spread in a template slot
const TPL_W = 320;            // a template's own preview beside its slots
const BIG = 1400, SHARP = 2600;  // the viewer: the preview sizes every page already keeps (images._LARGER)
const PICKS_KEY = 'mk-picks'; // the last picks per book: dropped in again, a book gets them back
const TYPE_SPREAD = 'application/x-mk-spread';
const TYPE_SLOT = 'application/x-mk-slot';
const SPREADS = ['розворот', 'розвороти', 'розворотів'];
const TEMPLATES = ['шаблон', 'шаблони', 'шаблонів'];
const busy = (on) => tellBusy({ mockups: on }); // the rail's dot
const FOR_BOOK = 'mk-for-book';   // the Workshop's «Мокапи» step: {id} — the book the next mockups are for
const LAST_BOOK = 'mk-last-book';

export async function mount(view) {
  const st = {
    meta: await api('/api/mockups/state'),
    book: null,         // {id, name, pageCount, cover: [w, h], spreads}
    label: '',          // what the book came as: the ZIP's or the dropped folder's name
    picks: {},          // template key -> [first page of the spread | null, …]
    active: null,       // {key, i} — the slot the next clicked spread goes into
    receiving: null,    // 'ask' — the Windows dialog is open, 'unzip', or the percent of a dropped ZIP
    bookError: '',
    out: '',            // another folder the pictures go to (picked by hand: «Інша папка…»)
    workshop: null,     // the Workshop book the mockups go into — its own folder, no question (29.09.2026)
    asking: false,      // the Windows "where to save" dialog is open
    run: null,          // {mode: make|finish, phase: prepare|ask|work, step, percent, rows}
    result: null,       // the last run: {saved, open, run, folder, seconds, problems, job}
    finished: null,     // «Зберегти відкриті»: {saved, cleaned, folder, problems, job}
    pending: null,      // {run, folder, open} — templates still waiting in Photoshop for the front cover
    runError: '',
  };
  st.pending = st.meta.pending || null;
  const bookById = (id) => (st.meta.books || []).find((b) => b.id === id) || null;
  // The Workshop's «Мокапи» step sends its book here (remember(FOR_BOOK) — a kept page takes it on revive()).
  // A book is the destination only when the owner asked for one — from the Workshop's step, or with the small book icon of
  // «Куди зберегти» (`force`); on its own the page asks for a folder when it runs (2026-09-30: it used to pick the last or the
  // first Workshop book by itself, so a standalone run could fill some book's folder).
  function takeWorkshopBook(force = false) {
    const asked = remembered(FOR_BOOK, null);
    if (asked) remember(FOR_BOOK, null);
    const pick = (asked && bookById(asked.id)) || (force && !st.workshop && !st.out
      && (bookById(remembered(LAST_BOOK, '')) || (st.meta.books || [])[0])) || null;
    if (!pick || (asked && st.run)) return false;
    const changed = st.workshop?.id !== pick.id;
    st.workshop = pick; st.out = '';
    remember(LAST_BOOK, pick.id);
    return changed && !!asked;
  }
  takeWorkshopBook();
  // Opened from a Workshop book (its «Мокапи» step): the page is that book's step — the book in its head, the way
  // back to it, the rail on «Книги». From «Інструменти» it is the tool on its own (2026-09-30).
  let fromBook = null;
  const arrived = () => {
    const m = /^#\/workshop\/([^/]+)$/.exec(store.here || '');
    fromBook = m && st.workshop && decodeURIComponent(m[1]) === st.workshop.id ? st.workshop : null;
    paintBack();
  };
  function paintBack() {
    const back = $('#mk-back'), sub = $('#mk-sub');
    if (!back || !sub) return;
    setHtml(back, fromBook ? html`<a class="back-link" href="#/workshop/${encodeURIComponent(fromBook.id)}" aria-label="До книги" data-tip="До книги">${ic('arrowLeft')}</a>` : backToTools());
    setHtml(sub, fromBook ? html`Для книги <b>${fromBook.name}</b> · демо-книга з Canva → картинки для лістингу` : 'Демо-книга з Canva → картинки для лістингу Etsy');
  }
  let gone = false;
  const offs = [];
  const $ = (sel) => view.querySelector(sel);
  const slotted = () => st.meta.templates.filter((t) => t.slots > 0);
  const tpl = (key) => st.meta.templates.find((t) => t.key === key);
  const src = (what, params) => media(`/media/mockups/${st.book.id}/${what}`, params);
  const pages = (n) => `${n}–${n + 1}`;
  const bookName = () => (st.book.name === 'Файли' ? '' : st.book.name); // loose pictures have no name of their own
  const folderName = (p) => String(p).split(/[\\/]/).filter(Boolean).pop() || String(p);
  const stepNo = (n, done) => html`<span class="step-no ${done ? 'done' : ''}">${done ? ic('check') : n}</span>`;

  // ---------------------------------------------------------------- the picks
  function resetPicks(from = null) {
    st.picks = from || Object.fromEntries(slotted().map((t) => [t.key, Array(t.slots).fill(null)]));
    st.active = firstEmpty();
  }
  function slotsInOrder() { return slotted().flatMap((t) => st.picks[t.key].map((_, i) => ({ key: t.key, i }))); }
  function firstEmpty(after = null) {
    const all = slotsInOrder();
    const from = after ? all.findIndex((s) => s.key === after.key && s.i === after.i) + 1 : 0;
    return [...all.slice(from), ...all.slice(0, from)].find((s) => st.picks[s.key][s.i] === null) || null;
  }
  const missing = () => slotsInOrder().filter((s) => st.picks[s.key][s.i] === null).length;
  const isActive = (key, i) => st.active?.key === key && st.active?.i === i;
  const slotName = (s) => `${tpl(s.key).label}${tpl(s.key).slots > 1 ? ` · ${s.i + 1}` : ''}`;

  const memKey = () => `${st.book.name}|${st.book.pageCount}`;
  function rememberPicks() {
    const all = remembered(PICKS_KEY, {});
    delete all[memKey()];
    all[memKey()] = st.picks;
    Object.keys(all).slice(0, -12).forEach((k) => delete all[k]); // the last dozen books
    remember(PICKS_KEY, all);
  }
  function recallPicks() {
    try {
      const p = remembered(PICKS_KEY, {})[memKey()];
      const starts = new Set(st.book.spreads.map(([n]) => n));
      const fits = p && slotted().every((t) => Array.isArray(p[t.key]) && p[t.key].length === t.slots
        && p[t.key].every((n) => n === null || starts.has(n)));
      return fits && Object.values(p).flat().some((n) => n !== null)
        ? Object.fromEntries(slotted().map((t) => [t.key, [...p[t.key]]])) : null;
    } catch { return null; }
  }

  // ---------------------------------------------------------------- the whole page
  function render() {
    setHtml(view, html`<div class="mk" data-folder-drop>
      <header class="page-head">
        <span id="mk-back"></span>
        <div class="grow">
          <h1 class="page-title">Мокапи</h1>
          <div class="page-sub" id="mk-sub">Демо-книга з Canva → картинки для лістингу Etsy</div>
        </div>
        <div class="page-actions" id="mk-actions"></div>
      </header>
      <div id="mk-lost"></div>
      <div class="creator-grid mk-layout">
        <div class="stack mk-steps">
          <section class="card card-pad stack" id="mk-s2"></section>
          <section class="card card-pad stack" id="mk-s3"></section>
          <section class="card card-pad stack" id="mk-s4"></section>
          <section class="card card-pad stack" id="mk-s5" hidden></section>
        </div>
        <section class="card card-pad stack-l mk-structure" id="mk-right"></section>
      </div>
    </div>`);
    paintAll();
  }
  // Every part painted again in its place — the page itself stays (a book taken used to rebuild it, and all six
  // templates' pictures faded in again, 26.09.2026).
  function paintAll() {
    paintHead(); paintLost(); paintTemplates(); paintOut(); paintAction(); paintStructure(); slides.paint();
  }

  // The header: where the templates and Photoshop are; «×» — this book is done, the page starts clean (the owner,
  // 26.09.2026: "a cross on the Mockups page, to finish the creation"), as the order card's × finishes an order.
  const something = () => !!(st.book || st.result || st.finished || st.pending || st.runError || st.bookError);
  function paintHead() {
    const box = $('#mk-actions');
    if (!box) return;
    setHtml(box, html`<div class="tools">${ib('sliders', 'Де шаблони і Photoshop', 'data-act="places"')}
      ${something() ? html`<span class="sep"></span>${ib('checkCircle', 'Завершити — наступна книга з чистого аркуша', 'data-act="close"')}` : ''}</div>`);
  }

  async function finishPage() {
    if (st.run || st.asking || st.receiving !== null) {
      toast(st.run ? 'Photoshop ще працює — дочекайтесь або зупиніть його (× у кроці 3)' : 'Зачекайте хвилинку — вікно Windows ще відкрите', 'info');
      return;
    }
    if (st.pending) {
      const ok = await confirmBox({
        title: 'Завершити без «Зберегти відкриті»?',
        text: `У Photoshop чекають: ${st.pending.open.join(', ')}. Вони лишаться відкритими — збережіть їх самі, як звикли; Book Studio більше не пропонуватиме їх зберегти.`,
        confirm: 'Завершити',
      });
      if (!ok || gone) return;
    }
    try {
      await post('/api/mockups/close', { run: st.pending?.run || '' });
    } catch (err) { toast(err.message, 'error'); return; }
    if (gone) return;
    Object.assign(st, { book: null, label: '', receiving: null, bookError: '', asking: false, run: null,
      result: null, finished: null, pending: null, runError: '' });
    slides.reset();
    resetPicks();
    paintAll();
    toast('Мокапи завершено — можна брати наступну книгу', 'success');
  }

  function paintLost() {
    const m = st.meta;
    const absent = m.templates.filter((t) => !t.found).map((t) => t.file);
    const lost = [
      !m.templatesFound || absent.length
        ? { what: 'templates', text: m.templatesFound ? `У папці з трафаретами немає: ${absent.join(', ')}` : `Не знайшов папку з трафаретами: ${m.templatesDir}` } : null,
      !m.photoshopFound ? { what: 'photoshop', text: `Не знайшов Photoshop у ${m.photoshopDir}` } : null,
    ].filter(Boolean);
    setHtml($('#mk-lost'), lost.map((x) => html`<div class="notice notice-warn mk-lost">${ic('alert')}<div class="grow">${x.text}</div>
      ${ib('folderPick', x.what === 'templates' ? 'Вказати папку з трафаретами' : 'Вказати папку з Photoshop', `data-act="place" data-what="${x.what}"`, { cls: 'sm' })}</div>`));
  }

  // ---------------------------------------------------------------- the demo book's state, in the structure's header
  // Another book coming in while one is shown (a drop, or the folder button there): a badge; a book that couldn't be
  // read: a line under the header.
  function paintBookState() {
    const box = $('#mk-book-state');
    if (!box) return;
    const spin = html`<span class="spinner"></span>`;
    let badge = '';
    if (st.receiving === 'ask') badge = html`<span class="v-badge run">${spin}Вікно Windows</span>`;
    else if (st.receiving === 'unzip') badge = html`<span class="v-badge run">${spin}Розпаковую</span>`;
    else if (st.receiving !== null) badge = html`<span class="v-badge run">${spin}<span class="num">${Math.round(st.receiving)}%</span></span>`;
    setHtml(box, badge);
    const err = $('#mk-book-error');
    if (err) setHtml(err, st.bookError ? html`<div class="notice notice-error">${ic('alertCircle')}<div>${st.bookError}</div></div>` : '');
  }

  // ---------------------------------------------------------------- 1 · spreads in the templates
  function paintTemplates() {
    const box = $('#mk-s2');
    if (!box.querySelector('.mk-tpls')) {
      setHtml(box, html`<div class="row" id="mk-s2-head"></div>
        <div class="mk-hint" id="mk-hint" hidden></div>
        <div class="mk-tpls"></div>`);
    }
    // The templates in place (patch()): a row whose markup didn't change keeps its picture and its slots.
    patch(box.querySelector('.mk-tpls'), st.meta.templates.map((tp) => [tp.key, tplRow(tp)])).forEach((row) => {
      row.querySelectorAll('.mk-tpl-pic img').forEach((img) => img.addEventListener('error', () => img.parentElement.classList.add('none'), { once: true }));
    });
    fadeImages(box);
    paintPicks();
  }

  function tplRow(t) {
    const auto = t.slots === 0;
    const note = !t.found ? html`<span class="mk-note bad">немає файлу</span>`
      : auto ? html`<span class="mk-note">${t.key === 'cover1' ? 'обкладинка' : 'сторінка 1'} · сама</span>`
        : html`<span class="mk-count num" data-count="${t.key}"></span>`;
    return html`<div class="mk-tpl" data-tpl="${t.key}">
      <button type="button" class="mk-tpl-pic ${t.found ? '' : 'none'}" data-act="tpl-view" data-key="${t.key}" aria-label="Роздивитися шаблон ${t.label}" data-tip="${t.file}">
        ${t.found ? html`<img data-fade alt="" draggable="false" src="${media(`/media/mockups/template/${t.key}`, { w: TPL_W })}">` : ''}${ic('image')}
      </button>
      <div class="mk-tpl-main">
        <div class="mk-tpl-head"><span class="mk-tpl-name">${t.label}</span>${t.hand || t.keep ? handMark(t) : ''}<span class="spacer"></span>${note}</div>
        <div class="mk-slots" data-slots="${t.key}">${auto ? autoSlot(t) : ''}</div>
      </div>
    </div>`;
  }

  // ✋ — the owner's own touch, so the template stays open in Photoshop: the front cover, or Dedication's colours.
  const yours = (t) => (t.keep === 'colours' ? 'колір фону й столу обираєте ви' : 'лицьову обкладинку підганяєте ви');
  function handMark(t) {
    return html`<span class="mk-hand" data-tip="${yours(t).replace(/^./, (c) => c.toUpperCase())}: шаблон лишиться відкритим у Photoshop">${ic('hand', 'icon-s')}</span>`;
  }

  function autoSlot(t) {
    if (!st.book) return html`<div class="mk-slot mk-still"></div>`;
    return t.key === 'cover1'
      ? html`<div class="mk-slot filled mk-still"><img data-fade alt="" draggable="false" src="${src('cover', { w: 480 })}"></div>`
      : html`<div class="mk-slot filled mk-still"><span class="mk-half"></span><img data-fade alt="" draggable="false" src="${src('page', { n: 1, w: 240 })}"></div>`;
  }

  function slotHtml(t, n, i) {
    const active = isActive(t.key, i) && !st.run;
    if (n === null) {
      return html`<button type="button" class="mk-slot ${active ? 'active' : ''}" data-slot="${t.key}:${i}" data-n=""
        ${st.book && !st.run ? '' : 'disabled'} aria-label="${t.label}, місце ${i + 1}"><span class="num">${i + 1}</span></button>`;
    }
    return html`<div class="mk-slot filled ${active ? 'active' : ''}" data-slot="${t.key}:${i}" data-n="${n}" draggable="true"
        role="button" tabindex="0" aria-label="${t.label}: розворот ${pages(n)}">
      <img data-fade alt="" draggable="false" src="${src('spread', { n, h: SLOT_H })}">
      <span class="mk-slot-no num">${pages(n)}</span>
      ${ib('x', 'Прибрати', `data-act="clear" data-slot="${t.key}:${i}"`, { cls: 'sm mk-clear' })}
    </div>`;
  }

  // The slots are patched one by one: a spread that stays put keeps its picture (no reload, no flicker).
  function paintPicks() {
    const total = slotsInOrder().length, left = missing(), filled = total - left;
    const full = !!st.book && !left;
    setHtml($('#mk-s2-head'), html`${stepNo(1, full)}<h3 class="card-title grow">Розвороти в шаблонах</h3>
      ${filled && !st.run ? ib('eraser', 'Прибрати всі розвороти', 'data-act="clear-all"', { cls: 'sm' }) : ''}
      <span class="v-badge ${full ? 'ok' : ''}" data-tip="Заповнено місць у шаблонах">${full ? ic('check') : ''}<span class="num">${filled}/${total}</span></span>`);
    const hint = $('#mk-hint');
    hint.hidden = !(st.book && left && !st.run);
    setHtml(hint, html`${ic('info', 'icon-s')}<span>Клацайте розвороти справа — вони стають у шаблони по черзі. Можна й перетягнути розворот на потрібне місце.</span>`);
    for (const t of slotted()) {
      const box = view.querySelector(`[data-slots="${t.key}"]`);
      if (!box) continue;
      const row = st.picks[t.key];
      if (box.children.length !== row.length) setHtml(box, row.map((n, i) => slotHtml(t, n, i)));
      else {
        row.forEach((n, i) => {
          const old = box.children[i];
          if (old.dataset.n !== String(n ?? '') || (n === null && old.disabled !== !(st.book && !st.run))) {
            box.replaceChild(el(slotHtml(t, n, i)), old);
          } else old.classList.toggle('active', isActive(t.key, i) && !st.run);
        });
      }
      fadeImages(box);
      const count = view.querySelector(`[data-count="${t.key}"]`);
      if (count) count.textContent = t.slots > 1 ? `${row.filter((n) => n !== null).length}/${t.slots}` : '';
    }
  }

  // ---------------------------------------------------------------- 2 · where the pictures go
  function paintOut() {
    const last = st.meta.lastOut;
    const books = st.meta.books || [];
    if (!st.out && st.workshop) {   // the Workshop book — its own folder «mockups», nothing asked
      setHtml($('#mk-s3'), html`
        <div class="row">${stepNo(2, !!st.workshop)}<h3 class="card-title grow">Книга</h3>
          ${st.workshop ? ib('folderOpen', 'Відкрити папку мокапів цієї книги', 'data-act="open-book-mockups"', { cls: 'sm' }) : ''}</div>
        <select class="select" id="mk-workshop" aria-label="Книга з Майстерні" ${st.run ? 'disabled' : ''}>
          ${books.map((b) => html`<option value="${b.id}" ${b.id === st.workshop?.id ? 'selected' : ''}>${b.name}</option>`)}</select>
        <div class="mk-foot">Мокапи й вирізані без фону ляжуть у папку книги <b>mockups</b>, слайди — у <b>etsy</b>. Нічого не перезаписується.
          <button type="button" class="btn btn-xs btn-ghost mk-other" data-act="pick-out">Інша папка…</button></div>`);
      return;
    }
    setHtml($('#mk-s3'), html`
      <div class="row">${stepNo(2, !!st.out)}<h3 class="card-title grow">Куди зберегти</h3>
        ${books.length && !st.run ? ib('book', 'Назад до книги з Майстерні', 'data-act="to-book"', { cls: 'sm' }) : ''}
        ${st.asking ? html`<span class="v-badge run"><span class="spinner"></span>Вікно Windows</span>` : ''}</div>
      <div class="input-group">
        <input class="input path-input mk-path" id="mk-out" readonly value="${st.out}" title="${st.out}" data-act="pick-out"
          placeholder="Папку ще не вибрано" aria-label="Папка для картинок" spellcheck="false">
        ${ib('folderPick', 'Обрати папку', 'data-act="pick-out"')}
      </div>
      ${!st.out && last && !st.asking ? html`<button type="button" class="btn btn-sm btn-ghost mk-last" data-act="same-out" data-tip="${last}">
        ${ic('folderOpen', 'icon-s')}<span class="truncate">Та сама, що минулого разу · ${folderName(last)}</span></button>` : ''}
      ${st.out ? html`<div class="mk-foot">Наявні картинки з такою самою назвою не перезаписуються — нові отримають « (2)».</div>` : ''}`);
  }

  // ---------------------------------------------------------------- 3 · Photoshop: the button, the run, the results
  function paintAction() {
    const box = $('#mk-s4');
    if (!box) return;
    const head = html`<div class="row">${stepNo(3, !!st.result && !st.run && !st.result.cancelled)}<h3 class="card-title grow">Photoshop</h3>
      ${st.run ? ib('x', 'Зупинити', 'data-act="stop"', { cls: 'sm' }) : ''}</div>`;
    if (st.asking) {
      setHtml(box, html`${head}<div class="mk-waiting"><span class="spinner"></span><span>Оберіть папку у вікні Windows «Куди зберегти мокапи»</span></div>`);
      return;
    }
    if (st.run) {
      setHtml(box, html`${head}${runView(st.run)}`);
      return;
    }
    setHtml(box, html`${head}<div class="stack" id="mk-make"></div>
      ${st.runError ? html`<div class="notice notice-error">${ic('alertCircle')}<div>${st.runError}</div></div>` : ''}
      ${st.result ? resultCard(st.result) : ''}
      ${st.pending ? turnCard(st.pending) : ''}
      ${st.finished ? finishedCard(st.finished) : ''}`);
    paintMake();
    fadeImages(box);
  }

  function paintMake() {
    const box = $('#mk-make');
    if (!box) return;
    const m = st.meta;
    const saves = m.templates.filter((t) => !t.hand && !t.keep).reduce((sum, t) => sum + t.slots, 0);
    const hands = m.templates.filter((t) => t.hand || t.keep).length;
    const ready = m.templatesFound && m.photoshopFound && m.templates.every((t) => t.found);
    const left = st.book ? missing() : 0;
    const need = !st.book ? 'Ще: демо-книга' : left ? `Ще ${left} ${plural(left, SPREADS)}` : '';
    setHtml(box, html`
      <div class="mk-plan">
        <span class="chip" data-tip="Photoshop сам збереже ${saves} ${plural(saves, PICTURES)}">${ic('image', 'icon-s')}<b class="num">${saves}</b></span>
        <span class="chip" data-tip="${hands} ${plural(hands, TEMPLATES)} Photoshop залишить відкритими — лицьову обкладинку й кольори Dedication підганяєте ви">${ic('hand', 'icon-s')}<b class="num">${hands}</b></span></div>
      <button type="button" class="btn btn-primary btn-block mk-make ${need ? 'waiting' : ''}" data-act="make" ${st.book && !st.out && !st.workshop ? 'data-tip="Папку для результату спитаю, коли натиснете"' : ''} ${ready ? '' : 'disabled'} ${need ? 'aria-disabled="true" aria-describedby="mk-left"' : ''}>${ic('mockup')}Зробити мокапи</button>
      ${need ? html`<div class="mk-left" id="mk-left">${need}</div>` : ''}`);
  }

  function patchRun() {
    const r = st.run;
    const step = $('#mk-step'), pct = $('#mk-pct'), bar = $('#mk-bar'), rows = $('#mk-rows');
    if (step) step.textContent = r.step;
    if (pct) pct.textContent = `${Math.round(r.percent)}%`;
    setProgress(bar, Math.max(3, r.percent));
    if (rows) setHtml(rows, rowsHtml(r.rows || [], r.mode === 'finish'));
  }

  // ---------------------------------------------------------------- the structure (right)
  function paintStructure() {
    const box = $('#mk-right');
    if (!st.book) {
      const busy = st.receiving !== null;
      const doing = st.receiving === 'ask' ? 'Оберіть архів у вікні Windows'
        : st.receiving === 'unzip' ? 'Розпаковую архів…' : html`Отримую архів… <span class="num">${Math.round(st.receiving || 0)}%</span>`;
      setHtml(box, html`
        <div class="row"><h2 class="card-title grow" style="font-size: var(--fs-l)">Структура</h2><span id="mk-book-state"></span></div>
        <div id="mk-book-error"></div>
        <div class="mk-ghost ${busy ? 'busy' : ''}" data-act="pick-zip" role="button" tabindex="0" aria-label="Обрати ZIP-архів із Canva">
          <div class="mk-ghost-art">
            <div class="mk-top">
              <div class="structure-cover" style="aspect-ratio:1.9"><div class="cover-ph"><div>Задня</div><div>Лицьова</div></div></div>
              <div class="spread-view"><div class="half blank"><span>Форзац</span></div><div class="half"><span class="ph-num">1</span></div><div class="gutter-s"></div></div>
            </div>
            <div class="spread-grid">${[2, 4, 6, 8, 10, 12].map((n) => html`<div class="spread-card"><div class="spread-view"><div class="half"><span class="ph-num">${n}</span></div>
              <div class="half"><span class="ph-num">${n + 1}</span></div><div class="gutter-s"></div></div><div class="spread-card-head"><span class="spread-no">${pages(n)}</span></div></div>`)}</div>
          </div>
          <div class="mk-veil">${busy ? html`<div class="spinner spinner-l"></div><b>${doing}</b>`
            : html`<div class="drop-ico">${ic('upload')}</div><b>Перетягніть сюди ZIP із Canva</b><span>або клацніть, щоб вибрати файл</span>`}</div>
        </div>`);
      paintBookState();
      return;
    }
    const b = st.book;
    setHtml(box, html`
      <div class="row" style="align-items:baseline">
        <h2 class="card-title grow" style="font-size: var(--fs-l)">Структура <span class="faint" style="font-weight:500">· ${bookName() ? html`${bookName()} · ` : ''}<span class="num">${b.pageCount}</span> стор.</span></h2>
        <span class="mk-next" id="mk-next"></span>
        <span id="mk-book-state"></span>
        ${ib('folderPick', 'Інша демо-книга — ZIP із Canva (або перетягніть його сюди)', 'data-act="pick-zip"', { cls: 'sm' })}
      </div>
      <div id="mk-book-error"></div>
      <div class="mk-top">
        <div class="stack-s">
          <div class="row"><span class="eyebrow grow">Обкладинка</span><span class="mk-to">задня й корінець → у шаблони</span></div>
          <div class="structure-cover mk-cover" data-act="cover" style="aspect-ratio:${b.cover ? `${b.cover[0]} / ${b.cover[1]}` : '1.9'}">
            <img data-fade decoding="async" draggable="false" src="${src('cover', { w: BIG })}" alt="Обкладинка">
            <div class="mk-zones" aria-hidden="true"><span>Задня<small>у всі шаблони</small></span><span class="spine"></span><span>Лицьова<small>підганяєте ви</small></span></div>
            <i class="crops"></i>
          </div>
        </div>
        <div class="stack-s">
          <div class="row"><span class="eyebrow grow">Присвята</span><span class="mk-to">→ Dedication</span></div>
          <div class="spread-view mk-fixed" data-act="dedication">
            <div class="half blank"><span>Форзац</span></div>
            <div class="half"><img data-fade decoding="async" draggable="false" src="${src('page', { n: 1, w: 700 })}" alt="Сторінка 1"></div>
            <div class="gutter-s"></div><i class="crops"></i>
          </div>
        </div>
      </div>
      <div class="stack-s">
        <div class="row"><span class="eyebrow grow">Розвороти</span><span class="faint" style="font-size: var(--fs-s)"><span class="num">${b.spreads.length}</span> ${plural(b.spreads.length, SPREADS)}</span></div>
        <div class="spread-grid mk-grid" id="mk-grid">${b.spreads.map(([n]) => spreadTile(n))}</div>
      </div>`);
    fadeImages(box);
    paintBookState();
    paintTiles();
  }

  function spreadTile(n) {
    return html`<div class="spread-card mk-spread" data-spread="${n}" draggable="true" role="button" tabindex="0" aria-label="Розворот ${pages(n)}">
      <div class="mk-art">
        <img data-fade alt="" draggable="false" src="${src('spread', { n, h: THUMB_H })}">
        <i class="gutter-s"></i><span class="crops"></span>
        <span class="img-actions">${ib('zoomIn', 'Роздивитися', `data-act="zoom" data-n="${n}"`)}</span>
        <span class="mk-put"></span>
      </div>
      <div class="spread-card-head"><span class="spread-no">${pages(n)}</span><span class="spacer"></span><span class="mk-uses"></span></div>
    </div>`;
  }

  // Which templates a spread is in, where a click puts it — patched in place, so the pictures never reload.
  function paintTiles() {
    const grid = $('#mk-grid');
    if (!grid) return;
    const uses = {};
    slotted().forEach((t) => st.picks[t.key].forEach((n) => { if (n !== null) (uses[n] ||= new Set()).add(t); }));
    const current = st.active ? st.picks[st.active.key][st.active.i] : null;
    const target = st.active && !st.run ? slotName(st.active) : '';
    grid.querySelectorAll('.mk-spread').forEach((tile) => {
      const n = +tile.dataset.spread;
      tile.classList.toggle('used', !!uses[n]);
      tile.classList.toggle('current', n === current && !st.run);
      setHtml(tile.querySelector('.mk-uses'), [...(uses[n] || [])].map((t) => html`<span class="chip chip-accent">${t.label}${st.run ? ''
        : html`<button type="button" class="chip-x" data-act="unpick" data-key="${t.key}" data-n="${n}" aria-label="Прибрати з ${t.label}" data-tip="Прибрати з ${t.label}">${ic('x')}</button>`}</span>`));
      setHtml(tile.querySelector('.mk-put'), target ? html`${ic('plus', 'icon-s')}${target}` : '');
    });
    grid.classList.toggle('picking', !!target);
    const next = $('#mk-next');
    if (next) setHtml(next, st.run ? '' : target ? html`Клацніть розворот → <b>${target}</b>` : html`${ic('check', 'icon-s')}Усі місця заповнено`);
  }

  function changed() {
    rememberPicks();
    paintPicks(); paintTiles(); paintMake();
  }

  // ---------------------------------------------------------------- picking
  function put(n) {
    if (st.run) return;
    if (!st.active) { toast('Усі місця заповнено — клацніть місце в шаблоні, щоб замінити розворот', 'info', 2800); return; }
    st.picks[st.active.key][st.active.i] = n;
    st.active = firstEmpty(st.active);
    changed();
  }

  function blink(elements) {
    elements.forEach((x) => {
      x.classList.remove('mk-need');
      void x.offsetWidth; // restart the blink on a second press
      x.classList.add('mk-need');
    });
  }

  function viewer(items, index = 0) { openLightbox(items, index); }

  function openSpread(n) {
    const spreads = st.book.spreads.map(([p]) => p);
    const items = [];
    const build = () => spreads.map((p) => ({
      src: src('spread', { n: p, h: 1200 }), full: src('spread', { n: p, h: 2400 }),
      title: `Розворот ${pages(p)}`,
      sub: st.active ? `Обрати → ${slotName(st.active)}` : 'Усі місця в шаблонах заповнено',
      actions: st.active && !st.run ? [{ icon: 'check', label: 'Обрати', tip: 'Поставити цей розворот у шаблон',
        run: (lb) => { put(p); items.splice(0, items.length, ...build()); lb.refresh(); } }] : [],
    }));
    items.push(...build());
    viewer(items, spreads.indexOf(n));
  }

  function openTemplates(key) {
    const found = st.meta.templates.filter((t) => t.found);
    viewer(found.map((t) => ({
      src: media(`/media/mockups/template/${t.key}`, { w: BIG }), full: media(`/media/mockups/template/${t.key}`, { w: SHARP }),
      title: t.label, sub: `${t.file}${t.hand || t.keep ? ` · ${yours(t)}` : ''}`,
    })), Math.max(0, found.findIndex((t) => t.key === key)));
  }

  function openShots(which, i) {
    const r = which === 'finished' ? st.finished : st.result;
    viewer(r.saved.map((name, n) => ({
      src: media(`/media/mockups/out/${r.job}/${n}`, { w: BIG }), full: media(`/media/mockups/out/${r.job}/${n}`, { w: SHARP }),
      title: name, sub: folderName(r.folder),
      onOriginal: () => post('/api/mockups/open-picture', { job: r.job, i: n }).catch((err) => toast(err.message, 'error')),
    })), i);
  }

  // ---------------------------------------------------------------- the demo book comes in
  const bookBusy = () => st.receiving !== null || !!st.run;

  function paintReceiving() {
    if (!st.book) paintStructure();
    else paintBookState();
  }

  async function loadBook(label, fetchBook) {
    st.bookError = '';
    try {
      const book = await fetchBook();
      if (gone) return;
      Object.assign(st, { book, label, out: '', result: null, finished: null, runError: '' });
      const again = recallPicks();
      resetPicks(again);
      st.receiving = null;
      paintAll();
      if (again) toast('Повернув ваш минулий вибір розворотів для цієї книги', 'info');
      return;
    } catch (err) {
      if (gone) return;
      st.bookError = err.message;
    }
    st.receiving = null;
    paintReceiving();
    paintHead();
  }

  async function takeDrop(dropped) {
    if (bookBusy()) return;
    // The Canva ZIP; its unpacked folder or the pictures themselves do too.
    const zip = dropped.files.length === 1 && /\.zip$/i.test(dropped.files[0].name);
    const pictures = dropped.files.filter((f) => /\.(png|jpe?g|webp)$/i.test(f.name)).length;
    if (!zip && !dropped.entries.some((e) => e.isDirectory) && pictures < 3) { toast('Перетягніть ZIP-архів із Canva', 'error'); return; }
    st.receiving = 0;
    paintReceiving();
    await loadBook(dropLabel(dropped), async () => {
      const path = await receiveDrop(dropped, (pct) => { st.receiving = pct; paintReceiving(); });
      return post('/api/mockups/book', { path });
    });
  }
  wireFolderDrop(view, () => $('#mk-right'), takeDrop);
  view.addEventListener('bs:dropped', (e) => { e.detail.handled = true; takeDrop(e.detail.dropped); });
  const handedDrop = take('mockups')?.drop; // files dropped anywhere in the window and sent here (drop-anywhere.js)

  async function pickZip() {
    if (bookBusy()) return;
    st.receiving = 'ask';
    paintReceiving();
    let path = null;
    try { path = (await post('/api/mockups/pick-zip', {})).path; } catch (err) { toast(err.message, 'error'); }
    if (gone) return;
    if (!path) { st.receiving = null; paintReceiving(); return; }
    st.receiving = 'unzip';
    paintReceiving();
    await loadBook(folderName(path), () => post('/api/mockups/open-zip', { path }));
  }

  // ---------------------------------------------------------------- the run
  // Every press gets an answer (23.09.2026: a greyed-out button that silently ignored the owner's click read as
  // "nothing happens"): what is missing lights up, and the wait for the Windows dialog is shown.
  async function make() {
    if (st.run || st.asking) return;
    if (!st.book) {
      toast('Спершу додайте демо-книгу: перетягніть ZIP із Canva у «Структуру» або клацніть там', 'info');
      blink([$('.mk-ghost')].filter(Boolean));
      return;
    }
    const empty = slotsInOrder().filter((s) => st.picks[s.key][s.i] === null);
    if (empty.length) {
      st.active = empty[0];
      paintPicks(); paintTiles();
      const where = [...new Set(empty.map((s) => tpl(s.key).label))].join(', ');
      toast(`Оберіть ще ${empty.length} ${plural(empty.length, SPREADS)}: ${where}`, 'info');
      blink([...view.querySelectorAll('.mk-slot[data-slot]:not(.filled)')]);
      return;
    }
    if (!st.out && st.workshop) {
      start('make', post('/api/mockups/make', { book: st.book.id, picks: st.picks, workshop: st.workshop.id }));
      return;
    }
    const folder = st.out || await askFolder(true);
    if (!folder || gone) return;
    start('make', post('/api/mockups/make', { book: st.book.id, picks: st.picks, folder }));
  }

  async function askFolder(forRun) {
    st.asking = true;
    paintOut(); paintAction();
    let path = null;
    try { path = (await post('/api/mockups/pick-folder', {})).path; } catch (err) { toast(err.message, 'error'); }
    st.asking = false;
    if (gone) return null;
    if (path) st.out = path;
    else if (forRun) toast('Папку не вибрано — мокапи не робились', 'info');
    paintOut(); paintAction();
    return path;
  }

  function start(mode, request) {
    st.runError = '';
    if (mode === 'make') { st.result = null; st.finished = null; slides.reset(); }
    slides.runStarted(); // its pictures' cut-outs are followed again (a «Зберегти відкриті» adds Cover 1)
    st.run = { mode, phase: 'prepare', step: 'Починаю…', percent: 0, rows: [] };
    paintAction(); paintPicks(); paintTiles();
    follow(request);
  }

  async function follow(request) {
    let jobId = null;
    busy(true);
    try {
      ({ jobId } = await request);
      const res = await runJob(Promise.resolve({ jobId }), (job) => {
        if (gone || !st.run) return;
        const p = job.partial || {};
        const again = (p.phase && p.phase !== st.run.phase) || (p.mode && p.mode !== st.run.mode);
        Object.assign(st.run, { mode: p.mode || st.run.mode, phase: p.phase || st.run.phase, rows: p.rows || st.run.rows,
          step: job.step, percent: job.percent });
        if (again || !$('#mk-rows')) paintAction(); else patchRun();
      }, 700, () => !gone);
      if (gone) return;
      if (st.run?.mode === 'finish') {
        st.finished = { ...res, job: jobId };
        st.pending = null;
        tellDone(`Збережено ще ${res.saved.length}`);
      } else {
        st.result = { ...res, job: jobId };
        st.pending = res.run ? { run: res.run, folder: res.folder, open: res.open, cover: res.coverOpen } : null;
        tellDone(`${res.cancelled ? 'Зупинено' : 'Готово'} · ${res.saved.length} ${plural(res.saved.length, PICTURES)}`);
      }
    } catch (err) {
      if (gone) return;
      if (err.message === 'Скасовано.') toast('Зупинено', 'info'); // the owner's own stop is no error
      else { st.runError = err.message; tellDone('Не вдалося'); }
    } finally {
      if (!gone) busy(false);
    }
    st.run = null;
    if (!gone) { paintAction(); paintPicks(); paintTiles(); paintHead(); slides.paint(); }
  }

  // The owner watches Photoshop while it works: the window's title says how it ended (app.js keeps it there until
  // he comes back), its taskbar button flashes and Windows plays its sound (only when the window is not the one in
  // front). Elsewhere in Book Studio (this page is kept hidden) a notice says it too.
  function tellDone(text) {
    if (!view.isConnected) toast(`Мокапи: ${text.toLowerCase()}`, text === 'Не вдалося' ? 'error' : 'success');
    if (document.hasFocus()) return;
    tellBusy({ done: text });
    setTimeout(() => post('/api/mockups/attention', {}).catch(() => {}), 250);
  }

  // ---------------------------------------------------------------- where the templates and Photoshop are
  function placesBody() {
    const m = st.meta;
    const absent = m.templates.filter((t) => !t.found).map((t) => t.file);
    const row = (label, what, path, ok, good, bad) => html`<div class="stack-s">
      <span class="eyebrow">${label}</span>
      <div class="input-group"><input class="input path-input" readonly value="${path}" title="${path}" aria-label="${label}">
        ${ib('folderPick', 'Обрати папку', `data-what="${what}"`)}</div>
      <div class="mk-place ${ok ? 'ok' : 'bad'}">${ic(ok ? 'check' : 'alertCircle', 'icon-s')}<span>${ok ? good : bad}</span></div>
    </div>`;
    return html`<div class="stack-l">
      ${row('Шаблони (трафарети)', 'templates', m.templatesDir, m.templatesFound && !absent.length,
        `Усі ${m.templates.length} шаблонів на місці. Програма їх лише читає — працює з копіями.`,
        m.templatesFound ? `Немає: ${absent.join(', ')}` : 'Папки не знайдено')}
      ${row('Photoshop', 'photoshop', m.photoshopDir, m.photoshopFound, 'Photoshop знайдено', 'Photoshop тут не знайдено')}
    </div>`;
  }

  function openPlaces() {
    const m = modal({ title: 'Де шаблони і Photoshop', body: placesBody() });
    m.body.addEventListener('click', async (e) => {
      const b = e.target.closest('[data-what]');
      if (b) await place(b.dataset.what, () => setHtml(m.body, placesBody()));
    });
  }

  async function place(what, then) {
    try { st.meta = await post('/api/mockups/place', { what }); }
    catch (err) { toast(err.message, 'error'); return; }
    if (gone) return;
    then?.();
    paintLost(); paintTemplates(); paintAction();
  }

  // ---------------------------------------------------------------- step 4: the listing slides (mockups-slides.js)
  const slides = slidesStep({
    view, st, stepNo, tellDone, busy,
    blinkFinish: () => { const b = $('[data-act="finish"]'); if (b) { b.scrollIntoView({ block: 'center', behavior: 'smooth' }); blink([b]); } },
  });
  offs.push(on(view, 'change', '#mk-s5 input[data-num]', (e, t) => slides.input(t)));
  offs.push(on(view, 'change', '#mk-workshop', (e, t) => {
    st.workshop = bookById(t.value);
    remember(LAST_BOOK, t.value);
    paintOut(); paintMake();
  }));

  // ---------------------------------------------------------------- events
  const slotOf = (v) => { const [key, i] = String(v).split(':'); return { key, i: +i }; };
  offs.push(on(view, 'click', '[data-act], .mk-spread, .mk-slot[data-slot]', async (e, t) => {
    const act = t.dataset.act;
    if (act?.startsWith('sl-') || act === 'open-nobg') { await slides.act(act, t); return; }
    if (act === 'zoom') { e.stopPropagation(); openSpread(+t.dataset.n); return; }
    if (act === 'clear' || act === 'unpick') {
      e.stopPropagation();
      if (st.run) return;
      const s = act === 'clear' ? slotOf(t.dataset.slot)
        : { key: t.dataset.key, i: st.picks[t.dataset.key].indexOf(+t.dataset.n) };
      if (s.i < 0) return;
      st.picks[s.key][s.i] = null;
      st.active = s;
      changed();
      return;
    }
    if (act === 'clear-all') { if (!st.run) { resetPicks(); changed(); } return; }
    if (act === 'pick-zip') { pickZip(); return; }
    if (act === 'pick-out') { if (!st.asking && !st.run) askFolder(false); return; }
    if (act === 'same-out') { st.out = st.meta.lastOut; paintOut(); paintMake(); return; }
    if (act === 'to-book') { st.out = ''; takeWorkshopBook(true); paintOut(); paintMake(); return; }
    if (act === 'open-book-mockups') {
      post('/api/workshop/open', { book: st.workshop.id, what: 'mockups' }).catch((err) => toast(err.message, 'error'));
      return;
    }
    if (act === 'places') { openPlaces(); return; }
    if (act === 'close') { finishPage(); return; }
    if (act === 'place') { place(t.dataset.what); return; }
    if (act === 'make') { make(); return; }
    if (act === 'finish') { if (!st.run && st.pending) start('finish', post('/api/mockups/finish', { run: st.pending.run })); return; }
    if (act === 'stop') { post('/api/mockups/cancel', {}).catch(() => {}); t.disabled = true; return; }
    if (act === 'open-out') { post('/api/mockups/open-folder', { path: t.dataset.path }).catch((err) => toast(err.message, 'error')); return; }
    if (act === 'shot') { openShots(t.dataset.which, +t.dataset.i); return; }
    if (act === 'tpl-view') { openTemplates(t.dataset.key); return; }
    if (act === 'cover') { viewer([{ src: src('cover', { w: BIG }), full: src('cover', { w: SHARP }), title: 'Обкладинка', sub: 'задня й корінець — у шаблони самі, лицьову підганяєте ви' }]); return; }
    if (act === 'dedication') { viewer([{ src: src('page', { n: 1, w: BIG }), full: src('page', { n: 1, w: SHARP }), title: 'Присвята · сторінка 1', sub: 'іде в шаблон Dedication сама' }]); return; }
    if (t.classList.contains('mk-spread')) { put(+t.dataset.spread); return; }
    if (t.dataset.slot && !st.run && !t.disabled) {
      const s = slotOf(t.dataset.slot);
      st.active = isActive(s.key, s.i) ? null : s;
      paintPicks(); paintTiles();
    }
  }));
  offs.push(on(view, 'keydown', '.mk-spread, .mk-slot.filled, .mk-ghost, .mk-path', (e, t) => {
    if (e.target !== t) return;
    if ((e.key === 'Delete' || e.key === 'Backspace') && t.matches('.mk-slot.filled')) {
      e.preventDefault();
      t.querySelector('[data-act="clear"]').click();
      return;
    }
    if (e.key !== 'Enter' && e.key !== ' ') return;
    e.preventDefault();
    t.click();
  }));

  // Dragging inside the window: a spread onto a slot puts it there; a slot onto another swaps the two.
  const ours = (e) => [...(e.dataTransfer?.types || [])].some((x) => x === TYPE_SPREAD || x === TYPE_SLOT);
  offs.push(on(view, 'dragstart', '.mk-spread, .mk-slot.filled', (e, t) => {
    if (st.run) { e.preventDefault(); return; }
    if (t.classList.contains('mk-spread')) e.dataTransfer.setData(TYPE_SPREAD, t.dataset.spread);
    else e.dataTransfer.setData(TYPE_SLOT, t.dataset.slot);
    e.dataTransfer.effectAllowed = 'copyMove';
    $('.mk')?.classList.add('dragging');
  }));
  offs.push(on(view, 'dragend', '.mk-spread, .mk-slot.filled', () => {
    $('.mk')?.classList.remove('dragging');
    view.querySelectorAll('.drag-over').forEach((x) => x.classList.remove('drag-over'));
  }));
  offs.push(on(view, 'dragover', '.mk-slot[data-slot]', (e, t) => {
    if (!ours(e) || !st.book || st.run) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    t.classList.add('drag-over');
  }));
  offs.push(on(view, 'dragleave', '.mk-slot[data-slot]', (e, t) => { if (!t.contains(e.relatedTarget)) t.classList.remove('drag-over'); }));
  offs.push(on(view, 'drop', '.mk-slot[data-slot]', (e, t) => {
    if (!ours(e) || !st.book || st.run) return;
    e.preventDefault();
    t.classList.remove('drag-over');
    const s = slotOf(t.dataset.slot);
    const n = e.dataTransfer.getData(TYPE_SPREAD), from = e.dataTransfer.getData(TYPE_SLOT);
    if (n) st.picks[s.key][s.i] = +n;
    else if (from) {
      const f = slotOf(from);
      [st.picks[f.key][f.i], st.picks[s.key][s.i]] = [st.picks[s.key][s.i], st.picks[f.key][f.i]];
    }
    st.active = firstEmpty();
    changed();
  }));

  resetPicks();
  render();
  arrived();
  if (handedDrop) takeDrop(handedDrop); // after the first paint, which would wipe the «receiving» state
  // A run still going (the window was reloaded): follow it again.
  if (st.meta.jobId) {
    st.run = { mode: 'make', phase: 'prepare', step: 'Photoshop працює…', percent: 0, rows: [] };
    paintAction();
    follow(Promise.resolve({ jobId: st.meta.jobId }));
  }

  return {
    // Kept when the owner steps away while there is something to come back to: a book, a run, its result.
    keep: () => !!(st.book || st.run || st.result || st.finished || st.receiving !== null || slides.keep()),
    // From «Інструменти» the page opens clean — except while Photoshop works for it or templates wait there for the owner's save.
    canStartOver: () => !st.run && !st.pending && !slides.running(),
    navFor: () => (fromBook ? '#/books' : null),
    revive: () => {
      if (takeWorkshopBook()) { paintOut(); paintMake(); toast(`Мокапи — для ${st.workshop.name}`, 'info'); }
      arrived();
      slides.wake();
      return true;
    },
    unmount() { gone = true; slides.stop(); offs.forEach((off) => off()); if (st.run) busy(false); },
  };
}
