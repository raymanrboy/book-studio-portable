// The second page of Profit: the owner's whiteboard calendar in the program (2026-10-21). A month by days, Monday first,
// a dot for every sale; hovering a day shows what it earned and how many sales; each week's profit stands at the end of
// its row, the month's in the head. The money is the cards' own (kpi()): the order profits minus the day's ads.
import { html, ic, ib, setHtml, money, plural } from '../lib.js';
import { costOf } from './profit-rows.js';

const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд'];
const MAX_DOTS = 12; // more sales than this in a day: the dots stop and «+N» says the rest
const dayKey = (d) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
// A sale is a dot unless it was cancelled or fully refunded (no book went out).
const sold = (o) => !['canceled', 'refund_full'].includes(o.state);
// A sale whose profit is not known yet (no print order matched): kpi() leaves it out — the hover says so.
const pending = (o) => o.profit === null || o.profit === undefined || (!(costOf(o) > 0) && !o.pod_dead && (!o.state || o.state === 'normal'));

/** The calendar inside `box`. `rows()` — the counted Etsy rows; `kpi(rows, days)` and `overhead(days)` — the page's money
 *  for those rows and days ("YYYY-MM-DD"); `from()` — the first day in the books (Date or null); `forecast(day)` — whether
 *  that day's ads are the ledger's forecast; `estimated()` — no ledger at all, the ads are the flat estimate a day. */
