// Library gallery: all reference books, search, active/archive, add a new book.
// Cards are built once; search / filter / sort only hide, show and move them (FLIP animation),
// so images are never reloaded and every change glides with intermediate frames.
import {
  api, html, ic, ib, setHtml, on, media, modal, toast, segHtml, syncSeg, setSeg, fadeImages, plural, naturalCompare,
  raw, flip, debounce, menu, copyText,
} from '../lib.js';
import { store, refreshInfo } from '../app.js';

const PREF = 'bs-lib-view';
const SORTS = [
  { value: 'recent', label: 'Нещодавно змінені', icon: 'clock' },
  { value: 'created', label: 'Нещодавно додані', icon: 'plus' },
  { value: 'title', label: 'За назвою', icon: 'sort' },
  { value: 'incomplete', label: 'Спочатку незавершені', icon: 'alertCircle' },
];

export async function mount(view) {
  const saved = JSON.parse(localStorage.getItem(PREF) || '{}');
  const state = { books: [], filter: saved.filter || 'active', sort: saved.sort || 'recent', query: '' };
  try {
    state.books = (await api('/api/library/books')).books;
  } catch (err) {
    setHtml(view, html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`);
    return null;
  }

  setHtml(view, html`
    <div class="page-head">
      <div>
        <h1 class="page-title">Бібліотека</h1>
        <div class="page-sub" id="lib-sub"></div>
      </div>
    </div>
    <div class="lib-toolbar">
      <div class="input-group">${ic('search')}<input class="input" id="lib-q" placeholder="Назва або ID лістингу" aria-label="Пошук книг" autocomplete="off"></div>
      <div id="lib-seg"></div>
      <div class="tools">${ib('sort', 'Сортування', 'data-act="sort" id="lib-sort"')}${ib('guide', 'Інструкція: як назвати файли й оформити текст', 'data-act="guide"')}</div>
      ${ib('plus', 'Нова книга', 'data-act="add"', { cls: 'primary', kbd: 'N' })}
    </div>
    <div class="lib-grid" id="lib-grid"></div>
    <div id="lib-empty"></div>`);

  const grid = view.querySelector('#lib-grid');
  const q = view.querySelector('#lib-q');
  const persist = () => localStorage.setItem(PREF, JSON.stringify({ filter: state.filter, sort: state.sort }));
  const sortTip = () => {
    const b = view.querySelector('#lib-sort');
    const label = `Сортування: ${SORTS.find((s) => s.value === state.sort)?.label.toLowerCase()}`;
    b.dataset.tip = label; b.setAttribute('aria-label', label);
  };

  const score = (b) => {
    const c = b.completeness;
    return (c.cover ? 1 : 0) + c.illustrations / c.illustrationsTotal + c.texts / c.textsTotal + (c.canva ? 1 : 0);
  };
  function filtered() {
    const needle = state.query.trim().toLowerCase();
    let list = state.books.filter((b) => (state.filter === 'archived') === !!b.archived);
    if (needle) list = list.filter((b) => `${b.title} ${b.listingId || ''}`.toLowerCase().includes(needle));
    const by = {
      recent: (a, b) => (b.updatedAt || '').localeCompare(a.updatedAt || ''),
      created: (a, b) => (b.createdAt || '').localeCompare(a.createdAt || ''),
      title: (a, b) => naturalCompare(a.title, b.title),
      incomplete: (a, b) => score(a) - score(b) || naturalCompare(a.title, b.title),
    }[state.sort];
    return list.sort(by);
  }

  function card(b, i) {
    const c = b.completeness;
    const parts = [['Обкладинка', c.cover ? 1 : 0], ['Ілюстрації', c.illustrations / c.illustrationsTotal],
      ['Тексти', c.texts / c.textsTotal], ['Canva', c.canva ? 1 : 0]];
    const state_ = parts.map(([l, v]) => `${l} ${v === 1 ? '✓' : `${Math.round(v * 100)}%`}`).join(' · ');
    const front = b.imageIsCover && b.imageW > b.imageH * 1.3;
    const bg = b.lqip ? raw(`style="background-image:url(${b.lqip});background-position:${front ? '100% 50%' : 'center'}"`) : '';
    return html`<button class="book-card enter" data-key="${b.id}" data-open="${b.id}" aria-label="${b.title}" style="animation-delay:${Math.min(i * 22, 400)}ms">
      <div class="book-frame">
        <div class="book-cover ${b.lqip ? 'lqip' : ''}" ${bg}>
          ${b.image ? html`<img data-fade loading="lazy" decoding="async" alt="" class="${front ? 'front' : ''}" src="${media(`/media/book/${b.id}/${b.image}`, { w: 720 })}">`
            : html`<div class="book-cover-ph"><span class="serif">${(b.title || '?').trim().charAt(0).toUpperCase()}</span></div>`}
          ${c.complete ? html`<span class="book-badge" data-tip="Книга готова">${ic('check')}</span>` : ''}
        </div>
        <i class="crops"></i>
      </div>
      <div class="book-meta">
        <div class="book-title">${b.title}</div>
        <div class="book-id"><span class="mono">${b.listingId ? `#${b.listingId}` : '—'}</span>${b.verified ? ic('shield') : ''}
          <span class="pips" data-tip="${state_}">${parts.map(([, v]) => html`<i><b style="transform:scaleX(${v})"></b></i>`)}</span></div>
      </div>
    </button>`;
  }

  function renderSeg() {
    const active = state.books.filter((b) => !b.archived).length;
    setHtml(view.querySelector('#lib-seg'), segHtml([
      { value: 'active', icon: 'stack', tip: 'У роботі', count: active },
      { value: 'archived', icon: 'archive', tip: 'Архів', count: state.books.length - active },
    ], state.filter, { name: 'filter' }));
  }

  function renderSub() {
    const activeBooks = state.books.filter((b) => !b.archived);
    const incomplete = activeBooks.filter((b) => !b.completeness.complete).length;
    setHtml(view.querySelector('#lib-sub'), activeBooks.length
      ? html`<span class="num">${activeBooks.length}</span> ${plural(activeBooks.length, ['книга', 'книги', 'книг'])}${incomplete ? html` · <span class="num">${incomplete}</span> не заповнено` : ' · усі готові'}`
      : 'Еталонні книги ваших лістингів Etsy');
  }

  function renderEmpty(list) {
    const box = view.querySelector('#lib-empty');
    if (!state.books.length) {
      setHtml(box, html`<div class="empty" style="padding:80px 20px">
        <div class="empty-icon">${ic('shelf')}</div>
        <h3>Бібліотека порожня</h3>
        <p>Додайте першу книгу за посиланням на лістинг Etsy — обкладинку, ілюстрації й тексти можна докласти пізніше.</p>
        <button class="btn btn-primary" data-act="add">${ic('plus')}Нова книга</button></div>`);
    } else if (!list.length) {
      setHtml(box, html`<div class="empty"><div class="empty-icon">${ic(state.query ? 'search' : 'archive')}</div>
        <h3>${state.query ? 'Нічого не знайдено' : state.filter === 'archived' ? 'Архів порожній' : 'Немає книг у роботі'}</h3>
        <p>${state.query ? 'Спробуйте іншу назву або ID лістингу.' : state.filter === 'archived' ? 'Книги, які ви перенесете в архів, з’являться тут.' : ''}</p></div>`);
    } else box.innerHTML = '';
  }

  // Hide / show / reorder the existing cards. animate=false for the very first paint.
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
  renderSeg();
  sortTip();
  apply(false);

  const runSearch = debounce(() => apply(true), 90);
  const offs = [
    on(view, 'click', '[data-open]', (e, b) => { location.hash = `#/book/${b.dataset.open}`; }),
    on(view, 'click', '[data-act="add"]', () => openAddBook(state.books)),
    on(view, 'click', '[data-act="sort"]', (e, b) => menu(b, SORTS.map((s) => ({
      label: s.label, icon: s.icon, on: state.sort === s.value,
      onClick: () => { state.sort = s.value; persist(); sortTip(); apply(true); },
    })))),
    on(view, 'click', '[data-seg="filter"] button', (e, b) => {
      state.filter = b.dataset.value; setSeg(b.closest('.seg'), state.filter); persist(); apply(true);
    }),
    // The instruction for whoever prepares a book (a person or an AI agent): file names for the batch
    // import and the book-text JSON — saved as a file to hand over, or copied to paste into a chat.
    on(view, 'click', '[data-act="guide"]', (e, b) => menu(b, [
      { label: 'Зберегти інструкцію у файл…', icon: 'download', onClick: saveGuide },
      { label: 'Скопіювати інструкцію', icon: 'copy', onClick: copyGuide },
    ])),
  ];
  q.addEventListener('input', () => { state.query = q.value; runSearch(); });
  const typing = () => /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName || '') || document.querySelector('.modal-root');
  const onKey = (e) => {
    if ((e.ctrlKey && e.key.toLowerCase() === 'f') || (e.key === '/' && !typing())) { e.preventDefault(); q.focus(); q.select(); }
    else if (e.key.toLowerCase() === 'n' && !e.ctrlKey && !e.altKey && !e.metaKey && !typing()) { e.preventDefault(); openAddBook(state.books); }
  };
  document.addEventListener('keydown', onKey);

  return {
    shown() { syncSeg(view.querySelector('#lib-seg .seg')); },
    unmount() { offs.forEach((f) => f()); runSearch.cancel(); document.removeEventListener('keydown', onKey); },
  };
}

