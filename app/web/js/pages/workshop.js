// The Workshop (the Listings mode): the books in development — the book pipeline's folders, where the agents in
// Antigravity write each book (the book console moved in, 26.09.2026). A card shows how far the book is on its path;
// the gallery follows the files by itself (an agent's new book appears, a caught picture shows) without a reload.
import {
  api, post, html, ic, ib, setHtml, on, fadeImages, plural, flip, debounce, menu, patch, segHtml, setSeg,
  highlightTokens, remembered, remember, galleryKeys, BOOKS,
} from '../lib.js';
import { watch, paintGenBar, genAction, genState, act } from '../workshop-live.js';
import { STATE_WORDS, checkWord, picture } from '../workshop-bits.js';
import { bookTile, segBar, tickBadge } from '../book-tile.js';

const PREF = 'bs-workshop-view';
const SORTS = [
  { value: 'most', label: 'Спочатку найбільш готові', icon: 'checkCircle' },
  { value: 'number', label: 'За номером — новіші спершу', icon: 'sort' },
  { value: 'recent', label: 'Нещодавно змінені', icon: 'clock' },
  { value: 'least', label: 'Спочатку найменш готові', icon: 'alertCircle' },
];


// `embedded` — drawn inside «Книги» (pages/books.js, 2026-09-30): the head is the hub's, and only the books still
// being made are shown (the ones passed on are the library's, under «У магазині»).
export async function mount(view, params, { embedded = false } = {}) {
  const saved = remembered(PREF, {});
  const state = { books: [], folder: '', sort: SORTS.some((s) => s.value === saved.sort) ? saved.sort : 'most', query: '', shelf: 'work' };
  let first;
  try {
    first = await api('/api/workshop/books');
  } catch (err) {
    setHtml(view, html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`);
    return null;
  }
  Object.assign(state, { books: first.books, folder: first.folder });

  setHtml(view, html`
    ${embedded ? '' : html`<div class="page-head">
      <div>
        <h1 class="page-title">Майстерня</h1>
        <div class="page-sub" id="ws-sub"></div>
      </div>
    </div>`}
    <div class="ws-genbar-slot" id="ws-gen"></div>
    <div class="lib-toolbar">
      <div class="input-group">${ic('search')}<input class="input" id="ws-q" placeholder="Назва або номер книги" aria-label="Пошук книг" autocomplete="off"></div>
      <span id="ws-shelf"></span>
      <div class="tools">${ib('sort', 'Сортування', 'data-act="sort" id="ws-sort"')}${ib('folderOpen', 'Відкрити папку книг', 'data-act="folder"')}</div>
      ${ib('plus', 'Нова книга — текст для агента в буфер', 'data-act="add"', { cls: 'primary', kbd: 'N' })}
    </div>
    <div class="lib-grid" id="ws-grid"></div>
    <div id="ws-empty"></div>`);

  const grid = view.querySelector('#ws-grid');
  const q = view.querySelector('#ws-q');
  const persist = () => remember(PREF, { sort: state.sort });
  const passed = () => state.books.filter((b) => b.library);
  const readiness = (b) => b.steps.reduce((sum, s) => sum + (s.state === 'done' || s.state === 'skip' ? 1 : s.state === 'part' ? s.p ?? 0.5 : 0), 0); // sorting only: a started step without a measured p counts as half

  function listed() {
    const needle = state.query.trim().toLowerCase();
    const list = state.books.filter((b) => (state.shelf === 'library') === !!b.library
      && (!needle || `№${b.number ?? ''} ${b.title} ${b.coverTitle}`.toLowerCase().includes(needle)));
    const by = {
      number: (a, b) => (b.number ?? -1) - (a.number ?? -1) || a.title.localeCompare(b.title),
      recent: (a, b) => b.updated - a.updated,
      most: (a, b) => readiness(b) - readiness(a) || (b.number ?? -1) - (a.number ?? -1),
      least: (a, b) => readiness(a) - readiness(b) || (b.number ?? -1) - (a.number ?? -1),
    }[state.sort];
    return list.sort(by);
  }

  function card(b) {
    const next = b.steps.find((s) => s.state === 'todo' || s.state === 'part');
    const check = b.steps.find((s) => s.key === 'prompts')?.check;
    const t = b.thumb;
    const VALUE = { done: 1, part: 0, todo: 0, skip: 0 };       // a started step fills only as far as it is really known (`p`), never by a guess
    const count = next?.key === 'pictures' ? html` <span class="num">${b.pictures}/${b.picturesTotal}</span>` : '';
    return bookTile({
      key: b.id, title: b.title, number: b.number,
      cover: { src: t ? picture(b, t.area, t.name, 720) : '', cls: t?.kind === 'cover' ? 'front' : '', letter: (b.title || '?').charAt(0).toUpperCase() },
      over: html`<span class="ws-card-wait" data-wait="${b.id}" data-tip="Чекаю картинку"><span class="ws-pulse"></span>${ic('images', 'icon-s')}</span>
        ${b.library ? tickBadge('У бібліотеці замовлень') : ''}`,
      sub: html`<span class="serif">${highlightTokens(b.coverTitle)}</span>`,
      bar: segBar(b.steps.map((s) => ({ v: s.state === 'part' ? s.p ?? 0 : VALUE[s.state] ?? 0, skip: s.state === 'skip', unk: s.state === 'part' && s.p == null, tip: `${s.label}: ${STATE_WORDS[s.state]}` }))),
      meta: html`${next ? html`<span class="book-go">${ic('chevRight', 'icon-s')}<b>${next.label}</b>${count}</span>` : html`<span class="book-go done">${ic('check', 'icon-s')}</span>`}
        ${check ? html`<span class="${check.go ? 'ws-go' : 'ws-nogo'}" data-tip="Перевірка промптів">${checkWord(check)}</span>` : ''}`,
    });
  }

  function paintSub() {
    if (embedded) { state.shelf = 'work'; return; }
    const n = state.books.length - passed().length;
    const done = passed().length;
    setHtml(view.querySelector('#ws-sub'), n || done
      ? html`<span class="num">${n}</span> ${plural(n, BOOKS)} у роботі${done ? html` · <span class="num">${done}</span> у бібліотеці` : ''}`
      : 'Книги в розробці: агенти пишуть, Майстерня ловить картинки');
    const shelf = view.querySelector('#ws-shelf');
    if (!done) { shelf.innerHTML = ''; state.shelf = 'work'; return; }
    if (!shelf.firstElementChild) {
      setHtml(shelf, segHtml([{ value: 'work', label: 'У роботі', count: n }, { value: 'library', label: 'У бібліотеці', count: done }], state.shelf, { name: 'shelf' }));
    } else {
      shelf.querySelectorAll('.seg-count').forEach((c, i) => { c.textContent = i ? done : n; });
    }
  }

  function paintEmpty(list) {
    const box = view.querySelector('#ws-empty');
    // patch(), not setHtml: a repaint with the same empty state leaves it alone instead of replaying its entrance.
    if (!state.books.length) {
      patch(box, [['none', html`<div class="empty" style="padding:72px 20px">
        <div class="empty-icon">${ic('workshop')}</div>
        <h3>Майстерня порожня</h3>
        <p>«Нова книга» покладе в буфер «Нова книга» з адресою папки книг — вставте в чат будь-якого агента. Книга з'явиться тут сама, щойно агент почне її писати.</p>
        <button class="btn btn-primary" data-act="add">${ic('agent')}Нова книга</button>
        <div class="faint mono ws-empty-path">${state.folder}</div></div>`]]);
    } else if (!list.length) {
      patch(box, [['found', html`<div class="empty"><div class="empty-icon">${ic('search')}</div><h3>Нічого не знайдено</h3><p>Спробуйте іншу назву чи номер.</p></div>`]]);
    } else patch(box, []);
  }

  let firstDraw = true;
  function paint() {
    const list = listed();
    const drawn = [];
    flip(grid, () => drawn.push(...patch(grid, list.map((b) => [b.id, card(b)]))));
    fadeImages(grid);
    if (firstDraw) {
      drawn.forEach((n, i) => { n.classList.add('enter'); n.style.animationDelay = `${Math.min(i * 16, 240)}ms`; });
      firstDraw = false;
    }
    paintSub();
    paintEmpty(list);
    paintGen();
  }

  function paintGen() {
    paintGenBar(view.querySelector('#ws-gen'), null);
    const waiting = genState()?.active?.book;
    grid.querySelectorAll('[data-wait]').forEach((w) => w.classList.toggle('on', w.dataset.wait === waiting));
  }

  const sortTip = () => {
    const b = view.querySelector('#ws-sort');
    const label = `Сортування: ${SORTS.find((s) => s.value === state.sort).label.toLowerCase()}`;
    b.dataset.tip = label; b.setAttribute('aria-label', label);
  };
  // The generation's state first (the bar and the cards' «чекаю картинку» are drawn from it), then the cards.
  const unwatch = watch(first, async () => {
    const fresh = await api('/api/workshop/books').catch(() => null);
    if (!fresh) return;
    Object.assign(state, { books: fresh.books, folder: fresh.folder });
    paint();
  });
  sortTip();
  paint();

  const newBook = (btn) => act(btn, () => post('/api/workshop/agent', {}),
    () => 'У буфері — «Нова книга» з адресою папки книг; вставте в чат агента');
  const runSearch = debounce(paint, 90);
  const offs = [
    on(view, 'click', '[data-open]', (e, b) => { location.hash = `#/workshop/${encodeURIComponent(b.dataset.open)}`; }),
    on(view, 'click', '[data-act="add"]', (e, b) => newBook(b)),
    on(view, 'click', '[data-act="folder"]', (e, b) => act(b, () => post('/api/workshop/open', { what: 'books' }))),
    on(view, 'click', '[data-act="sort"]', (e, b) => menu(b, SORTS.map((s) => ({
      label: s.label, icon: s.icon, on: state.sort === s.value,
      onClick: () => { state.sort = s.value; persist(); sortTip(); paint(); },
    })))),
    on(view, 'click', '[data-seg="shelf"] button', (e, b) => { state.shelf = b.dataset.value; setSeg(b.parentElement, state.shelf); paint(); }),
    on(view, 'click', '[data-gen]', (e, b) => genAction(b, b.dataset.gen)),
  ];
  q.addEventListener('input', () => { state.query = q.value; runSearch(); });
  const onKey = galleryKeys(q, () => newBook(view.querySelector('[data-act="add"]')));
  document.addEventListener('keydown', onKey);

  return {
    unmount() { unwatch(); offs.forEach((f) => f()); runSearch.cancel(); document.removeEventListener('keydown', onKey); },
  };
}
