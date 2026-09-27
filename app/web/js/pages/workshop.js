// The Workshop (the Listings mode): the books in development — the book pipeline's folders, where the agents in
// Antigravity write each book (the book console moved in, 26.09.2026). A card shows how far the book is on its path;
// the gallery follows the files by itself (an agent's new book appears, a caught picture shows) without a reload.
import {
  api, post, html, ic, ib, setHtml, on, media, fadeImages, plural, flip, debounce, menu, patch, segHtml, setSeg, highlightTokens,
  remembered, remember,
} from '../lib.js';
import { watch, genBar, genAction, genState, act } from '../workshop-live.js';

const PREF = 'bs-workshop-view';
const SORTS = [
  { value: 'number', label: 'За номером — новіші спершу', icon: 'sort' },
  { value: 'recent', label: 'Нещодавно змінені', icon: 'clock' },
  { value: 'least', label: 'Спочатку найменш готові', icon: 'alertCircle' },
];
const BOOKS = ['книга', 'книги', 'книг'];
const ERRORS = ['помилка', 'помилки', 'помилок'];
const STATE_WORDS = { done: 'готово', part: 'почато', todo: 'ще ні', skip: 'не потрібно' };

/** A book's picture address; with its version the browser keeps it for good — nothing blinks on a redraw. */
export function picture(b, area, name, w, variant = '') {
  const v = b.v?.[`${area}/${variant ? `variants/${variant}/` : ''}${name}`];
  const path = `/media/workshop/${encodeURIComponent(b.id)}/${area}${variant ? `/v/${encodeURIComponent(variant)}` : ''}/${encodeURIComponent(name)}`;
  return media(path, { w, ...(v ? { v } : {}) });
}

/** «Промпти · GO» — the book check's word for a card or a step. */
export function checkWord(c) {
  return c.go ? 'GO' : `${c.fails} ${plural(c.fails, ERRORS)}`;
}

