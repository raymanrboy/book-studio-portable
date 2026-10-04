// Order Creator: Printify unpublished photo books and Gelato draft orders from Canva PNG folders.
import {
  api, post, html, ic, ib, setHtml, on, media, toast, runJob, segHtml, syncSeg, setSeg, bytes, copyText, openExternal,
  debounce, keepFocus, fadeImages, setProgress, patch, enterOnce, confirmChecked, markMissing, backToTools, plural, BOOKS, attr,
} from '../lib.js';
import { openFolderViewer } from '../folder-viewer.js';
import {
  COUNTRIES, addressFromEtsy, spreadsOf, pagesText, restorable, childOf, receiptOfTitle, pageVersion, filesBadge,
  checkNotices,
} from '../order-bits.js';
import { receiveDrop, dropLabel, wireFolderDrop } from '../drop.js';
import { take } from '../handoff.js';
import { markSent, finish } from '../keep.js';
import { pickEtsyOrder } from './creator-picker.js';
import { gelatoResultHtml, runCountdown, resultAction, linkUntil } from './gelato-result.js';
import { pathHtml } from '../path.js';

export async function mount(view) {
  let status;
  let finished = false; // «Завершити»: this page is not kept when the owner leaves it
  try { status = await api('/api/creator/status'); }
  catch (err) { setHtml(view, html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`); return null; }

  // Every visit starts empty: nothing from an earlier book (folder, buyer, address) is remembered.
  // The one exception is an order handed over from its card a moment ago (in memory only); while that
  // order is new, this page is kept — form or result — when the owner steps to another tab (keep.js).
  // Printify: without an address only the unpublished book is made; with one, also an order for it that
  // waits "On hold" in Printify (like Gelato's draft) — nothing goes to production from here.
  // reprint: set only by the order archive's "Передрук" ({archiveId, productId}); another folder cancels it.
  // A book of the send: its own folder, name, format and file check. An Etsy order of two or three books
  // sends them all at once — one draft, one address (owner, 20.09.2026).
  // receiptId: the Etsy order the book was taken from (its card or «Заповнити із замовлення Etsy") — the
  // server keeps records by it, not by the number typed in the title.
  const newBook = (extra = {}) => ({
    folder: '', label: null, title: '', receiptId: '', validation: null, validating: 0, seq: 0,
    versions: {},        // page file -> how often it was replaced or put back: only its own pictures are fetched anew
    replaced: new Set(), // pages a new file was put over — they can be put back
    format: status.gelato.defaultFormat || status.gelato.formats[0]?.key, ...extra,
  });
  // From 1 October 2026 only Gelato prints (printify.retired()): Printify is not offered here any more.
  const gelatoOnly = !!status.printify.retired;
  const st = {
    mode: gelatoOnly ? 'gelato' : 'printify',
    printify: { books: [newBook()], pick: 0, running: false, result: null, error: null, address: { country: 'US' }, reprint: null },
    gelato: { books: [newBook()], pick: 0, running: false, result: null, error: null, address: { country: 'US' }, reprint: null },
  };
  const parcel = take('creator');
  const handedDrop = parcel?.drop || null; // files dropped anywhere in the window and sent here (drop-anywhere.js)
  const handed = handedDrop ? null : parcel;
  // The new order this page works on (from its card, or picked below); a reprint from the archive is not one.
  st.receiptId = handed?.receiptId && !handed.reprint ? String(handed.receiptId) : '';
  st.buyer = st.receiptId ? handed.buyer || '' : ''; // the order it prints: its head, its path (2026-09-30)
  if (handed && !(gelatoOnly && handed.mode === 'printify')) {
    st.mode = handed.mode;
    Object.assign(st[handed.mode], {
      books: handed.books.map((h) => newBook({ folder: h.folder, label: h.label, title: h.title, receiptId: st.receiptId, ...(h.format ? { format: h.format } : {}) })),
      pick: 0, address: { ...handed.address }, reprint: handed.reprint || null,
    });
  }
  const ADDRESS_NEEDED = { firstName: "Ім'я", lastName: 'Прізвище', addressLine1: 'Адреса', city: 'Місто', postCode: 'Індекс', country: 'Країна' };
  const hasAddress = (a) => ['firstName', 'lastName', 'addressLine1', 'city', 'postCode'].some((k) => (a[k] || '').trim());
  // A Printify reprint is always an order (for the book Printify already has), so it needs the address.
  const withOrder = () => st.mode === 'gelato' || !!st.printify.reprint || hasAddress(st.printify.address);
  const createLabel = () => (st.mode === 'gelato' ? (st.gelato.reprint ? 'Створити чернетку-передрук' : 'Створити чернетку')
    : st.printify.reprint ? 'Створити замовлення-передрук'
      : withOrder() ? 'Створити чернетку замовлення' : 'Створити книгу без замовлення');
  let stopCountdown = () => {};
  let gone = false; // the page was let go: its polls stop (runJob keepGoing)
  const cur = () => st[st.mode];
  const bk = (i = cur().pick) => cur().books[i] || cur().books[0];   // the book being shown / edited
  const many = () => cur().books.length > 1;
  const bookName = (i) => childOf(cur().books[i].title) || `Книга ${i + 1}`;

  // Pages: Printify takes exactly its template's 24; Gelato as many as the folder holds (28 or 30), and
  // its catalog says which of those each format is printed with (asked once, when Gelato is shown).
  const pageTotal = (i = cur().pick) => (st.mode === 'printify' ? status.printify.pageCount : bk(i).validation?.pageCount || 0);
  let pageCounts = null, pageProblems = {};
  let countsAsked = false;
  function loadPageCounts() {
    if (countsAsked || !status.gelato.keyConfigured) return;
    countsAsked = true;
    api('/api/creator/gelato/page-counts').then((r) => {
      pageCounts = r.formats || null;
      pageProblems = r.problems || {};
      if (st.mode === 'gelato') renderLeft();
    }).catch(() => {});
  }
  /** Why Gelato would not print the chosen folder in this format; '' when fine or not known. The words come
   *  from the server — the same the order card and the send itself use. */
  function formatProblem(key = bk().format, i = cur().pick) {
    const n = bk(i).validation?.pageCount;
    return (n && pageProblems[key]?.[n]) || '';
  }

  setHtml(view, html`<div class="creator" id="cr">
    <div class="page-head">
      <span id="cr-back"></span>
      <div class="grow"><h1 class="page-title truncate" id="cr-title-h">Order Creator</h1><div class="page-sub" id="cr-sub"></div></div>
      <div class="page-actions" id="cr-switch"></div>
    </div>
    <div id="cr-path"></div>
    <div id="cr-status"></div>
    <div id="cr-tunnels"></div>
    <div class="creator-grid">
      <div class="stack-l" id="cr-left"></div>
      <div class="stack-l" id="cr-right"></div>
    </div></div>`);
  const $ = (s) => view.querySelector(s);
  const root = $('#cr');

  // ---------------------------------------------------------------- header / status
  function renderSwitch() {
    // The tick closes the work on this order: the page and its card forget it and the queue opens.
    setHtml($('#cr-switch'), html`<div class="tools cr-tools">${st.receiptId && cur().result
      ? ib('checkCircle', 'Завершити роботу над замовленням', 'data-act="finish"') : ''}${ib('sendLog', 'Журнал відправок', 'data-act="open-sendlog"')}</div>${gelatoOnly ? '' : html`<div class="mode-switch">${segHtml([
      { value: 'printify', icon: 'printify', tip: 'Printify — неопублікована книга' },
      { value: 'gelato', icon: 'gelato', tip: 'Gelato — чернетка замовлення' }], st.mode, { name: 'mode' })}</div>`}`);
    if (!gelatoOnly) requestAnimationFrame(() => syncSeg($('#cr-switch .seg')));
  }

  // Only the service name in the header; a line appears under it only when something is missing.
  function renderStatus() {
    const p = status.printify, g = status.gelato;
    const pr = st.mode === 'printify';
    root.classList.toggle('mode-gelato', !pr);
    // Opened from an order's card, this page is that order's print step: its buyer, the way back, its path. On its
    // own (from «Інструменти»), the tool's name (2026-09-30; the service's name alone read like another program).
    const printer = pr ? 'Printify' : 'Gelato';
    $('#cr-title-h').textContent = st.receiptId ? (st.buyer || `#${st.receiptId}`) : 'Order Creator';
    setHtml($('#cr-sub'), st.receiptId ? html`<span class="mono">#${st.receiptId}</span> · друк у ${printer}` : html`Друк у ${printer} з папки файлів`);
    setHtml($('#cr-back'), st.receiptId ? html`<a class="back-link" href="#/orders/${st.receiptId}" aria-label="До замовлення" data-tip="До замовлення">${ic('arrowLeft')}</a>` : backToTools());
    const made = !!cur().result;
    setHtml($('#cr-path'), st.receiptId ? pathHtml([
      { key: 'canva', label: 'Canva', icon: 'canva', state: 'done' }, { key: 'files', label: 'Файли', icon: 'folderIn', state: 'done' },
      { key: 'proof', label: 'Вичитка', icon: 'textScan', state: 'done' },
      { key: 'print', label: 'Друк', icon: 'printer', state: made ? 'part' : 'todo', count: made ? 'підтвердіть' : '',
        tip: made ? 'Чернетку створено — підтвердіть і оплатіть її в друкарні' : 'Друк: створіть чернетку нижче' },
      { key: 'ship', label: 'Відправка', icon: 'truck', state: 'todo' }], { label: 'Шлях замовлення', active: 'print', act: 'order-path' }) : '');
    const missing = pr
      ? [!p.tokenConfigured && html`Немає токена Printify — <a href="#/settings/printify">Налаштування</a>`,
        p.tokenConfigured && !p.masterId && html`Не обрано шаблон книги — <a href="#/settings/printify">Налаштування</a>`]
      : [!g.keyConfigured && html`Немає ключа Gelato — <a href="#/settings/gelato">Налаштування</a>`,
        !g.cloudflared && html`Немає bin/cloudflared.exe — Gelato не зможе забрати файли`];
    const lines = missing.filter(Boolean);
    setHtml($('#cr-status'), lines.length ? html`<div class="notice notice-warn" style="margin-bottom:16px">${ic('alert')}<div>${lines.map((l) => html`<div>${l}</div>`)}</div></div>` : '');
  }

  function renderTunnels() {
    const active = status.gelato.activeTunnels || [];
    if (!active.length || st.mode !== 'gelato' || st.gelato.result) { setHtml($('#cr-tunnels'), ''); return; }
    setHtml($('#cr-tunnels'), html`<div class="notice notice-warn" style="margin-bottom:16px">${ic('clock')}<div class="grow">
      Тимчасове посилання на файли чернетки Gelato ще працює (${active.map((t) => `${t.key.slice(0, 8)}… — ${Math.ceil(t.secondsLeft / 60)} хв`).join(', ')}).
      Gelato забирає файли сам, зазвичай за хвилину.</div>
      ${active.map((t) => ib('unlink', 'Закрити посилання', `data-close-tunnel="${t.key}"`, { cls: 'sm' }))}</div>`);
  }

  // ---------------------------------------------------------------- left column
  /** A book's file check as a badge: running (with its own id, so each book's percent lands on its own badge),
   *  passed, or failed. */
  function checkBadge(b, i) {
    return filesBadge(b.validation, { busy: b.validating, id: `cr-badge-${i}` });
  }
  const badgeProgress = (i, pct) => { const num = view.querySelector(`#cr-badge-${i} .num`); if (num) num.textContent = `${Math.round(pct)}%`; };

  /** One book's folder: the path, what the check found, and (with several books) its own name. */
  function folderBlock(i) {
    const s = cur();
    const b = cur().books[i];
    const v = b.validation;
    // A dragged folder is shown by its own name (b.label); b.folder is where the program copied it.
    return html`<div class="cr-book ${many() && i === cur().pick ? 'is-shown' : ''}" data-folder-drop data-book="${i}">
      ${many() ? html`<div class="row cr-book-head"><button class="cr-book-name" data-act="show-book" data-book="${i}" data-tip="Показати структуру цієї книги">${ic('book', 'icon-s')}Книга ${i + 1}</button>
        <span class="spacer"></span>${checkBadge(b, i)}${cur().books.length > 2 || !cur().books[i].folder ? ib('x', 'Прибрати книгу', `data-act="drop-book" ${attr('data-book', i)}`, { cls: 'sm' }) : ''}</div>` : ''}
      <div class="input-group">
        <input class="input path-input" id="cr-folder-${i}" data-book="${i}" placeholder="Папку ще не вибрано" value="${b.label || b.folder}" title="${b.label ? b.folder : ''}" spellcheck="false" autocomplete="off" aria-label="Шлях до папки">
        ${ib('folderPick', 'Обрати папку', `data-act="browse" ${attr('data-book', i)}`)}
      </div>
      ${s.reprint && i === 0 ? html`<div class="row faint cr-reprint">${ic('orderArchive', 'icon-s')}<span>${st.mode === 'printify'
        ? 'Передрук з архіву: нове замовлення на книгу, яка вже є в Printify'
        : 'Передрук з архіву: нова чернетка з тих самих файлів'}</span></div>` : ''}
      ${v && !b.validating ? html`
        ${checkNotices(v.errors, v.warnings, 'Перевірка не пройдена')}
        <div class="row">${v.ok ? html`<span class="faint mono" style="font-size: var(--fs-s)">${bytes(v.totalBytes)}</span>` : ''}<span class="spacer"></span>
          ${v.ok ? ib('folderOpen', 'Відкрити папку', `data-act="open-folder" ${attr('data-book', i)}`, { cls: 'sm' }) : ''}
          ${ib('scan', 'Перевірити файли знову', `data-act="revalidate" ${attr('data-book', i)}`, { cls: 'sm' })}</div>` : ''}
    </div>`;
  }

  function folderCard(num) {
    const one = !many();
    const badge = one ? checkBadge(bk(), cur().pick) : '';
    return html`<section class="card card-pad stack">
      <div class="row"><span class="step-no">${num}</span><h3 class="card-title grow">${one ? 'Папка з файлами' : `Папки з файлами · ${cur().books.length} ${plural(cur().books.length, BOOKS)}`}</h3>${badge}</div>
      ${cur().books.map((x, i) => folderBlock(i))}
      ${st.receiptId || many() ? html`<button class="btn btn-sm btn-ghost" style="align-self:flex-start" data-act="add-book"
        data-tip="Ще одна книга цього ж замовлення — вони підуть у друк разом, однією чернеткою">${ic('plus', 'icon-s')}Ще книга</button>` : ''}
    </section>`;
  }

  function titleCard(num) {
    return html`<section class="card card-pad stack">
      <div class="row"><span class="step-no">${num}</span><h3 class="card-title grow">${many() ? 'Назви книг' : 'Назва'}</h3>
        ${ib('receipt', st.mode === 'gelato' ? 'Заповнити назву й адресу із замовлення Etsy' : 'Заповнити із замовлення Etsy', 'data-act="from-etsy"', { cls: 'sm' })}</div>
      ${cur().books.map((b, i) => html`${many() ? html`<label class="eyebrow" for="cr-title-${i}">Книга ${i + 1}</label>` : ''}
        <input class="input input-lg" id="cr-title-${i}" data-book="${i}" placeholder="4100000001 - Emma" value="${b.title}" autocomplete="off" aria-label="Назва книги ${i + 1}">`)}
    </section>`;
  }

  function formatCard(num) {
    const pill = (f, i) => {
      const valid = pageCounts?.[f.key];
      const bad = formatProblem(f.key, i);
      const tip = bad || (valid?.length ? `${valid[0]}–${valid.at(-1)} стор.` : '');
      return html`<button class="fmt-pill ${cur().books[i].format === f.key ? 'active' : ''} ${bad ? 'bad' : ''}" data-format="${f.key}" data-book="${i}" data-tip="${tip}">${f.label}</button>`;
    };
    return html`<section class="card card-pad stack">
      <div class="row"><span class="step-no">${num}</span><h3 class="card-title">${many() ? 'Формати книг' : 'Формат'}</h3></div>
      ${cur().books.map((b, i) => {
        const problem = formatProblem(b.format, i);
        return html`${many() ? html`<span class="eyebrow">Книга ${i + 1}</span>` : ''}
          <div class="fmt-pills">${status.gelato.formats.map((f) => pill(f, i))}</div>
          ${problem ? html`<div class="notice notice-warn">${ic('alert')}<div>${problem}</div></div>` : ''}`;
      })}
    </section>`;
  }

  function addressCard(num) {
    const a = cur().address;
    // Every field keeps its name above it once filled (2026-09-30: a filled form could not tell «Місто» from «Штат»).
    const inp = (key, label, { span = '', ph = '', need = false } = {}) => html`<label class="fld ${span}"><span class="fld-label">${label}${need ? html`<i class="fld-need" aria-hidden="true">*</i>` : ''}</span>
      <input class="input" id="addr-${key}" data-addr="${key}" placeholder="${ph}" value="${a[key] || ''}" autocomplete="off" ${need ? html`aria-required="true"` : ''}></label>`;
    return html`<section class="card card-pad stack">
      <div class="row"><span class="step-no">${num}</span><h3 class="card-title grow">Адреса отримувача</h3>
        ${ib('eraser', 'Очистити адресу', 'data-act="clear-address"', { cls: 'sm' })}</div>
      <div class="addr-grid">
        ${inp('firstName', "Ім'я", { need: true })}${inp('lastName', 'Прізвище', { need: true })}
        ${inp('addressLine1', 'Адреса', { span: 'span2', need: true })}${inp('addressLine2', 'Адреса, рядок 2', { span: 'span2' })}
        ${inp('city', 'Місто', { need: true })}${inp('state', 'Штат / провінція', { ph: 'для US, CA, AU' })}
        ${inp('postCode', 'Індекс', { need: true })}
        <label class="fld"><span class="fld-label">Країна</span><select class="select" data-addr="country">${COUNTRIES.map(([c, n]) => html`<option value="${c}" ${(a.country || 'US') === c ? 'selected' : ''}>${c} — ${n}</option>`)}</select></label>
        ${inp('phone', 'Телефон', { span: 'span2', ph: st.mode === 'gelato' ? 'порожньо — підставиться вигаданий' : 'необов’язково' })}
      </div>
    </section>`;
  }

  function createCard(num) {
    const s = cur();
    return html`<section class="card card-pad stack">
      <div class="row"><span class="step-no">${num}</span><h3 class="card-title grow">Чернетка</h3></div>
      <div id="cr-alert">${s.error ? html`<div class="notice notice-error">${ic('alertCircle')}<div class="grow" style="white-space:pre-line">${s.error}</div>${sendLogButton(null)}</div>` : ''}</div>
      <div class="row" style="justify-content:center;padding:4px 0">
        <button class="btn btn-xl create-btn btn-block" id="cr-create" ${s.running ? 'disabled' : ''}>
          ${s.running ? html`<span class="spinner" style="border-color:color-mix(in srgb, currentColor 35%, transparent);border-top-color:currentColor"></span>Створення…` : html`${ic('send', 'icon-l')}<span id="cr-create-label">${createLabel()}</span>`}</button>
      </div>
      <div id="cr-progress" ${s.running ? '' : 'hidden'}>
        <div class="row" style="margin-bottom:6px;font-size: var(--fs)"><span id="cr-step" style="font-weight:600" class="grow">Підготовка…</span><span class="num" id="cr-pct" style="color:var(--accent-ink);font-weight:600">0%</span></div>
        <div class="progress"><i id="cr-bar"></i></div>
        <div class="faint mono truncate" id="cr-detail" style="font-size: var(--fs-s);margin-top:6px"></div>
      </div>
      <div id="cr-result">${resultHtml()}</div>
    </section>`;
  }

  // Every send is written to data/logs/sends — the icon opens this one's record (or the folder).
  const sendLogButton = (r) => ib('sendLog', 'Журнал відправки', `data-act="open-sendlog" ${attr('data-file', r?.sendLog || '')}`, { cls: 'sm' });

  function resultHtml() {
    const s = cur();
    const r = s.result;
    if (!r) return '';
    if (st.mode === 'printify') {
      // A reprint for the book Printify already has sends nothing but the order (no upload counts to show).
      const sameBook = r.reprint && r.uploaded === undefined;
      return html`<div class="result-card">
        <h4>${ic('checkCircle')}${r.reprint ? 'Передрук: замовлення створено в Printify!' : r.order ? 'Чернетку замовлення створено в Printify!' : 'Книгу створено в Printify!'}</h4>
        <dl class="kv">
          <dt>Назва</dt><dd>${r.title}</dd>
          ${(r.books || []).length > 1
            ? html`<dt>Книги</dt><dd>${r.books.map((b) => html`<div>${b.title} · <span class="mono">${b.productId}</span></div>`)}</dd>`
            : html`<dt>Product ID</dt><dd class="mono">${r.productId}</dd>`}
          ${r.order ? html`<dt>Order ID</dt><dd class="mono">${r.order.id}</dd>
            <dt>Замовлення</dt><dd>На утриманні (On hold) · ${r.order.variant} — у виробництво лише після «Submit order» у Printify</dd>`
            : html`<dt>Статус</dt><dd>Неопублікована книга (Unpublished)</dd>`}
          ${sameBook ? html`<dt>Книга</dt><dd>та сама, що й першого разу — нічого не завантажувалось</dd>`
            : html`<dt>Ілюстрації</dt><dd>${r.total}/${r.total} на позиціях Master${r.reused ? ` · ${r.reused} вже були завантажені` : ''}</dd>
          <dt>Перевірка</dt><dd>${r.verified ? '✓ позиції збігаються' : '— не підтверджено'} · Master ${r.masterSafe === true ? '✓ не змінено' : r.masterSafe === false ? '⚠ змінився' : '—'}</dd>`}
        </dl>
        ${r.orderError ? html`<div class="notice notice-error" style="margin-top:10px">${ic('alertCircle')}<div>${r.orderError}</div></div>` : ''}
        ${(r.warnings || []).map((w) => html`<div class="notice notice-warn" style="margin-top:10px">${ic('alert')}<div>${w}</div></div>`)}
        <div class="row" style="margin-top:14px">${r.order
          ? html`<button class="btn btn-primary grow" data-act="open-orders">${ic('external', 'icon-s')}Замовлення в Printify</button>${ib('copy', 'Копіювати Order ID', 'data-act="copy-printify-order"')}`
          : html`<button class="btn btn-primary grow" data-act="open-product">${ic('external', 'icon-s')}Відкрити в Printify</button>${ib('copy', 'Копіювати Product ID', 'data-act="copy-id"')}`}${sendLogButton(r)}</div>
      </div>`;
    }
    return gelatoResultHtml(r);
  }

  function renderLeft() {
    const blocks = st.mode === 'printify'
      ? [folderCard(1), titleCard(2), addressCard(3), createCard(4)]
      : [formatCard(1), folderCard(2), titleCard(3), addressCard(4), createCard(5)];
    // In place (patch()): an unchanged step card stays as it is — the green result card and the warnings no longer
    // bounce in again on every click and twice per dropped folder (26.09.2026).
    keepFocus(() => patch($('#cr-left'), blocks.map((markup, i) => [String(i), markup])));
    if (st.mode === 'gelato') loadPageCounts();
    if (st.mode === 'gelato' && st.gelato.result) startCountdown();
  }

  // ---------------------------------------------------------------- right column (structure)
  const fileState = (name) => {
    const v = bk().validation;
    if (!v) return null;
    const row = v.files.find((r) => r.file.toLowerCase() === name.toLowerCase());
    return row ? (row.ok ? 'ok' : 'bad') : 'missing';
  };
  const thumb = (name, w = 420) => media('/media/folder', { path: bk().folder, file: name, w, ...pageVersion(bk().versions, name) });

  function renderRight() {
    const s = cur();
    const b = bk();
    const pr = st.mode === 'printify';
    const known = pageTotal(); // a Gelato book's length is known once its folder is checked
    const total = known || Math.max(...status.gelato.pageCounts);
    const v = b.validation;
    const has = (n) => v && v.files.some((r) => r.file.toLowerCase() === n.toLowerCase());
    const coverRow = v?.files.find((r) => r.position === 'cover');
    const ratio = coverRow?.width ? `${coverRow.width} / ${coverRow.height}` : pr ? `${status.printify.coverSize[0]} / ${status.printify.coverSize[1]}` : '464 / 249';
    const spreads = spreadsOf(total);
    const count = v ? v.found : 0;
    const expectedCount = total + 1;
    const fmtLabel = pr ? 'Hardcover 8×8' : (status.gelato.formats.find((f) => f.key === b.format)?.label || '');
    const half = (n, side, blankLabel) => {
      if (n === null) return html`<div class="half blank"><span>${blankLabel}</span></div>`;
      const name = `${n}.png`;
      const stt = fileState(name);
      return html`<div class="half ${stt === 'bad' ? 'bad' : ''}">${has(name) ? html`<img data-fade loading="lazy" decoding="async" src="${thumb(name)}" alt="">` : html`<span class="ph-num">${n}</span>`}</div>`;
    };
    // The structure is redrawn in place: an unchanged spread card keeps its pictures and no card replays its entrance
    // (every format pill, «Книга N», drop and check end redrew all of it, 26.09.2026). The entrance plays once, when
    // the cards first come.
    const grid = $('#cr-right .spread-grid');
    const hadCards = !!grid?.children.length;
    if (!grid) setHtml($('#cr-right'), html`<section class="card card-pad stack-l"><div id="cr-st-head"></div><div id="cr-st-cover"></div>
      <div class="stack-s"><div id="cr-st-spreads"></div><div class="spread-grid"></div></div></section>`);
    patch($('#cr-st-head'), [['head', html`
      <div class="row" style="align-items:baseline">
        <h2 class="card-title grow" style="font-size: var(--fs-l)">Структура <span class="faint" style="font-weight:500">· ${many() ? `${bookName(cur().pick)} · ` : ''}${fmtLabel}</span></h2>
        <span class="v-badge ${count === expectedCount && v?.ok ? 'ok' : ''}" data-tip="Зображень у папці"><span class="num">${count}/${expectedCount}</span></span>
      </div>`]]);
    patch($('#cr-st-cover'), [['cover', html`
      <div class="stack-s">
        <div class="row"><span class="eyebrow grow">Обкладинка</span><span class="num faint" style="font-size: var(--fs-s)">${coverRow?.width ? `${coverRow.width}×${coverRow.height}` : ''}</span></div>
        <div class="structure-cover" data-lb="0" role="button" tabindex="0" data-press aria-label="Відкрити обкладинку" style="aspect-ratio:${ratio}">
          ${has('Cover.png') ? html`<img data-fade decoding="async" src="${thumb(coverRow.file, 1400)}" alt="Обкладинка">` : html`<div class="cover-ph"><div>Задня</div><div>Передня</div></div>`}
          <div class="gutter"></div>
          ${coverRow && !coverRow.ok ? html`<div class="page-tag" style="background:var(--red);left:auto;right:8px">${coverRow.error}</div>` : ''}
          <i class="crops"></i>
        </div>
      </div>`]]);
    patch($('#cr-st-spreads'), [['spreads', html`
        <div class="row"><span class="eyebrow grow">Розвороти</span><span class="faint" style="font-size: var(--fs-s)">${known
          ? html`<span class="num">${spreads.length}</span> · <span class="num">${total}</span> стор.`
          : html`<span class="num">${pagesText(status.gelato.pageCounts)}</span> стор.`}</span></div>`]]);
    const cards = patch($('#cr-right .spread-grid'), spreads.map((sp, i) => {
          const lp = i === 0 ? 1 : sp.left + 1;
          const rp = i === 0 ? 2 : lp + 1;
          const lf = sp.left ? `${sp.left}.png` : null, rf = sp.right ? `${sp.right}.png` : null;
          const mark = (f) => { if (!f) return ''; const x = fileState(f); return html`<span class="${x === 'ok' ? 'file-ok' : x ? 'file-bad' : ''}">${f}</span>`; };
          return [`s${i}`, html`<div class="spread-card" data-lb="${i + 1}" role="button" tabindex="0" data-press aria-label="Відкрити розворот ${lp}–${rp}">
            <div class="spread-view">${half(sp.left, 'left', 'Форзац')}${half(sp.right, 'right', 'Нахзац')}<div class="gutter-s"></div><i class="crops"></i></div>
            <div class="spread-card-head"><span class="spread-no">${lp}–${rp}</span><span class="spacer"></span><span class="spread-files">${mark(lf)}${mark(rf)}</span></div></div>`];
        }));
    if (!hadCards) cards.forEach((n, i) => enterOnce(n, Math.min(i * 25, 300)));
    fadeImages(view.querySelector('#cr-right'));
  }

  // The viewer of one book's structure (folder-viewer.js): a page replaced or put back there, the folder is checked
  // again — a page of the wrong size is caught here.
  function openStructure(index) {
    const b = bk();
    const i = cur().pick;
    if (!b.validation || !b.folder) { toast('Спершу оберіть папку з ілюстраціями', 'info'); return; }
    openFolderViewer(b, index, {
      total: pageTotal(i), label: b.label || b.folder,
      sent: () => !!cur().result,
      again: 'створити чернетку ще раз?',
      changed: () => validate(i),
    });
  }

  function renderAll() {
    renderSwitch(); renderStatus(); renderTunnels(); renderLeft(); renderRight();
  }

  // ---------------------------------------------------------------- validation (each book on its own)
  async function validate(i = cur().pick) {
    const s = cur();
    const b = s.books[i];
    const mode = st.mode;
    if (!b || !b.folder.trim()) { if (b) b.validation = null; renderLeft(); renderRight(); return; }
    const my = ++b.seq;
    b.validating = 1; s.error = null;
    renderLeft();
    try {
      const res = await runJob(post('/api/creator/validate', { mode, folder: b.folder }), (j) => {
        if (my !== b.seq || st.mode !== mode) return;
        b.validating = Math.max(1, j.percent);
        badgeProgress(i, b.validating);
      }, 300, () => my === b.seq && !gone);
      if (my !== b.seq) return;
      b.validation = res;
      b.replaced = restorable(res);
    } catch (err) {
      if (my !== b.seq) return;
      b.validation = { ok: false, errors: [err.message], warnings: [], files: [], found: 0, expected: 0 };
    } finally {
      if (my === b.seq) {
        b.validating = 0;
        if (st.mode === mode) { renderLeft(); renderRight(); }
      }
    }
  }
  const validateSoon = debounce((i) => validate(i), 600);

  // ---------------------------------------------------------------- create
  async function create() {
    const s = cur();
    if (s.running) return; // Enter in a title while it sends: the send already under way goes on alone
    const mode = st.mode;
    s.books.forEach((b, i) => { b.title = ($(`#cr-title-${i}`)?.value ?? b.title).trim(); });
    const problems = [];
    // A Printify reprint sends no files (the book is already in Printify; if it is gone, the server checks
    // the archived files itself before making it again), so the folder check does not hold it back.
    const filesSent = !(mode === 'printify' && s.reprint);
    s.books.forEach((b, i) => {
      const which = many() ? ` (книга ${i + 1})` : '';
      if (!b.folder) problems.push(`Оберіть папку з ілюстраціями${which}.`);
      else if (filesSent && b.validating) problems.push(`Зачекайте завершення перевірки файлів${which}.`);
      else if (filesSent && b.validation && !b.validation.ok) problems.push(`Виправте помилки у файлах${which}.`);
      if (!b.title) problems.push(`Введіть назву книги${which}.`);
      if (mode === 'gelato' && formatProblem(b.format, i)) problems.push(formatProblem(b.format, i));
    });
    const order = withOrder();
    if (order) {
      const a = s.address;
      const empty = Object.keys(ADDRESS_NEEDED).filter((k) => !(a[k] || '').trim());
      const miss = empty.map((k) => ADDRESS_NEEDED[k]);
      if (miss.length) problems.push(`Заповніть адресу: ${miss.join(', ')}.`);
      const needState = ['US', 'CA', 'AU'].includes((a.country || '').toUpperCase()) && !(a.state || '').trim();
      if (needState) problems.push('Для цієї країни потрібен штат/провінція.');
      markMissing([...empty, ...(needState ? ['state'] : [])].map((k) => $(`#addr-${k}`)));
      if (mode === 'printify' && !status.printify.matteVariant) problems.push('У шаблоні Printify немає увімкненого матового варіанту.');
    }
    if (problems.length) {
      setHtml($('#cr-alert'), html`<div class="notice notice-warn">${ic('alert')}<div>${problems.map((p) => html`<div>${p}</div>`)}</div></div>`);
      return;
    }
    if (mode === 'printify' && order && !status.printify.manualApproval && !(await confirmManualApproval())) return;
    s.running = true; s.result = null; s.error = null;
    renderLeft();
    const reprint = s.reprint;
    const url = mode === 'gelato' ? '/api/creator/gelato/create' : reprint ? '/api/creator/printify/reprint' : '/api/creator/printify/create';
    const books = s.books.map((b) => ({ folder: b.folder, title: b.title, format: b.format, receiptId: b.receiptId || null }));
    const body = mode === 'gelato'
      ? { books, address: s.address, ...(reprint ? { reprintOf: reprint.archiveId } : {}) }
      : reprint ? { archiveId: reprint.archiveId, title: bk().title, address: s.address }
        : { books, address: order ? s.address : null };
    try {
      s.result = await runJob(post(url, body), (j) => {
        if (st.mode !== mode) return;
        const bar = $('#cr-bar');
        if (!bar) return;
        $('#cr-step').textContent = j.step;
        $('#cr-pct').textContent = `${Math.round(j.percent)}%`;
        $('#cr-detail').textContent = j.detail || '';
        setProgress(bar, j.percent);
      });
      if (mode === 'gelato') linkUntil(s.result);
      if (st.receiptId && !reprint) markSent(st.receiptId, { provider: mode, what: sentText(mode, s.result), result: mode === 'gelato' ? s.result : null });
      if (s.result?.orderError) toast('Книгу створено, але замовлення — ні. Подробиці в картці.', 'error', 7000);
      else if (reprint) toast(mode === 'gelato' ? 'Передрук: чернетку створено в Gelato' : 'Передрук: замовлення створено в Printify', 'success');
      else toast(mode === 'gelato' ? 'Чернетку створено в Gelato' : s.result?.order ? 'Чернетку замовлення створено в Printify' : 'Книгу створено в Printify', 'success');
      status = await api('/api/creator/status');
    } catch (err) {
      s.error = err.message;
    } finally {
      s.running = false;
      if (st.mode === mode) { renderSwitch(); renderStatus(); renderLeft(); }
    }
  }

  /** What the order's card says once the draft is made (its print step shows it instead of «До друку»). */
  function sentText(mode, r) {
    const n = (r?.books || []).length;
    const books = n > 1 ? ` · ${n} ${plural(n, BOOKS)}` : '';
    if (mode === 'gelato') return `Чернетку замовлення створено в Gelato${books}`;
    if (r?.orderError) return `${n > 1 ? 'Книги' : 'Книгу'} створено в Printify, замовлення — ні (подробиці в Order Creator)`;
    return r?.order ? `Чернетку замовлення створено в Printify (On hold)${books}`
      : `${n > 1 ? 'Книги' : 'Книгу'} створено в Printify, без замовлення`;
  }

  // Once: an order from here is safe only while the Printify store approves orders by hand — with
  // automatic approval Printify itself would send it to production (and charge) at the set time.
  function confirmManualApproval() {
    return confirmChecked({
      title: 'Ручне затвердження замовлень у Printify',
      warning: html`Замовлення з Book Studio чекає в Printify «On hold» і не списує гроші, доки ви не натиснете <b>Submit order</b>. Але якщо в магазині стоїть <b>автоматичне</b> затвердження, Printify сам відправить його у виробництво в заданий час і спише оплату.`,
      extra: html`<div class="faint" style="font-size: var(--fs)">Printify → Store settings → Order settings → Order approval: <b>Manual</b></div>`,
      check: 'У моєму магазині стоїть ручне затвердження (Manual)',
      act: async () => {
        await post('/api/printify/manual-approval', {});
        status.printify.manualApproval = true;
      },
    });
  }

  function startCountdown() {
    stopCountdown();
    const card = $('#cr-left .result-card');
    if (st.gelato.result && card) stopCountdown = runCountdown(card, st.gelato.result, () => renderLeft());
  }

  // ---------------------------------------------------------------- an Etsy order picked (creator-picker.js)
  function fillFromOrder(o) {
    const s = cur();
    if (o.stage === 'new') { st.receiptId = String(o.receiptId); st.buyer = o.name || ''; renderStatus(); }
    // An order of several books gives a name to each of them (a folder is still chosen for each by hand).
    const names = (o.items || []).map((it) => it.childName || o.childName || '');
    while (s.books.length < Math.max(1, names.length)) s.books.push(newBook({ format: bk(0).format }));
    s.books.forEach((b, i) => {
      b.receiptId = String(o.receiptId);
      b.title = `${o.receiptId} - ${names[i] || names[0] || ''}`.trim().replace(/-$/, '- ');
    });
    s.address = { ...s.address, ...addressFromEtsy(o) };
    renderLeft();
    const ti = $('#cr-title-0');
    if (ti) { ti.focus(); ti.setSelectionRange(ti.value.length, ti.value.length); }
    toast(o.childName ? 'Заповнено із замовлення — перевірте назву' : 'Допишіть ім’я дитини в назві', 'info', 3500);
  }

  // ---------------------------------------------------------------- drag & drop onto the folder block
  // A dragged folder or ZIP is copied into the program first; the field shows the folder's own name.
  async function dropFolder(dropped, zone) {
    const s = cur();
    const i = zone?.dataset.book ? +zone.dataset.book : cur().pick;
    const b = s.books[i];
    const mode = st.mode;
    const my = ++b.seq; // anything still being checked for the old folder is ignored from now on
    s.pick = i;
    s.reprint = null;
    Object.assign(b, { folder: '', label: dropLabel(dropped), validation: null, validating: 1 });
    s.error = null;
    renderLeft(); renderRight();
    try {
      const path = await receiveDrop(dropped, (pct) => {
        if (my !== b.seq || st.mode !== mode) return;
        b.validating = pct;
        badgeProgress(i, pct);
      });
      if (my !== b.seq) return;
      b.folder = path;
      b.validating = 0;
      if (st.mode === mode) validate(i);
    } catch (err) {
      if (my !== b.seq) return;
      Object.assign(b, { folder: '', label: null, validating: 0, validation: { ok: false, errors: [err.message], warnings: [], files: [], found: 0, expected: 0 } });
      if (st.mode === mode) { renderLeft(); renderRight(); }
    }
  }
  wireFolderDrop(view, (zone) => zone?.querySelector('.path-input') || $(`#cr-folder-${cur().pick}`), dropFolder);
  // A drop anywhere else on this page is the current book's folder too; one handed over from another page is taken as it opens.
  view.addEventListener('bs:dropped', (e) => { e.detail.handled = true; dropFolder(e.detail.dropped); });
  if (handedDrop) dropFolder(handedDrop);

  // ---------------------------------------------------------------- events
  const offs = [
    on(view, 'click', '[data-seg="mode"] button', (e, b) => {
      if (st.mode === b.dataset.value) return;
      st.mode = b.dataset.value; setSeg(b.closest('.seg'), st.mode);
      renderStatus(); renderTunnels(); renderLeft(); renderRight();
      cur().books.forEach((x, i) => { if (x.folder && !x.validation && !x.validating) validate(i); });
    }),
    on(view, 'click', '[data-act]', async (e, t) => {
      const a = t.dataset.act;
      const s = cur();
      const i = t.dataset.book ? +t.dataset.book : s.pick;
      const b = s.books[i] || bk();
      if (a === 'browse') {
        try {
          const { path } = await post('/api/creator/pick-folder', { title: `Оберіть папку з Cover.png та ${(st.mode === 'printify' ? [status.printify.pageCount] : status.gelato.pageCounts).map((n) => `1–${n}.png`).join(' або ')}`, initial: b.folder });
          if (path) { Object.assign(b, { folder: path, label: null, validation: null }); s.pick = i; s.reprint = null; renderLeft(); renderRight(); validate(i); }
        } catch (err) { toast(err.message, 'error'); }
      } else if (a === 'finish') { finished = true; finish(st.receiptId); toast('Роботу над замовленням завершено', 'success'); location.hash = '#/orders'; }
      else if (a === 'order-path') { if (t.dataset.step !== 'print') location.hash = `#/orders/${st.receiptId}`; }
      else if (a === 'revalidate') validate(i);
      else if (a === 'show-book') { s.pick = i; renderLeft(); renderRight(); }
      else if (a === 'add-book') {
        const receipt = bk(0).receiptId || receiptOfTitle(bk(0).title);
        s.books.push(newBook({ format: bk(0).format, receiptId: bk(0).receiptId, title: receipt ? `${receipt} - ` : '' }));
        s.pick = s.books.length - 1; renderLeft(); renderRight();
      }
      else if (a === 'drop-book' && s.books.length > 1) { s.books.splice(i, 1); s.pick = Math.min(s.pick, s.books.length - 1); renderLeft(); renderRight(); }
      else if (a === 'open-folder') post('/api/creator/open-folder', { path: b.folder }).catch((er) => toast(er.message, 'error'));
      else if (a === 'from-etsy') pickEtsyOrder(fillFromOrder);
      else if (a === 'clear-address') { s.address = { country: 'US' }; renderLeft(); $('#addr-firstName')?.focus(); }
      else if (a === 'open-orders') openExternal('https://printify.com/app/orders');
      else if (a === 'copy-printify-order') copyText(st.printify.result?.order?.id || '', 'Order ID скопійовано');
      else if (a === 'open-product') openExternal(st.printify.result?.url);
      else if (a === 'copy-id') copyText(st.printify.result?.productId || '', 'Product ID скопійовано');
      else if (st.gelato.result && await resultAction(a, st.gelato.result, t)) {
        if (a === 'close-tunnel') { stopCountdown(); renderLeft(); }
      }
      else if (a === 'open-sendlog') post('/api/sends/open', { file: t.dataset.file || '' }).catch((er) => toast(er.message, 'error'));
    }),
    on(view, 'click', '#cr-create', () => create()),
    on(view, 'click', '[data-format]', (e, b) => {
      const i = b.dataset.book ? +b.dataset.book : cur().pick;
      cur().books[i].format = b.dataset.format;
      cur().pick = i;
      renderLeft(); renderRight();
    }),
    on(view, 'click', '[data-lb]', (e, c) => openStructure(+c.dataset.lb)),
    on(view, 'click', '[data-close-tunnel]', async (e, b) => {
      await post('/api/creator/gelato/close-tunnel', { orderId: b.dataset.closeTunnel }).catch(() => {});
      status = await api('/api/creator/status'); renderTunnels();
    }),
  ];
  view.addEventListener('input', (e) => {
    const s = cur();
    const i = e.target.dataset?.book ? +e.target.dataset.book : s.pick;
    if (e.target.classList?.contains('path-input')) {
      const wasReprint = !!s.reprint;
      Object.assign(s.books[i], { folder: e.target.value.trim().replace(/^"|"$/g, ''), label: null, validation: null });
      s.pick = i; s.reprint = null;
      if (wasReprint) renderLeft(); // the reprint line and the button's words go with the archived folder
      validateSoon(i);
    }
    if (e.target.id === `cr-title-${i}`) { s.books[i].title = e.target.value; const al = $('#cr-alert'); if (al && !s.error) al.innerHTML = ''; }
    if (e.target.dataset.addr) {
      s.address[e.target.dataset.addr] = e.target.value;
      const label = $('#cr-create-label'); // Printify: the button says whether an order will be made too
      if (label) label.textContent = createLabel();
    }
  });
  view.addEventListener('change', (e) => {
    if (e.target.dataset.addr === 'country') cur().address.country = e.target.value;
  });
  view.addEventListener('keydown', (e) => { if (e.target.id?.startsWith('cr-title-') && e.key === 'Enter') { e.preventDefault(); create(); } });

  renderAll();
  if (handed) cur().books.forEach((b, i) => { if (b.folder) validate(i); });
  // Working on a new order, the page is kept when left and brought back as it was — while the order is new.
  return {
    get receiptId() { return st.receiptId; },
    navFor: () => (st.receiptId ? '#/orders' : null),
    keep: () => !!st.receiptId && !finished,
    belongsToObject: () => !!st.receiptId,   // an order's own work stays kept for that order; «Інструменти» opens a clean Creator beside it
    canStartOver: () => !st.printify.running && !st.gelato.running,
    async revive() {
      const o = await api(`/api/orders/${st.receiptId}`);
      return o.stage === 'new';
    },
    // A kept page out of sight does not tick; back in sight, the countdown goes on from the same moment (_until).
    hidden() { stopCountdown(); },
    shown() { if (st.gelato.result) startCountdown(); },
    unmount() { gone = true; validateSoon.cancel(); offs.forEach((f) => f()); stopCountdown(); },
  };
}

