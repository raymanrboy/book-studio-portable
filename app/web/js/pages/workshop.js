// The Workshop (the Listings mode): the books still in development — "a place where I create books before
// sending them to the library with orders" (owner, 24.09.2026). Search, sort, a new book by its title alone.
// Laid out like the library's gallery: cards are built once; search and sort only hide and move them (FLIP).
import { api, html, ic, ib, setHtml, on, media, modal, toast, fadeImages, plural, naturalCompare, raw, flip, debounce, menu, copyText } from '../lib.js';

const PREF = 'bs-workshop-view';
const SORTS = [
  { value: 'recent', label: 'Нещодавно змінені', icon: 'clock' },
  { value: 'created', label: 'Нещодавно додані', icon: 'plus' },
  { value: 'title', label: 'За назвою', icon: 'sort' },
  { value: 'least', label: 'Спочатку найменш готові', icon: 'alertCircle' },
];
const BOOKS = ['книга', 'книги', 'книг'];

/** How far a Workshop book is: its prompts, texts and pictures (17 rows each), 0…1 per part. */
export function progress(c) {
  return [['Промпти', c.prompts, c.promptsTotal], ['Тексти', c.texts, c.textsTotal], ['Картинки', c.pictures, c.picturesTotal]];
}
export const ready = (c) => c.pictures === c.picturesTotal && c.texts === c.textsTotal;

export async function mount(view) {
  let saved = {};
  try { saved = JSON.parse(localStorage.getItem(PREF) || '{}'); } catch { /* a convenience only */ }
  const state = { books: [], sort: saved.sort || 'recent', query: '' };
  try {
    state.books = (await api('/api/library/books?stage=workshop')).books;
  } catch (err) {
    setHtml(view, html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`);
    return null;
  }

  setHtml(view, html`
    <div class="page-head">
      <div>
        <h1 class="page-title">Майстерня</h1>
        <div class="page-sub" id="ws-sub"></div>
      </div>
    </div>
    <div class="lib-toolbar">
      <div class="input-group">${ic('search')}<input class="input" id="ws-q" placeholder="Назва книги" aria-label="Пошук книг" autocomplete="off"></div>
      <div class="tools">${ib('sort', 'Сортування', 'data-act="sort" id="ws-sort"')}${ib('guide', 'Інструкція для агента: промпти й тексти книги', 'data-act="guide"')}</div>
      ${ib('plus', 'Нова книга', 'data-act="add"', { cls: 'primary', kbd: 'N' })}
    </div>
    <div class="lib-grid" id="ws-grid"></div>
    <div id="ws-empty"></div>`);

  const grid = view.querySelector('#ws-grid');
  const q = view.querySelector('#ws-q');
  const persist = () => { try { localStorage.setItem(PREF, JSON.stringify({ sort: state.sort })); } catch { /* fine */ } };
  const sortTip = () => {
    const b = view.querySelector('#ws-sort');
    const label = `Сортування: ${SORTS.find((s) => s.value === state.sort)?.label.toLowerCase()}`;
    b.dataset.tip = label; b.setAttribute('aria-label', label);
  };
  const score = (b) => progress(b.completeness).reduce((sum, [, n, total]) => sum + n / total, 0);

  function filtered() {
    const needle = state.query.trim().toLowerCase();
    const list = needle ? state.books.filter((b) => b.title.toLowerCase().includes(needle)) : [...state.books];
    const by = {
      recent: (a, b) => (b.updatedAt || '').localeCompare(a.updatedAt || ''),
      created: (a, b) => (b.createdAt || '').localeCompare(a.createdAt || ''),
      title: (a, b) => naturalCompare(a.title, b.title),
      least: (a, b) => score(a) - score(b) || naturalCompare(a.title, b.title),
    }[state.sort];
    return list.sort(by);
  }

  function card(b, i) {
    const c = b.completeness;
    const parts = progress(c);
    const tip = parts.map(([label, n, total]) => `${label} ${n}/${total}`).join(' · ');
    const front = b.imageW > b.imageH * 1.3;
    const bg = b.lqip ? raw(`style="background-image:url(${b.lqip});background-position:${front ? '100% 50%' : 'center'}"`) : '';
    return html`<button class="book-card ws-card enter" data-key="${b.id}" data-open="${b.id}" aria-label="${b.title}" style="animation-delay:${Math.min(i * 22, 400)}ms">
      <div class="book-frame">
        <div class="book-cover ${b.lqip ? 'lqip' : ''}" ${bg}>
          ${b.image ? html`<img data-fade loading="lazy" decoding="async" alt="" class="${front ? 'front' : ''}" src="${media(`/media/book/${b.id}/${b.image}`, { w: 720 })}">`
            : html`<div class="book-cover-ph"><span class="serif">${(b.title || '?').trim().charAt(0).toUpperCase()}</span></div>`}
          ${ready(c) ? html`<span class="book-badge" data-tip="Готова до бібліотеки">${ic('check')}</span>` : ''}
        </div>
        <i class="crops"></i>
      </div>
      <div class="book-meta">
        <div class="book-title">${b.title}</div>
        <div class="book-id">${ic('image')}<span class="mono">${c.pictures}/${c.picturesTotal}</span>
          <span class="pips" data-tip="${tip}">${parts.map(([, n, total]) => html`<i><b style="transform:scaleX(${n / total})"></b></i>`)}</span></div>
      </div>
    </button>`;
  }

  function renderSub() {
    const n = state.books.length;
    const done = state.books.filter((b) => ready(b.completeness)).length;
    setHtml(view.querySelector('#ws-sub'), n
      ? html`<span class="num">${n}</span> ${plural(n, BOOKS)} у роботі${done ? html` · <span class="num">${done}</span> готов${done === 1 ? 'а' : 'і'} до бібліотеки` : ''}`
      : 'Книги в розробці: промпти, тексти, розвороти');
  }

  function renderEmpty(list) {
    const box = view.querySelector('#ws-empty');
    if (!state.books.length) {
      setHtml(box, html`<div class="empty" style="padding:80px 20px">
        <div class="empty-icon">${ic('workshop')}</div>
        <h3>Майстерня порожня</h3>
        <p>Почніть нову книгу — досить назви. Промпти й тексти можна вписати по одному або залити одним JSON від агента.</p>
        <button class="btn btn-primary" data-act="add">${ic('plus')}Нова книга</button></div>`);
    } else if (!list.length) {
      setHtml(box, html`<div class="empty"><div class="empty-icon">${ic('search')}</div><h3>Нічого не знайдено</h3><p>Спробуйте іншу назву.</p></div>`);
    } else box.innerHTML = '';
  }

  function apply(animate = true) {
    const list = filtered();
    const wanted = new Set(list.map((b) => b.id));
    const mutate = () => {
      const nodes = new Map([...grid.children].map((n) => [n.dataset.key, n]));
      nodes.forEach((n, key) => { n.hidden = !wanted.has(key); });
      const order = [...grid.children].filter((n) => !n.hidden).map((n) => n.dataset.key);
      if (order.join() !== list.map((b) => b.id).join()) list.forEach((b) => grid.appendChild(nodes.get(b.id)));
    };
    if (animate) flip(grid, mutate); else mutate();
    renderEmpty(list);
  }

  setHtml(grid, state.books.map((b, i) => card(b, i)));
  grid.querySelectorAll('.book-card').forEach((n) => n.addEventListener('animationend', () => n.classList.remove('enter'), { once: true }));
  fadeImages(grid);
  renderSub();
  sortTip();
  apply(false);

  const runSearch = debounce(() => apply(true), 90);
  const offs = [
    on(view, 'click', '[data-open]', (e, b) => { location.hash = `#/workshop/${b.dataset.open}`; }),
    on(view, 'click', '[data-act="add"]', () => newBook()),
    on(view, 'click', '[data-act="sort"]', (e, b) => menu(b, SORTS.map((s) => ({
      label: s.label, icon: s.icon, on: state.sort === s.value,
      onClick: () => { state.sort = s.value; persist(); sortTip(); apply(true); },
    })))),
    on(view, 'click', '[data-act="guide"]', (e, b) => guideMenu(b)),
  ];
  q.addEventListener('input', () => { state.query = q.value; runSearch(); });
  const typing = () => /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName || '') || document.querySelector('.modal-root');
  const onKey = (e) => {
    if ((e.ctrlKey && e.key.toLowerCase() === 'f') || (e.key === '/' && !typing())) { e.preventDefault(); q.focus(); q.select(); }
    else if (e.key.toLowerCase() === 'n' && !e.ctrlKey && !e.altKey && !e.metaKey && !typing()) { e.preventDefault(); newBook(); }
  };
  document.addEventListener('keydown', onKey);

  return {
    unmount() { offs.forEach((f) => f()); runSearch.cancel(); document.removeEventListener('keydown', onKey); },
  };
}

