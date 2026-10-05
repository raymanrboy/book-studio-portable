// The printer's history in a placed order's card: Gelato's status and its events, newest first, as a timeline, and
// when Gelato expects it delivered. Asked for when the card is opened — one order, never the whole queue, never at
// launch — so the card shows a skeleton for a second or two. Beside the order's data; what it shows comes from the
// server's GET /api/orders/<receipt>/history (gelato.history()).
import { api, html, ic, attr, raw, setHtml, on, openExternal, dateTime } from './lib.js';
import { statusText } from './order-bits.js';

// A status as a picture (first match wins); nothing known — the hourglass: it has not happened yet.
const ICONS = [[/deliver/, 'checkCircle'], [/transit/, 'truck'], [/ship/, 'package'], [/product|print/, 'printer'],
  [/passed/, 'check'], [/cancel|fail|return|connect|refus/, 'alertCircle']];
const iconOf = (status) => (ICONS.find(([re]) => re.test(status || '')) || [0, 'hourglass'])[1];

const clock = (at) => (at ? new Date(at).toLocaleString('uk-UA', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '');
const day = (at) => new Date(at).toLocaleDateString('uk-UA', { day: 'numeric', month: 'long' });

function rows(data) {
  const events = data.events || [];
  const expected = data.due?.length && !/deliver|cancel|return/.test(data.status) ? data.due[data.due.length - 1] : '';
  if (!events.length && !expected) return html`<div class="oh-note">Gelato поки не записав подій.</div>`;
  return html`<ol class="oh-list">
    ${expected ? html`<li class="oh-item is-due"><span class="oh-dot">${ic('calendar', 'icon-s')}</span>
      <div class="oh-what"><b>Очікується до ${day(expected)}</b></div></li>` : ''}
    ${events.map((e, i) => html`<li class="oh-item${i === 0 ? ' is-now' : ''}">
      <span class="oh-dot">${ic(iconOf(e.status), 'icon-s')}</span>
      <div class="oh-what"><b>${e.status ? statusText(e.status) : e.text}</b>${e.status && e.text ? html`<span class="oh-text">${e.text}</span>` : ''}</div>
      <time class="oh-time" data-tip="${dateTime(e.at)}">${clock(e.at)}</time></li>`)}
  </ol>`;
}

/** Fills `host` (an empty element of the card) with the history of order `o`; removes it when there is nothing to
 *  ask about (not placed, or not at Gelato). Returns a function that stops it (the card closed). */
export function mountHistory(host, o) {
  let data = null;
  let ask = 0;
  let state = 'busy';
  let error = '';

  function paint() {
    const url = data?.shipments?.find((s) => s.url)?.url || '';
    const body = state === 'error' && !data ? html`<div class="oh-note oh-fail">Не вдалося отримати історію: ${error}</div>`
      : data ? rows(data)
        : html`<div class="oh-wait">${[0, 1, 2].map(() => html`<div class="skeleton oh-sk"></div>`)}</div>`;
    setHtml(host, html`<section class="card card-pad oh-card">
      <div class="row"><h3 class="card-title grow">Історія</h3>
        ${url ? raw(`<button type="button" class="ib" aria-label="Відстежити в перевізника" data-tip="Відстежити в перевізника" data-act="hist-track" ${attr('data-url', url)}>${ic('external')}</button>`) : ''}
        <button type="button" class="ib" aria-label="Оновити історію" data-tip="Оновити історію" data-act="hist-refresh">${ic('sync', state === 'busy' ? 'spin' : '')}</button>
      </div>
      ${state === 'error' && data ? html`<div class="oh-note oh-fail">Не вдалося оновити: ${error}</div>` : ''}
      ${body}
    </section>`);
  }

  async function load(fresh) {
    const mine = ++ask;
    state = 'busy';
    paint();
    try {
      const got = await api(`/api/orders/${o.receiptId}/history${fresh ? '?fresh=1' : ''}`);
      if (mine !== ask || !host.isConnected) return;
      if (!got.available) { host.remove(); document.querySelector('.ord-grid')?.classList.remove('ord-hist'); return; }
      data = got;
      state = 'ready';
    } catch (err) {
      if (mine !== ask || !host.isConnected) return;
      state = 'error';
      error = err.message || 'невідома помилка';
    }
    paint();
  }

  const stops = [
    on(host, 'click', '[data-act="hist-refresh"]', () => load(true)),
    on(host, 'click', '[data-act="hist-track"]', (e, el) => openExternal(el.dataset.url)),
  ];
  load(false);
  return () => { ask += 1; stops.forEach((stop) => stop()); };
}
