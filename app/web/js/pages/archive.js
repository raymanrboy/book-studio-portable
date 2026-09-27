// Order archive: every book sent to print from Book Studio with exactly the files that went — to look
// back at what was printed and to reprint it in a couple of clicks. The server keeps the files 14 days
// after the order became "shipped" (studio/archive.py); "Не видаляти" keeps a book until unmarked.
import {
  api, html, ic, ib, setHtml, on, media, toast, relTime, dateTime, copyText, fadeImages, openExternal, plural, patch,
  enterOnce,
} from '../lib.js';
import { openLightbox } from '../lightbox.js';
import {
  STAGE_LABEL, providerName, countryName, addressFromEtsy, spreadsOf, folderViewerItems, smoothWheel, trackChips,
  statusChip, receiptCopy, copyChip, isCustomText, isNameField, isFormatField, childOf as childOfTitle,
} from '../order-bits.js';
import { give } from '../handoff.js';

// Page previews the server prepares when a book is archived (archive._warm_previews): 360 and 1400.
const THUMB = 360;
const file = (e, name, w) => media('/media/folder', { path: e.folder, file: name, w });
/** The child's name from the title "4100000001 - Emma". */
const childOf = (e) => childOfTitle(e.title);
const printerChip = (e) => html`<span class="chip svc-${e.provider}">${ic(e.provider, 'icon-s')}${providerName(e.provider)}</span>`;

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
    <div class="page-head"><div><h1 class="page-title">Архів замовлень</h1>
      <div class="page-sub">${count ? `${count} ${plural(count, ['книга', 'книги', 'книг'])}` : ''}</div></div></div>
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
        <span class="row ord-chips"><b class="truncate">${e.buyer || e.title}</b>${e.receiptId ? receiptCopy(e, 'chip chip-mono') : ''}${printerChip(e)}
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
    setHtml(view, html`<button class="back-link" onclick="location.hash='#/archive'">${ic('arrowLeft', 'icon-s')}</button>
      <div class="empty"><div class="empty-icon">${ic('orderArchive')}</div><h3>Книгу не знайдено</h3><p>${err.message}</p></div>`);
    return null;
  }
  // The Etsy order it was printed for, when the last sync still has it (for the buyer's fields).
  let o = null;
  if (e.receiptId) { try { o = await api(`/api/orders/${e.receiptId}`); } catch { o = null; } }
  const keepDays = e.keepDays;
  const child = childOf(e);
  let pick = Math.max(0, (o?.items || []).findIndex((it) => it.childName && it.childName === child));
  const item = () => o?.items?.[pick] || {};

  setHtml(view, html`
    <div class="page-head">
      <button class="back-link" data-act="back" aria-label="До архіву" data-tip="До архіву" data-kbd="Esc">${ic('arrowLeft')}</button>
      <div class="grow" style="min-width:0">
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
      <span class="chip chip-lg svc-${e.provider}">${ic(e.provider, 'icon-s')}<span>${providerName(e.provider)} · ${e.pageCount} стор.</span></span>`);
  }

  // ---------------------------------------------------------------- left: what was printed, then the reprint
  function proofCard() {
    const it = item();
    const cover = (e.files || []).find((f) => f.file === 'Cover.png') || {};
    const ratio = cover.width ? cover.width / cover.height : 1.9;
    const half = (n) => (n === null ? html`<div class="half blank"></div>` : html`<div class="half"><img data-fade loading="lazy" decoding="async" src="${file(e, `${n}.png`, THUMB)}" alt=""></div>`);
    const notes = (it.variations || []).filter((v) => !isNameField(v) && !isFormatField(v));
    const name = it.childName || child;
    return html`<section class="card card-pad stack-l">
      <div class="row"><h3 class="card-title grow">Що пішло в друк</h3></div>
      <div class="proof">
        <div class="structure-cover" data-lb="0" style="aspect-ratio:${ratio}">
          <img data-fade decoding="async" src="${file(e, 'Cover.png', 1400)}" alt="Обкладинка"><div class="gutter"></div><i class="crops"></i>
        </div>
        <div class="spread-view proof-spread" data-lb="1">
          <div class="half proof-note">
            ${name ? html`<div class="proof-name">${name}</div>` : ''}
            <dl>${notes.map((v) => html`<dt>${v.name}</dt><dd>${v.value}</dd>`)}</dl>
          </div>
          <div class="half"><img data-fade decoding="async" src="${file(e, '1.png', 1400)}" alt="Сторінка 1"></div>
          <div class="gutter-s"></div><i class="crops"></i>
        </div>
      </div>
      <div class="strip" id="ar-strip">
        <div class="strip-item" data-lb="0" style="width:${Math.round(110 * ratio)}px">
          <div class="structure-cover" style="height:110px"><img data-fade loading="lazy" decoding="async" src="${file(e, 'Cover.png', THUMB)}" alt=""></div>
          <span class="strip-no">обкладинка</span></div>
        ${spreadsOf(e.pageCount).map((sp, i) => html`<div class="strip-item" data-lb="${i + 1}">
          <div class="spread-view">${half(sp.left)}${half(sp.right)}<div class="gutter-s"></div></div>
          <span class="strip-no num">${[sp.left, sp.right].filter(Boolean).join('–')}</span></div>`)}
      </div>
    </section>`;
  }

  function reprintCard() {
    const pr = e.provider === 'printify';
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
        ${pr && e.productId ? html`<dt>Product ID</dt><dd class="mono arc-id">${e.productId}${ib('copy', 'Копіювати Product ID', `data-act="copy-id" data-text="${e.productId}"`, { cls: 'sm' })}</dd>` : ''}
        ${e.orderId ? html`<dt>Order ID</dt><dd class="mono arc-id">${e.orderId}${ib('copy', 'Копіювати Order ID', `data-act="copy-id" data-text="${e.orderId}"`, { cls: 'sm' })}</dd>` : ''}
        ${e.reprintOf ? html`<dt>Передрук</dt><dd><a href="#/archive/${e.reprintOf}">першої відправки</a></dd>` : ''}
      </dl>
      <div class="faint arc-clock">${ic(e.keep ? 'pin' : 'clock', 'icon-s')}<span>${clockText(e, keepDays)}</span></div>
      <div class="row">${pr
        ? html`<button class="btn btn-sm" data-act="open-product">${ic('external', 'icon-s')}Відкрити в Printify</button>`
        : html`<button class="btn btn-sm" data-act="open-gelato">${ic('external', 'icon-s')}Gelato Dashboard</button>`}</div>
    </section>`;
  }

  function fieldsCard() {
    if (!o) return '';
    const it = item();
    const vars = it.variations || [];
    return html`<section class="card card-pad stack">
      <div class="row"><h3 class="card-title grow">Персоналізація</h3></div>
      ${vars.length ? html`<dl class="ord-fields">${vars.map((v, i) => html`
        <dt>${v.name}${isCustomText(v) ? html`<span class="chip chip-amber">свій текст</span>` : ''}</dt>
        <dd class="${isCustomText(v) ? 'custom' : ''} ${isNameField(v) ? 'is-name' : ''}"><span>${v.value}</span>${isFormatField(v) ? '' : ib('copy', 'Копіювати', `data-copy="${i}"`, { cls: 'sm' })}</dd>`)}</dl>`
        : html`<div class="faint">Покупець нічого не вказав.</div>`}
    </section>`;
  }

  function addressCard() {
    // The address the printer got (Order Creator's fields); else the one on Etsy.
    const a = e.address || null;
    const b = o?.address || {};
    const lines = a
      ? [[a.firstName, a.lastName].filter(Boolean).join(' '), a.addressLine1, a.addressLine2,
        [a.city, a.state, a.postCode].filter(Boolean).join(', '), countryName(a.country)]
      : [b.name, b.first_line, b.second_line, [b.city, b.state, b.zip].filter(Boolean).join(', '), countryName(b.country_iso)];
    if (!lines.some(Boolean)) return '';
    return html`<section class="card card-pad stack-s">
      <h3 class="card-title">${a ? 'Адреса, куди відправлено' : 'Доставка'}</h3>
      <div class="ord-address">${lines.filter(Boolean).map((line) => html`<div>${line}</div>`)}</div>
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
      e = await api(`/api/archive/${e.id}/keep`, { method: 'POST', body: { keep: !e.keep } });
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
      mode: e.provider, folder: e.folder, label: `Архів · ${e.title}`, title: e.title, address, format: e.format || null,
      reprint: { archiveId: e.id, productId: e.productId || null },
    });
    location.hash = '#/creator';
  }

  const offs = [
    on(view, 'click', '[data-act]', (ev, t) => {
      const a = t.dataset.act;
      if (a === 'back') location.hash = '#/archive';
      else if (a === 'keep') toggleKeep();
      else if (a === 'open-folder') api('/api/creator/open-folder', { method: 'POST', body: { path: e.folder } }).catch((er) => toast(er.message, 'error'));
      else if (a === 'open-sendlog') api('/api/sends/open', { method: 'POST', body: { file: e.sendLog || '' } }).catch((er) => toast(er.message, 'error'));
      else if (a === 'reprint') reprint();
      else if (a === 'open-product') openExternal(e.url || `https://printify.com/app/product-details/${e.productId}`);
      else if (a === 'open-gelato') openExternal('https://dashboard.gelato.com/');
      else if (a === 'copy-id') copyText(t.dataset.text, 'Скопійовано');
      else if (a === 'copy-text') copyChip(ev, t);
    }),
    on(view, 'click', '[data-copy]', (ev, b) => copyText(item().variations?.[+b.dataset.copy]?.value || '', 'Скопійовано')),
    on(view, 'click', '[data-lb]', (ev, c) => openLightbox(folderViewerItems(e.folder, e.pageCount, e.title), +c.dataset.lb)),
  ];
  // Esc steps back to the archive list when nothing else (a dialog, the viewer, a menu) owns the key.
  const onKey = (ev) => {
    if (ev.key !== 'Escape' || ev.defaultPrevented) return;
    if (document.querySelector('.modal-root, .lightbox, .menu')) return;
    location.hash = '#/archive';
  };
  document.addEventListener('keydown', onKey);

  render();
  return { unmount() { offs.forEach((fn) => fn()); document.removeEventListener('keydown', onKey); } };
}
