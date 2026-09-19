// Order pipeline: the queue of Etsy orders and one order's card — its book and Canva template, all
// the buyer wrote, the Canva export dropped in and put in page order, a proof of the first spread and
// every page with the text check by the local model, then the hand-over to the Order Creator. Nothing is
// saved to disk; while an order is new, its card is kept in memory when the owner steps to another tab and
// comes back as it was left (keep.js).
import {
  api, html, ic, ib, raw, esc, setHtml, on, media, toast, segHtml, syncSeg, setSeg, relTime, dateTime, copyText,
  openExternal, runJob, fadeImages, plural, confirmBox,
} from '../lib.js';
import { openLightbox } from '../lightbox.js';
import {
  STAGES, STAGE_EMPTY, STAGE_LABEL, matchesOrder, providerName, planText, pagesText, countryName, addressFromEtsy, syncOrders, runningSync, watchSync, spreadsOf,
  folderViewerItems, receiveDrop, dropLabel, wireFolderDrop, smoothWheel, trackChips, statusChip, receiptCopy, copyChip,
  isCustomText, isNameField, isFormatField,
} from '../order-bits.js';
import { give } from '../handoff.js';
import { settle, sentOf, keptOrder } from '../keep.js';

// Strip thumbnails: the server prepares this size ahead (creator.STRIP_PREVIEW), so scrolling never waits.
const STRIP_THUMB = 360;

// Text check (textcheck.py): how its findings are counted and why a check was only the light one.
const LEVEL_WORDS = { error: ['помилка', 'помилки', 'помилок'], warn: ['питання', 'питання', 'питань'] };
const LIGHT_TIP = {
  noBook: 'Легка перевірка: книги немає в бібліотеці',
  noTexts: 'Легка перевірка: у паспорті книги немає текстів',
  noName: 'Легка перевірка: ім\'я дитини не знайдено в персоналізації',
};
// «Ollivia» замість «Olivia» — the quoted words stand out.
const quoteBold = (text) => raw(String(text).split(/(«[^»]*»)/).map((part) => (part.startsWith('«') ? `<b>${esc(part)}</b>` : esc(part))).join(''));
// Viewer position of a page: the cover, then spreads [форзац|1], [2|3], [4|5] …
const viewerIndex = (page) => (page === 0 ? 0 : 1 + (page === 1 ? 0 : Math.floor(page / 2)));

const bookImage = (b, w) => media(`/media/book/${b.id}/${b.image}`, { w });

export function mount(view, [rid]) {
  return rid ? mountCard(view, rid) : mountQueue(view);
}

