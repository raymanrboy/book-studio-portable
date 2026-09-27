// Profit: one order's row and its open panel — pure templates of (order, the data's mode), out of the page's
// mount() since 27.09.2026.
import { html, ic, segHtml, money, signedMoney, dateTime } from '../lib.js';

const STATE_OPTS = [
  { value: 'normal', label: 'Звичайне' },
  { value: 'canceled', label: 'Скасовано' },
  { value: 'refund_full', label: 'Повне повернення' },
  { value: 'refund_partial', label: 'Часткове повернення' },
  { value: 'replacement', label: 'Заміна' },
];
const STATE_TEXT = { normal: 'звичайне', canceled: 'скасовано', refund_full: 'повне повернення', refund_partial: 'часткове повернення', replacement: 'заміна' };
const STATE_CHIP = { canceled: 'chip-red', refund_full: 'chip-red', refund_partial: 'chip-amber', replacement: 'chip-purple' };
// Why the print order costs nothing (outcomes.unpaid()): a draft, not paid yet (on hold, awaiting payment), cancelled.
export const DEAD_SHORT = { draft: 'чернетка', unpaid: 'не оплачено', canceled: 'скасовано' };
const deadText = (o) => (o.pod_dead === 'draft' ? 'чернетка Gelato — не оплачена'
  : o.pod_dead === 'unpaid' ? `ще не оплачено в ${podName(o)}` : `скасовано в ${podName(o)}`);
export const costOf = (o) => o.cost_total ?? ((o.pod_total_cost || 0) > 0 ? o.pod_total_cost : (o.printify_total_cost || 0));
const podName = (o) => (o.pod_provider === 'gelato' ? 'Gelato' : 'Printify');

export function providerCell(o, mode) {
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

export function statusCell(o, mode) {
  if (mode === 'printify_only') return html`<span class="chip chip-lime">Printify</span>`;
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

export function stateChip(o, mode) {
  if (!o.state || o.state === 'normal') return '';
  const text = o.state === 'refund_partial' && o.refund_amount ? `повернення ${money(-o.refund_amount)}` : STATE_TEXT[o.state];
  return html`<span class="chip ${STATE_CHIP[o.state]}" data-tip="${o.state_manual ? 'Статус встановлено вручну' : 'Статус з Etsy'}">${o.state_manual ? ic('edit', 'icon-s') : ''}${text}</span>`;
}

export function netCell(o, mode) {
  if (o.etsy_net === undefined) return html`<span class="faint">—</span>`;
  const changed = o.state && o.state !== 'normal' && o.etsy_net_original !== undefined && Math.abs(o.etsy_net - o.etsy_net_original) > 0.004;
  return html`<div class="o-net ${o.etsy_net < 0 ? 'neg' : o.etsy_net === 0 ? 'zero' : ''}">${money(o.etsy_net)}</div>
    ${changed ? html`<div class="o-was" data-tip="До повернення">${money(o.etsy_net_original)}</div>` : o.etsy_fees > 0 ? html`<div class="o-fees">збори: ${money(-o.etsy_fees)}</div>` : ''}`;
}

export function rowInner(o, mode) {
  return html`
    <div><div class="o-name truncate" data-toggle="${o.id}">${o.customer_name}</div><div class="o-sub truncate">${stateChip(o, mode)}${o.cover_label}</div></div>
    <div class="r num">${netCell(o, mode)}</div>
    <div class="r">${providerCell(o, mode)}</div>
    <div class="r">${o.profit !== null && o.profit !== undefined ? html`<span class="profit-pill ${o.profit > 0 ? 'profit-pos' : o.profit < 0 ? 'profit-neg' : 'profit-zero'}">${o.profit === 0 ? '$0.00' : signedMoney(o.profit)}</span>
      ${o.profit_margin !== null && o.profit_margin !== undefined ? html`<div class="o-margin">маржа ${o.profit_margin}%</div>` : ''}` : html`<span class="faint">—</span>`}</div>
    <div class="c">${statusCell(o, mode)}</div>`;
}

// ---------------------------------------------------------------- order state panel
export function econLines(o, mode) {
  const s = o.state;
  if (!s || s === 'normal') return '';
  const lines = [];
  const line = (label, value, cls = '') => lines.push(html`<span>${label}</span><b class="${cls || (value < 0 ? 'neg' : value > 0 ? 'pos' : '')}">${value > 0 ? '+' : ''}${money(value)}</b>`);
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

export function stateBox(o, mode) {
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
    ${econLines(o, mode)}
    ${(o.refunds || []).length ? html`<div class="state-hint state-refunds">Повернення в Etsy: ${o.refunds.map((r) => `${r.at ? dateTime(r.at * 1000) : ''} · ${money(r.amount)}${r.reason ? ` · ${r.reason}` : ''}${r.note ? ` · «${r.note}»` : ''}`).join('; ')}</div>` : ''}
  </div>`;
}

export function detailHtml(o, mode) {
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
      ${mode === 'etsy' ? html`<button class="btn btn-xs" data-match="${o.id}">${ic('link', 'icon-s')}Змінити зіставлення</button>` : ''}
    </div>
    ${mode === 'etsy' ? stateBox(o, mode) : ''}
    ${mode === 'etsy' ? html`<div class="detail-grid">
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
    ${mode === 'etsy' && o.profit === null && !(o.pod_dead === 'unpaid' || o.cost_unknown) ? html`<div class="dbox dbox-row">
      ${ic('info')}<span class="grow muted">${o.link_blocked ? 'Позначено як замовлення без собівартості.'
        : o.needs_link ? `Знайдено лише ${deadText(o)}. Зв’яжіть замовлення, яким книгу справді надрукували.`
          : 'Не знайдено ні в Printify, ні в Gelato.'}</span>
      <button class="btn btn-sm" data-match="${o.id}">${ic('link', 'icon-s')}Зв'язати вручну</button></div>` : ''}
  </div>`;
}
