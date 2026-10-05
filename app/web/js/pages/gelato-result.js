// The green card of a Gelato draft just made — drawn by the Order Creator and, while the temporary link to its PDF is
// up, by the order's own card too (owner, 01.10.2026: "щоб він лишався поки живе посилання"). One markup, one timer,
// one set of buttons for both.
import { post, html, ic, ib, toast, copyText, openExternal, attr } from '../lib.js';

const ORDERS_URL = 'https://dashboard.gelato.com/orders/list';

/** When the link closes (ms); the first call fixes it for the result, so every view counts down from one moment. */
export const linkUntil = (r) => r._until || (r._until = Date.now() + (r.keepAliveSeconds || 0) * 1000);
export const linkAlive = (r) => !!r && !r._closed && linkUntil(r) > Date.now();

export function gelatoResultHtml(r) {
  return html`<div class="result-card">
    <h4>${ic('checkCircle')}${r.reprint ? 'Передрук: чернетку створено в Gelato!' : 'Чернетку замовлення створено в Gelato!'}</h4>
    <dl class="kv">
      <dt>Назва</dt><dd>${r.title}</dd>
      <dt>Order ID</dt><dd class="mono">${r.orderId}</dd>
      <dt>Reference</dt><dd class="mono">${r.orderReferenceId}</dd>
      <dt>Тип</dt><dd class="mono">${r.orderType || 'draft'}</dd>
      ${(r.books || []).length > 1
        ? html`<dt>Книги</dt><dd>${r.books.map((b) => html`<div>${b.title} · ${b.format} · <span class="num">${b.pageCount}</span> стор.</div>`)}</dd>`
        : html`<dt>Формат</dt><dd>${r.format}</dd>
          ${r.pdfPages ? html`<dt>Файл</dt><dd>один PDF, <span class="num">${r.pdfPages}</span> стор.: обкладинка · форзац · <span class="num">${r.pdfPages - 3}</span> сторінок · нахзац</dd>` : ''}`}
    </dl>
    ${(r.warnings || []).map((w) => html`<div class="notice notice-warn" style="margin-top:10px">${ic('alert')}<div>${w}</div></div>`)}
    ${linkNotice(r)}
    <div class="row" style="margin-top:12px"><button class="btn btn-primary grow" data-act="open-gelato">${ic('external', 'icon-s')}Замовлення в Gelato</button>${ib('copy', 'Копіювати Order ID', 'data-act="copy-order"')}${ib('sendLog', 'Журнал відправки', `data-act="open-sendlog" ${attr('data-file', r.sendLog || '')}`)}</div>
  </div>`;
}

// Gelato fetches the PDF on its own within a minute of the draft (checked 17.09 and 30.09.2026), so the notice tells
// how long the link lives, not a step to take.
function linkNotice(r) {
  if (r._closed) return html`<div class="notice" style="margin-top:12px" data-link>${ic('check')}<div>Тимчасове посилання закрито.</div></div>`;
  return html`<div class="notice notice-warn" style="margin-top:12px" data-link>${ic('clock')}<div class="grow">
    Тимчасове посилання на файли працює ще <b class="num" data-countdown>--:--</b> — Gelato забирає їх сам, зазвичай за хвилину.
    <div class="progress progress-thin drain"><i data-drain></i></div></div>
    ${ib('unlink', 'Файли забрано — закрити посилання', 'data-act="close-tunnel"', { cls: 'sm' })}</div>`;
}

/** Ticks the countdown inside `root`; `onEnd` runs once, when the link closes while this one is ticking (the card
 *  is drawn again then, showing it closed). Returns the stop function. */
export function runCountdown(root, r, onEnd) {
  let timer = 0;
  const alive = linkAlive(r);
  const tick = () => {
    const left = r._closed ? 0 : Math.max(0, Math.round((linkUntil(r) - Date.now()) / 1000));
    const node = root.querySelector('[data-countdown]');
    if (node) node.textContent = `${String(Math.floor(left / 60)).padStart(2, '0')}:${String(left % 60).padStart(2, '0')}`;
    // the time left is really known: the bar drains in proportion, one linear second per tick
    const drain = root.querySelector('[data-drain]'), total = (r.keepAliveSeconds || 0);
    if (drain && total) drain.style.transform = `scaleX(${Math.max(0, Math.min(1, left / total))})`;
    if (!left) { clearInterval(timer); if (alive && !r._closed) { r._closed = true; onEnd?.(); } }
  };
  tick();
  if (linkAlive(r)) timer = setInterval(tick, 1000);
  return () => clearInterval(timer);
}

/** The card's buttons; true when `act` was one of them. */
export async function resultAction(act, r, t) {
  if (act === 'open-gelato') openExternal(ORDERS_URL);
  else if (act === 'copy-order') copyText(r.orderId || '', 'Order ID скопійовано');
  else if (act === 'open-sendlog') post('/api/sends/open', { file: t.dataset.file || '' }).catch((er) => toast(er.message, 'error'));
  else if (act === 'close-tunnel') {
    try { await post('/api/creator/gelato/close-tunnel', { orderId: r.orderId }); }
    catch (er) { toast(`Посилання не закрилося: ${er.message}`, 'error'); return true; }     // never say «закрито» when it is not
    r._closed = true;
  } else return false;
  return true;
}
