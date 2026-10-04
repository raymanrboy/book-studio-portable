// Order archive: every book sent to print from Book Studio with exactly the files that went — to look
// back at what was printed and to reprint it in a couple of clicks. The server keeps the files 14 days
// after the order became "shipped" (studio/archive.py); "Не видаляти" keeps a book until unmarked.
import {
  api, post, html, ic, ib, setHtml, on, media, toast, relTime, dateTime, copyText, fadeImages, openExternal, plural,
  patch, enterOnce, escBack, notFound, backToTools, BOOKS, attr,
} from '../lib.js';
import { openLightbox } from '../lightbox.js';
import {
  STAGE_LABEL, providerName, countryName, addressFromEtsy, folderViewerItems, smoothWheel, trackChips, statusChip,
  receiptCopy, copyChip, childOf as childOfTitle, proofHtml, fieldsHtml, addressHtml, etsyAddressLines, svcChip,
} from '../order-bits.js';
import { give } from '../handoff.js';
import { store } from '../info.js';

// Page previews the server prepares when a book is archived (archive._warm_previews): 360 and 1400.
const THUMB = 360;
const file = (e, name, w) => media('/media/folder', { path: e.folder, file: name, w });
/** The child's name from the title "4100000001 - Emma". */
const childOf = (e) => childOfTitle(e.title);

/** How long the files stay: marked "keep", counting down, or waiting for the order to be shipped. */
function clockChip(e) {
  if (e.keep) return html`<span class="chip chip-accent" data-tip="Не видаляти — файли лишаються, доки не знімете позначку">${ic('pin', 'icon-s')}не видаляти</span>`;
  if (!e.deleteAt) return html`<span></span>`;
  const soon = e.daysLeft <= 3;
  return html`<span class="chip ${soon ? 'chip-amber' : ''}" data-tip="Файли видаляться ${dateTime(e.deleteAt)}">${ic('clock', 'icon-s')}${e.daysLeft ? `ще ${e.daysLeft} дн.` : 'сьогодні'}</span>`;
}

function clockText(e, keepDays) {
  if (e.keep) return 'Не видаляти: файли лишаються, доки не знімете позначку.';
  if (e.deleteAt) return `Файли видаляться ${dateTime(e.deleteAt)} — ${e.daysLeft ? `через ${e.daysLeft} дн.` : 'сьогодні'}`;
  return e.reprintOf
    ? `Файли зберігатимуться ${keepDays} днів після того, як друкарня відправить передрук.`
    : `Файли зберігатимуться ${keepDays} днів після того, як замовлення стане «Відправленим».`;
}

export function mount(view, [id]) {
  return id ? mountBook(view, id) : mountList(view);
}

