// The Order Creator's «Замовлення Etsy»: the queue's own orders (GET /api/orders) by stage, searched, the buyer's
// fields unfolded on demand; a picked order goes to `onPick(order)` — the page fills itself in (out of creator.js on
// 27.09.2026).
import {
  api, html, ic, ib, setHtml, modal, toast, segHtml, syncSeg, setSeg, dateTime, relTime, slide, debounce, patch,
} from '../lib.js';
import {
  STAGES, matchesOrder, variationsOf, holdClicks, orderSync, svcChip, countStages, emptyOrders, inTab,
} from '../order-bits.js';

export async function pickEtsyOrder(onPick) {
  let data;
  try { data = await api('/api/orders'); } catch (err) { toast(err.message, 'error'); return; }  // the queue's own list
  let term = '', stage = 'new', shown = [];
  const syncedText = () => (data.syncedAt ? `Оновлено ${relTime(data.syncedAt)}` : 'Ще не завантажено');
  const m = modal({
    title: 'Замовлення Etsy',
    sub: syncedText(),
    size: 'l',
    body: html`<div class="stack"><div class="row eo-head"><div class="input-group grow">${ic('search')}<input class="input" id="eo-q" placeholder="Ім'я покупця або номер чека" aria-label="Пошук замовлення" autofocus></div>
        ${segHtml(STAGES.map((s) => ({ ...s, count: 0 })), stage, { name: 'stage' })}
        <div class="tools">${ib('sync', 'Оновити замовлення з Etsy', 'data-x="sync"')}</div></div>
      <div class="cand-list" id="eo-list" role="listbox" aria-label="Замовлення Etsy" style="max-height:440px"></div></div>`,
    foot: null,
  });
  const list = m.el.querySelector('#eo-list');
  const seg = m.el.querySelector('[data-seg="stage"]');
  const syncBtn = m.el.querySelector('[data-x="sync"]');
  const setSub = (text) => { const node = m.el.querySelector('.modal-sub'); if (node) node.textContent = text; };
  // The buyer's personalization stays folded; the chevron unfolds it as a label/value list,
  // one group per book when the order holds several.
  const unfolded = new Set();
  const details = (o) => html`<div class="acc ${unfolded.has(o.receiptId) ? 'open' : ''}" data-vars="${o.receiptId}"><div>
      ${o.items.map((it) => html`${o.items.length > 1 ? html`<div class="cand-item">${it.quantity > 1 ? `${it.quantity} × ` : ''}${it.title}</div>` : ''}
        <dl class="cand-vars">${(it.variations || []).map((v) => html`<dt>${v.name}</dt><dd>${v.value}</dd>`)}</dl>`)}
    </div></div>`;
  const rowHtml = (o, entering) => html`<div class="cand ${entering ? 'enter' : ''}" data-rid="${o.receiptId}" role="option" aria-selected="false" tabindex="0" data-press style="align-items:flex-start">
      <div class="grow">
        <div class="row" style="gap:8px"><b>${o.name}</b><span class="chip chip-mono">#${o.receiptId}</span>
          ${o.books > 1 ? html`<span class="chip" data-tip="Книг у замовленні">${ic('book', 'icon-s')}${o.books}</span>` : ''}
          ${o.provider ? svcChip(o.provider) : ''}</div>
        <div class="faint" style="font-size: var(--fs-s);margin-top:3px"><span data-tip="${dateTime(o.createdAt)}">${relTime(o.createdAt)}</span> · ${o.coverLabel} · ${[o.address.city, o.address.country_iso].filter(Boolean).join(', ')}</div>
        ${variationsOf(o).length ? details(o) : ''}
      </div>
      ${o.childName ? html`<span class="chip chip-accent">${o.childName}</span>` : ''}
      ${variationsOf(o).length ? ib('chevDown', 'Персоналізація', `data-vars-toggle="${o.receiptId}" aria-expanded="${unfolded.has(o.receiptId)}"`, { cls: `sm details-toggle ${unfolded.has(o.receiptId) ? 'on' : ''}` }) : ''}</div>`;

  const render = ({ fresh = false } = {}) => {
    const t = term.trim().toLowerCase();
    countStages(seg, data.orders, t);
    const rows = data.orders.filter((o) => inTab(o, stage) && matchesOrder(o, t));
    const before = shown;
    shown = rows.map((o) => o.receiptId);
    if (!rows.length) { setHtml(list, emptyOrders(data.orders, t, stage, sync.syncing, 'empty-sm')); return; }
    // in place: a letter in the search or a tab keeps the rows that stay (no flash, no entrance again)
    patch(list, rows.map((o) => [o.receiptId, rowHtml(o, fresh && !before.includes(o.receiptId))]));
    if (fresh && before.join() !== shown.join()) holdClicks(list);
  };

  const sync = orderSync({
    fetch: () => api('/api/orders'), alive: () => m.el.isConnected, setSub, syncedText, button: syncBtn,
    onStart: () => { if (!data.orders.length) render(); },
    onFresh: (next) => { data = next; setSub(syncedText()); render({ fresh: true }); },
  });
  syncBtn.addEventListener('click', () => sync.refresh());
  seg.addEventListener('click', (e) => {
    const b = e.target.closest('button[data-value]');
    if (!b || b.dataset.value === stage) return;
    stage = b.dataset.value;
    setSeg(seg, stage);
    render();
  });
  render();
  sync.follow();
  requestAnimationFrame(() => syncSeg(seg));
  const typed = debounce(() => render(), 90);   // a pause in typing redraws the list, not every letter (04.10.2026)
  m.el.querySelector('#eo-q').addEventListener('input', (e) => { term = e.target.value; typed(); });
  list.addEventListener('click', (e) => {
    const fold = e.target.closest('[data-vars-toggle]');
    if (fold) {
      const id = fold.dataset.varsToggle;
      const open = !unfolded.has(id);
      if (open) unfolded.add(id); else unfolded.delete(id);
      fold.classList.toggle('on', open);
      fold.setAttribute('aria-expanded', String(open));
      const body = list.querySelector(`[data-vars="${id}"]`);
      if (body) slide(body, open);
      return;
    }
    if (e.target.closest('[data-vars]')) return; // reading or copying the personalization is not a choice
    const row = e.target.closest('[data-rid]');
    if (!row) return;
    const o = data.orders.find((x) => x.receiptId === row.dataset.rid);
    m.close();
    onPick(o);
  });
}
