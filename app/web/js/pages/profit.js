// Profit: Etsy Net − Printify/Gelato cost for every Etsy order (analogue of Etsy Profit Calculator),
// plus order states: cancelled, full / partial refund, replacement reprint.
import {
  api, html, ic, ib, setHtml, on, modal, toast, runJob, segHtml, syncSeg, setSeg, money, signedMoney, menu,
  dateTime, relTime, plural, slide, debounce, reducedMotion, idle, keepFocus, remembered, remember,
} from '../lib.js';
import { refreshInfo, store } from '../info.js';

const PAGE_SIZE = 50;
const PERIODS = [
  { value: 'today', label: 'Сьогодні' },
  { value: '7d', label: '7 днів' },
  { value: 'month', label: '30 днів' },
  { value: 'all', label: 'Увесь час' },
  { value: 'custom', label: 'Свій період' },
];
const STATE_OPTS = [
  { value: 'normal', label: 'Звичайне' },
  { value: 'canceled', label: 'Скасовано' },
  { value: 'refund_full', label: 'Повне повернення' },
  { value: 'refund_partial', label: 'Часткове повернення' },
  { value: 'replacement', label: 'Заміна' },
];
const STATE_TEXT = { normal: 'звичайне', canceled: 'скасовано', refund_full: 'повне повернення', refund_partial: 'часткове повернення', replacement: 'заміна' };
const STATE_CHIP = { canceled: 'chip-red', refund_full: 'chip-red', refund_partial: 'chip-amber', replacement: 'chip-purple' };
const EASE = 'cubic-bezier(.22, 1, .36, 1)';
const toCal = (d) => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
const usd = (n) => (n === null || n === undefined ? '—' : n < 0 ? `-$${Math.abs(n).toFixed(2)}` : `$${Number(n).toFixed(2)}`);
const costOf = (o) => o.cost_total ?? ((o.pod_total_cost || 0) > 0 ? o.pod_total_cost : (o.printify_total_cost || 0));
const isIssue = (o) => (o.state && o.state !== 'normal') || o.needs_link || o.pod_dead || o.cost_unknown;
const podName = (o) => (o.pod_provider === 'gelato' ? 'Gelato' : 'Printify');
// Why the print order costs nothing (outcomes.unpaid()): a draft, not paid yet (on hold, awaiting payment), cancelled.
const DEAD_SHORT = { draft: 'чернетка', unpaid: 'не оплачено', canceled: 'скасовано' };
const deadText = (o) => (o.pod_dead === 'draft' ? 'чернетка Gelato — не оплачена'
  : o.pod_dead === 'unpaid' ? `ще не оплачено в ${podName(o)}` : `скасовано в ${podName(o)}`);

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
    <div id="pf-progress" class="pf-progress" hidden>
      <div class="row"><b id="pf-step"></b><span class="faint" id="pf-detail"></span><span class="spacer"></span><span class="mono faint" id="pf-pct"></span></div>
      <div class="progress progress-thin"><i id="pf-bar"></i></div>
    </div>
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
    return { net: r2(net), cost: r2(cost), profit: r2(profit), margin: net > 0 ? Math.round((profit / net) * 1000) / 10 : 0, n, impact: r2(impact), issues };
  }

  // ---------------------------------------------------------------- render
  function renderHead() {
    const d = st.data;
    const bits = [];
    if (d?.shopName) bits.push(`магазин ${d.shopName}`);
    if (d?.printifyShop?.title) bits.push(`Printify: ${d.printifyShop.title}`);
    bits.push(st.syncing ? 'оновлення…' : d?.syncedAt ? `оновлено ${relTime(d.syncedAt)}` : 'ще не оновлено');
    $('#pf-sub').textContent = bits.join(' · ');
    $('#pf-sync').disabled = st.syncing;
    $('#pf-sync').firstElementChild?.classList.toggle('spin', st.syncing);
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
        <div class="kpi-label"><span>${label}</span><span class="kpi-ico">${ic(iconName, 'icon-s')}</span></div>
        <div class="kpi-value" data-k="${key}"></div><div class="kpi-foot" data-f="${key}"></div></div>`;
      setHtml(box, [
        card('net', 'На руки (Etsy Net)', 'dollar', 'tone-green'),
        card('cost', 'Собівартість друку', 'bag', ''),
        card('profit', 'Чистий прибуток', 'chart', 'tone-green'),
        card('margin', 'Середня маржа', 'shield', 'tone-accent'),
      ]);
    }
    box.querySelector('[data-f="net"]').textContent = `${k.n} ${plural(k.n, ['замовлення', 'замовлення', 'замовлень'])}`;
    const pf = box.querySelector('[data-f="profit"]');
    pf.textContent = k.issues ? `Повернення й заміни: ${usd(k.impact)}` : '';
    pf.dataset.tip = k.issues ? `${k.issues} ${plural(k.issues, ['замовлення', 'замовлення', 'замовлень'])}: скасування, повернення, заміни` : '';
    pf.classList.toggle('neg', Boolean(k.issues && k.impact < 0));
    const card = box.querySelector('[data-card="profit"]');
    card.classList.toggle('tone-green', k.profit >= 0);
    card.classList.toggle('tone-red', k.profit < 0);
    const from = { ...shownKpi };
    const to = { net: k.net, cost: k.cost, profit: k.profit, margin: k.margin };
    const fmt = { net: money, cost: money, profit: usd, margin: (v) => `${(Math.round(v * 10) / 10).toFixed(1).replace(/\.0$/, '')}%` };
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
    kpiRaf = requestAnimationFrame(step);
  }

  function providerCell(o) {
    const cost = costOf(o);
    const matched = o.match_type && o.match_type !== 'unmatched';
    if (o.needs_link) {
      return html`<button class="cost-btn" data-toggle="${o.id}" data-tip="Знайдено лише ${deadText(o)} — зв'яжіть актуальне замовлення"><span class="chip chip-amber">${ic('alert', 'icon-s')}Потрібна пара</span><span class="chev">${ic('chevDown', 'icon-s')}</span></button>`;
    }
    if (cost > 0 || (matched && o.pod_dead) || (o.state === 'canceled' && o.profit !== null)) {
      const gel = o.pod_provider === 'gelato';
      const sub = !matched ? html`<span class="prov prov-none">без друку</span>`
        : html`<span class="prov ${gel ? 'prov-gelato' : 'prov-printify'}">${gel ? 'Gelato' : 'Printify'}${o.is_bundle ? html` <span class="prov-note bundle">(1/${o.bundle_count || 2})</span>` : ''}${o.pod_dead ? html` <span class="prov-note">${DEAD_SHORT[o.pod_dead]}</span>` : ''}</span>`;
      return html`<button class="cost-btn" data-toggle="${o.id}">
        <span class="cost-sum"><b class="num">${money(cost)}</b>${sub}
          ${o.replacement_cost > 0 ? html`<span class="prov prov-note bundle">у т.ч. заміна ${money(o.replacement_cost)}</span>` : ''}</span>
        <span class="chev">${ic('chevDown', 'icon-s')}</span></button>`;
    }
    return html`<button class="cost-btn" data-toggle="${o.id}"><span class="chip chip-amber">${ic('clock', 'icon-s')}Не зіставлено</span><span class="chev">${ic('chevDown', 'icon-s')}</span></button>`;
  }

  function statusCell(o) {
    if (st.data?.mode === 'printify_only') return html`<span class="chip chip-lime">Printify</span>`;
    const matched = o.match_type && o.match_type !== 'unmatched';
    if (matched && (o.pod_dead === 'unpaid' || o.cost_unknown)) {
      const tip = o.cost_unknown ? `Gelato списує в ${o.gelato_currency} — курсу до долара немає`
        : `Замовлення в ${podName(o)} ще не оплачене — прибуток буде після оплати`;
      return html`<button class="chip chip-amber chip-btn" data-match="${o.id}" data-tip="${tip}">${ic('clock', 'icon-s')}${o.cost_unknown ? o.gelato_currency : 'Не оплачено'}</button>`;
    }
    if (o.profit !== null && o.profit !== undefined && !matched) {
      return html`<button class="chip chip-btn" data-match="${o.id}" data-tip="Скасовано до друку — витрат немає">${ic('check', 'icon-s')}Без витрат</button>`;
    }
    if (o.profit !== null && o.profit !== undefined) {
      return html`<button class="chip chip-green chip-btn" data-match="${o.id}" data-tip="${o.match_type === 'manual' ? 'Зв’язано вручну' : 'Знайдено автоматично'}">
        ${ic(o.match_type === 'manual' ? 'link' : 'checkCircle', 'icon-s')}${o.match_type === 'manual' ? 'Вручну' : 'Зіставлено'}</button>`;
    }
    if (o.link_blocked) return html`<button class="chip chip-btn" data-match="${o.id}" data-tip="Позначено без собівартості">${ic('unlink', 'icon-s')}Без друку</button>`;
    return html`<button class="chip chip-accent chip-btn" data-match="${o.id}">${ic('link', 'icon-s')}Зв'язати</button>`;
  }

  function stateChip(o) {
    if (!o.state || o.state === 'normal') return '';
    const text = o.state === 'refund_partial' && o.refund_amount ? `повернення ${usd(-o.refund_amount)}` : STATE_TEXT[o.state];
    return html`<span class="chip ${STATE_CHIP[o.state]}" data-tip="${o.state_manual ? 'Статус встановлено вручну' : 'Статус з Etsy'}">${o.state_manual ? ic('edit', 'icon-s') : ''}${text}</span>`;
  }

  function netCell(o) {
    if (o.etsy_net === undefined) return html`<span class="faint">—</span>`;
    const changed = o.state && o.state !== 'normal' && o.etsy_net_original !== undefined && Math.abs(o.etsy_net - o.etsy_net_original) > 0.004;
    return html`<div class="o-net ${o.etsy_net < 0 ? 'neg' : o.etsy_net === 0 ? 'zero' : ''}">${usd(o.etsy_net)}</div>
      ${changed ? html`<div class="o-was" data-tip="До повернення">${money(o.etsy_net_original)}</div>` : o.etsy_fees > 0 ? html`<div class="o-fees">збори: -$${o.etsy_fees.toFixed(2)}</div>` : ''}`;
  }

  function rowInner(o) {
    return html`
      <div><div class="o-name truncate" data-toggle="${o.id}">${o.customer_name}</div><div class="o-sub truncate">${stateChip(o)}${o.cover_label}</div></div>
      <div class="r num">${netCell(o)}</div>
      <div class="r">${providerCell(o)}</div>
      <div class="r">${o.profit !== null && o.profit !== undefined ? html`<span class="profit-pill ${o.profit > 0 ? 'profit-pos' : o.profit < 0 ? 'profit-neg' : 'profit-zero'}">${o.profit === 0 ? '$0.00' : signedMoney(o.profit)}</span>
        ${o.profit_margin !== null && o.profit_margin !== undefined ? html`<div class="o-margin">маржа ${o.profit_margin}%</div>` : ''}` : html`<span class="faint">—</span>`}</div>
      <div class="c">${statusCell(o)}</div>`;
  }

  // ---------------------------------------------------------------- order state panel
  function econLines(o) {
    const s = o.state;
    if (!s || s === 'normal') return '';
    const lines = [];
    const line = (label, value, cls = '') => lines.push(html`<span>${label}</span><b class="${cls || (value < 0 ? 'neg' : value > 0 ? 'pos' : '')}">${value > 0 ? '+' : ''}${usd(value)}</b>`);
    line(s === 'replacement' ? 'Etsy Net (на руки)' : 'Etsy Net до повернення', o.etsy_net_original);
    if (s === 'canceled' || s === 'refund_full' || s === 'refund_partial') {
      line(`Повернено покупцю${o.revenue_back !== o.refund_amount ? ' (без податку США, його повертає Etsy)' : ''}`, -o.revenue_back);
      line(s === 'canceled' ? 'Etsy повернув усі свої збори' : 'Etsy повернув частину зборів', o.fee_credit);
    }
    const matched = o.match_type && o.match_type !== 'unmatched';
    if (o.needs_link) lines.push(html`<span>Друк і доставка</span><b class="faint">невідомо — потрібна пара</b>`);
    else if (matched && o.pod_dead) lines.push(html`<span>Друк і доставка (${deadText(o)})</span><b>$0.00</b>`);
    else if (matched) line(`Друк і доставка (${podName(o)})`, -(o.pod_total_cost || 0));
    else if (s === 'canceled') lines.push(html`<span>Друк і доставка</span><b>не було</b>`);
    else lines.push(html`<span>Друк і доставка</span><b class="faint">невідомо — потрібна пара</b>`);
    if (s === 'replacement') line('Передрук (заміна)', -(o.replacement_cost || 0));
    lines.push(html`<span class="sum">Результат замовлення</span><b class="sum ${o.profit < 0 ? 'neg' : ''}">${o.profit === null || o.profit === undefined ? '—' : signedMoney(o.profit)}</b>`);
    return html`<div class="econ">${lines}</div>`;
  }

  function stateBox(o) {
    const s = o.state || 'normal';
    const id = o.id;
    return html`<div class="dbox state-box" data-state-box="${id}">
      <div class="dbox-title">Статус замовлення
        <span class="dbox-note">· в Etsy: ${STATE_TEXT[o.state_auto || 'normal']}${o.state_manual ? ', тут змінено вручну' : ''}</span>
        <span class="spacer"></span>
        ${o.state_manual ? html`<button class="btn btn-ghost btn-xs" data-state-auto="${id}" data-tip="Повернути статус, який показує Etsy">${ic('restore', 'icon-s')}Як в Etsy</button>` : ''}
      </div>
      <div class="state-seg">${segHtml(STATE_OPTS, s, { name: `state-${id}` })}</div>
      ${s === 'refund_partial' ? html`<div class="state-extra">
        <label class="st-label" for="st-amt-${id}">Сума повернення покупцю, $</label>
        <input class="input mono" id="st-amt-${id}" data-state-amount="${id}" inputmode="decimal" value="${o.refund_amount ? o.refund_amount.toFixed(2) : ''}" placeholder="${o.etsy_refund_total ? o.etsy_refund_total.toFixed(2) : '0.00'}">
        <span class="state-hint">з ${money(o.fee_breakdown?.gross)}</span>
      </div>` : ''}
      ${s === 'replacement' ? html`<div class="state-extra">
        <span class="st-label">Передрук:</span>
        ${(o.replacement_orders || []).map((r) => html`<span class="chip chip-purple chip-mono">${r.provider === 'gelato' ? 'Gelato' : 'Printify'} #${r.label} · ${r.dead ? DEAD_SHORT[r.dead] : money(r.cost)}
          <button class="chip-x" data-repl-remove="${r.provider}:${r.id}" data-row-id="${id}" aria-label="Прибрати" data-tip="Прибрати">${ic('x', 'icon-s')}</button></span>`)}
        <button class="btn btn-xs" data-repl-add="${id}">${ic('plus', 'icon-s')}${(o.replacement_orders || []).length ? 'Ще замовлення' : 'Обрати замовлення Printify / Gelato'}</button>
        <label class="st-label push" for="st-rc-${id}">Інші витрати, $</label>
        <input class="input mono" id="st-rc-${id}" data-state-rcost="${id}" inputmode="decimal" value="${o.replacement_manual ? o.replacement_manual.toFixed(2) : ''}" placeholder="0.00">
      </div>` : ''}
      ${s !== 'normal' ? html`<div class="state-extra">
        <label class="st-label" for="st-note-${id}">Примітка</label>
        <input class="input state-note" id="st-note-${id}" data-state-note="${id}" value="${o.state_note || ''}" placeholder="Причина: пошкоджено в доставці, помилка в імені…" maxlength="500">
      </div>` : ''}
      ${econLines(o)}
      ${(o.refunds || []).length ? html`<div class="state-hint state-refunds">Повернення в Etsy: ${o.refunds.map((r) => `${r.at ? dateTime(new Date(r.at * 1000).toISOString()) : ''} · ${money(r.amount)}${r.reason ? ` · ${r.reason}` : ''}${r.note ? ` · «${r.note}»` : ''}`).join('; ')}</div>` : ''}
    </div>`;
  }

  function detailHtml(o) {
    const fb = o.fee_breakdown;
    const a = o.shipping_address || {};
    const gel = o.pod_provider === 'gelato';
    const cityLine = [a.city, a.state ? `${a.state} ${a.zip || ''}`.trim() : a.zip, a.country_iso].filter(Boolean).join(', ');
    return html`<div class="detail">
      <div class="detail-ids">
        ${o.etsy_receipt_id ? html`<span class="chip chip-accent chip-mono">Чек Etsy: #${o.etsy_receipt_id}</span>` : ''}
        ${gel ? html`<span class="chip chip-blue chip-mono">Gelato: #${o.gelato_order_reference || (o.gelato_order_id || '').slice(-8).toUpperCase()}</span>`
          : o.printify_order_id ? html`<span class="chip chip-lime chip-mono">Printify: #${o.app_order_id || o.printify_order_id.slice(-6).toUpperCase()}</span>` : ''}
        ${o.pod_dead ? html`<span class="chip">${deadText(o)}</span>` : ''}
        ${o.is_bundle ? html`<span class="chip chip-purple">${ic('package', 'icon-s')}Спільна посилка: 1 з ${o.bundle_count || 2}</span>` : ''}
        ${o.match_type === 'manual' ? html`<span class="chip">${ic('link', 'icon-s')}зв'язано вручну</span>` : ''}
        ${o.is_shipped ? html`<span class="chip chip-green">відправлено</span>` : o.status ? html`<span class="chip">${o.status}</span>` : ''}
        <span class="spacer"></span>
        <span class="detail-date">${dateTime(o.created_at)}</span>
        ${st.data?.mode === 'etsy' ? html`<button class="btn btn-xs" data-match="${o.id}">${ic('link', 'icon-s')}Змінити зіставлення</button>` : ''}
      </div>
      ${st.data?.mode === 'etsy' ? stateBox(o) : ''}
      ${st.data?.mode === 'etsy' ? html`<div class="detail-grid">
        <div class="dbox"><div class="dbox-title">Адреса доставки</div>
          <div class="dbox-strong">${a.name || o.customer_name}</div>
          ${a.first_line || a.second_line ? html`<div class="muted">${[a.first_line, a.second_line].filter(Boolean).join(', ')}</div>` : ''}
          ${cityLine ? html`<div class="muted">${cityLine}</div>` : ''}
        </div>
        <div class="dbox"><div class="dbox-title">Товари Etsy</div>
          ${(o.items || []).length ? o.items.map((it) => html`<div class="item-line"><span class="truncate muted">${it.quantity}× ${it.title}</span><b class="num">$${(it.price || 0).toFixed(2)}</b></div>
            ${(it.variations || []).length ? html`<div class="item-vars">${it.variations.map((v) => `${v.name}: ${v.value}`).join(' · ')}</div>` : ''}`) : html`<span class="faint">—</span>`}
          ${fb?.discount_amt > 0 ? html`<div class="item-line item-discount"><span>Знижка магазину / купон:</span><b class="num">-$${fb.discount_amt.toFixed(2)}</b></div>` : ''}
        </div>
      </div>` : ''}
      ${fb ? html`<div class="dbox">
        <div class="dbox-title">Утримання Etsy<span class="spacer"></span><span class="dbox-note">Разом: <b class="num neg">-$${(fb.total_etsy_fees + fb.sales_tax).toFixed(2)}</b></span></div>
        <div class="fee-grid">
          <div class="fee-cell"><span>Комісія товару (6.5%+ПДВ)</span><b>-$${(fb.trans_item_fee + fb.vat_trans_item).toFixed(2)}</b></div>
          <div class="fee-cell"><span>Комісія доставки (6.5%+ПДВ)</span><b>-$${(fb.trans_ship_fee + fb.vat_trans_ship).toFixed(2)}</b></div>
          <div class="fee-cell"><span>Еквайринг (6%+0.30+ПДВ)</span><b>-$${(fb.processing_fee + fb.vat_processing).toFixed(2)}</b></div>
          <div class="fee-cell"><span>Лістинг ($0.20+ПДВ)</span><b>-$${(fb.listing_renew_fee + fb.vat_listing_renew).toFixed(2)}</b></div>
        </div>
        <div class="dbox-foot">З картки покупця: <b class="num">$${fb.gross.toFixed(2)}</b> · товари: $${fb.item_total.toFixed(2)} · доставка: $${fb.shipping_total.toFixed(2)}
          ${fb.sales_tax > 0 ? html` · податок США $${fb.sales_tax.toFixed(2)} (утримує Etsy)` : ''}</div>
      </div>` : ''}
      ${o.pod_provider === 'printify' && (o.pod_cost_original || o.printify_total_cost || 0) > 0 ? html`<div class="dbox">
        <div class="dbox-title"><span class="svc-dot printify"></span>Собівартість Printify
          ${o.matched_printify_recipient ? html`<span class="dbox-note">· одержувач ${o.matched_printify_recipient}</span>` : ''}</div>
        <div class="fee-grid three">
          <div class="fee-cell"><span>Друк товару</span><b>$${(o.printify_production_cost || 0).toFixed(2)}</b></div>
          <div class="fee-cell"><span>Доставка клієнту</span><b>$${(o.printify_shipping_cost || 0).toFixed(2)}</b></div>
          <div class="fee-cell"><span>Разом</span><b class="neg">$${(o.pod_dead ? 0 : o.printify_total_cost || 0).toFixed(2)}</b></div>
        </div>
        ${o.pod_dead ? html`<div class="dbox-foot">${deadText(o)} — нічого не списано</div>` : ''}
        ${o.is_bundle ? html`<div class="dbox-foot bundle">${ic('package', 'icon-s')}Спільне замовлення на ${o.bundle_count || 2} чеки: витрати поділено порівну</div>` : ''}
      </div>` : ''}
      ${gel ? html`<div class="dbox">
        <div class="dbox-title"><span class="svc-dot gelato"></span>Собівартість Gelato
          ${o.matched_gelato_recipient ? html`<span class="dbox-note">· одержувач ${o.matched_gelato_recipient}</span>` : ''}</div>
        <div class="fee-grid three">
          <div class="fee-cell"><span>Статус</span><b>${o.pod_dead ? DEAD_SHORT[o.pod_dead] : o.gelato_status || '—'}</b></div>
          <div class="fee-cell"><span>Списано</span><b>${o.gelato_cost} ${o.gelato_currency || 'USD'}</b></div>
          <div class="fee-cell"><span>Разом</span><b class="neg">${o.cost_unknown ? '—' : `$${(o.pod_total_cost || 0).toFixed(2)}`}</b></div>
        </div>
        ${o.pod_dead ? html`<div class="dbox-foot">${deadText(o)} — нічого не списано</div>` : ''}
        ${o.cost_unknown ? html`<div class="dbox-foot">${ic('alert', 'icon-s')}Курсу ${o.gelato_currency} до долара немає — прибуток не пораховано</div>` : ''}
        ${o.is_bundle ? html`<div class="dbox-foot bundle">${ic('package', 'icon-s')}Спільне замовлення на ${o.bundle_count || 2} чеки: витрати поділено порівну</div>` : ''}
      </div>` : ''}
      ${st.data?.mode === 'etsy' && o.profit === null && !(o.pod_dead === 'unpaid' || o.cost_unknown) ? html`<div class="dbox dbox-row">
        ${ic('info')}<span class="grow muted">${o.link_blocked ? 'Позначено як замовлення без собівартості.'
          : o.needs_link ? `Знайдено лише ${deadText(o)}. Зв’яжіть замовлення, яким книгу справді надрукували.`
            : 'Не знайдено ні в Printify, ні в Gelato.'}</span>
        <button class="btn btn-sm" data-match="${o.id}">${ic('link', 'icon-s')}Зв'язати вручну</button></div>` : ''}
    </div>`;
  }

  function renderTable() {
    const rows = visibleRows();
    $('#pf-count').textContent = rows.length;
    const box = $('#pf-table');
    const d = st.data;
    if (!d) return;
    if (d.mode === 'empty') {
      const integ = store.info?.integrations || {};
      const ready = integ.etsy?.connected || integ.printify?.configured;
      setHtml(box, html`<div class="empty"><div class="empty-icon">${ic(ready ? 'refresh' : 'key')}</div>
        <h3>${ready ? 'Даних ще немає' : 'Підключіть Etsy та Printify'}</h3>
        ${ready ? '' : html`<p>Потрібні доступ до Etsy і токен Printify; Gelato — за бажанням.</p>`}
        ${ready ? html`<button class="btn btn-primary" data-act="sync">${ic('sync')}Оновити</button>` : html`<a class="btn btn-primary" href="#/settings">${ic('sliders')}Відкрити налаштування</a>`}</div>`);
      return;
    }
    const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
    st.page = Math.min(Math.max(1, st.page), pages);
    const slice = rows.slice((st.page - 1) * PAGE_SIZE, st.page * PAGE_SIZE);
    if (!slice.length) {
      setHtml(box, html`<div class="empty"><div class="empty-icon">${ic('package')}</div><h3>${st.filter === 'issues' ? 'Проблемних замовлень немає' : 'Замовлень не знайдено'}</h3></div>`);
      return;
    }
    setHtml(box, html`<div class="olist" role="table">
      <div class="ohead" role="row"><div>Замовлення Etsy (доставка)</div><div class="r">На руки (Etsy Net)</div><div class="r">Собівартість</div><div class="r">Чистий прибуток</div><div class="c">Зіставлення</div></div>
      ${slice.map((o) => html`<div class="oitem">
        <div class="orow ${st.open === o.id ? 'open' : ''}" role="row" data-row="${o.id}">${rowInner(o)}</div>
        <div class="acc ${st.open === o.id && st.details.has(o.id) ? 'open' : ''}" data-acc="${o.id}"><div>${st.open === o.id && st.details.has(o.id) ? detailHtml(st.details.get(o.id)) : ''}</div></div>
      </div>`)}
    </div>
      ${pages > 1 ? html`<div class="pager"><span><b>${st.page}</b> з <b>${pages}</b></span>
        <span class="tools">${ib('chevLeft', 'Попередня сторінка', `data-page="-1" ${st.page === 1 ? 'disabled' : ''}`)}${ib('chevRight', 'Наступна сторінка', `data-page="1" ${st.page === pages ? 'disabled' : ''}`)}</span></div>` : ''}`);
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
    setHtml(acc.firstElementChild, detailHtml(full));
    slide(acc, true);
    requestAnimationFrame(() => acc.querySelectorAll('.state-seg .seg').forEach(syncSeg));
  }

  // One order changed: its row and open panel are updated in place; the panel height glides to the new size.
  function patchRow(id) {
    const slim = st.data?.rows.find((r) => r.id === id);
    const rowEl = view.querySelector(`.orow[data-row="${CSS.escape(id)}"]`);
    if (slim && rowEl) setHtml(rowEl, rowInner(slim));
    const acc = view.querySelector(`[data-acc="${CSS.escape(id)}"]`);
    const full = st.details.get(id);
    if (acc && full && st.open === id) {
      const from = acc.getBoundingClientRect().height;
      keepFocus(() => setHtml(acc.firstElementChild, detailHtml(full)));
      const to = acc.scrollHeight;
      if (!reducedMotion() && Math.abs(to - from) > 1) acc.animate([{ height: `${from}px` }, { height: `${to}px` }], { duration: 260, easing: EASE });
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
    $('#pf-progress').hidden = false;
    try {
      const res = await runJob(api('/api/profit/sync', { method: 'POST', body: { full } }), (j) => {
        $('#pf-step').textContent = j.step;
        $('#pf-detail').textContent = j.detail ? ` · ${j.detail}` : '';
        $('#pf-pct').textContent = `${Math.round(j.percent)}%`;
        $('#pf-bar').style.width = `${j.percent}%`;
      }, 420, () => !gone);
      const etsyPart = res.changed === null || res.changed === undefined
        ? `Завантажено ${res.receipts} ${plural(res.receipts, ['замовлення', 'замовлення', 'замовлень'])} Etsy.`
        : `Змінених чеків Etsy: ${res.changed} (усього ${res.receipts}).`;
      st.notice = res.etsyConnected
        ? { type: 'success', text: `Оновлено. ${etsyPart} Зіставлено з Printify/Gelato: ${res.matched}.` }
        : { type: 'success', text: `Etsy не підключено — завантажено ${res.printify} замовлень Printify.` };
      clearTimeout(noticeTimer);
      noticeTimer = setTimeout(() => { if (st.notice?.type === 'success') { st.notice = null; renderNotice(); } }, 5000);
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
      if (!gone) { $('#pf-progress').hidden = true; renderHead(); }
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
        const res = await api('/api/profit/state', { method: 'POST', body: stateBody(o, patch) });
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
  const parseMoney = (v) => {
    const t = String(v || '').replace(',', '.').replace(/[^\d.]/g, '');
    return t === '' ? '' : Number(t);
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
        <div class="cand-list" id="mm-list"></div>
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
        return html`<div class="cand ${sel.has(key) ? 'sel' : ''}" data-key="${key}">
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
        if (multi) { if (sel.has(key)) sel.delete(key); else sel.add(key); c.classList.toggle('sel', sel.has(key)); }
        else { sel.clear(); sel.add(key); list.querySelectorAll('.cand').forEach((x) => x.classList.toggle('sel', x === c)); }
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
      sub: `Покупець: ${o.customer_name} · Чек #${o.etsy_receipt_id} · Etsy Net ${usd(o.etsy_net)}`,
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
          else if (x === 'none') await api('/api/profit/links', { method: 'POST', body: { receiptId: o.etsy_receipt_id, provider: 'none' } });
          else if (x === 'save' && keys[0]) {
            const [prov, orderId] = keys[0].split(/:(.+)/);
            await api('/api/profit/links', { method: 'POST', body: { receiptId: o.etsy_receipt_id, provider: prov, orderId } });
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
    { label: 'Швидке оновлення (лише змінені чеки)', icon: 'refresh', onClick: () => sync(false) },
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