// ------------------------------------------------------------------ preparation guide
async function saveGuide() {
  let folder;
  try { folder = (await api('/api/app/pick-folder', { method: 'POST', body: { title: 'Куди зберегти інструкцію?' } })).path; }
  catch (err) { toast(err.message, 'error'); return; }
  if (!folder) return;
  try {
    await api('/api/library/guide/save', { method: 'POST', body: { folder } });
    toast('Інструкцію збережено — файл виділено в Провіднику', 'success');
  } catch (err) { toast(err.message, 'error'); }
}

async function copyGuide() {
  try { copyText((await api('/api/library/guide')).text, 'Інструкцію скопійовано — вставте її агенту'); }
  catch (err) { toast(err.message, 'error'); }
}

// ------------------------------------------------------------------ add book dialog
export function openAddBook(existing = []) {
  const keysReady = !!store.info?.integrations?.etsy?.keysConfigured;
  let listing = null;
  let unverified = !keysReady;

  const m = modal({
    title: 'Нова книга',
    sub: 'Книга прив’язується до лістингу Etsy. Усе інше можна додати пізніше.',
    body: html`<div class="stack">
      <div class="field">
        <label class="field-label">Посилання на лістинг Etsy або його ID</label>
        <div class="input-group">
          <input class="input" id="nb-ref" placeholder="https://www.etsy.com/listing/4542179572/…" autofocus autocomplete="off" style="padding-right:40px">
          ${keysReady ? ib('search', 'Перевірити лістинг', 'id="nb-verify"', { kbd: 'Enter' }) : ''}
        </div>
      </div>
      <div id="nb-result"></div>
      <div id="nb-manual" ${unverified ? '' : 'hidden'}>
        <div class="notice notice-warn" style="margin-bottom:12px">${ic('alert')}<div>${keysReady
          ? 'Лістинг не вдалося перевірити. Можна додати книгу без перевірки — вкажіть назву вручну, а перевірити пізніше.'
          : raw('Ключі Etsy ще не налаштовано (Налаштування → Etsy). Книгу можна додати без перевірки — вкажіть назву вручну.')}</div></div>
        <div class="field"><label class="field-label">Назва книги</label><input class="input" id="nb-title" placeholder="Напр.: Personalized Baptism Storybook"></div>
      </div>
      <div class="field"><label class="field-label">Посилання на макет Canva <span class="faint">(необов'язково)</span></label>
        <input class="input" id="nb-canva" placeholder="https://www.canva.com/design/…" autocomplete="off"></div>
      <label class="check" id="nb-photo-wrap" hidden><input type="checkbox" id="nb-photo" checked><span>Взяти головне фото лістингу як заставку книги</span></label>
    </div>`,
    foot: html`<button class="btn btn-ghost" data-close2>Скасувати</button><button class="btn btn-primary" id="nb-create" disabled>${ic('plus')}Створити книгу</button>`,
  });
  const $ = (s) => m.el.querySelector(s);
  const ref = $('#nb-ref'), result = $('#nb-result'), create = $('#nb-create');
  m.foot.querySelector('[data-close2]').onclick = () => m.close();

  const listingIdOf = (text) => (text.match(/\/listing\/(\d{5,})/) || text.trim().match(/^(\d{5,})$/) || [])[1] || null;

  function refresh() {
    const id = listingIdOf(ref.value);
    const dup = id && existing.find((b) => String(b.listingId) === id);
    if (dup) {
      setHtml(result, html`<div class="notice notice-info">${ic('info')}<div>Ця книга вже є в бібліотеці${dup.archived ? ' (в архіві)' : ''}: <b>${dup.title}</b>.
        <div style="margin-top:8px"><button class="btn btn-sm" data-open-dup="${dup.id}">Відкрити книгу</button></div></div></div>`);
      create.disabled = true;
      return;
    }
    if (listing) create.disabled = false;
    else create.disabled = !(unverified && id && $('#nb-title').value.trim());
  }

  async function verify() {
    const id = listingIdOf(ref.value);
    if (!id) { toast('Вставте посилання на лістинг або його числовий ID', 'error'); return; }
    if (existing.find((b) => String(b.listingId) === id)) { refresh(); return; }
    const btn = $('#nb-verify');
    btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>';
    listing = null;
    try {
      listing = await api(`/api/etsy/listing?ref=${encodeURIComponent(ref.value)}`);
      unverified = false;
      $('#nb-manual').hidden = true;
      const shopId = store.info?.integrations?.etsy?.shopId;
      const otherShop = shopId && listing.shopId && String(shopId) !== String(listing.shopId);
      setHtml(result, html`<div class="card-soft" style="padding:12px;display:flex;gap:12px;align-items:center">
        ${listing.imageUrl ? html`<img src="${listing.imageUrl}" alt="" style="width:64px;height:64px;border-radius:10px;object-fit:cover;flex:none">` : ''}
        <div class="grow"><div style="font-weight:650;line-height:1.35">${listing.title}</div>
          <div class="row-wrap" style="margin-top:6px">
            <span class="chip ${listing.state === 'active' ? 'chip-green' : 'chip-amber'}">${listing.state || 'невідомо'}</span>
            <span class="chip chip-mono">#${listing.id}</span>
            ${listing.shopId ? html`<span class="chip chip-mono">магазин ${listing.shopId}</span>` : ''}
          </div></div></div>
        ${otherShop ? html`<div class="notice notice-warn" style="margin-top:10px">${ic('alert')}<div>Цей лістинг належить іншому магазину (${listing.shopId}), ніж підключений (${shopId}).</div></div>` : ''}`);
      $('#nb-photo-wrap').hidden = !listing.imageUrl;
    } catch (err) {
      unverified = true;
      setHtml(result, html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`);
      $('#nb-manual').hidden = false;
    } finally {
      btn.disabled = false; btn.innerHTML = `${ic('search')}`;
      refresh();
    }
  }

  ref.addEventListener('input', () => { listing = null; result.innerHTML = ''; $('#nb-photo-wrap').hidden = true; refresh(); });
  ref.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); keysReady ? verify() : $('#nb-title').focus(); } });
  ref.addEventListener('paste', () => setTimeout(() => { if (keysReady && listingIdOf(ref.value)) verify(); }, 30));
  if ($('#nb-verify')) $('#nb-verify').onclick = verify;
  $('#nb-title').addEventListener('input', refresh);
  m.el.addEventListener('click', (e) => {
    const d = e.target.closest('[data-open-dup]');
    if (d) { m.close(); location.hash = `#/book/${d.dataset.openDup}`; }
  });

  create.onclick = async () => {
    create.disabled = true;
    create.innerHTML = '<span class="spinner"></span>Створення…';
    try {
      const book = await api('/api/library/books', {
        method: 'POST',
        body: listing
          ? { listing, canvaUrl: $('#nb-canva').value, useListingImage: !!(listing.imageUrl && $('#nb-photo').checked) }
          : { listingRef: ref.value, title: $('#nb-title').value, canvaUrl: $('#nb-canva').value },
      });
      m.close();
      toast('Книгу додано до бібліотеки', 'success');
      refreshInfo();
      location.hash = `#/book/${book.id}`;
    } catch (err) {
      toast(err.message, 'error');
      if (err.data?.bookId) { m.close(); location.hash = `#/book/${err.data.bookId}`; }
      create.disabled = false;
      create.innerHTML = `${ic('plus')}Створити книгу`;
    }
  };
}
