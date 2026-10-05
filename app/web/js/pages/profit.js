// Profit: Etsy Net − Printify/Gelato cost for every Etsy order (analogue of Etsy Profit Calculator),
// plus order states: cancelled, full / partial refund, replacement reprint.
import {
  api, post, html, raw, ic, ib, setHtml, on, modal, toast, runJob, segHtml, syncSeg, setSeg, money, menu, dateTime, relTime,
  plural, slide, debounce, reducedMotion, idle, keepFocus, remembered, remember, setProgress, glide, patch, enterOnce,
} from '../lib.js';
import { stopSpin } from '../order-bits.js';
import { refreshInfo, store } from '../info.js';
import { DEAD_SHORT, costOf, detailHtml, rowInner } from './profit-rows.js';

const PAGE_SIZE = 50;
const PERIODS = [
  { value: 'today', label: 'Сьогодні' },
  { value: '7d', label: '7 днів' },
  { value: 'month', label: '30 днів' },
  { value: 'all', label: 'Увесь час' },
  { value: 'custom', label: 'Свій період' },
];
const toCal = (d) => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
const isIssue = (o) => (o.state && o.state !== 'normal') || o.needs_link || o.pod_dead || o.cost_unknown;

export async function mount(view) {
  const saved = remembered('bs-profit', {}); // the period picked last time
  let gone = false; // the page was let go: its polls stop (runJob keepGoing)
  const st = {
    data: null,
    period: saved.period || 'all',
    start: saved.start || toCal(new Date(Date.now() - 6 * 86400000)),
    end: saved.end || toCal(new Date()),
    query: '',
    filter: 'all',
    details: new Map(),
    candidates: null,
    page: 1,
    open: null,
    syncing: false,
    notice: null,
  };
  const persist = () => remember('bs-profit', { period: st.period, start: st.start, end: st.end });

  setHtml(view, html`
    <div class="page-head">
      <div><h1 class="page-title">Прибуток</h1><div class="page-sub" id="pf-sub"></div></div>
      <div class="page-actions"><div class="tools">${ib('sync', 'Оновити замовлення', 'id="pf-sync"')}${ib('more', 'Інші способи оновлення', 'id="pf-more"')}</div></div>
    </div>
    <div id="pf-progress" class="pf-progress"><div>
      <div class="row"><b id="pf-step"></b><span class="faint" id="pf-detail"></span><span class="spacer"></span><span class="mono faint" id="pf-pct"></span></div>
      <div class="progress progress-thin live indet" id="pf-barbox"><i id="pf-bar"></i></div>
    </div></div>
    <div id="pf-notice" class="pf-notices"></div>
    <div id="pf-kpis" class="kpis"></div>
    <div class="period-bar">
      <span class="row pf-period-label"><span class="pf-period-ico">${ic('calendar', 'icon-s')}</span>Період</span>
      <span class="spacer"></span>
      <div id="pf-period"></div>
      <div class="period-custom ${st.period === 'custom' ? 'open' : ''}" id="pf-custom"><div>
        <div class="row-wrap pf-dates">
          <label class="date-field">Від:<input type="date" id="pf-start" value="${st.start}"></label>
          <label class="date-field">До:<input type="date" id="pf-end" value="${st.end}"></label>
        </div></div></div>
    </div>
    <div class="table-card">
      <div class="table-top">
        <div class="input-group pf-search">${ic('search')}<input class="input" id="pf-q" placeholder="Замовник, чек чи товар…" autocomplete="off"></div>
        <div id="pf-filter"></div>
        <span class="spacer"></span>
        <span class="pf-count" data-tip="Замовлень у вибірці">${ic('receipt', 'icon-s')}<b class="num" id="pf-count">0</b></span>
      </div>
      <div id="pf-table"></div>
    </div>`);

  const $ = (s) => view.querySelector(s);
  setHtml($('#pf-period'), segHtml(PERIODS, st.period, { accent: true, name: 'period' }));
  requestAnimationFrame(() => syncSeg($('#pf-period .seg')));

  // ---------------------------------------------------------------- data shaping
  function inPeriod(o) {
    if (st.period === 'all' || !o.created_at) return true;
    const d = new Date(o.created_at);
    if (Number.isNaN(d.getTime())) return true;
    const now = new Date();
    if (st.period === 'today') return d >= new Date(now.getFullYear(), now.getMonth(), now.getDate());
    if (st.period === '7d') return d >= new Date(now.getTime() - 7 * 86400000);
    if (st.period === 'month') return d >= new Date(now.getTime() - 30 * 86400000);
    if (st.period === 'custom') return d >= new Date(`${st.start}T00:00:00`) && d <= new Date(`${st.end}T23:59:59`);
    return true;
  }
  const periodRows = () => (st.data?.rows || []).filter(inPeriod);
  function visibleRows() {
    const term = st.query.trim().toLowerCase();
    return periodRows().filter((o) => {
      if (st.filter === 'unmatched' && o.profit !== null) return false;
      if (st.filter === 'issues' && !isIssue(o)) return false;
      if (!term) return true;
      // The server pre-builds one lowercase search string per order (name, receipt, Printify number, titles).
      return (o.search || `${o.customer_name || ''} ${o.id}`.toLowerCase()).includes(term);
    });
  }
  // How many days of the chosen period are inside the books (not before the clean slate, not after today).
  function periodDays() {
    const day = new Date(new Date().getFullYear(), new Date().getMonth(), new Date().getDate());
    const from = st.data?.accountingFrom ? new Date(`${st.data.accountingFrom}T00:00:00`) : null;
    let start = new Date(day);
    if (st.period === '7d') start.setDate(start.getDate() - 6);
    else if (st.period === 'month') start.setDate(start.getDate() - 29);
    else if (st.period === 'custom') start = new Date(`${st.start}T00:00:00`);
    else if (st.period === 'all') start = from || day;
    let end = st.period === 'custom' ? new Date(`${st.end}T00:00:00`) : day;
    if (end > day) end = day;
    if (from && start < from) start = from;
    return Math.max(0, Math.round((end - start) / 86400000) + 1);
  }
  function kpi(rows) {
    let net = 0, cost = 0, profit = 0, n = 0, impact = 0, issues = 0;
    for (const o of rows) {
      if (o.profit === null || o.profit === undefined) continue;
      const c = costOf(o);
      const special = o.state && o.state !== 'normal';
      // Normal orders count once their cost is known (as in the original); cancelled/refunded/replaced ones always.
      if (c > 0 || special || o.pod_dead) { net += o.etsy_net || 0; cost += c; profit += o.profit || 0; n++; }
      if (special) { impact += o.impact || 0; issues++; }
    }
    const r2 = (v) => Math.round(v * 100) / 100;
    // Ads and new listings a day (profit.OVERHEAD_PER_DAY): counted into the profit and the margin, not shown (2026-10-05).
    if (n) profit -= periodDays() * (st.data?.overheadPerDay || 0);
    return { net: r2(net), cost: r2(cost), profit: r2(profit), margin: net > 0 ? Math.round((profit / net) * 1000) / 10 : 0, n, impact: r2(impact), issues };
  }

  // ---------------------------------------------------------------- render
  function renderHead() {
    const d = st.data;
    const bits = [];
    if (d?.shopName) bits.push(`магазин ${d.shopName}`);
    if (d?.gelatoConnected) bits.push('Gelato');  // only the printers connected now (2026-10-05)
    if (d?.printifyShop?.title) bits.push(`Printify: ${d.printifyShop.title}`);
    bits.push(st.syncing ? 'оновлення…' : d?.syncedAt ? `оновлено ${relTime(d.syncedAt)}` : 'ще не оновлено');
    $('#pf-sub').textContent = bits.join(' · ');
    $('#pf-sync').disabled = st.syncing;
    { const ico = $('#pf-sync').firstElementChild; if (st.syncing) ico?.classList.add('spin'); else stopSpin(ico); }
    $('#pf-more').disabled = st.syncing;
  }

  function renderNotice() {
    const box = $('#pf-notice');
    const n = st.notice;
    const warnings = st.data?.warnings || [];
    const parts = [];
    if (n) parts.push(html`<div class="notice notice-${n.type}">${ic(n.type === 'success' ? 'checkCircle' : 'alertCircle')}<div class="grow">${n.text}
      ${n.settings ? html`<div class="pf-notice-act"><a class="btn btn-sm" href="#/settings/etsy">Відкрити налаштування</a></div>` : ''}</div></div>`);
    if (warnings.length && st.data?.mode !== 'empty') parts.push(html`<div class="notice notice-warn">${ic('alert')}<div>${warnings.map((w) => html`<div>${w}</div>`)}</div></div>`);
    setHtml(box, parts);
  }

  function renderFilter() {
    const issues = periodRows().filter(isIssue).length;
    const opts = [{ value: 'all', label: 'Усі' }, { value: 'unmatched', label: 'Без пари' },
      { value: 'issues', label: issues ? `Проблемні · ${issues}` : 'Проблемні' }];
    setHtml($('#pf-filter'), segHtml(opts, st.filter, { name: 'filter' }));
    requestAnimationFrame(() => syncSeg($('#pf-filter .seg')));
  }

  // KPI cards are built once; on every change the numbers count to their new values (tweened per frame).
  const shownKpi = { net: 0, cost: 0, profit: 0, margin: 0 };
  let kpiRaf = 0;
  function renderKpis() {
    const k = kpi(periodRows());
    const box = $('#pf-kpis');
    if (!box.querySelector('[data-k]')) {
      const card = (key, label, iconName, tone) => html`<div class="kpi ${tone}" data-card="${key}">
        <div class="kpi-label"><span data-l="${key}">${label}</span><span class="kpi-ico">${ic(iconName, 'icon-s')}</span></div>
        <div class="kpi-value" data-k="${key}"></div><div class="kpi-foot" data-f="${key}"></div></div>`;
      setHtml(box, [
        card('net', 'На руки (Etsy Net)', 'dollar', 'tone-green'),
        card('cost', 'Собівартість друку', 'bag', ''),
        card('profit', 'Чистий прибуток', 'chart', 'tone-green'),
        card('margin', 'Середня маржа', 'shield', ''), // a number, not an action: no ink of its own (2026-09-30)
      ]);
    }
    // With Etsy's ledger the first card is the Etsy balance — what Etsy pays out next — and under it what the program
    // expects there by its own sums: equal means the sums are right (the owner, 2026-10-05). Without it, the period's Etsy Net.
    const bal = st.data?.etsyBalance;
    const orders = `${k.n} ${plural(k.n, ['замовлення', 'замовлення', 'замовлень'])}`;
    const nf = box.querySelector('[data-f="net"]');
    box.querySelector('[data-l="net"]').textContent = bal ? 'Доступно до виводу' : 'На руки (Etsy Net)';
    box.querySelector('[data-f="cost"]').textContent = bal ? orders : '';
    if (bal?.expected) {
      const off = Math.abs(bal.balance - bal.expected.amount) > 1;
      const day = (t) => new Date(t * 1000).toLocaleDateString('uk-UA', { day: 'numeric', month: 'long' });
      const last = bal.lastPayout;
      nf.textContent = `за розрахунком ${money(bal.expected.amount)}`;
      nf.dataset.tip = [`Баланс Etsy, не залежить від періоду. Розрахунок програми: що лишилось після виплати ${day(bal.expected.from)} + ${bal.expected.orders} ${plural(bal.expected.orders, ['замовлення', 'замовлення', 'замовлень'])} відтоді − реклама й лістинги`,
        last ? `Виплата ${day(last.at)}: ${money(last.amount)}, за розрахунком ${money(last.expected.amount)}` : ''].filter(Boolean).join('. ');
      nf.classList.toggle('warn', off);
    } else {
      nf.textContent = bal ? '' : orders;
      nf.dataset.tip = '';
      nf.classList.remove('warn');
    }
    box.classList.toggle('kpi-none', !k.n); // no sales in the period: grey zeros, not green ones that look earned
    const pf = box.querySelector('[data-f="profit"]');
    pf.textContent = k.issues ? `Повернення й заміни: ${money(k.impact)}` : '';
    pf.dataset.tip = k.issues ? `${k.issues} ${plural(k.issues, ['замовлення', 'замовлення', 'замовлень'])}: скасування, повернення, заміни` : '';
    pf.classList.toggle('neg', Boolean(k.issues && k.impact < 0));
    const card = box.querySelector('[data-card="profit"]');
    card.classList.toggle('tone-green', k.profit >= 0);
    card.classList.toggle('tone-red', k.profit < 0);
    const from = { ...shownKpi };
    const to = { net: bal ? bal.balance : k.net, cost: k.cost, profit: k.profit, margin: k.margin };
    const fmt = { net: money, cost: money, profit: money, margin: (v) => `${(Math.round(v * 10) / 10).toFixed(1).replace(/\.0$/, '')}%` };
    const start = performance.now();
    // First paint shows final numbers (the page transition is the entrance); later changes count smoothly.
    const dur = reducedMotion() || !st.kpiShown ? 0 : 520;
    st.kpiShown = true;
    cancelAnimationFrame(kpiRaf);
    const step = (now) => {
      const t = dur ? Math.min(1, (now - start) / dur) : 1;
      const e = 1 - Math.pow(1 - t, 3); // ease-out cubic
      for (const key of Object.keys(to)) {
        shownKpi[key] = from[key] + (to[key] - from[key]) * e;
        box.querySelector(`[data-k="${key}"]`).textContent = fmt[key](t === 1 ? to[key] : shownKpi[key]);
      }
      if (t < 1) kpiRaf = requestAnimationFrame(step);
    };
    if (dur === 0) step(start); // no tween: the numbers are written now (a frame callback may never run, e.g. in a hidden window)
    else kpiRaf = requestAnimationFrame(step);
  }

  function renderTable() {
    const rows = visibleRows();
    $('#pf-count').textContent = rows.length;
    const box = $('#pf-table');
    const d = st.data;
    // A custom period that ends before it begins matches nothing: the two dates light up and the empty list says why.
    const badRange = st.period === 'custom' && !!st.start && !!st.end && st.start > st.end;
    $('#pf-start').classList.toggle('is-missing', badRange);
    $('#pf-end').classList.toggle('is-missing', badRange);
    if (!d) return;
    if (d.mode === 'empty') {
      const integ = store.info?.integrations || {};
      const ready = integ.etsy?.connected || integ.printify?.configured;
      setHtml(box, html`<div class="empty"><div class="empty-icon">${ic(ready ? 'sync' : 'key')}</div>
        <h3>${ready ? 'Даних ще немає' : 'Підключіть Etsy та Printify'}</h3>
        ${ready ? '' : html`<p>Потрібні доступ до Etsy і токен Printify; Gelato — за бажанням.</p>`}
        ${ready ? html`<button class="btn btn-primary" data-act="sync">${ic('sync')}Оновити</button>` : html`<a class="btn btn-primary" href="#/settings">${ic('sliders')}Відкрити налаштування</a>`}</div>`);
      return;
    }
    const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
    st.page = Math.min(Math.max(1, st.page), pages);
    const slice = rows.slice((st.page - 1) * PAGE_SIZE, st.page * PAGE_SIZE);
    if (!slice.length) {
      // Bookkeeping counts only sales from its first day (profit.ACCOUNTING_FROM): until then the page is empty.
      const none = !(d.rows || []).length && d.accountingFrom;
      setHtml(box, html`<div class="empty"><div class="empty-icon">${ic(none ? 'calendar' : 'package')}</div><h3>${none
        ? `Продажів від ${new Date(`${d.accountingFrom}T00:00:00`).toLocaleDateString('uk-UA', { day: 'numeric', month: 'long' })} ще немає`
        : badRange ? 'Дата «Від» пізніша за «До» — поміняйте їх місцями'
        : st.filter === 'issues' ? 'Проблемних замовлень немає' : 'Замовлень не знайдено'}</h3></div>`);
      return;
    }
    // The rows are drawn in place (patch(), keyed by order): a filter, a period or a page keeps the rows that stay, and the ones
    // new to the table come in one after another; the whole table is no longer replaced (every row flashed).
    if (!box.querySelector('.olist-rows')) {
      setHtml(box, html`<div class="olist" role="table">
        <div class="ohead" role="row"><div>Замовлення Etsy (доставка)</div><div class="r">На руки (Etsy Net)</div><div class="r">Собівартість</div><div class="r">Чистий прибуток</div><div class="c">Зіставлення</div></div>
        <div class="olist-rows"></div></div><div id="pf-pager"></div>`);
    }
    const rowsEl = box.querySelector('.olist-rows');
    const known = new Set([...rowsEl.children].map((n) => n.dataset.key));
    patch(rowsEl, slice.map((o) => [o.id, html`<div class="oitem">
        <div class="orow ${st.open === o.id ? 'open' : ''}" role="row" data-row="${o.id}">${rowInner(o, st.data?.mode)}</div>
        <div class="acc ${st.open === o.id && st.details.has(o.id) ? 'open' : ''}" data-acc="${o.id}"><div>${st.open === o.id && st.details.has(o.id) ? detailHtml(st.details.get(o.id), st.data?.mode) : ''}</div></div>
      </div>`]));
    if (!reducedMotion()) [...rowsEl.children].filter((n) => !known.has(n.dataset.key)).forEach((n, i) => enterOnce(n, Math.min(i * 18, 220)));
    setHtml(box.querySelector('#pf-pager'), pages > 1 ? html`<div class="pager"><span><b>${st.page}</b> з <b>${pages}</b></span>
        <span class="tools">${ib('chevLeft', 'Попередня сторінка', `data-page="-1" ${st.page === 1 ? 'disabled' : ''}`)}${ib('chevRight', 'Наступна сторінка', `data-page="1" ${st.page === pages ? 'disabled' : ''}`)}</span></div>` : '');
    requestAnimationFrame(() => view.querySelectorAll('.state-seg .seg').forEach(syncSeg));
  }

  function renderAll() { renderHead(); renderNotice(); renderKpis(); renderFilter(); renderTable(); }

  // Details (fees, address, items) are fetched when a row is opened, then the row grows smoothly.
  function closeRow(id) {
    view.querySelector(`.orow[data-row="${CSS.escape(id)}"]`)?.classList.remove('open');
    const acc = view.querySelector(`[data-acc="${CSS.escape(id)}"]`);
    if (acc) slide(acc, false);
  }
  async function toggle(id) {
    const prev = st.open;
    if (prev) closeRow(prev);
    if (prev === id) { st.open = null; return; }
    st.open = id;
    view.querySelector(`.orow[data-row="${CSS.escape(id)}"]`)?.classList.add('open');
    let full = st.details.get(id);
    if (!full) {
      try { full = await api(`/api/profit/row?id=${encodeURIComponent(id)}`); } catch (err) { toast(err.message, 'error'); return; }
      st.details.set(id, full);
    }
    if (st.open !== id) return;
    const acc = view.querySelector(`[data-acc="${CSS.escape(id)}"]`);
    if (!acc) return;
    setHtml(acc.firstElementChild, detailHtml(full, st.data?.mode));
    slide(acc, true);
    requestAnimationFrame(() => acc.querySelectorAll('.state-seg .seg').forEach(syncSeg));
  }

  // One order changed: its row and open panel are updated in place; the panel height glides to the new size.
  function patchRow(id) {
    const slim = st.data?.rows.find((r) => r.id === id);
    const rowEl = view.querySelector(`.orow[data-row="${CSS.escape(id)}"]`);
    if (slim && rowEl) setHtml(rowEl, rowInner(slim, st.data?.mode));
    const acc = view.querySelector(`[data-acc="${CSS.escape(id)}"]`);
    const full = st.details.get(id);
    if (acc && full && st.open === id) {
      glide(acc, () => keepFocus(() => setHtml(acc.firstElementChild, detailHtml(full, st.data?.mode))));
      requestAnimationFrame(() => acc.querySelectorAll('.state-seg .seg').forEach(syncSeg));
    }
    renderKpis();
    renderFilter();
  }

  // ---------------------------------------------------------------- data & sync
  async function load(render = true) {
    try { st.data = await api('/api/profit/data'); }
    catch (err) { st.notice = { type: 'error', text: err.message }; st.data = { rows: [], mode: 'empty' }; }
    st.details.clear();
    st.candidates = null;
    st.open = null;
    if (render) renderAll();
    // Provider orders for manual matching are fetched in idle time, so the dialog opens instantly.
    if (st.data?.mode === 'etsy') idle(() => { ensureCandidates().catch(() => {}); });
  }
  async function ensureCandidates() {
    if (!st.candidates) st.candidates = (await api('/api/profit/candidates')).candidates;
    return st.candidates;
  }

  let noticeTimer;
  async function sync(full = false) {
    if (st.syncing) return;
    st.syncing = true; st.notice = null;
    renderHead(); renderNotice();
    setProgress($('#pf-bar'), 0, { reset: true }); // not from the last run's end
    $('#pf-barbox').classList.add('indet');
    $('#pf-pct').textContent = '';
    $('#pf-progress').classList.add('on');
    try {
      const res = await runJob(post('/api/profit/sync', { full }), (j) => {
        $('#pf-step').textContent = j.step;
        $('#pf-detail').textContent = j.detail ? ` · ${j.detail}` : '';
        const known = j.percent > 0;
        $('#pf-pct').textContent = known ? `${Math.round(j.percent)}%` : '';
        $('#pf-barbox').classList.toggle('indet', !known);
        setProgress($('#pf-bar'), known ? j.percent : 0);
      }, 420, () => !gone);
      const etsyPart = res.changed === null || res.changed === undefined
        ? `Завантажено ${res.receipts} ${plural(res.receipts, ['замовлення', 'замовлення', 'замовлень'])} Etsy.`
        : `Змінених чеків Etsy: ${res.changed} (усього ${res.receipts}).`;
      st.notice = res.etsyConnected
        ? { type: 'success', text: `Оновлено. ${etsyPart} Зіставлено з Printify/Gelato: ${res.matched}.` }
        : { type: 'success', text: `Etsy не підключено — завантажено ${res.printify} замовлень Printify.` };
      clearTimeout(noticeTimer);
      noticeTimer = setTimeout(() => {
        if (st.notice?.type !== 'success') return;
        const gone = () => { if (st.notice?.type === 'success') { st.notice = null; renderNotice(); } };
        const el = $('#pf-notice').firstElementChild; // fades out (150 ms) before the list closes over it
        if (el && !reducedMotion()) el.animate([{ opacity: 1 }, { opacity: 0, transform: 'translateY(-4px)' }], { duration: 150, easing: 'ease-out', fill: 'forwards' }).finished.then(gone, gone);
        else gone();
      }, 5000);
      st.page = 1;
      await load();
      refreshInfo();
    } catch (err) {
      if (gone) return;
      const code = err.data?.code || '';
      st.notice = { type: 'error', text: err.message, settings: /etsy|not_configured/.test(code) || /Etsy|Налаштування/.test(err.message) };
      renderNotice();
    } finally {
      st.syncing = false;
      if (!gone) { $('#pf-progress').classList.remove('on'); renderHead(); }
    }
  }

  // ---------------------------------------------------------------- order state
  function stateBody(o, patch = {}) {
    const status = patch.status || o.state || 'normal';
    const body = { receiptId: o.etsy_receipt_id, status, note: patch.note ?? o.state_note ?? '' };
    if (status === 'refund_partial') {
      body.refundAmount = patch.refundAmount ?? (o.state === 'refund_partial' ? o.refund_amount : (o.etsy_refund_total || ''));
    }
    if (status === 'replacement') {
      body.replacementOrders = patch.replacementOrders ?? (o.replacement_orders || []).map((r) => ({ provider: r.provider, orderId: r.id }));
      body.replacementCost = patch.replacementCost ?? (o.replacement_manual || '');
    }
    return body;
  }
  let saving = Promise.resolve();
  function saveState(id, patch) {
    // Saves run one after another, so quick clicks never overwrite each other out of order.
    saving = saving.then(async () => {
      const o = st.details.get(id);
      if (!o) return;
      // Replacement orders are withheld from automatic matching, which can change other rows too.
      const wide = patch.replacementOrders !== undefined || patch.status === 'replacement' || o.state === 'replacement';
      try {
        const res = await post('/api/profit/state', stateBody(o, patch));
        const summary = await api('/api/profit/data');
        st.data = summary;
        st.candidates = null;
        // A replacement can take a provider order away from another receipt: other cached panels are stale.
        st.details.clear();
        if (res.row) st.details.set(id, res.row);
        if (wide) { keepFocus(renderTable); renderKpis(); renderFilter(); } else patchRow(id);
        // Guide to the one thing still missing: the refunded amount, or which order was the reprint.
        const now = st.details.get(id);
        if (patch.status === 'refund_partial' && !now?.refund_amount) document.getElementById(`st-amt-${id}`)?.focus();
        if (patch.status === 'replacement' && !patch.replacementOrders && !(now?.replacement_orders || []).length && !now?.replacement_manual) openReplacement(id);
      } catch (err) {
        toast(err.message, 'error');
        patchRow(id);
      }
    });
    return saving;
  }
  // «12,5», «12.50», «1,234.56» and «1.234,56» all read as a number: the last separator is the decimal point, unless it is
  // the only one and stands before exactly three digits (a thousands mark: «1,234»).
  const parseMoney = (v) => {
    let t = String(v || '').replace(/[^\d.,]/g, '');
    if (t === '') return '';
    const dot = t.lastIndexOf('.'), comma = t.lastIndexOf(',');
    if (dot >= 0 && comma >= 0) {
      const dec = dot > comma ? '.' : ',';
      t = t.split(dec === '.' ? ',' : '.').join('').replace(dec, '.');
    } else if (comma >= 0) t = t.split(',').length > 2 || /^\d{1,3},\d{3}$/.test(t) ? t.split(',').join('') : t.replace(',', '.');
    else if (dot >= 0 && t.split('.').length > 2) t = `${t.slice(0, dot).split('.').join('')}.${t.slice(dot + 1)}`;
    const n = Number(t);
    return Number.isNaN(n) ? '' : n;
  };

  // ---------------------------------------------------------------- provider order picker
  async function orderPicker({ o, title, sub, multi = false, selected = [], exclude = [], foot, onFoot }) {
    try { await ensureCandidates(); } catch (err) { toast(err.message, 'error'); return; }
    const norm = (s) => (s || '').toLowerCase().replace(/[^\p{L}\p{N}\s]/gu, '').replace(/\s+/g, ' ').trim();
    const words = new Set(norm(o.customer_name).split(' ').filter((w) => w.length > 1));
    const skip = new Set(exclude);
    const taken = (c) => (c.usedBy && c.usedBy.receipt !== o.id ? 1 : 0);
    const cands = st.candidates.filter((c) => !skip.has(`${c.provider}:${c.id}`))
      .map((c) => ({ ...c, score: norm(c.name).split(' ').filter((w) => words.has(w)).length }))
      .sort((a, b) => b.score - a.score || taken(a) - taken(b) || (b.createdAt || '').localeCompare(a.createdAt || ''));
    const sel = new Set(selected.filter(Boolean));
    let provider = 'all', term = '';

    const m = modal({
      title, sub, size: 'l',
      body: html`<div class="stack">
        <div class="row">
          <div class="input-group grow">${ic('search')}<input class="input" id="mm-q" placeholder="Пошук за ім'ям або номером замовлення…" autofocus></div>
          ${segHtml([{ value: 'all', label: 'Усі' }, { value: 'printify', label: 'Printify' }, { value: 'gelato', label: 'Gelato' }], 'all', { name: 'prov' })}
        </div>
        <div class="cand-list" id="mm-list" role="listbox" aria-label="Замовлення друкарні"${multi ? raw(' aria-multiselectable="true"') : ''}></div>
      </div>`,
      foot,
    });
    requestAnimationFrame(() => syncSeg(m.el.querySelector('.seg')));
    const list = m.el.querySelector('#mm-list');
    const saveBtn = m.foot.querySelector('[data-x="save"]');
    const syncSave = () => { if (saveBtn) saveBtn.disabled = !multi && !sel.size; };
    syncSave();

    let limit = 60; // render a screenful at once; more on demand (keeps the modal opening in one frame)
    function usedNote(c) {
      const u = c.usedBy;
      if (!u || u.receipt === o.id) return '';
      return u.kind === 'replacement' ? ` · заміна для чека #${u.receipt}` : ` · у чеку #${u.receipt}${u.name ? ` (${u.name})` : ''}`;
    }
    function renderList() {
      const t = term.trim().toLowerCase();
      const all = cands.filter((c) => (provider === 'all' || c.provider === provider)
        && (!t || c.name.toLowerCase().includes(t) || c.id.toLowerCase().includes(t) || String(c.label).toLowerCase().includes(t)));
      const shown = all.slice(0, limit);
      const more = all.length - shown.length;
      setHtml(list, shown.length ? [...shown.map((c) => {
        const key = `${c.provider}:${c.id}`;
        return html`<div class="cand ${sel.has(key) ? 'sel' : ''}" data-key="${key}" role="option" aria-selected="${String(sel.has(key))}" tabindex="0" data-press>
          <span class="${multi ? 'box' : 'radio'}"></span>
          <div class="cand-main"><div class="cand-name"><b class="truncate">${c.name}</b>${c.score ? html`<span class="chip chip-green">схоже</span>` : ''}
            ${c.dead ? html`<span class="chip">${DEAD_SHORT[c.dead]}</span>` : ''}</div>
            <div class="cand-meta">#${c.label} · ${dateTime(c.createdAt)}${c.status ? ` · ${c.status}` : ''}${usedNote(c)}</div></div>
          <span class="chip ${c.provider === 'gelato' ? 'chip-blue' : 'chip-lime'}">${c.provider === 'gelato' ? 'Gelato' : 'Printify'}</span>
          <b class="num cand-cost">${money(c.cost)}</b></div>`;
      }), more > 0 ? html`<button class="btn btn-ghost btn-sm btn-block cand-more" data-more>Показати ще (${more})</button>` : '']
        : html`<div class="empty empty-sm">Замовлень не знайдено</div>`);
    }
    renderList();
    const onSearch = debounce(() => { limit = 60; renderList(); }, 80);
    m.el.querySelector('#mm-q').addEventListener('input', (e) => { term = e.target.value; onSearch(); });
    m.el.addEventListener('click', (e) => {
      if (e.target.closest('[data-more]')) { limit += 150; renderList(); return; }
      const c = e.target.closest('.cand');
      if (c) {
        const key = c.dataset.key;
        if (multi) { if (sel.has(key)) sel.delete(key); else sel.add(key); c.classList.toggle('sel', sel.has(key)); c.setAttribute('aria-selected', String(sel.has(key))); }
        else { sel.clear(); sel.add(key); list.querySelectorAll('.cand').forEach((x) => { x.classList.toggle('sel', x === c); x.setAttribute('aria-selected', String(x === c)); }); }
        syncSave();
      }
      const segB = e.target.closest('[data-seg="prov"] button');
      if (segB) { provider = segB.dataset.value; setSeg(segB.closest('.seg'), provider); renderList(); }
    });
    if (!multi) m.el.addEventListener('dblclick', (e) => { if (e.target.closest('.cand')) saveBtn?.click(); });
    m.foot.addEventListener('click', async (e) => {
      const b = e.target.closest('[data-x]');
      if (!b) return;
      if (b.dataset.x === 'cancel') { m.close(); return; }
      b.disabled = true;
      try { if (await onFoot(b.dataset.x, [...sel])) m.close(); } finally { b.disabled = false; }
    });
  }

  function openMatch(id) {
    const o = st.data.rows.find((r) => r.id === id);
    if (!o) return;
    const current = o.pod_provider === 'printify' ? `printify:${o.printify_order_id}` : o.pod_provider === 'gelato' ? `gelato:${o.gelato_order_id}` : '';
    orderPicker({
      o,
      title: 'Зіставлення замовлення',
      sub: `Покупець: ${o.customer_name} · Чек #${o.etsy_receipt_id} · Etsy Net ${money(o.etsy_net)}`,
      selected: [current],
      foot: html`
        ${o.match_type === 'manual' || o.link_blocked ? html`<button class="btn btn-ghost btn-ghost-danger" data-x="reset">${ic('unlink', 'icon-s')}Скинути ручний зв'язок</button>` : ''}
        ${!o.link_blocked ? html`<button class="btn btn-ghost" data-x="none" data-tip="Замовлення виконано поза Printify і Gelato">Без собівартості</button>` : ''}
        <span class="spacer"></span>
        <button class="btn btn-ghost" data-x="cancel">Скасувати</button>
        <button class="btn btn-primary" data-x="save">${ic('link', 'icon-s')}Зберегти пару</button>`,
      async onFoot(x, keys) {
        try {
          if (x === 'reset') await api(`/api/profit/links?receipt=${encodeURIComponent(o.etsy_receipt_id)}`, { method: 'DELETE' });
          else if (x === 'none') await post('/api/profit/links', { receiptId: o.etsy_receipt_id, provider: 'none' });
          else if (x === 'save' && keys[0]) {
            const [prov, orderId] = keys[0].split(/:(.+)/);
            await post('/api/profit/links', { receiptId: o.etsy_receipt_id, provider: prov, orderId });
          } else return false;
          toast(x === 'reset' ? 'Ручний зв’язок скинуто' : x === 'none' ? 'Позначено без собівартості' : 'Пару збережено', 'success');
          await load();
          return true;
        } catch (err) { toast(err.message, 'error'); return false; }
      },
    });
  }

  function openReplacement(id) {
    const o = st.details.get(id);
    if (!o) return;
    const primary = o.pod_provider === 'printify' ? `printify:${o.printify_order_id}` : o.pod_provider === 'gelato' ? `gelato:${o.gelato_order_id}` : '';
    orderPicker({
      o,
      multi: true,
      title: 'Замовлення заміни',
      sub: `${o.customer_name} · Чек #${o.etsy_receipt_id} · оберіть замовлення, якими книгу передрукували за ваш рахунок`,
      selected: (o.replacement_orders || []).map((r) => `${r.provider}:${r.id}`),
      exclude: [primary],
      foot: html`<span class="spacer"></span>
        <button class="btn btn-ghost" data-x="cancel">Скасувати</button>
        <button class="btn btn-primary" data-x="save">${ic('check', 'icon-s')}Зберегти заміну</button>`,
      async onFoot(x, keys) {
        if (x !== 'save') return false;
        const refs = keys.map((k) => { const [provider, orderId] = k.split(/:(.+)/); return { provider, orderId }; });
        await saveState(id, { status: 'replacement', replacementOrders: refs });
        return true;
      },
    });
  }

  // ---------------------------------------------------------------- events
  const offs = [
    on(view, 'click', '[data-toggle]', (e, t) => toggle(t.dataset.toggle)),
    on(view, 'click', '[data-match]', (e, t) => { e.stopPropagation(); openMatch(t.dataset.match); }),
    on(view, 'click', '[data-page]', (e, t) => { st.page += +t.dataset.page; st.open = null; renderTable(); view.querySelector('.table-card').scrollIntoView({ behavior: 'smooth', block: 'start' }); }),
    on(view, 'click', '[data-act="sync"]', () => sync()),
    on(view, 'click', '[data-seg="period"] button', (e, b) => {
      st.period = b.dataset.value; setSeg(b.closest('.seg'), st.period); persist();
      $('#pf-custom').classList.toggle('open', st.period === 'custom');
      st.page = 1; st.open = null; renderKpis(); renderFilter(); renderTable();
    }),
    on(view, 'click', '[data-seg="filter"] button', (e, b) => {
      st.filter = b.dataset.value; setSeg(b.closest('.seg'), st.filter);
      st.page = 1; st.open = null; renderTable();
    }),
    on(view, 'click', '.state-seg [data-seg] button', (e, b) => {
      const id = b.closest('[data-state-box]').dataset.stateBox;
      const o = st.details.get(id);
      if (!o || b.dataset.value === o.state) return;
      setSeg(b.closest('.seg'), b.dataset.value); // the pill glides right away; numbers follow after saving
      saveState(id, { status: b.dataset.value });
    }),
    on(view, 'click', '[data-state-auto]', (e, b) => saveState(b.dataset.stateAuto, { status: 'auto' })),
    on(view, 'click', '[data-repl-add]', (e, b) => openReplacement(b.dataset.replAdd)),
    on(view, 'click', '[data-repl-remove]', (e, b) => {
      const id = b.dataset.rowId;
      const o = st.details.get(id);
      const refs = (o?.replacement_orders || []).filter((r) => `${r.provider}:${r.id}` !== b.dataset.replRemove).map((r) => ({ provider: r.provider, orderId: r.id }));
      saveState(id, { status: 'replacement', replacementOrders: refs });
    }),
  ];
  // Amount / cost / note fields save when the user leaves the field or presses Enter.
  const commitField = (input) => {
    const o = st.details.get(input.dataset.stateAmount || input.dataset.stateRcost || input.dataset.stateNote);
    if (!o) return;
    if (input.dataset.stateAmount) {
      const v = parseMoney(input.value);
      if (v !== '' && Math.abs(v - (o.refund_amount || 0)) < 0.005) return;
      saveState(o.id, { status: 'refund_partial', refundAmount: v });
    } else if (input.dataset.stateRcost) {
      const v = parseMoney(input.value);
      if (Math.abs((v || 0) - (o.replacement_manual || 0)) < 0.005) return;
      saveState(o.id, { status: 'replacement', replacementCost: v });
    } else {
      if (input.value.trim() === (o.state_note || '')) return;
      saveState(o.id, { note: input.value.trim() });
    }
  };
  const fieldSel = '[data-state-amount], [data-state-rcost], [data-state-note]';
  view.addEventListener('focusout', (e) => { if (e.target.matches?.(fieldSel)) commitField(e.target); });
  view.addEventListener('keydown', (e) => { if (e.key === 'Enter' && e.target.matches?.(fieldSel)) { e.preventDefault(); e.target.blur(); } });

  $('#pf-sync').addEventListener('click', () => sync());
  $('#pf-more').addEventListener('click', (e) => menu(e.currentTarget, [
    { label: 'Швидке оновлення (лише змінені чеки)', icon: 'sync', onClick: () => sync(false) },
    { label: 'Повна синхронізація (усі чеки заново)', icon: 'download', onClick: () => sync(true) },
  ]));
  const runSearch = debounce(() => { st.page = 1; st.open = null; renderTable(); }, 90);
  $('#pf-q').addEventListener('input', (e) => { st.query = e.target.value; runSearch(); });
  $('#pf-start').addEventListener('change', (e) => { st.start = e.target.value; persist(); st.page = 1; renderKpis(); renderFilter(); renderTable(); });
  $('#pf-end').addEventListener('change', (e) => { st.end = e.target.value; persist(); st.page = 1; renderKpis(); renderFilter(); renderTable(); });

  setHtml($('#pf-kpis'), Array.from({ length: 4 }, () => html`<div class="kpi"><div class="skeleton sk-label"></div><div class="skeleton sk-value"></div></div>`));
  await load();
  return { unmount() { gone = true; offs.forEach((f) => f()); clearTimeout(noticeTimer); runSearch.cancel(); cancelAnimationFrame(kpiRaf); } };
}
