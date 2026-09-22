// Order Creator: Printify unpublished photo books and Gelato draft orders from Canva PNG folders.
import {
  api, html, ic, ib, raw, setHtml, on, media, modal, toast, runJob, segHtml, syncSeg, setSeg, bytes, dateTime,
  relTime, copyText, openExternal, debounce, keepFocus, fadeImages, slide, confirmBox,
} from '../lib.js';
import { openLightbox } from '../lightbox.js';
import {
  COUNTRIES, STAGES, STAGE_EMPTY, addressFromEtsy, syncOrders, runningSync, watchSync, spreadsOf, folderViewerItems, receiveDrop, dropLabel,
  wireFolderDrop, matchesOrder, variationsOf, providerName, pagesText, restorable,
} from '../order-bits.js';
import { take } from '../handoff.js';
import { markSent, finish } from '../keep.js';

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
  const newBook = (extra = {}) => ({
    folder: '', label: null, title: '', validation: null, validating: 0, seq: 0,
    stamp: 0,            // grows with every replaced page, so its pictures are fetched anew
    replaced: new Set(), // pages a new file was put over — they can be put back
    format: status.gelato.defaultFormat || status.gelato.formats[0]?.key, ...extra,
  });
  const st = {
    mode: 'printify',
    printify: { books: [newBook()], pick: 0, running: false, result: null, error: null, address: { country: 'US' }, reprint: null },
    gelato: { books: [newBook()], pick: 0, running: false, result: null, error: null, address: { country: 'US' }, reprint: null },
  };
  const handed = take('creator');
  // The new order this page works on (from its card, or picked below); a reprint from the archive is not one.
  st.receiptId = handed?.receiptId && !handed.reprint ? String(handed.receiptId) : '';
  if (handed) {
    st.mode = handed.mode;
    const list = handed.books?.length ? handed.books : [handed];
    Object.assign(st[handed.mode], {
      books: list.map((h) => newBook({ folder: h.folder, label: h.label, title: h.title, ...(h.format ? { format: h.format } : {}) })),
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
  let tunnelTimer = null;
  const cur = () => st[st.mode];
  const bk = (i = cur().pick) => cur().books[i] || cur().books[0];   // the book being shown / edited
  const many = () => cur().books.length > 1;
  const bookName = (i) => cur().books[i].title.split(' - ').slice(1).join(' - ').trim() || `Книга ${i + 1}`;

  // Pages: Printify takes exactly its template's 24; Gelato as many as the folder holds (28 or 30), and
  // its catalog says which of those each format is printed with (asked once, when Gelato is shown).
  const pageTotal = (i = cur().pick) => (st.mode === 'printify' ? status.printify.pageCount : bk(i).validation?.pageCount || 0);
  let pageCounts = null;
  let countsAsked = false;
  function loadPageCounts() {
    if (countsAsked || !status.gelato.keyConfigured) return;
    countsAsked = true;
    api('/api/creator/gelato/page-counts').then((r) => {
      pageCounts = r.formats || null;
      if (st.mode === 'gelato') renderLeft();
    }).catch(() => {});
  }
  /** Why Gelato would not print the chosen folder in this format; '' when fine or not known. */
  function formatProblem(key = bk().format, i = cur().pick) {
    const valid = pageCounts?.[key];
    const n = bk(i).validation?.pageCount;
    if (!valid?.length || !n || valid.includes(n)) return '';
    const label = status.gelato.formats.find((f) => f.key === key)?.label || key;
    return `Gelato не друкує ${label} на ${n} сторінках (можна від ${valid[0]}).`;
  }

  setHtml(view, html`<div class="creator" id="cr">
    <div class="page-head">
      <h1 class="page-title" id="cr-title-h">Order Creator</h1>
      <div class="page-actions" id="cr-switch"></div>
    </div>
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
    // The cross closes the work on this order: the page and its card forget it and the queue opens.
    setHtml($('#cr-switch'), html`<div class="tools cr-tools">${st.receiptId && cur().result
      ? ib('x', 'Завершити роботу над замовленням', 'data-act="finish"') : ''}${ib('sendLog', 'Журнал відправок', 'data-act="open-sendlog"')}</div><div class="mode-switch">${segHtml([
      { value: 'printify', icon: 'printify', tip: 'Printify — неопублікована книга' },
      { value: 'gelato', icon: 'gelato', tip: 'Gelato — чернетка замовлення' }], st.mode, { name: 'mode' })}</div>`);
    requestAnimationFrame(() => syncSeg($('#cr-switch .seg')));
  }

  // Only the service name in the header; a line appears under it only when something is missing.
  function renderStatus() {
    const p = status.printify, g = status.gelato;
    const pr = st.mode === 'printify';
    root.classList.toggle('mode-gelato', !pr);
    $('#cr-title-h').textContent = pr ? 'Printify' : 'Gelato';
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
    setHtml($('#cr-tunnels'), html`<div class="notice notice-warn" style="margin-bottom:16px">${ic('globe')}<div class="grow">
      Активне тимчасове посилання для файлів чернетки Gelato (${active.map((t) => `${t.key.slice(0, 8)}… — ${Math.ceil(t.secondsLeft / 60)} хв`).join(', ')}).
      Відкрийте чернетку в Gelato Dashboard, поки посилання працює.</div>
      ${active.map((t) => ib('unlink', 'Закрити посилання', `data-close-tunnel="${t.key}"`, { cls: 'sm' }))}</div>`);
  }

  // ---------------------------------------------------------------- left column
  /** One book's folder: the path, what the check found, and (with several books) its own name. */
  function folderBlock(i) {
    const s = cur();
    const b = cur().books[i];
    const v = b.validation;
    let badge;
    if (b.validating) badge = html`<span class="v-badge run"><span class="spinner" style="width:12px;height:12px;border-width:2px"></span><span class="num">${Math.round(b.validating)}%</span></span>`;
    else if (!v) badge = '';
    else if (v.ok) badge = html`<span class="v-badge ok" data-tip="Усі PNG повністю прочитано й перевірено">${ic('check')}<span class="num">${v.found}/${v.expected}</span></span>`;
    else badge = html`<span class="v-badge bad">${ic('x')}Є проблеми</span>`;
    // A dragged folder is shown by its own name (b.label); b.folder is where the program copied it.
    return html`<div class="cr-book ${many() && i === cur().pick ? 'is-shown' : ''}" data-folder-drop data-book="${i}">
      ${many() ? html`<div class="row cr-book-head"><button class="cr-book-name" data-act="show-book" data-book="${i}" data-tip="Показати структуру цієї книги">${ic('book', 'icon-s')}Книга ${i + 1}</button>
        <span class="spacer"></span>${badge}${cur().books.length > 2 || !cur().books[i].folder ? ib('x', 'Прибрати книгу', `data-act="drop-book" data-book="${i}"`, { cls: 'sm' }) : ''}</div>` : ''}
      <div class="input-group">
        <input class="input path-input" id="cr-folder-${i}" data-book="${i}" placeholder="Папку ще не вибрано" value="${b.label || b.folder}" title="${b.label ? b.folder : ''}" spellcheck="false" autocomplete="off" aria-label="Шлях до папки">
        ${ib('folderPick', 'Обрати папку', `data-act="browse" data-book="${i}"`)}
      </div>
      ${!many() ? html`<div class="row" style="display:none">${badge}</div>` : ''}
      ${s.reprint && i === 0 ? html`<div class="row faint cr-reprint">${ic('orderArchive', 'icon-s')}<span>${st.mode === 'printify'
        ? 'Передрук з архіву: нове замовлення на книгу, яка вже є в Printify'
        : 'Передрук з архіву: нова чернетка з тих самих файлів'}</span></div>` : ''}
      ${v && !b.validating ? html`
        ${v.errors.length ? html`<div class="notice notice-error">${ic('alertCircle')}<div><b>Перевірка не пройдена</b><ul>${v.errors.slice(0, 12).map((e) => html`<li>${e}</li>`)}</ul>${v.errors.length > 12 ? html`<div>…та ще ${v.errors.length - 12}</div>` : ''}</div></div>` : ''}
        ${v.warnings.length ? html`<div class="notice notice-warn">${ic('alert')}<div>${v.warnings.map((w) => html`<div>${w}</div>`)}</div></div>` : ''}
        <div class="row">${v.ok ? html`<span class="faint mono" style="font-size:12px">${bytes(v.totalBytes)}</span>` : ''}<span class="spacer"></span>
          ${v.ok ? ib('folderOpen', 'Відкрити папку', `data-act="open-folder" data-book="${i}"`, { cls: 'sm' }) : ''}
          ${ib('scan', 'Перевірити файли знову', `data-act="revalidate" data-book="${i}"`, { cls: 'sm' })}</div>` : ''}
    </div>`;
  }

  function folderCard(num) {
    const one = !many();
    const b = bk();
    let badge = '';
    if (one && b.validating) badge = html`<span class="v-badge run"><span class="spinner" style="width:12px;height:12px;border-width:2px"></span><span class="num">${Math.round(b.validating)}%</span></span>`;
    else if (one && b.validation) badge = b.validation.ok
      ? html`<span class="v-badge ok" data-tip="Усі PNG повністю прочитано й перевірено">${ic('check')}<span class="num">${b.validation.found}/${b.validation.expected}</span></span>`
      : html`<span class="v-badge bad">${ic('x')}Є проблеми</span>`;
    return html`<section class="card card-pad stack">
      <div class="row"><span class="step-no">${num}</span><h3 class="card-title grow">${one ? 'Папка з файлами' : `Папки з файлами · ${cur().books.length} книги`}</h3>${badge}</div>
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
    const inp = (key, ph, span = '') => html`<input class="input ${span}" id="addr-${key}" data-addr="${key}" placeholder="${ph}" value="${a[key] || ''}" autocomplete="off">`;
    return html`<section class="card card-pad stack">
      <div class="row"><span class="step-no">${num}</span><h3 class="card-title grow">Адреса отримувача</h3>
        ${ib('eraser', 'Очистити адресу', 'data-act="clear-address"', { cls: 'sm' })}</div>
      <div class="addr-grid">
        ${inp('firstName', "Ім'я *")}${inp('lastName', 'Прізвище *')}
        ${inp('addressLine1', 'Адреса, рядок 1 *', 'span2')}${inp('addressLine2', 'Адреса, рядок 2', 'span2')}
        ${inp('city', 'Місто *')}${inp('state', 'Штат / провінція (US, CA, AU)')}
        ${inp('postCode', 'Індекс *')}
        <select class="select" data-addr="country">${COUNTRIES.map(([c, n]) => html`<option value="${c}" ${(a.country || 'US') === c ? 'selected' : ''}>${c} — ${n}</option>`)}</select>
        ${inp('phone', st.mode === 'gelato' ? 'Телефон (порожньо — підставиться вигаданий)' : 'Телефон (необов’язково)', 'span2')}
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
        <div class="row" style="margin-bottom:6px;font-size:12.5px"><span id="cr-step" style="font-weight:600" class="grow">Підготовка…</span><span class="num" id="cr-pct" style="color:var(--accent-ink);font-weight:600">0%</span></div>
        <div class="progress"><i id="cr-bar"></i></div>
        <div class="faint mono truncate" id="cr-detail" style="font-size:11.5px;margin-top:6px"></div>
      </div>
      <div id="cr-result">${resultHtml()}</div>
    </section>`;
  }

  // Every send is written to data/logs/sends — the icon opens this one's record (or the folder).
  const sendLogButton = (r) => ib('sendLog', 'Журнал відправки', `data-act="open-sendlog" data-file="${r?.sendLog || ''}"`, { cls: 'sm' });

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
      <div class="notice notice-warn" style="margin-top:12px" id="cr-tunnel">${ic('clock')}<div class="grow">
        <b>Важливо:</b> Gelato завантажує файли лише коли ви відкриєте чернетку в Dashboard. Зробіть це зараз, поки тимчасове посилання працює — лишилось <b class="mono" id="cr-countdown">--:--</b>.
        <div class="row" style="margin-top:8px"><button class="btn btn-sm btn-primary" data-act="open-gelato">${ic('external', 'icon-s')}Gelato Dashboard</button>
          ${ib('copy', 'Копіювати Order ID', 'data-act="copy-order"', { cls: 'sm' })}
          ${ib('unlink', 'Файли забрано — закрити посилання', 'data-act="close-tunnel"', { cls: 'sm' })}
          ${sendLogButton(r)}</div></div></div>
    </div>`;
  }

  function renderLeft() {
    const blocks = st.mode === 'printify'
      ? [folderCard(1), titleCard(2), addressCard(3), createCard(4)]
      : [formatCard(1), folderCard(2), titleCard(3), addressCard(4), createCard(5)];
    keepFocus(() => setHtml($('#cr-left'), blocks));
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
  const thumb = (name, w = 420) => media('/media/folder', { path: bk().folder, file: name, w, ...(bk().stamp ? { v: bk().stamp } : {}) });

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
    setHtml($('#cr-right'), html`<section class="card card-pad stack-l">
      <div class="row" style="align-items:baseline">
        <h2 class="card-title grow" style="font-size:17px">Структура <span class="faint" style="font-weight:500">· ${many() ? `${bookName(cur().pick)} · ` : ''}${fmtLabel}</span></h2>
        <span class="v-badge ${count === expectedCount && v?.ok ? 'ok' : ''}" data-tip="Зображень у папці"><span class="num">${count}/${expectedCount}</span></span>
      </div>
      <div class="stack-s">
        <div class="row"><span class="eyebrow grow">Обкладинка</span><span class="num faint" style="font-size:12px">${coverRow?.width ? `${coverRow.width}×${coverRow.height}` : ''}</span></div>
        <div class="structure-cover" data-lb="0" style="aspect-ratio:${ratio}">
          ${has('Cover.png') ? html`<img data-fade decoding="async" src="${thumb(coverRow.file, 1400)}" alt="Обкладинка">` : html`<div class="cover-ph"><div>Задня</div><div>Лицьова</div></div>`}
          <div class="gutter"></div>
          ${coverRow && !coverRow.ok ? html`<div class="page-tag" style="background:var(--red);left:auto;right:8px">${coverRow.error}</div>` : ''}
          <i class="crops"></i>
        </div>
      </div>
      <div class="stack-s">
        <div class="row"><span class="eyebrow grow">Розвороти</span><span class="faint" style="font-size:12px">${known
          ? html`<span class="num">${spreads.length}</span> · <span class="num">${total}</span> стор.`
          : html`<span class="num">${pagesText(status.gelato.pageCounts)}</span> стор.`}</span></div>
        <div class="spread-grid">${spreads.map((sp, i) => {
          const lp = i === 0 ? 1 : sp.left + 1;
          const rp = i === 0 ? 2 : lp + 1;
          const lf = sp.left ? `${sp.left}.png` : null, rf = sp.right ? `${sp.right}.png` : null;
          const mark = (f) => { if (!f) return ''; const x = fileState(f); return html`<span class="${x === 'ok' ? 'file-ok' : x ? 'file-bad' : ''}">${f}</span>`; };
          return html`<div class="spread-card enter" data-lb="${i + 1}" style="animation-delay:${Math.min(i * 25, 300)}ms">
            <div class="spread-view">${half(sp.left, 'left', 'Форзац')}${half(sp.right, 'right', 'Нахзац')}<div class="gutter-s"></div><i class="crops"></i></div>
            <div class="spread-card-head"><span class="spread-no">${lp}–${rp}</span><span class="spacer"></span><span class="spread-files">${mark(lf)}${mark(rf)}</span></div></div>`;
        })}</div>
      </div>
    </section>`);
    fadeImages(view.querySelector('#cr-right'));
  }

  // The viewer of one book's structure. A page can be replaced right there by a file from the computer
  // (the owner fixed it in Canva and downloaded that page again) — and put back while the card is open.
  const pageNo = (file) => (/^cover/i.test(file) ? 0 : parseInt(file, 10));
  const pageWord = (file) => (pageNo(file) ? `сторінку ${pageNo(file)}` : 'обкладинку');

  function structureItems(b, i, again) {
    const items = folderViewerItems(b.folder, pageTotal(i), b.label || b.folder, b.stamp);
    for (const it of items) {
      it.actions = [];
      for (const file of it.files || []) {
        const num = pageNo(file) ? String(pageNo(file)) : '';
        it.actions.push({ icon: 'swap', label: num, tip: `Замінити ${pageWord(file)} — обрати файл на комп'ютері`,
          run: (lb) => replacePage(b, i, file, lb, again) });
        if (b.replaced.has(file.toLowerCase())) {
          it.actions.push({ icon: 'restore', label: num, on: true, tip: `Повернути попередню ${pageWord(file)}`,
            run: (lb) => restorePage(b, i, file, lb, again) });
        }
      }
    }
    return items;
  }

  function openStructure(index) {
    const b = bk();
    const i = cur().pick;
    if (!b.validation || !b.folder) { toast('Спершу оберіть папку з ілюстраціями', 'info'); return; }
    const items = [];
    const again = (lb) => { items.splice(0, items.length, ...structureItems(b, i, again)); lb.refresh(); };
    items.push(...structureItems(b, i, again));
    openLightbox(items, index);
  }

  async function replacePage(b, i, file, lb, again) {
    let path;
    try {
      path = (await api('/api/creator/pick-file', { method: 'POST',
        body: { title: `Оберіть ${pageWord(file)} (${file})`, initial: b.folder } })).path;
    } catch (err) { toast(err.message, 'error'); return; }
    if (!path) return;
    if (cur().result && !(await confirmBox({ title: 'Чернетку вже створено',
      text: 'У друкарні лежить стара сторінка. Замінити її тут і створити чернетку ще раз?',
      confirm: 'Замінити', cancel: 'Не чіпати' }))) return;
    let res;
    try {
      res = await api('/api/creator/replace-page', { method: 'POST', body: { folder: b.folder, file, path } });
    } catch (err) { toast(err.message, 'error'); return; }
    setRestorable(b, file, res.canRestore);
    pageChanged(b, i, lb, again, `Замінено ${pageWord(file)}`);
  }

  async function restorePage(b, i, file, lb, again) {
    let res;
    try {
      res = await api('/api/creator/restore-page', { method: 'POST', body: { folder: b.folder, file } });
    } catch (err) { toast(err.message, 'error'); return; }
    setRestorable(b, file, res.canRestore);   // an older version may still be there
    pageChanged(b, i, lb, again, `Повернено ${pageWord(file)}`);
  }

  /** The server says whether this page still has a previous version; the page only repeats it. */
  function setRestorable(b, file, can) {
    if (can) b.replaced.add(file.toLowerCase());
    else b.replaced.delete(file.toLowerCase());
  }

  function pageChanged(b, i, lb, again, message) {
    b.stamp++;
    toast(message, 'success');
    again(lb);
    validate(i);   // the folder is checked again: a page of the wrong size is caught here
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
      const res = await runJob(api('/api/creator/validate', { method: 'POST', body: { mode, folder: b.folder } }), (j) => {
        if (my !== b.seq || st.mode !== mode) return;
        b.validating = Math.max(1, j.percent);
        const badge = view.querySelector(`[data-book="${i}"] .v-badge.run, #cr-left .v-badge.run`);
        if (badge) badge.lastChild.textContent = `Перевірка… ${Math.round(b.validating)}%`;
      }, 300);
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
      const miss = Object.entries(ADDRESS_NEEDED).filter(([k]) => !(a[k] || '').trim()).map(([, v]) => v);
      if (miss.length) problems.push(`Заповніть адресу: ${miss.join(', ')}.`);
      if (['US', 'CA', 'AU'].includes((a.country || '').toUpperCase()) && !(a.state || '').trim()) problems.push('Для цієї країни потрібен штат/провінція.');
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
    const books = s.books.map((b) => ({ folder: b.folder, title: b.title, format: b.format }));
    const body = mode === 'gelato'
      ? { books, address: s.address, ...(reprint ? { reprintOf: reprint.archiveId } : {}) }
      : reprint ? { archiveId: reprint.archiveId, title: bk().title, address: s.address }
        : { books, address: order ? s.address : null };
    try {
      s.result = await runJob(api(url, { method: 'POST', body }), (j) => {
        if (st.mode !== mode) return;
        const bar = $('#cr-bar');
        if (!bar) return;
        $('#cr-step').textContent = j.step;
        $('#cr-pct').textContent = `${Math.round(j.percent)}%`;
        $('#cr-detail').textContent = j.detail || '';
        bar.style.width = `${j.percent}%`;
      });
      if (st.receiptId && !reprint) markSent(st.receiptId, { provider: mode, what: sentText(mode, s.result) });
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
    const books = n > 1 ? ` · ${n} книги` : '';
    if (mode === 'gelato') return `Чернетку замовлення створено в Gelato${books}`;
    if (r?.orderError) return `${n > 1 ? 'Книги' : 'Книгу'} створено в Printify, замовлення — ні (подробиці в Order Creator)`;
    return r?.order ? `Чернетку замовлення створено в Printify (On hold)${books}`
      : `${n > 1 ? 'Книги' : 'Книгу'} створено в Printify, без замовлення`;
  }

  // Once: an order from here is safe only while the Printify store approves orders by hand — with
  // automatic approval Printify itself would send it to production (and charge) at the set time.
  function confirmManualApproval() {
    return new Promise((resolve) => {
      let ok = false;
      const m = modal({
        title: 'Ручне затвердження замовлень у Printify',
        body: html`<div class="stack">
          <div class="notice notice-warn">${ic('alert')}<div>Замовлення з Book Studio чекає в Printify «On hold» і не списує гроші, доки ви не натиснете <b>Submit order</b>. Але якщо в магазині стоїть <b>автоматичне</b> затвердження, Printify сам відправить його у виробництво в заданий час і спише оплату.</div></div>
          <div class="faint" style="font-size:12.5px">Printify → Store settings → Order settings → Order approval: <b>Manual</b></div>
          <label class="check card-soft" style="padding:12px"><input type="checkbox" id="ma-ok"><span style="font-weight:600">У моєму магазині стоїть ручне затвердження (Manual)</span></label>
        </div>`,
        foot: html`<button class="btn btn-ghost" data-c>Скасувати</button><button class="btn btn-primary" data-go disabled>Продовжити</button>`,
        onClose: () => resolve(ok),
      });
      const go = m.foot.querySelector('[data-go]');
      m.el.querySelector('#ma-ok').addEventListener('change', (e) => { go.disabled = !e.target.checked; });
      m.foot.querySelector('[data-c]').onclick = () => m.close();
      go.onclick = async () => {
        go.disabled = true;
        try {
          await api('/api/printify/manual-approval', { method: 'POST', body: {} });
          status.printify.manualApproval = true;
          ok = true;
          m.close();
        } catch (err) { toast(err.message, 'error'); go.disabled = false; }
      };
    });
  }

  function startCountdown() {
    clearInterval(tunnelTimer);
    const r = st.gelato.result;
    if (!r) return;
    const until = r._until || (r._until = Date.now() + r.keepAliveSeconds * 1000);
    const tick = () => {
      const left = Math.max(0, Math.round((until - Date.now()) / 1000));
      const node = $('#cr-countdown');
      if (node) node.textContent = `${String(Math.floor(left / 60)).padStart(2, '0')}:${String(left % 60).padStart(2, '0')}`;
      if (!left) { clearInterval(tunnelTimer); const t = $('#cr-tunnel'); if (t) setHtml(t, html`${ic('info')}<div>Тимчасове посилання закрито. Якщо Gelato ще не завантажив файли — створіть чернетку повторно.</div>`); }
    };
    tick();
    tunnelTimer = setInterval(tick, 1000);
  }

  // ---------------------------------------------------------------- Etsy order picker
  async function fromEtsy() {
    let data;
    try { data = await api('/api/creator/etsy-orders'); } catch (err) { toast(err.message, 'error'); return; }
    let term = '', stage = 'new', syncing = false, shown = [], unfreeze = 0;
    const syncedText = () => (data.syncedAt ? `Оновлено ${relTime(data.syncedAt)}` : 'Ще не завантажено');
    const m = modal({
      title: 'Замовлення Etsy',
      sub: syncedText(),
      size: 'l',
      body: html`<div class="stack"><div class="row eo-head"><div class="input-group grow">${ic('search')}<input class="input" id="eo-q" placeholder="Ім'я покупця або номер чека" aria-label="Пошук замовлення" autofocus></div>
          ${segHtml(STAGES.map((s) => ({ ...s, count: 0 })), stage, { name: 'stage' })}
          <div class="tools">${ib('sync', 'Оновити замовлення з Etsy', 'data-x="sync"')}</div></div>
        <div class="cand-list" id="eo-list" style="max-height:440px"></div></div>`,
      foot: null,
    });
    const list = m.el.querySelector('#eo-list');
    const seg = m.el.querySelector('[data-seg="stage"]');
    const syncBtn = m.el.querySelector('[data-x="sync"]');
    const setSub = (text) => { const node = m.el.querySelector('.modal-sub'); if (node) node.textContent = text; };
    const matches = matchesOrder;
    const variations = variationsOf;
    // The buyer's personalization stays folded; the chevron unfolds it as a label/value list,
    // one group per book when the order holds several.
    const unfolded = new Set();
    const details = (o) => html`<div class="acc ${unfolded.has(o.receiptId) ? 'open' : ''}" data-vars="${o.receiptId}"><div>
        ${o.items.map((it) => html`${o.items.length > 1 ? html`<div class="cand-item">${it.quantity > 1 ? `${it.quantity} × ` : ''}${it.title}</div>` : ''}
          <dl class="cand-vars">${(it.variations || []).map((v) => html`<dt>${v.name}</dt><dd>${v.value}</dd>`)}</dl>`)}
      </div></div>`;
    const rowHtml = (o, entering) => html`<div class="cand ${entering ? 'enter' : ''}" data-rid="${o.receiptId}" style="align-items:flex-start">
        <div class="grow" style="min-width:0">
          <div class="row" style="gap:8px"><b>${o.name}</b><span class="chip chip-mono">#${o.receiptId}</span>
            ${o.books > 1 ? html`<span class="chip" data-tip="Книг у замовленні">${ic('book', 'icon-s')}${o.books}</span>` : ''}
            ${o.provider ? html`<span class="chip svc-${o.provider}">${ic(o.provider, 'icon-s')}${providerName(o.provider)}</span>` : ''}</div>
          <div class="faint" style="font-size:12px;margin-top:3px"><span data-tip="${dateTime(o.createdAt)}">${relTime(o.createdAt)}</span> · ${o.coverLabel} · ${[o.address.city, o.address.country_iso].filter(Boolean).join(', ')}</div>
          ${variations(o).length ? details(o) : ''}
        </div>
        ${o.childName ? html`<span class="chip chip-accent">${o.childName}</span>` : ''}
        ${variations(o).length ? ib('chevDown', 'Персоналізація', `data-vars-toggle="${o.receiptId}" aria-expanded="${unfolded.has(o.receiptId)}"`, { cls: `sm details-toggle ${unfolded.has(o.receiptId) ? 'on' : ''}` }) : ''}</div>`;

    const render = ({ fresh = false } = {}) => {
      const t = term.trim().toLowerCase();
      seg.querySelectorAll('button[data-value]').forEach((b) => {
        b.querySelector('.seg-count').textContent = data.orders.filter((o) => o.stage === b.dataset.value && matches(o, t)).length;
      });
      syncSeg(seg);
      const rows = data.orders.filter((o) => o.stage === stage && matches(o, t));
      const before = shown;
      shown = rows.map((o) => o.receiptId);
      if (!rows.length) {
        if (!data.orders.length && syncing) setHtml(list, html`<div class="empty" style="padding:30px"><div class="empty-icon"><span class="spinner"></span></div><p>Завантаження замовлень з Etsy…</p></div>`);
        else if (t) setHtml(list, html`<div class="empty" style="padding:30px">Нічого не знайдено</div>`);
        else {
          const [icon, title, text] = STAGE_EMPTY[stage];
          setHtml(list, html`<div class="empty" style="padding:30px"><div class="empty-icon">${ic(icon)}</div><h3>${title}</h3>${text ? html`<p>${text}</p>` : ''}</div>`);
        }
        return;
      }
      setHtml(list, rows.map((o) => rowHtml(o, fresh && !before.includes(o.receiptId))));
      if (fresh && before.join() !== shown.join()) {
        // The rows just moved: ignore clicks for a moment so a click aimed at one buyer never lands on another.
        list.inert = true;
        clearTimeout(unfreeze);
        unfreeze = setTimeout(() => { list.inert = false; }, 450);
      }
    };

    // The refresh button pulls the latest orders; opening the picker only follows a sync already
    // running (the program's start-up one) and never starts one itself.
    async function refresh(pull = () => syncOrders(setSub)) {
      if (syncing) return;
      syncing = true;
      syncBtn.disabled = true; syncBtn.firstElementChild?.classList.add('spin');
      setSub('Оновлення…');
      if (!data.orders.length) render();
      try {
        await pull();
        const next = await api('/api/creator/etsy-orders');
        if (!m.el.isConnected) return;
        data = next;
        setSub(syncedText());
        render({ fresh: true });
      } catch (err) {
        if (m.el.isConnected) setSub(`${syncedText()} · не вдалося оновити: ${err.message}`);
      } finally {
        syncing = false;
        syncBtn.disabled = false; syncBtn.firstElementChild?.classList.remove('spin');
      }
    }
    syncBtn.addEventListener('click', () => refresh());
    seg.addEventListener('click', (e) => {
      const b = e.target.closest('button[data-value]');
      if (!b || b.dataset.value === stage) return;
      stage = b.dataset.value;
      setSeg(seg, stage);
      render();
    });
    render();
    runningSync().then((jobId) => { if (jobId && m.el.isConnected) refresh(() => watchSync(jobId, setSub)); });
    requestAnimationFrame(() => syncSeg(seg));
    m.el.querySelector('#eo-q').addEventListener('input', (e) => { term = e.target.value; render(); });
    list.addEventListener('click', (e) => {
      const fold = e.target.closest('[data-vars-toggle]');
      if (fold) {
        const id = fold.dataset.varsToggle;
        const open = !unfolded.has(id);
        if (open) unfolded.add(id); else unfolded.delete(id);
        fold.classList.toggle('on', open);
        fold.setAttribute('aria-expanded', String(open));
        const body = list.querySelector(`[data-vars="${id}"]`);
        if (body) slide(body, open);
        return;
      }
      if (e.target.closest('[data-vars]')) return; // reading or copying the personalization is not a choice
      const row = e.target.closest('[data-rid]');
      if (!row) return;
      const o = data.orders.find((x) => x.receiptId === row.dataset.rid);
      m.close();
      const s = cur();
      if (o.stage === 'new') st.receiptId = String(o.receiptId);
      // An order of several books gives a name to each of them (a folder is still chosen for each by hand).
      const names = (o.items || []).map((it) => it.childName || o.childName || '');
      while (s.books.length < Math.max(1, names.length)) s.books.push(newBook({ format: bk(0).format }));
      s.books.forEach((b, i) => { b.title = `${o.receiptId} - ${names[i] || names[0] || ''}`.trim().replace(/-$/, '- '); });
      s.address = { ...s.address, ...addressFromEtsy(o) };
      renderLeft();
      const ti = $('#cr-title-0');
      if (ti) { ti.focus(); ti.setSelectionRange(ti.value.length, ti.value.length); }
      toast(o.childName ? 'Заповнено із замовлення — перевірте назву' : 'Допишіть ім’я дитини в назві', 'info', 3500);
    });
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
        const num = view.querySelector(`[data-book="${i}"] .v-badge.run .num, #cr-left .v-badge.run .num`);
        if (num) num.textContent = `${Math.round(pct)}%`;
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

  // ---------------------------------------------------------------- events
  const offs = [
    on(view, 'click', '[data-seg="mode"] button', (e, b) => {
      if (st.mode === b.dataset.value) return;
      cur().books.forEach((x, i) => { const t = $(`#cr-title-${i}`); if (t) x.title = t.value; });
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
          const { path } = await api('/api/creator/pick-folder', { method: 'POST', body: { title: `Оберіть папку з Cover.png та ${(st.mode === 'printify' ? [status.printify.pageCount] : status.gelato.pageCounts).map((n) => `1–${n}.png`).join(' або ')}`, initial: b.folder } });
          if (path) { Object.assign(b, { folder: path, label: null, validation: null }); s.pick = i; s.reprint = null; renderLeft(); renderRight(); validate(i); }
        } catch (err) { toast(err.message, 'error'); }
      } else if (a === 'finish') { finished = true; finish(st.receiptId); location.hash = '#/orders'; }
      else if (a === 'revalidate') validate(i);
      else if (a === 'show-book') { s.pick = i; renderLeft(); renderRight(); }
      else if (a === 'add-book') { s.books.push(newBook({ format: bk(0).format, title: bk(0).title.split(' - ')[0] ? `${bk(0).title.split(' - ')[0]} - ` : '' })); s.pick = s.books.length - 1; renderLeft(); renderRight(); }
      else if (a === 'drop-book' && s.books.length > 1) { s.books.splice(i, 1); s.pick = Math.min(s.pick, s.books.length - 1); renderLeft(); renderRight(); }
      else if (a === 'open-folder') api('/api/creator/open-folder', { method: 'POST', body: { path: b.folder } }).catch((er) => toast(er.message, 'error'));
      else if (a === 'from-etsy') fromEtsy();
      else if (a === 'clear-address') { s.address = { country: 'US' }; renderLeft(); $('#addr-firstName')?.focus(); }
      else if (a === 'open-orders') openExternal('https://printify.com/app/orders');
      else if (a === 'copy-printify-order') copyText(st.printify.result?.order?.id || '', 'Order ID скопійовано');
      else if (a === 'open-product') openExternal(st.printify.result?.url);
      else if (a === 'copy-id') copyText(st.printify.result?.productId || '', 'Product ID скопійовано');
      else if (a === 'copy-order') copyText(st.gelato.result?.orderId || '', 'Order ID скопійовано');
      else if (a === 'open-gelato') openExternal('https://dashboard.gelato.com/');
      else if (a === 'open-sendlog') api('/api/sends/open', { method: 'POST', body: { file: t.dataset.file || '' } }).catch((er) => toast(er.message, 'error'));
      else if (a === 'close-tunnel') {
        try { await api('/api/creator/gelato/close-tunnel', { method: 'POST', body: { orderId: st.gelato.result.orderId } }); } catch {}
        clearInterval(tunnelTimer);
        const box = $('#cr-tunnel');
        if (box) setHtml(box, html`${ic('check')}<div>Тимчасове посилання закрито.</div>`);
      }
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
      await api('/api/creator/gelato/close-tunnel', { method: 'POST', body: { orderId: b.dataset.closeTunnel } }).catch(() => {});
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
    keep: () => !!st.receiptId && !finished,
    async revive() {
      if (!st.receiptId) return true;
      const o = await api(`/api/orders/${st.receiptId}`);
      return o.stage === 'new';
    },
    unmount() { offs.forEach((f) => f()); clearInterval(tunnelTimer); },
  };
}