// ==================================================================== queue
async function mountQueue(view) {
  let data;
  try { data = await api('/api/orders'); }
  catch (err) { setHtml(view, html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`); return null; }
  settle(data.orders); // kept cards of orders that are no longer new are let go
  let stage = 'new', term = '', syncing = false, shown = [], unfreeze = 0;

  setHtml(view, html`
    <div class="page-head"><div><h1 class="page-title">Замовлення</h1><div class="page-sub" id="or-sub"></div></div></div>
    <div class="lib-toolbar">
      <div class="input-group">${ic('search')}<input class="input" id="or-q" placeholder="Ім'я покупця або номер чека" aria-label="Пошук замовлення" autocomplete="off"></div>
      ${segHtml(STAGES.map((s) => ({ ...s, count: 0 })), stage, { name: 'stage' })}
      <div class="tools">${ib('sync', 'Оновити замовлення', 'data-act="sync"')}</div>
    </div>
    <div class="ord-list" id="or-list"></div>`);
  const $ = (s) => view.querySelector(s);
  const list = $('#or-list');
  const seg = view.querySelector('[data-seg="stage"]');
  const syncBtn = view.querySelector('[data-act="sync"]');
  const syncedText = () => (data.syncedAt ? `Оновлено ${relTime(data.syncedAt)}` : 'Ще не завантажено');
  const setSub = (text) => { $('#or-sub').textContent = text; };

  // Once ordered: where it was ordered. Before that: where the printer rule sends it.
  const printerChip = (o) => {
    const p = o.provider || (o.stage === 'new' ? o.plan?.provider : null);
    if (!p) return o.stage === 'new' ? html`<span class="chip chip-amber" data-tip="${planText(o.plan)}">${ic('alert', 'icon-s')}друкарня?</span>` : '';
    const tip = o.provider ? `Замовлено в ${providerName(p)}` : planText(o.plan);
    return html`<span class="chip svc-${p}" data-tip="${tip}">${ic(p, 'icon-s')}${providerName(p)}</span>`;
  };
  const rowHtml = (o, entering) => html`<a class="ord-row ${entering ? 'enter' : ''}" href="#/orders/${o.receiptId}" data-rid="${o.receiptId}">
      <span class="ord-thumb ${o.book?.lqip ? 'lqip' : ''}" ${o.book?.lqip ? raw(`style="background-image:url(${o.book.lqip})"`) : ''}>
        ${o.book?.image ? html`<img data-fade loading="lazy" decoding="async" src="${bookImage(o.book, 160)}" alt="">` : ic('book')}</span>
      <span class="ord-main">
        <span class="row ord-chips"><b class="truncate">${o.name}</b>${receiptCopy(o, 'chip chip-mono')}
          ${o.books > 1 ? html`<span class="chip" data-tip="Книг у замовленні">${ic('book', 'icon-s')}${o.books}</span>` : ''}${printerChip(o)}${trackChips(o)}</span>
        <span class="ord-meta faint truncate"><span data-tip="${dateTime(o.createdAt)}">${relTime(o.createdAt)}</span> ·
          ${o.childName ? html`<b class="ord-child">${o.childName}</b> · ` : ''}${o.book ? o.book.title : html`<span class="ord-miss">книги немає в бібліотеці</span>`} · ${[o.address.city, o.address.country_iso].filter(Boolean).join(', ')}</span>
      </span>
      ${statusChip(o) || html`<span></span>`}
      <span class="ord-go">${ic('chevRight')}</span>
    </a>`;

  const render = ({ fresh = false } = {}) => {
    const t = term.trim().toLowerCase();
    seg.querySelectorAll('button[data-value]').forEach((b) => {
      b.querySelector('.seg-count').textContent = data.orders.filter((o) => o.stage === b.dataset.value && matchesOrder(o, t)).length;
    });
    syncSeg(seg);
    const rows = data.orders.filter((o) => o.stage === stage && matchesOrder(o, t));
    const before = shown;
    shown = rows.map((o) => o.receiptId);
    if (!rows.length) {
      if (!data.orders.length && syncing) setHtml(list, html`<div class="empty"><div class="empty-icon"><span class="spinner"></span></div><p>Завантаження замовлень з Etsy…</p></div>`);
      else if (t) setHtml(list, html`<div class="empty">Нічого не знайдено</div>`);
      else {
        const [icon, title, text] = STAGE_EMPTY[stage];
        setHtml(list, html`<div class="empty"><div class="empty-icon">${ic(icon)}</div><h3>${title}</h3>${text ? html`<p>${text}</p>` : ''}</div>`);
      }
      return;
    }
    setHtml(list, rows.map((o) => rowHtml(o, !before.length || (fresh && !before.includes(o.receiptId)))));
    fadeImages(list);
    if (fresh && before.join() !== shown.join()) {
      // The rows just moved: ignore clicks for a moment so a click aimed at one buyer never lands on another.
      list.inert = true;
      clearTimeout(unfreeze);
      unfreeze = setTimeout(() => { list.inert = false; }, 450);
    }
  };

  // pull: the refresh button starts a sync; on opening the page we only follow one already running
  // (the one the program does at start-up) — pages never start a sync by themselves.
  async function refresh(pull = () => syncOrders(setSub)) {
    if (syncing) return;
    syncing = true;
    syncBtn.disabled = true; syncBtn.firstElementChild?.classList.add('spin');
    setSub('Оновлення…');
    if (!data.orders.length) render();
    try {
      await pull();
      const next = await api('/api/orders');
      settle(next.orders);
      if (!view.isConnected) return;
      data = next;
      setSub(syncedText());
      render({ fresh: true });
    } catch (err) {
      if (view.isConnected) setSub(`${syncedText()} · не вдалося оновити: ${err.message}`);
    } finally {
      syncing = false;
      syncBtn.disabled = false; syncBtn.firstElementChild?.classList.remove('spin');
    }
  }

  const offs = [
    on(view, 'click', '[data-act="sync"]', () => refresh()),
    on(view, 'click', '[data-act="copy-text"]', copyChip),
    on(view, 'click', '[data-seg="stage"] button', (e, b) => {
      if (b.dataset.value === stage) return;
      stage = b.dataset.value;
      setSeg(seg, stage);
      render();
    }),
  ];
  const q = $('#or-q');
  q.addEventListener('input', () => { term = q.value; render(); });
  q.addEventListener('keydown', (e) => { if (e.key === 'Enter' && shown.length) location.hash = `#/orders/${shown[0]}`; });

  setSub(syncedText());
  render();
  runningSync().then((jobId) => { if (jobId && view.isConnected) refresh(() => watchSync(jobId, setSub)); });
  return {
    shown() { syncSeg(seg); },
    unmount() { offs.forEach((f) => f()); clearTimeout(unfreeze); },
  };
}

// ==================================================================== one order
async function mountCard(view, rid) {
  let o;
  try { o = await api(`/api/orders/${rid}`); }
  catch (err) {
    setHtml(view, html`<button class="back-link" onclick="location.hash='#/orders'">${ic('arrowLeft', 'icon-s')}</button>
      <div class="empty"><div class="empty-icon">${ic('receipt')}</div><h3>Замовлення не відкрилось</h3><p>${err.message}</p></div>`);
    return null;
  }
  let pick = 0;        // which book of the order this pass is for (most orders hold one)
  let chosen = null;   // printer picked by hand when the cover type could not be read
  let seq = 0;
  let checkSeq = 0;
  let freshIssues = false; // the next paint of the findings is a new result: they slide in (once)
  const dismissed = new Set(); // text-check findings the owner marked «це не помилка» (kept for the card's life)
  // check: null (none yet / switched off) | {state:'run', percent, step} | {state:'done', result} | {state:'error', message}
  const f = { folder: '', label: '', note: '', pages: 0, validation: null, busy: 0, error: '', check: null };
  const item = () => o.items[pick] || {};
  const plan = () => item().plan || {};
  const provider = () => plan().provider || chosen;
  // Printify takes 24 pages; Gelato as many as were downloaded (28 or 30) — known once the files are in (f.pages).
  const pageOptions = () => (plan().provider ? plan().pages : (o.pageOptions || {})[provider()]) || [];
  const pagesLabel = () => (f.pages ? String(f.pages) : pagesText(pageOptions()));

  setHtml(view, html`
    <div class="page-head">
      <button class="back-link" data-act="back" aria-label="До замовлень" data-tip="До замовлень" data-kbd="Esc">${ic('arrowLeft')}</button>
      <div class="grow" style="min-width:0">
        <div class="ord-title"><h1 class="page-title truncate">${o.name}</h1>${statusChip(o)}</div>
        <div class="page-sub ord-sub">${receiptCopy(o, 'mono')} · <span data-tip="${dateTime(o.createdAt)}">${relTime(o.createdAt)}</span> · ${STAGE_LABEL[o.stage] || ''}${trackChips(o)}</div>
      </div>
      <div id="oc-plan"></div>
    </div>
    ${o.stage !== 'new' ? html`<div class="notice notice-warn" style="margin-bottom:18px">${ic('alert')}<div>${{
      work: `Цю книгу вже замовлено в ${providerName(o.provider)}. Друкуйте ще раз лише для передруку.`,
      sent: `${providerName(o.provider)} уже відправив цю книгу — позначте замовлення відправленим в Etsy. Друкуйте ще раз лише для передруку.`,
    }[o.stage] || 'Замовлення вже відправлено. Друкуйте ще раз лише для передруку.'}</div></div>` : ''}
    <div class="ord-grid">
      <div class="stack-l" id="oc-flow"></div>
      <div class="stack-l ord-side" id="oc-data"></div>
    </div>`);
  const $ = (s) => view.querySelector(s);

  // ---------------------------------------------------------------- header: where it is printed
  function renderPlan() {
    const p = provider();
    setHtml($('#oc-plan'), plan().provider
      ? html`<span class="chip chip-lg svc-${p}" data-tip="${planText(plan())}">${ic(p, 'icon-s')}<span>${providerName(p)} · ${pagesLabel()} стор.</span></span>`
      : html`<div class="row" style="gap:10px"><span class="faint" style="font-size:12.5px">Друкарня</span>${segHtml([
        { value: 'printify', icon: 'printify', tip: `Printify · ${pagesText(o.pageOptions?.printify)} стор.` },
        { value: 'gelato', icon: 'gelato', tip: `Gelato · ${pagesText(o.pageOptions?.gelato)} стор.` }], chosen, { name: 'provider' })}</div>`);
    requestAnimationFrame(() => syncSeg($('#oc-plan .seg')));
  }

  // ---------------------------------------------------------------- right (stays in view): book, personalization, delivery
  function renderLeft() {
    const it = item();
    const b = it.book;
    const vars = it.variations || [];
    const a = o.address || {};
    setHtml($('#oc-data'), html`
      <section class="card card-pad ord-book">
        <div class="ord-book-art ${b?.lqip ? 'lqip' : ''}" ${b?.lqip ? raw(`style="background-image:url(${b.lqip})"`) : ''}>
          ${b?.image ? html`<img data-fade decoding="async" src="${bookImage(b, 360)}" alt="">` : ic('book')}</div>
        <div class="stack-s grow" style="min-width:0">
          ${b ? html`<a class="ord-book-title" href="#/book/${b.id}" data-tip="Паспорт книги">${b.title}</a>`
            : html`<b>Книги немає в бібліотеці</b><span class="faint mono" style="font-size:12px">лістинг #${it.listingId || '—'}</span>`}
          ${b?.canvaUrl ? html`<button class="btn btn-primary" data-act="canva">${ic('canva')}Відкрити шаблон у Canva</button>`
            : b ? html`<a class="btn" href="#/book/${b.id}">${ic('link')}Додати посилання на Canva</a>`
              : html`<a class="btn" href="#/library">${ic('shelf')}До бібліотеки</a>`}
        </div>
      </section>
      <section class="card card-pad stack">
        <div class="row"><h3 class="card-title grow">Персоналізація</h3>
          ${o.items.length > 1 ? segHtml(o.items.map((x, i) => ({ value: String(i), label: `Книга ${i + 1}`, tip: x.title })), String(pick), { name: 'book' }) : ''}</div>
        ${vars.length ? html`<dl class="ord-fields">${vars.map((v, i) => html`
          <dt>${v.name}${isCustomText(v) ? html`<span class="chip chip-amber">свій текст</span>` : ''}</dt>
          <dd class="${isCustomText(v) ? 'custom' : ''} ${isNameField(v, it) ? 'is-name' : ''}"><span>${v.value}</span>${isFormatField(v) ? '' : ib('copy', 'Копіювати', `data-copy="${i}"`, { cls: 'sm' })}</dd>`)}</dl>`
          : html`<div class="faint">Покупець нічого не вказав.</div>`}
        ${o.buyerMessage ? html`<div class="ord-message"><span class="eyebrow">Повідомлення покупця</span><div>${o.buyerMessage}</div></div>` : ''}
      </section>
      <section class="card card-pad stack-s">
        <h3 class="card-title">Доставка</h3>
        <div class="ord-address">${[a.name, a.first_line, a.second_line, [a.city, a.state, a.zip].filter(Boolean).join(', '), countryName(a.country_iso)]
          .filter(Boolean).map((line) => html`<div>${line}</div>`)}</div>
      </section>`);
    fadeImages($('#oc-data'));
    requestAnimationFrame(() => syncSeg($('#oc-data .seg')));
  }

  // ---------------------------------------------------------------- left: files → proof → print
  const thumb = (name, w) => media('/media/folder', { path: f.folder, file: name, w });
  // The newest send of this order to the chosen printer that never went to print (a cancelled order, a
  // deleted or unconfirmed draft): its archived files can be taken instead of downloading them again.
  const earlier = () => (o.earlierSends || []).find((e) => e.provider === provider());

  function filesCard() {
    const v = f.validation;
    let badge = '';
    if (f.busy) badge = html`<span class="v-badge run"><span class="spinner" style="width:12px;height:12px;border-width:2px"></span><span class="num">${Math.round(f.busy)}%</span></span>`;
    else if (v?.ok) badge = html`<span class="v-badge ok" data-tip="Усі PNG прочитано й перевірено">${ic('check')}<span class="num">${v.found}/${v.expected}</span></span>`;
    else if (f.error || v) badge = html`<span class="v-badge bad">${ic('x')}Є проблеми</span>`;
    const errors = f.error ? [f.error] : (v?.errors || []);
    return html`<section class="card card-pad stack" data-folder-drop>
      <div class="row"><span class="step-no">1</span><h3 class="card-title grow">Файли з Canva</h3>${badge}</div>
      <div class="input-group">
        <input class="input path-input" id="oc-folder" readonly value="${f.label}" title="${f.folder}" aria-label="Файли з Canva"
          placeholder="${provider() ? `ZIP або папка · обкладинка і ${pagesText(pageOptions())} ${plural(pageOptions().at(-1) || 0, ['сторінка', 'сторінки', 'сторінок'])}` : 'Спершу оберіть друкарню'}">
        ${ib('folderPick', 'Обрати папку', `data-act="browse" ${provider() ? '' : 'disabled'}`)}
      </div>
      ${!f.folder && !f.busy && earlier() ? html`<button class="btn btn-sm btn-ghost" style="align-self:flex-start" data-act="earlier"
        data-tip="Ці файли вже відправлялись ${dateTime(earlier().sentAt)}, але замовлення в друкарні не оформлене чи скасоване">${ic('orderArchive', 'icon-s')}Взяти файли минулої відправки · ${relTime(earlier().sentAt)}</button>` : ''}
      ${f.note && !f.busy ? html`<div class="row faint" style="font-size:12.5px">${ic('swap', 'icon-s')}<span>${f.note}</span></div>` : ''}
      ${errors.length && !f.busy ? html`<div class="notice notice-error">${ic('alertCircle')}<div><ul>${errors.slice(0, 10).map((e) => html`<li>${e}</li>`)}</ul>${errors.length > 10 ? html`<div>…та ще ${errors.length - 10}</div>` : ''}</div></div>` : ''}
      ${v?.warnings?.length && !f.busy ? html`<div class="notice notice-warn">${ic('alert')}<div>${v.warnings.map((w) => html`<div>${w}</div>`)}</div></div>` : ''}
    </section>`;
  }

  function proofCard() {
    const it = item();
    const cover = f.validation.files.find((r) => r.position === 'cover') || {};
    const ratio = cover.width ? cover.width / cover.height : 1.9;
    const half = (n) => (n === null ? html`<div class="half blank"></div>` : html`<div class="half" data-page="${n}"><img data-fade loading="lazy" decoding="async" src="${thumb(`${n}.png`, STRIP_THUMB)}" alt=""></div>`);
    const notes = (it.variations || []).filter((v) => !isNameField(v, it) && !isFormatField(v)); // only what the page itself says
    return html`<section class="card card-pad stack-l" id="oc-proof">
      <div class="row"><span class="step-no">2</span><h3 class="card-title grow">Звірка</h3><span class="row tc-head" id="oc-check-badge">${checkBadge()}</span></div>
      <div id="oc-check">${checkBody()}</div>
      <div class="proof">
        <div class="structure-cover" data-lb="0" data-page="0" style="aspect-ratio:${ratio}">
          <img data-fade decoding="async" src="${thumb('Cover.png', 1400)}" alt="Обкладинка"><div class="gutter"></div><i class="crops"></i>
        </div>
        <div class="spread-view proof-spread" data-lb="1">
          <div class="half proof-note">
            ${it.childName ? html`<div class="proof-name">${it.childName}</div>` : ''}
            <dl>${notes.map((v) => html`<dt>${v.name}</dt><dd>${v.value}</dd>`)}</dl>
          </div>
          <div class="half" data-page="1"><img data-fade decoding="async" src="${thumb('1.png', 1400)}" alt="Сторінка 1"></div>
          <div class="gutter-s"></div><i class="crops"></i>
        </div>
      </div>
      <div class="strip" id="oc-strip">
        <div class="strip-item" data-lb="0" style="width:${Math.round(110 * ratio)}px">
          <div class="structure-cover" data-page="0" style="height:110px"><img data-fade loading="lazy" decoding="async" src="${thumb('Cover.png', STRIP_THUMB)}" alt=""></div>
          <span class="strip-no">обкладинка</span></div>
        ${spreadsOf(f.pages).map((sp, i) => html`<div class="strip-item" data-lb="${i + 1}">
          <div class="spread-view">${half(sp.left)}${half(sp.right)}<div class="gutter-s"></div></div>
          <span class="strip-no num">${[sp.left, sp.right].filter(Boolean).join('–')}</span></div>`)}
      </div>
    </section>`;
  }

  // ---------------------------------------------------------------- text check (the local model reads every page)
  // Starts by itself once the files are in; the proof stays usable meanwhile. Red — certain mistakes,
  // amber — worth a look; «це не помилка» hides a finding (a deliberate edit) for as long as the card lives.
  const openIssues = () => (f.check?.state === 'done' ? f.check.result.issues.filter((i) => !dismissed.has(i.id)) : []);
  const countOf = (level) => openIssues().filter((i) => i.level === level).length;

  function checkTip(r) {
    const lettered = r.pages.filter((p) => p.text).length;
    return [r.mode === 'full' ? 'Звірено з текстами паспорта книги' : LIGHT_TIP[r.light],
      `сторінок з текстом: ${lettered}`, r.skipped.length ? `без розворотів ${r.skipped.join(', ')}` : '', `${r.seconds} с`]
      .filter(Boolean).join(' · ');
  }

  function checkBadge() {
    const c = f.check;
    if (!c) return '';
    if (c.state === 'run') {
      return html`<span class="v-badge run" data-tip="${c.step || 'Перевірка тексту…'}"><span class="spinner" style="width:12px;height:12px;border-width:2px"></span>${ic('textScan')}<span class="num">${Math.round(c.percent)}%</span></span>`;
    }
    const again = ib('sync', 'Перевірити текст ще раз', 'data-act="recheck"', { cls: 'sm' });
    if (c.state === 'error') return html`<span class="v-badge" data-tip="${c.message}">${ic('textScan')}Текст не перевірено</span>`;
    const tip = checkTip(c.result);
    const errors = countOf('error'), warns = countOf('warn');
    if (errors) return html`<span class="v-badge bad" data-tip="${tip}">${ic('textScan')}<span class="num">${errors}</span>${plural(errors, LEVEL_WORDS.error)}</span>${again}`;
    if (warns) return html`<span class="v-badge warn" data-tip="${tip}">${ic('textScan')}<span class="num">${warns}</span>${plural(warns, LEVEL_WORDS.warn)}</span>${again}`;
    return html`<span class="v-badge ok" data-tip="${tip}">${ic('textScan')}Текст збігається</span>${again}`;
  }

  function checkBody() {
    const c = f.check;
    if (c?.state === 'error') {
      return html`<div class="notice notice-warn">${ic('alert')}<div class="grow">Текст не перевірено: ${c.message}</div>${ib('sync', 'Перевірити ще раз', 'data-act="recheck"', { cls: 'sm' })}</div>`;
    }
    if (c?.state !== 'done') return '';
    const r = c.result;
    const light = r.mode === 'light' ? html`<div class="row faint tc-light">${ic('info', 'icon-s')}<span>${LIGHT_TIP[r.light]}${r.bookId && r.light === 'noTexts' ? html` · <a href="#/book/${r.bookId}">паспорт книги</a>` : ''}</span></div>` : '';
    const list = openIssues();
    const learn = learnable();
    return html`${list.length ? html`<div class="tc-list">${list.map((i) => html`<div class="tc-issue ${i.level} ${freshIssues ? 'enter' : ''}" data-lb="${viewerIndex(i.page)}">
        <span class="tc-where">${i.label}</span>
        <span class="tc-text">${quoteBold(i.text)}${i.note ? html`<span class="tc-note">${i.note}</span>` : ''}</span>
        ${ib('check', 'Це не помилка', `data-dismiss="${i.id}"`, { cls: 'sm' })}
      </div>`)}</div>` : ''}${learn.length ? html`<div class="row tc-light faint">${ic('book', 'icon-s')}<span class="grow">Якщо в шаблоні Canva саме так — паспорт книги застарів</span>
        <button class="btn btn-sm" data-act="learn">Оновити паспорт · <span class="num">${learn.length}</span> ${plural(learn.length, ['сторінка', 'сторінки', 'сторінок'])}</button></div>` : ''}${light}`;
  }

  // Pages that differ from the book's passport only in their words (no name or placeholder mistakes)
  // and whose findings are all still shown: «Так у шаблоні Canva» writes them into the passport.
  function learnable() {
    if (f.check?.state !== 'done' || !f.check.result.bookId) return [];
    const shown = new Set(openIssues().map((i) => `${i.page}|${i.part}`));
    return f.check.result.pages.filter((p) => p.learn && shown.has(`${p.page}|${p.part}`));
  }

  async function learnPassport() {
    const r = f.check.result, pages = learnable();
    const ok = await confirmBox({
      title: 'Оновити паспорт книги?', confirm: 'Оновити паспорт',
      text: `Тексти ${pages.length} ${plural(pages.length, ['сторінки', 'сторінок', 'сторінок'])} (${pages.map((p) => p.label).join(', ')}) у паспорті книги стануть такими, як у цьому друці; ім'я дитини — знову {Name}.\n\nРобіть це, лише якщо ці сторінки в шаблоні Canva правильні — тоді наступні замовлення цієї книги звірятимуться вже з ними.`,
    });
    if (!ok) return;
    try {
      await api('/api/textcheck/passport', { method: 'POST', body: { bookId: r.bookId, child: r.child, pages: pages.map((p) => ({ key: p.learn, text: p.text })) } });
      toast('Паспорт книги оновлено', 'success');
      startCheck();
    } catch (err) { toast(err.message, 'error'); }
  }

  // Red / amber outline on the pages with findings: the big cover and page 1, and the strip.
  function markPages() {
    const worst = {};
    for (const i of openIssues()) if (worst[i.page] !== 'error') worst[i.page] = i.level;
    view.querySelectorAll('#oc-proof [data-page]').forEach((el) => {
      el.classList.toggle('tc-error', worst[el.dataset.page] === 'error');
      el.classList.toggle('tc-warn', worst[el.dataset.page] === 'warn');
    });
  }

  function paintCheck() {
    const badge = $('#oc-check-badge'), body = $('#oc-check');
    if (!badge || !body) return;
    setHtml(badge, checkBadge());
    setHtml(body, checkBody());
    freshIssues = false;
    markPages();
  }

  // The check is no longer wanted (the card closes, other files, another book): the model stops on it.
  function dropCheck() {
    checkSeq++;
    const c = f.check;
    if (c?.state === 'run' && c.jobId) {
      api(`/api/orders/${o.receiptId}/textcheck/cancel`, { method: 'POST', body: { jobId: c.jobId } }).catch(() => {});
    }
  }

  async function startCheck() {
    const my = seq, mine = ++checkSeq;
    const live = () => my === seq && mine === checkSeq;
    f.check = { state: 'run', percent: 0, step: 'Перевірка тексту…' };
    paintCheck();
    try {
      const start = await api(`/api/orders/${o.receiptId}/textcheck`, { method: 'POST', body: { folder: f.folder, pages: f.pages, pick } });
      if (!live()) return;
      if (start.off) { f.check = null; paintCheck(); return; } // switched off in Settings
      f.check.jobId = start.jobId;
      const result = await runJob(Promise.resolve(start), (j) => {
        if (!live() || f.check?.state !== 'run') return;
        Object.assign(f.check, { percent: j.percent || 0, step: j.step || '' });
        const badge = view.querySelector('#oc-check-badge .v-badge.run');
        if (badge) { badge.querySelector('.num').textContent = `${Math.round(f.check.percent)}%`; badge.dataset.tip = f.check.step; }
      }, 700, live);
      if (!live()) return;
      f.check = { state: 'done', result };
      freshIssues = true;
    } catch (err) {
      if (!live()) return;
      f.check = { state: 'error', message: err.message };
    }
    paintCheck();
  }

  // The viewer shows, with T, what the model read on a spread's pages and what they must say.
  function viewerItems() {
    const items = folderViewerItems(f.folder, f.pages, f.label);
    for (const p of f.check?.state === 'done' ? f.check.result.pages : []) {
      const item = items[viewerIndex(p.page)];
      if (!item || (!p.text && !p.expected)) continue;
      const block = [`${p.label} — надруковано:`, p.text || '—', ...(p.expected ? ['', 'Має бути:', p.expected] : [])].join('\n');
      item.text = item.text ? `${item.text}\n\n${block}` : block;
    }
    return items;
  }

  // Once the Order Creator has made the draft for this order, the step says so instead of offering
  // «До друку» again (the order stays in «Нові» until the next sync finds it at the printer).
  function printCard() {
    const p = provider();
    const done = sentOf(o.receiptId);
    const result = keptOrder('#/creator') === String(o.receiptId);
    return html`<section class="card card-pad stack ${p === 'printify' ? 'tint-printify' : ''}" id="oc-print">
      <div class="row"><span class="step-no">3</span><h3 class="card-title grow">Друк</h3></div>
      ${done ? html`<div class="notice notice-success">${ic('checkCircle')}<div class="grow">${done.what}</div></div>
        <div class="row">${result ? html`<button class="btn btn-primary grow" data-act="to-creator">${ic('printer', 'icon-s')}Результат в Order Creator</button>` : ''}
          ${ib('send', 'Надіслати ще раз', 'data-act="print"')}</div>`
    : html`<button class="btn btn-xl btn-primary btn-block" data-act="print">${ic('send', 'icon-l')}До друку в ${providerName(p)}</button>`}
    </section>`;
  }

  function renderRight() {
    const ready = !!(f.folder && f.validation?.ok && !f.busy);
    setHtml($('#oc-flow'), [filesCard(), ready ? proofCard() : '', ready ? printCard() : '']);
    fadeImages($('#oc-flow'));
    const strip = $('#oc-strip');
    if (strip) smoothWheel(strip);
    markPages();
  }

  const setBusy = (pct) => {
    f.busy = Math.max(1, Math.min(99, pct));
    const num = view.querySelector('#oc-flow .v-badge.run .num');
    if (num) num.textContent = `${Math.round(f.busy)}%`;
  };

  // Put the export in page order (Cover.png + 1..N.png), then run the same full check as the Order Creator.
  async function arrange(path, my) {
    const res = await api(`/api/orders/${o.receiptId}/files`, { method: 'POST', body: { folder: path, provider: provider(), format: plan().format || null } });
    if (my !== seq) return;
    Object.assign(f, { folder: res.path, note: res.note, pages: res.pageCount });
    renderPlan();
    const v = await runJob(api('/api/creator/validate', { method: 'POST', body: { mode: provider(), folder: f.folder } }),
      (j) => { if (my === seq) setBusy(60 + (j.percent || 0) * 0.4); }, 300);
    if (my !== seq) return;
    Object.assign(f, { validation: v, busy: 0, check: null });
    renderRight();
    if (v.ok) {
      requestAnimationFrame(() => $('#oc-proof')?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
      startCheck();
    }
  }
  const failed = (my, err) => {
    if (my !== seq) return;
    Object.assign(f, { busy: 0, error: err.message, validation: null, pages: 0 });
    renderPlan(); renderRight();
  };

  async function takeDrop(dropped) {
    if (!provider()) { toast('Спершу оберіть друкарню', 'info'); return; }
    dropCheck();
    const my = ++seq;
    Object.assign(f, { folder: '', label: dropLabel(dropped), note: '', pages: 0, validation: null, busy: 1, error: '', check: null });
    renderPlan(); renderRight();
    try {
      const path = await receiveDrop(dropped, (pct) => { if (my === seq) setBusy(pct * 0.6); });
      if (my === seq) await arrange(path, my);
    } catch (err) { failed(my, err); }
  }

  async function takeFolder() {
    let path;
    try { path = (await api('/api/creator/pick-folder', { method: 'POST', body: { title: `Оберіть папку з обкладинкою і ${pagesText(pageOptions())} сторінками` } })).path; }
    catch (err) { toast(err.message, 'error'); return; }
    if (!path) return;
    dropCheck();
    const my = ++seq;
    Object.assign(f, { folder: '', label: path.split(/[\\/]/).pop(), note: '', pages: 0, validation: null, busy: 1, error: '', check: null });
    renderPlan(); renderRight();
    try { await arrange(path, my); } catch (err) { failed(my, err); }
  }

  async function takeEarlier() {
    const e = earlier();
    if (!e) return;
    dropCheck();
    const my = ++seq;
    Object.assign(f, { folder: '', label: `Минула відправка · ${relTime(e.sentAt)}`, note: '', pages: 0, validation: null, busy: 1, error: '', check: null });
    renderPlan(); renderRight();
    try {
      const { path } = await api(`/api/archive/${e.id}/reuse`, { method: 'POST', body: {} });
      if (my === seq) await arrange(path, my);
    } catch (err) { failed(my, err); }
  }

  function resetFiles() {
    dropCheck();
    seq++;
    Object.assign(f, { folder: '', label: '', note: '', pages: 0, validation: null, busy: 0, error: '', check: null });
  }

  // The text check never blocks printing — it asks once when it is still running or found mistakes.
  async function print() {
    const c = f.check;
    if (c?.state === 'run' && !(await confirmBox({ title: 'Текст ще перевіряється',
      text: 'Відправити до друку, не дочекавшись перевірки тексту?', confirm: 'До друку', cancel: 'Зачекати' }))) return;
    const errors = c?.state === 'done' ? countOf('error') : 0;
    if (errors && !(await confirmBox({ title: 'У тексті є помилки', danger: true, confirm: 'Все одно до друку', cancel: 'Повернутись',
      text: `Перевірка знайшла ${errors} ${plural(errors, LEVEL_WORDS.error)} у тексті сторінок.` }))) return;
    const it = item();
    const name = it.childName || o.childName || '';
    give('creator', {
      receiptId: String(o.receiptId), // the Order Creator keeps its work (and result) for this order
      mode: provider(), folder: f.folder, label: f.label, format: plan().format || null,
      title: name ? `${o.receiptId} - ${name}` : String(o.receiptId), address: addressFromEtsy(o),
    });
    location.hash = '#/creator';
  }

  // ---------------------------------------------------------------- events
  const offs = [
    on(view, 'click', '[data-act]', (e, t) => {
      const a = t.dataset.act;
      if (a === 'back') location.hash = '#/orders';
      else if (a === 'canva') openExternal(item().book?.canvaUrl);
      else if (a === 'browse') takeFolder();
      else if (a === 'earlier') takeEarlier();
      else if (a === 'print') print();
      else if (a === 'to-creator') location.hash = '#/creator';
      else if (a === 'copy-text') copyChip(e, t);
      else if (a === 'recheck') startCheck();
      else if (a === 'learn') learnPassport();
    }),
    on(view, 'click', '[data-copy]', (e, b) => copyText(item().variations?.[+b.dataset.copy]?.value || '', 'Скопійовано')),
    on(view, 'click', '[data-dismiss]', (e, b) => { dismissed.add(b.dataset.dismiss); paintCheck(); }),
    on(view, 'click', '[data-lb]', (e, c) => {
      if (e.target.closest('[data-dismiss]') || !f.folder || !f.pages) return;
      openLightbox(viewerItems(), +c.dataset.lb);
    }),
    on(view, 'click', '[data-seg="provider"] button', (e, b) => {
      chosen = b.dataset.value;
      setSeg(b.closest('.seg'), chosen);
      resetFiles();
      renderPlan(); renderRight();
    }),
    on(view, 'click', '[data-seg="book"] button', (e, b) => {
      if (+b.dataset.value === pick) return;
      pick = +b.dataset.value;
      chosen = null;
      resetFiles();
      renderPlan(); renderLeft(); renderRight();
    }),
  ];
  wireFolderDrop(view, () => $('#oc-folder'), takeDrop);

  // Esc steps back to the queue when nothing else (a dialog, the viewer, a menu) owns the key.
  const onKey = (e) => {
    if (e.key !== 'Escape' || e.defaultPrevented) return;
    if (document.querySelector('.modal-root, .lightbox, .menu')) return;
    location.hash = '#/orders';
  };
  const keys = (listen) => document[listen ? 'addEventListener' : 'removeEventListener']('keydown', onKey);
  keys(true);

  renderPlan(); renderLeft(); renderRight();
  // A new order's card is kept when the owner steps to another tab (keep.js): hidden, it lets go of Esc;
  // brought back, it first asks whether the order is still new, then shows a draft made meanwhile.
  return {
    receiptId: String(o.receiptId),
    keep: () => o.stage === 'new',
    hidden() { keys(false); },
    async revive() {
      const fresh = await api(`/api/orders/${rid}`);
      if (fresh.stage !== 'new') return false;
      keys(true);
      const step = $('#oc-print');
      if (step) step.outerHTML = String(printCard());
      return true;
    },
    // Nothing but a position to remember: such cards give way first when many are kept (keep.js).
    idle: () => !(f.folder || f.busy || f.label || sentOf(o.receiptId)),
    unmount() { dropCheck(); offs.forEach((fn) => fn()); seq++; keys(false); },
  };
}