export async function mount(view) {
  const saved = remembered(PREF, {});
  const state = { books: [], folder: '', sort: SORTS.some((s) => s.value === saved.sort) ? saved.sort : 'number', query: '', shelf: 'work' };
  let first;
  try {
    first = await api('/api/workshop/books');
  } catch (err) {
    setHtml(view, html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`);
    return null;
  }
  Object.assign(state, { books: first.books, folder: first.folder });

  setHtml(view, html`
    <div class="page-head">
      <div>
        <h1 class="page-title">Майстерня</h1>
        <div class="page-sub" id="ws-sub"></div>
      </div>
    </div>
    <div class="ws-genbar-slot" id="ws-gen"></div>
    <div class="lib-toolbar">
      <div class="input-group">${ic('search')}<input class="input" id="ws-q" placeholder="Назва або номер книги" aria-label="Пошук книг" autocomplete="off"></div>
      <span id="ws-shelf"></span>
      <div class="tools">${ib('sort', 'Сортування', 'data-act="sort" id="ws-sort"')}${ib('folderOpen', 'Відкрити папку книг', 'data-act="folder"')}</div>
      ${ib('plus', 'Нова книга — в Antigravity', 'data-act="add"', { cls: 'primary', kbd: 'N' })}
    </div>
    <div class="ws-grid" id="ws-grid"></div>
    <div id="ws-empty"></div>`);

  const grid = view.querySelector('#ws-grid');
  const q = view.querySelector('#ws-q');
  const persist = () => remember(PREF, { sort: state.sort });
  const passed = () => state.books.filter((b) => b.library);
  const readiness = (b) => b.steps.reduce((sum, s) => sum + (s.state === 'done' || s.state === 'skip' ? 1 : s.state === 'part' ? 0.5 : 0), 0);

  function listed() {
    const needle = state.query.trim().toLowerCase();
    const list = state.books.filter((b) => (state.shelf === 'library') === !!b.library
      && (!needle || `№${b.number ?? ''} ${b.title} ${b.coverTitle}`.toLowerCase().includes(needle)));
    const by = {
      number: (a, b) => (b.number ?? -1) - (a.number ?? -1) || a.title.localeCompare(b.title),
      recent: (a, b) => b.updated - a.updated,
      least: (a, b) => readiness(a) - readiness(b) || (b.number ?? -1) - (a.number ?? -1),
    }[state.sort];
    return list.sort(by);
  }

  function card(b) {
    const next = b.steps.find((s) => s.state === 'todo' || s.state === 'part');
    const check = b.steps.find((s) => s.key === 'prompts')?.check;
    const t = b.thumb;
    return html`<button class="ws-card" data-open="${b.id}" aria-label="${b.title}">
      <div class="ws-card-art">
        ${t ? html`<img data-fade alt="" class="${t.kind}" src="${picture(b, t.area, t.name, 720)}">`
          : html`<div class="ws-card-letter serif">${(b.title || '?').charAt(0).toUpperCase()}</div>`}
        <span class="ws-card-wait" data-wait="${b.id}"><span class="ws-pulse"></span>чекаю картинку</span>
        ${b.library ? html`<span class="book-badge" data-tip="У бібліотеці замовлень">${ic('check')}</span>` : ''}
      </div>
      <div class="ws-card-body">
        <div class="ws-card-title">${b.number != null ? html`<span class="ws-no num">№${b.number}</span>` : ''}${b.title}</div>
        <div class="ws-card-sub serif">${highlightTokens(b.coverTitle)}</div>
        <div class="ws-card-bar">${b.steps.map((s) => html`<i class="${s.state}" data-tip="${s.label}: ${STATE_WORDS[s.state]}"></i>`)}</div>
        <div class="ws-card-meta">${next ? html`<span>Далі: <b>${next.label}</b></span>` : html`<span><b>Усе готово</b></span>`}
          <span class="num">Картинки ${b.pictures}/${b.picturesTotal}</span>
          ${check ? html`<span class="${check.go ? 'ws-go' : 'ws-nogo'}" data-tip="Перевірка промптів">${checkWord(check)}</span>` : ''}</div>
      </div>
    </button>`;
  }

  function paintSub() {
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
    if (!state.books.length) {
      setHtml(box, html`<div class="empty" style="padding:72px 20px">
        <div class="empty-icon">${ic('workshop')}</div>
        <h3>Майстерня порожня</h3>
        <p>«Нова книга» відкриє Antigravity, а в буфері буде «Нова книга» з адресою папки книг — вставте в чат агента. Книга з'явиться тут сама, щойно агент почне її писати.</p>
        <button class="btn btn-primary" data-act="add">${ic('agent')}Нова книга</button>
        <div class="faint mono ws-empty-path">${state.folder}</div></div>`);
    } else if (!list.length) {
      setHtml(box, html`<div class="empty"><div class="empty-icon">${ic('search')}</div><h3>Нічого не знайдено</h3><p>Спробуйте іншу назву чи номер.</p></div>`);
    } else box.innerHTML = '';
  }

  let firstDraw = true;
  function paint() {
    const list = listed();
    const drawn = [];
    flip(grid, () => drawn.push(...patch(grid, list.map((b) => [b.id, card(b)]))));
    fadeImages(grid);
    if (firstDraw) {
      drawn.forEach((n, i) => { n.classList.add('enter'); n.style.animationDelay = `${Math.min(i * 26, 360)}ms`; });
      firstDraw = false;
    }
    paintSub();
    paintEmpty(list);
    paintGen();
  }

  function paintGen() {
    const bar = genBar(null);
    patch(view.querySelector('#ws-gen'), bar ? [['bar', bar]] : []);
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
    () => 'Antigravity відкривається · у буфері — «Нова книга» з адресою папки книг; вставте в чат агента');
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
  const typing = () => /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName || '') || document.querySelector('.modal-root');
  const onKey = (e) => {
    if ((e.ctrlKey && e.key.toLowerCase() === 'f') || (e.key === '/' && !typing())) { e.preventDefault(); q.focus(); q.select(); }
    else if (e.key.toLowerCase() === 'n' && !e.ctrlKey && !e.altKey && !e.metaKey && !typing()) { e.preventDefault(); newBook(view.querySelector('[data-act="add"]')); }
  };
  document.addEventListener('keydown', onKey);

  return {
    unmount() { unwatch(); offs.forEach((f) => f()); runSearch.cancel(); document.removeEventListener('keydown', onKey); },
  };
}
