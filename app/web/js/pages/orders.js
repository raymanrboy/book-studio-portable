// Orders: the queue of Etsy orders — by stage, searched by name or receipt, the printer and its status at a
// glance; a row opens the order's card (order-card.js).
import {
  api, html, ic, ib, raw, setHtml, on, segHtml, syncSeg, setSeg, relTime, dateTime, fadeImages, patch, enterOnce,
} from '../lib.js';
import {
  STAGES, matchesOrder, providerName, planText, trackChips, statusChip, receiptCopy, copyChip, alsoSentChip,
  holdClicks, orderSync, svcChip, countStages, emptyOrders, bookImage,
} from '../order-bits.js';
import { settle } from '../keep.js';
import { mountCard } from './order-card.js';

export function mount(view, [rid]) {
  return rid ? mountCard(view, rid) : mountQueue(view);
}

// ==================================================================== queue
// Where the owner was in the queue — the tab, the search, how far down: the card's back arrow (and Esc, the
// Orders icon) bring him back there, not to «Нові» (owner, 19.09.2026). Memory only: the program starts at «Нові».
const queueState = { stage: 'new', term: '', scroll: 0, visited: false };

async function mountQueue(view) {
  let data;
  try { data = await api('/api/orders'); }
  catch (err) { setHtml(view, html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`); return null; }
  settle(data.orders); // kept cards of orders that are no longer new are let go
  let { stage, term } = queueState;
  let shown = [];
  const returning = queueState.visited; // coming back: the rows stand where they were, no entrance
  queueState.visited = true;

  setHtml(view, html`
    <div class="page-head"><div><h1 class="page-title">Замовлення</h1><div class="page-sub" id="or-sub"></div></div></div>
    <div class="bk-tabs">${segHtml(STAGES.map((s) => ({ ...s, count: 0 })), stage, { name: 'stage', compact: true })}</div>
    <div class="lib-toolbar">
      <div class="input-group">${ic('search')}<input class="input" id="or-q" placeholder="Ім'я покупця або номер чека" aria-label="Пошук замовлення" autocomplete="off"></div>
      ${ib('sync', 'Оновити замовлення з Etsy і друкарень', 'data-act="sync"')}
    </div>
    <div class="ord-list" id="or-list"></div>
    <div id="or-empty"></div>`);
  const $ = (s) => view.querySelector(s);
  const list = $('#or-list');
  const empty = $('#or-empty');
  const seg = view.querySelector('[data-seg="stage"]');
  const syncBtn = view.querySelector('[data-act="sync"]');
  const syncedText = () => (data.syncedAt ? `Оновлено ${relTime(data.syncedAt)}` : 'Ще не завантажено');
  const setSub = (text) => { $('#or-sub').textContent = text; };

  // Once ordered: where it was ordered. Before that: where the printer rule sends it.
  const printerChip = (o) => {
    const p = o.provider || (o.stage === 'new' ? o.plan?.provider : null);
    if (!p) return o.stage === 'new' ? html`<span class="chip chip-amber" data-tip="${planText(o.plan)}">${ic('alert', 'icon-s')}друкарня?</span>` : '';
    const tip = o.provider ? `Замовлено в ${providerName(p)}` : planText(o.plan);
    return svcChip(p, { tip });
  };
  const rowHtml = (o) => html`<a class="ord-row" href="#/orders/${o.receiptId}" data-rid="${o.receiptId}">
      <span class="ord-thumb ${o.book?.lqip ? 'lqip' : ''}" ${o.book?.lqip ? raw(`style="background-image:url(${o.book.lqip})"`) : ''}>
        ${o.book?.image ? html`<img data-fade loading="lazy" decoding="async" src="${bookImage(o.book, 160)}" alt="">` : ic('book')}</span>
      <span class="ord-main">
        <span class="row ord-chips"><b class="truncate">${o.name}</b>${receiptCopy(o, 'chip chip-mono')}
          ${o.books > 1 ? html`<span class="chip" data-tip="Книг у замовленні">${ic('book', 'icon-s')}${o.books}</span>` : ''}${printerChip(o)}${alsoSentChip(o)}${trackChips(o)}</span>
        <span class="ord-meta faint truncate"><span data-tip="${dateTime(o.createdAt)}">${relTime(o.createdAt)}</span> ·
          ${o.childName ? html`<b class="ord-child">${o.childName}</b> · ` : ''}${o.book ? o.book.title : html`<span class="ord-miss">книги немає в бібліотеці</span>`} · ${[o.address.city, o.address.country_iso].filter(Boolean).join(', ')}</span>
      </span>
      ${statusChip(o) || html`<span></span>`}
      <span class="ord-go">${ic('chevRight')}</span>
    </a>`;

  // The tab's rows are drawn once and redrawn in place (patch()): a search only hides rows, so typing never reloads a
  // thumbnail or replays an entrance (every letter redrew every row until 26.09.2026). A row new to the tab comes in
  // with the entrance: all of them on the first look, the new orders after a refresh.
  let drawnOnce = false;
  const render = ({ fresh = false } = {}) => {
    const before = shown;
    const known = new Set([...list.children].map((n) => n.dataset.key));
    const drawn = patch(list, data.orders.filter((o) => o.stage === stage).map((o) => [o.receiptId, rowHtml(o)]));
    const entering = (!drawnOnce && !returning) || fresh;
    drawn.filter((n) => entering && !known.has(n.dataset.key))
      .forEach((n, i) => enterOnce(n, drawnOnce ? 0 : Math.min(i * 30, 300)));
    drawnOnce = true;
    narrow();
    fadeImages(list);
    if (fresh && before.join() !== shown.join()) holdClicks(list);
  };
  // What the search hides and shows — typing only runs this: no row is built again for a letter (04.10.2026).
  const narrow = () => {
    const t = term.trim().toLowerCase();
    countStages(seg, data.orders, t);
    shown = data.orders.filter((o) => o.stage === stage && matchesOrder(o, t)).map((o) => o.receiptId);
    const visible = new Set(shown);
    [...list.children].forEach((n) => { n.hidden = !visible.has(n.dataset.key); });
    setHtml(empty, shown.length ? '' : emptyOrders(data.orders, t, stage, sync.syncing));
  };

  const sync = orderSync({
    fetch: async () => { const next = await api('/api/orders'); settle(next.orders); return next; },
    alive: () => view.isConnected, setSub, syncedText, button: syncBtn,
    onStart: () => { if (!data.orders.length) render(); },
    onFresh: (next) => { data = next; setSub(syncedText()); render({ fresh: true }); },
  });

  const offs = [
    on(view, 'click', '[data-act="sync"]', () => sync.refresh()),
    on(view, 'click', '[data-act="copy-text"]', copyChip),
    on(view, 'click', '[data-seg="stage"] button', (e, b) => {
      if (b.dataset.value === stage) return;
      stage = queueState.stage = b.dataset.value;
      setSeg(seg, stage);
      render();
    }),
  ];
  const q = $('#or-q');
  q.value = term;
  q.addEventListener('input', () => { term = queueState.term = q.value; narrow(); });
  q.addEventListener('keydown', (e) => { if (e.key === 'Enter' && shown.length) location.hash = `#/orders/${shown[0]}`; });

  setSub(syncedText());
  render();
  sync.follow();
  const main = document.getElementById('main');
  return {
    shown() {
      syncSeg(seg);
      if (returning) main.scrollTo({ top: queueState.scroll, behavior: 'instant' }); // .main scrolls smoothly otherwise
    },
    unmount() { queueState.scroll = main.scrollTop; offs.forEach((f) => f()); clearTimeout(list.holdTimer); },
  };
}
