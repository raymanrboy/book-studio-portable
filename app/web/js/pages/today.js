// «Сьогодні» (2026-09-30, wiki/plans/ui-redesign.md): what needs the owner right now, across every place, in one short
// list — the brand mark opens it. A row is a picture, a few words and a count; nothing is listed that does not need him.
// It only reads (the orders from the last sync, the Workshop's books, what /api/app says about the services): it never
// starts a sync and writes nothing.
import { api, html, ic, setHtml } from '../lib.js';
import { store, refreshInfo } from '../info.js';
import { checkWord } from '../workshop-bits.js';

const row = ({ icon, label, chip = '', tone = '', hash, area, act = '' }) => html`<a class="tool-tile today-row" href="${hash}" data-mode="${area}" ${act ? html`data-stage="${act}"` : ''}>
  <span class="tool-icon">${ic(icon)}</span><span class="tool-text"><b>${label}</b></span>${chip ? html`<span class="chip ${tone}">${chip}</span>` : ''}
  <span class="tool-go">${ic('chevRight')}</span></a>`;

export async function mount(view) {
  let gone = false;
  setHtml(view, html`
    <div class="page-head"><div><h1 class="page-title">Сьогодні</h1></div></div>
    <div class="today-list" id="td"><div class="empty"><div class="empty-icon"><span class="spinner"></span></div></div></div>`);

  const [ords, ws] = await Promise.all([api('/api/orders').catch(() => null), api('/api/workshop/books').catch(() => null), refreshInfo()]);
  if (gone) return {};
  const orders = ords?.orders || [];
  const count = (stage) => orders.filter((o) => o.stage === stage).length;
  const integ = store.info?.integrations || {};
  const missing = [integ.etsy?.connected, integ.printify?.configured, integ.gelato?.configured].filter((x) => x === false).length;

  const rows = [];
  if (count('new')) rows.push(row({ icon: 'inbox', label: 'Нові замовлення', chip: count('new'), tone: 'chip-accent', hash: '#/orders', area: 'orders', act: 'new' }));
  if (count('sent')) rows.push(row({ icon: 'truck', label: 'Трек-номери в Etsy', chip: count('sent'), tone: 'chip-accent', hash: '#/orders', area: 'orders', act: 'sent' }));
  for (const b of (ws?.books || []).filter((x) => !x.library)) {
    const name = `${b.number != null ? `№${b.number} ` : ''}${b.title}`;
    const check = b.steps.find((s) => s.key === 'prompts')?.check;
    const done = (k) => b.steps.find((s) => s.key === k)?.state === 'done';
    if (check && !check.go) rows.push(row({ icon: 'alert', label: name, chip: checkWord(check), tone: 'ws-nogo', hash: `#/workshop/${encodeURIComponent(b.id)}`, area: 'listings' }));
    else if (done('pictures') && done('cover')) rows.push(row({ icon: 'shelf', label: name, chip: ic('check', 'icon-s'), tone: 'ws-go', hash: `#/workshop/${encodeURIComponent(b.id)}`, area: 'listings' }));
  }
  if (missing) rows.push(row({ icon: 'sliders', label: 'Підключення', chip: missing, tone: 'chip-accent', hash: '#/settings', area: 'orders' }));

  setHtml(view.querySelector('#td'), rows.length ? rows
    : html`<div class="empty"><div class="empty-icon">${ic('checkCircle')}</div><p>Усе гаразд — нічого не чекає на вас</p></div>`);

  // A row that leads into the queue opens the tab it is about, not the one the owner last left.
  view.addEventListener('click', async (e) => {
    const a = e.target.closest('[data-stage]');
    if (!a) return;
    e.preventDefault();
    (await import('./orders.js')).openStage(a.dataset.stage);
    location.hash = a.getAttribute('href');
  });
  return { unmount() { gone = true; } };
}