// ==================================================================== list
async function mountList(view) {
  let data;
  try { data = await api('/api/archive'); }
  catch (err) { setHtml(view, html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`); return null; }
  let term = '', shown = [];
  const count = data.entries.length;
  setHtml(view, html`
    <div class="page-head">${backToTools()}<div><h1 class="page-title">Архів друку</h1>
      <div class="page-sub">${count ? `${count} ${plural(count, BOOKS)}` : ''}</div></div></div>
    ${count ? html`<div class="lib-toolbar"><div class="input-group">${ic('search')}<input class="input" id="ar-q" placeholder="Ім'я, номер чека або назва" aria-label="Пошук в архіві" autocomplete="off"></div></div>` : ''}
    <div class="ord-list" id="ar-list"></div>
    <div id="ar-empty"></div>`);
  const list = view.querySelector('#ar-list');
  const empty = view.querySelector('#ar-empty');

  const rowHtml = (e) => {
    const child = childOf(e);
    return html`<a class="ord-row" href="#/archive/${e.id}" data-id="${e.id}">
      <span class="ord-thumb arc-thumb"><img data-fade loading="lazy" decoding="async" src="${file(e, 'Cover.png', THUMB)}" alt=""></span>
      <span class="ord-main">
        <span class="row ord-chips"><b class="truncate">${e.buyer || e.title}</b>${e.receiptId ? receiptCopy(e, 'chip chip-mono') : ''}${svcChip(e.provider)}
          ${e.reprintOf ? html`<span class="chip" data-tip="Передрук книги з архіву">${ic('sync', 'icon-s')}передрук</span>` : ''}${trackChips(e)}</span>
        <span class="ord-meta faint truncate"><span data-tip="${dateTime(e.sentAt)}">у друці ${relTime(e.sentAt)}</span> ·
          ${child ? html`<b class="ord-child">${child}</b> · ` : ''}<span class="num">${e.pageCount}</span> стор.${e.formatLabel ? ` · ${e.formatLabel}` : ''}</span>
      </span>
      ${clockChip(e)}
      <span class="ord-go">${ic('chevRight')}</span>
    </a>`;
  };

  const matches = (e, t) => !t || [e.buyer, e.title, e.receiptId].some((v) => String(v || '').toLowerCase().includes(t));
  // Every book drawn once, with the entrance; a search only hides rows — no picture reloads, no entrance replays
  // on each letter (until 26.09.2026 every letter redrew the list).
  patch(list, data.entries.map((e) => [e.id, rowHtml(e)])).forEach((n, i) => enterOnce(n, Math.min(i * 30, 300)));
  fadeImages(list);
  const render = () => {
    const t = term.trim().toLowerCase();
    shown = data.entries.filter((e) => matches(e, t)).map((e) => e.id);
    const visible = new Set(shown);
    [...list.children].forEach((n) => { n.hidden = !visible.has(n.dataset.key); });
    if (shown.length) { setHtml(empty, ''); return; }
    setHtml(empty, t ? html`<div class="empty">Нічого не знайдено</div>`
      : html`<div class="empty"><div class="empty-icon">${ic('orderArchive')}</div><h3>Архів порожній</h3>
        <p>Сюди потрапляє кожна книга, відправлена в друк з Book Studio, — рівно ті файли, що пішли в друк.
        Вони зберігаються ${data.keepDays} днів після того, як замовлення стане «Відправленим».</p></div>`);
  };

  const offs = [on(view, 'click', '[data-act="copy-text"]', copyChip)];
  const q = view.querySelector('#ar-q');
  if (q) {
    q.addEventListener('input', () => { term = q.value; render(); });
    q.addEventListener('keydown', (ev) => { if (ev.key === 'Enter' && shown.length) location.hash = `#/archive/${shown[0]}`; });
  }
  render();
  return { unmount() { offs.forEach((f) => f()); } };
}

// ==================================================================== one book
async function mountBook(view, id) {
  let e;
  try { e = await api(`/api/archive/${id}`); }
  catch (err) {
    notFound(view, { back: '#/archive', backLabel: 'До архіву', icon: 'orderArchive', title: 'Книгу не знайдено', text: err.message });
    return null;
  }
  // The Etsy order it was printed for, when the last sync still has it (for the buyer's fields).
  let o = null;
  if (e.receiptId) { try { o = await api(`/api/orders/${e.receiptId}`); } catch { o = null; } }
  const keepDays = e.keepDays;
  const child = childOf(e);
  // Opened from its order's card: «back» and Esc lead there, and the rail stays on «Замовлення» (2026-09-30).
  const fromOrder = e.receiptId && store.from === `#/orders/${e.receiptId}` ? store.from : '';
  const backTo = fromOrder || '#/archive';
  const backLabel = fromOrder ? 'До замовлення' : 'До архіву';
  let pick = Math.max(0, (o?.items || []).findIndex((it) => it.childName && it.childName === child));
  const item = () => o?.items?.[pick] || {};

  setHtml(view, html`
    <div class="page-head">
      <button class="back-link" data-act="back" aria-label="${backLabel}" data-tip="${backLabel}" data-kbd="Esc">${ic('arrowLeft')}</button>
      <div class="grow">
        <div class="ord-title"><h1 class="page-title truncate">${e.buyer || o?.name || e.title}</h1>${statusChip(e)}</div>
        <div class="page-sub ord-sub">${e.receiptId ? html`${receiptCopy(e, 'mono')} · ` : ''}<span data-tip="${dateTime(e.sentAt)}">у друці ${relTime(e.sentAt)}</span>${e.stage ? ` · ${STAGE_LABEL[e.stage] || ''}` : ''}${trackChips(e)}</div>
      </div>
      <div class="page-actions" id="ar-actions"></div>
    </div>
    <div class="ord-grid">
      <div class="stack-l" id="ar-flow"></div>
      <div class="stack-l ord-side" id="ar-data"></div>
    </div>`);
  const $ = (s) => view.querySelector(s);

  function renderActions() {
    setHtml($('#ar-actions'), html`<div class="tools">
        ${ib('pin', e.keep ? 'Зняти «Не видаляти»' : 'Не видаляти', `data-act="keep" aria-pressed="${e.keep}"`, { cls: e.keep ? 'on' : '' })}
        ${ib('folderOpen', 'Відкрити папку з файлами', 'data-act="open-folder"')}
        ${e.sendLog ? ib('sendLog', 'Журнал відправки', 'data-act="open-sendlog"') : ''}</div>
      ${svcChip(e.provider, { lg: true, text: `${providerName(e.provider)} · ${e.pageCount} стор.` })}`);
  }

  // ---------------------------------------------------------------- left: what was printed, then the reprint
  function proofCard() {
    const it = item();
    const cover = (e.files || []).find((x) => x.file === 'Cover.png') || {};
    return html`<section class="card card-pad stack-l">
      <div class="row"><h3 class="card-title grow">Що пішло в друк</h3></div>
      ${proofHtml({ src: (name, side) => file(e, name, side), pages: e.pageCount, ratio: cover.width ? cover.width / cover.height : 1.9,
        name: it.childName || child, variations: it.variations, stripId: 'ar-strip' })}
    </section>`;
  }

  function reprintCard() {
    const pr = e.provider === 'printify';
    // From 1 October Printify only reads: its 24 pages do not fit Gelato (28 or 30), so a reprint starts from the
    // order's card with a book downloaded anew.
    if (pr && store.info?.integrations?.printify?.readOnly) {
      return html`<section class="card card-pad"><div class="row faint">${ic('info', 'icon-s')}<span>Printify більше не друкує. Для передруку завантажте книгу з Canva на 28 або 30 сторінок і відправте в Gelato з картки замовлення.</span></div></section>`;
    }
    return html`<section class="card card-pad stack ${pr ? 'tint-printify' : ''}">
      <button class="btn btn-xl btn-primary btn-block" data-act="reprint">${ic('send', 'icon-l')}Передрук у ${providerName(e.provider)}</button>
    </section>`;
  }

  // ---------------------------------------------------------------- right: the send, the buyer's fields, the address
  function sendCard() {
    const pr = e.provider === 'printify';
    return html`<section class="card card-pad stack-s">
      <h3 class="card-title">Відправка</h3>
      <dl class="kv">
        <dt>Друкарня</dt><dd>${providerName(e.provider)} · ${e.pageCount} стор.${e.formatLabel ? ` · ${e.formatLabel}` : ''}</dd>
        <dt>Коли</dt><dd>${dateTime(e.sentAt)}</dd>
        <dt>Назва</dt><dd>${e.title}</dd>
        ${pr && e.productId ? html`<dt>Product ID</dt><dd class="mono arc-id">${e.productId}${ib('copy', 'Копіювати Product ID', `data-act="copy-id" ${attr('data-text', e.productId)}`, { cls: 'sm' })}</dd>` : ''}
        ${e.orderId ? html`<dt>Order ID</dt><dd class="mono arc-id">${e.orderId}${ib('copy', 'Копіювати Order ID', `data-act="copy-id" ${attr('data-text', e.orderId)}`, { cls: 'sm' })}</dd>` : ''}
        ${e.reprintOf ? html`<dt>Передрук</dt><dd><a href="#/archive/${e.reprintOf}">першої відправки</a></dd>` : ''}
      </dl>
      <div class="faint arc-clock">${ic(e.keep ? 'pin' : 'clock', 'icon-s')}<span>${clockText(e, keepDays)}</span></div>
      <div class="row">${pr
        ? html`<button class="btn btn-sm" data-act="open-product">${ic('external', 'icon-s')}Відкрити в Printify</button>`
        : html`<button class="btn btn-sm" data-act="open-gelato">${ic('external', 'icon-s')}Замовлення в Gelato</button>`}</div>
    </section>`;
  }

  function fieldsCard() {
    if (!o) return '';
    return html`<section class="card card-pad stack">
      <div class="row"><h3 class="card-title grow">Персоналізація</h3></div>
      ${fieldsHtml(item().variations)}
    </section>`;
  }

  function addressCard() {
    // The address the printer got (Order Creator's fields); else the one on Etsy.
    const a = e.address || null;
    const b = o?.address || {};
    const lines = a
      ? [[a.firstName, a.lastName].filter(Boolean).join(' '), a.addressLine1, a.addressLine2,
        [a.city, a.state, a.postCode].filter(Boolean).join(', '), countryName(a.country)]
      : etsyAddressLines(b);
    if (!lines.some(Boolean)) return '';
    return html`<section class="card card-pad stack-s">
      <h3 class="card-title">${a ? 'Адреса, куди відправлено' : 'Доставка'}</h3>
      ${addressHtml(lines)}
    </section>`;
  }

  function render() {
    renderActions();
    setHtml($('#ar-flow'), [proofCard(), reprintCard()]);
    setHtml($('#ar-data'), [sendCard(), fieldsCard(), addressCard()]);
    fadeImages(view);
    const strip = $('#ar-strip');
    if (strip) smoothWheel(strip);
  }

  // ---------------------------------------------------------------- actions
  async function toggleKeep() {
    try {
      e = await post(`/api/archive/${e.id}/keep`, { keep: !e.keep });
      toast(e.keep ? 'Книгу не буде видалено, доки не знімете позначку' : 'Позначку знято — файли видаляться за звичайним правилом', 'success');
      renderActions();
      setHtml($('#ar-data'), [sendCard(), fieldsCard(), addressCard()]);
    } catch (err) { toast(err.message, 'error'); }
  }

  // The reprint is made in the Order Creator from these very files: Printify gets a new order for the
  // book it already has, Gelato a new draft. The address is the one the printer got (editable there).
  function reprint() {
    const address = e.address ? { ...e.address } : o ? addressFromEtsy(o) : { country: 'US' };
    give('creator', {
      mode: e.provider, books: [{ folder: e.folder, label: `Архів · ${e.title}`, title: e.title, format: e.format || null }],
      address, reprint: { archiveId: e.id, productId: e.productId || null },
    });
    location.hash = '#/creator';
  }

  const offs = [
    on(view, 'click', '[data-act]', (ev, t) => {
      const a = t.dataset.act;
      if (a === 'back') location.hash = backTo;
      else if (a === 'keep') toggleKeep();
      else if (a === 'open-folder') post('/api/creator/open-folder', { path: e.folder }).catch((er) => toast(er.message, 'error'));
      else if (a === 'open-sendlog') post('/api/sends/open', { file: e.sendLog || '' }).catch((er) => toast(er.message, 'error'));
      else if (a === 'reprint') reprint();
      else if (a === 'open-product') openExternal(e.url || `https://printify.com/app/product-details/${e.productId}`);
      else if (a === 'open-gelato') openExternal('https://dashboard.gelato.com/orders/list');
      else if (a === 'copy-id') copyText(t.dataset.text, 'Скопійовано');
      else if (a === 'copy-text') copyChip(ev, t);
    }),
    on(view, 'click', '[data-copy]', (ev, b) => copyText(item().variations?.[+b.dataset.copy]?.value || '', 'Скопійовано')),
    on(view, 'click', '[data-lb]', (ev, c) => openLightbox(folderViewerItems(e.folder, e.pageCount, e.title), +c.dataset.lb)),
  ];
  const esc = escBack(backTo);

  render();
  return { navFor: () => (fromOrder ? '#/orders' : null), unmount() { offs.forEach((fn) => fn()); esc(false); } };
}