// ------------------------------------------------------------------ a new book: a title is all it needs
function newBook() {
  const m = modal({
    title: 'Нова книга',
    sub: 'Лістинг Etsy не потрібен — його вкажете, коли передаватимете книгу в бібліотеку.',
    body: html`<div class="field"><label class="field-label" for="ws-title">Назва книги</label>
      <input class="input" id="ws-title" placeholder="Напр.: Silly Goose — a birthday story" autocomplete="off" autofocus></div>`,
    foot: html`<button class="btn btn-ghost" data-no>Скасувати</button><button class="btn btn-primary" data-yes>${ic('plus')}Створити</button>`,
  });
  const input = m.el.querySelector('#ws-title');
  const create = m.foot.querySelector('[data-yes]');
  m.foot.querySelector('[data-no]').onclick = () => m.close();
  const go = async () => {
    if (!input.value.trim()) { toast('Вкажіть назву книги', 'error'); input.focus(); return; }
    create.disabled = true;
    try {
      const book = await api('/api/workshop/books', { method: 'POST', body: { title: input.value } });
      m.close();
      location.hash = `#/workshop/${book.id}`;
    } catch (err) {
      toast(err.message, 'error');
      create.disabled = false;
    }
  };
  create.onclick = go;
  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); go(); } });
  setTimeout(() => input.focus(), 30);
}

// ------------------------------------------------------------------ the agent's instruction (prompts and texts)
export function guideMenu(anchor) {
  menu(anchor, [
    { label: 'Скопіювати інструкцію для агента', icon: 'copy', onClick: copyGuide },
    { label: 'Зберегти інструкцію у файл…', icon: 'download', onClick: saveGuide },
  ]);
}

export async function copyGuide() {
  try { copyText((await api('/api/workshop/guide')).text, 'Інструкцію скопійовано — вставте її агенту'); }
  catch (err) { toast(err.message, 'error'); }
}

export async function saveGuide() {
  let folder;
  try { folder = (await api('/api/app/pick-folder', { method: 'POST', body: { title: 'Куди зберегти інструкцію?' } })).path; }
  catch (err) { toast(err.message, 'error'); return; }
  if (!folder) return;
  try {
    await api('/api/workshop/guide/save', { method: 'POST', body: { folder } });
    toast('Інструкцію збережено — файл виділено в Провіднику', 'success');
  } catch (err) { toast(err.message, 'error'); }
}