export function makeCalendar(box, { rows, kpi, overhead, from, forecast, estimated }) {
  const now = new Date();
  let month = new Date(now.getFullYear(), now.getMonth(), 1);
  let days = new Map(); // "YYYY-MM-DD" -> what the hover shows

  function render() {
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const start = from();
    // No books yet (no data, a load error): nothing to draw — the notice above the page says why.
    if (!start) { setHtml(box, html`<div class="cal-card"><div class="empty"><div class="empty-icon">${ic('calendar')}</div><h3>Продажів ще немає</h3></div></div>`); return; }
    const inBooks = (d) => d <= today && (!start || d >= start);
    const byDay = new Map();
    for (const o of rows()) {
      const d = o.created_at ? new Date(o.created_at) : null;
      if (!d || Number.isNaN(d.getTime())) continue;
      const k = dayKey(d);
      if (!byDay.has(k)) byDay.set(k, []);
      byDay.get(k).push(o);
    }
    days = new Map();
    // The weeks of the month, Monday first; a week's days of the next or last month stay empty (as on the board).
    const first = new Date(month);
    const last = new Date(month.getFullYear(), month.getMonth() + 1, 0);
    const lead = (first.getDay() + 6) % 7;
    const cells = [...Array(lead).fill(null)];
    for (let n = 1; n <= last.getDate(); n++) cells.push(new Date(month.getFullYear(), month.getMonth(), n));
    while (cells.length % 7) cells.push(null);
    const weeks = [];
    for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));

    const sumOf = (dates) => {
      const live = dates.filter((d) => d && inBooks(d));
      const rs = live.flatMap((d) => byDay.get(dayKey(d)) || []);
      return { live, rs, k: kpi(rs, live.map(dayKey)), sales: rs.filter(sold).length };
    };
    const dayCell = (d) => {
      if (!d) return html`<div class="cal-day cal-blank"></div>`;
      const k = dayKey(d);
      const isToday = d.getTime() === today.getTime();
      if (!inBooks(d)) return html`<div class="cal-day is-off"><span class="cal-num">${d.getDate()}</span></div>`;
      const rs = byDay.get(k) || [];
      const sales = rs.filter(sold);
      const m = kpi(rs, [k]);
      const ads = overhead([k]);
      days.set(k, { d, sales: sales.length, profit: m.profit, net: m.net, ads, forecast: forecast(k), pending: sales.filter(pending).length });
      const label = `${d.toLocaleDateString('uk-UA', { day: 'numeric', month: 'long' })}: ${sales.length} ${plural(sales.length, ['продаж', 'продажі', 'продажів'])}, прибуток ${money(m.profit)}`;
      const more = sales.length - MAX_DOTS;
      return html`<button type="button" class="cal-day ${isToday ? 'is-today' : ''} ${sales.length ? 'has-sales' : ''}" data-day="${k}" aria-label="${label}">
        <span class="cal-num">${d.getDate()}</span>
        <span class="cal-dots">${sales.slice(0, MAX_DOTS).map(() => html`<i></i>`)}${more > 0 ? html`<em>+${more}</em>` : ''}</span>
      </button>`;
    };
    const weekCell = (week) => {
      const w = sumOf(week);
      if (!w.live.length) return html`<div class="cal-week"></div>`;
      return html`<div class="cal-week" data-tip="${w.sales} ${plural(w.sales, ['продаж', 'продажі', 'продажів'])} · на руки ${money(w.k.net)}">
        <b class="num ${w.k.profit < 0 ? 'neg' : !w.sales ? 'zero' : ''}">${money(w.k.profit)}</b></div>`;
    };

    const total = sumOf(cells);
    const startMonth = start ? new Date(start.getFullYear(), start.getMonth(), 1) : null;
    const canBack = !startMonth || month > startMonth;
    const canNext = month < new Date(today.getFullYear(), today.getMonth(), 1);
    const title = month.toLocaleDateString('uk-UA', { month: 'long', year: 'numeric' }).replace(/\s*р\.$/, '');
    setHtml(box, html`<div class="cal-card">
      <div class="cal-head">
        <div class="cal-month">
          ${ib('chevLeft', 'Попередній місяць', `data-cal="-1" ${canBack ? '' : 'disabled'}`)}
          <h2 class="cal-title">${title.charAt(0).toUpperCase() + title.slice(1)}</h2>
          ${ib('chevRight', 'Наступний місяць', `data-cal="1" ${canNext ? '' : 'disabled'}`)}
        </div>
        <span class="spacer"></span>
        <div class="cal-total" data-tip="Прибуток за місяць: замовлення мінус собівартість і реклама">
          <b class="num ${total.k.profit < 0 ? 'neg' : ''}">${money(total.k.profit)}</b>
          <span>${total.sales} ${plural(total.sales, ['продаж', 'продажі', 'продажів'])}</span>
        </div>
      </div>
      <div class="cal-grid" role="group">
        ${WEEKDAYS.map((w) => html`<div class="cal-wd">${w}</div>`)}<div class="cal-wd cal-wd-sum">${ic('chart', 'icon-s')}</div>
        ${weeks.map((week) => html`${week.map(dayCell)}${weekCell(week)}`)}
      </div>
      <div class="cal-pop" id="cal-pop" role="tooltip"></div>
    </div>`);
  }

  // The hover card: the day, its profit, the sales and the money in.
  function show(cell) {
    const x = days.get(cell.dataset.day);
    const pop = box.querySelector('#cal-pop');
    if (!x || !pop) return;
    const date = x.d.toLocaleDateString('uk-UA', { weekday: 'short', day: 'numeric', month: 'long' });
    setHtml(pop, html`<div class="cal-pop-date">${date}</div>
      <div class="cal-pop-profit num ${x.profit < 0 ? 'neg' : ''}">${money(x.profit)}</div>
      <div class="cal-pop-line"><span class="cal-dots">${Array.from({ length: Math.min(x.sales, MAX_DOTS) }, () => html`<i></i>`)}</span>
        ${x.sales} ${plural(x.sales, ['продаж', 'продажі', 'продажів'])}${x.sales ? ` · на руки ${money(x.net)}` : ''}</div>
      ${x.ads < 0 ? html`<div class="cal-pop-faint">Реклама й нові лістинги ${money(x.ads)}${estimated() ? ' (оцінка)' : x.forecast ? ' (прогноз)' : ''} — уже віднято</div>` : ''}
      ${x.pending ? html`<div class="cal-pop-faint">${x.pending} ще без собівартості — не в сумі</div>` : ''}`);
    pop.style.left = '0px'; pop.style.top = '0px'; // measured at the card's corner: not squeezed by the last position
    const card = box.querySelector('.cal-card').getBoundingClientRect();
    const r = cell.getBoundingClientRect();
    const w = pop.offsetWidth, h = pop.offsetHeight;
    const mid = r.left - card.left + r.width / 2;
    const left = Math.max(8, Math.min(card.width - w - 8, mid - w / 2));
    const above = r.top - card.top - h - 6;
    pop.dataset.side = above >= 8 ? 'top' : 'bottom';
    pop.style.left = `${Math.round(left)}px`;
    pop.style.top = `${Math.round(above >= 8 ? above : r.bottom - card.top + 6)}px`;
    pop.style.setProperty('--tail', `${Math.round(mid - left)}px`); // the little tail points at the day
    pop.classList.add('on');
  }
  const hide = () => box.querySelector('#cal-pop')?.classList.remove('on');

  const onOver = (e) => { const c = e.target.closest?.('[data-day]'); if (c) show(c); else if (!e.target.closest?.('.cal-pop')) hide(); };
  const onFocus = (e) => { const c = e.target.closest?.('[data-day]'); if (c) show(c); };
  const onClick = (e) => {
    const b = e.target.closest('[data-cal]');
    if (!b || b.disabled) return;
    month = new Date(month.getFullYear(), month.getMonth() + Number(b.dataset.cal), 1);
    render();
    // At the last month the same arrow is now disabled: the focus goes to the other one, not lost.
    (box.querySelector(`[data-cal="${b.dataset.cal}"]:not([disabled])`) || box.querySelector('[data-cal]:not([disabled])'))?.focus();
  };
  box.addEventListener('pointerover', onOver);
  box.addEventListener('pointerleave', hide);
  box.addEventListener('focusin', onFocus);
  box.addEventListener('focusout', hide);
  box.addEventListener('click', onClick);
  return {
    render,
    destroy() {
      box.removeEventListener('pointerover', onOver); box.removeEventListener('pointerleave', hide);
      box.removeEventListener('focusin', onFocus); box.removeEventListener('focusout', hide); box.removeEventListener('click', onClick);
    },
  };
}
