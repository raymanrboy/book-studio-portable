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
  isCustomText, isNameField, isFormatField, restorable, alsoSentChip,
} from '../order-bits.js';
import { give } from '../handoff.js';
import { settle, sentOf, keptOrder, finish } from '../keep.js';

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
// Where the owner was in the queue — the tab, the search, how far down: the card's back arrow (and Esc, the
// Orders icon) bring him back there, not to «Нові» (owner, 19.09.2026). Memory only: the program starts at «Нові».
const queueState = { stage: 'new', term: '', scroll: 0, visited: false };

async function mountQueue(view) {
  let data;
  try { data = await api('/api/orders'); }
  catch (err) { setHtml(view, html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`); return null; }
  settle(data.orders); // kept cards of orders that are no longer new are let go
  let { stage, term } = queueState;
  let syncing = false, shown = [], unfreeze = 0;
  const returning = queueState.visited; // coming back: the rows stand where they were, no entrance
  queueState.visited = true;

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
          ${o.books > 1 ? html`<span class="chip" data-tip="Книг у замовленні">${ic('book', 'icon-s')}${o.books}</span>` : ''}${printerChip(o)}${alsoSentChip(o)}${trackChips(o)}</span>
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
    setHtml(list, rows.map((o) => rowHtml(o, (!before.length && !returning) || (fresh && !before.includes(o.receiptId)))));
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
      stage = queueState.stage = b.dataset.value;
      setSeg(seg, stage);
      render();
    }),
  ];
  const q = $('#or-q');
  q.value = term;
  q.addEventListener('input', () => { term = queueState.term = q.value; render(); });
  q.addEventListener('keydown', (e) => { if (e.key === 'Enter' && shown.length) location.hash = `#/orders/${shown[0]}`; });

  setSub(syncedText());
  render();
  runningSync().then((jobId) => { if (jobId && view.isConnected) refresh(() => watchSync(jobId, setSub)); });
  const main = document.getElementById('main');
  return {
    shown() {
      syncSeg(seg);
      if (returning) main.scrollTo({ top: queueState.scroll, behavior: 'instant' }); // .main scrolls smoothly otherwise
    },
    unmount() { queueState.scroll = main.scrollTop; offs.forEach((f) => f()); clearTimeout(unfreeze); },
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
  let finished = false; // «Завершити»: this card is not kept when the owner leaves it
  // Every book of the order goes its own way — its own files, proof and text check — and they all leave
  // for the printer together, in one draft to one address (owner, 20.09.2026).
  // check: null (none yet / switched off) | {state:'run', percent, step} | {state:'done', result} | {state:'error', message}
  const blank = () => ({ folder: '', label: '', note: '', pages: 0, validation: null, busy: 0, error: '', check: null,
    chosen: null,        // printer picked by hand when the cover type could not be read
    seq: 0, checkSeq: 0, // a flow whose number moved on is no longer this book's newest
    fresh: false,        // the next paint of the findings is a new result: they slide in (once)
    stamp: 0,            // grows with every replaced page, so pictures are fetched anew
    replaced: new Set(), // pages a new file was put over — they can be put back
    dismissed: new Set() }); // findings the owner marked «це не помилка» (kept for the card's life)
  const work = (o.items.length ? o.items : [{}]).map(blank);
  let f = work[pick];
  const showing = (w) => w === f;
  const item = () => o.items[pick] || {};
  const plan = (i = pick) => o.items[i]?.plan || {};
  const providerOf = (i) => plan(i).provider || work[i].chosen;
  const provider = () => providerOf(pick);
  // Printify takes 24 pages; Gelato as many as were downloaded (28 or 30) — known once the files are in (f.pages).
  const pageOptions = () => (plan().provider ? plan().pages : (o.pageOptions || {})[provider()]) || [];
  // «4100000001 - Emma»; two books for children of the same name are told apart by a number.
  const titleOf = (i) => {
    const name = o.items[i]?.childName || o.childName || '';
    const same = o.items.filter((x, j) => j < i && (x.childName || '') === (o.items[i]?.childName || ''));
    return (name ? `${o.receiptId} - ${name}` : String(o.receiptId)) + (same.length ? ` (${same.length + 1})` : '');
  };
  const pagesLabel = () => (f.pages ? String(f.pages) : pagesText(pageOptions()));

  setHtml(view, html`
    <div class="page-head">
      <button class="back-link" data-act="back" aria-label="До замовлень" data-tip="До замовлень" data-kbd="Esc">${ic('arrowLeft')}</button>
      <span id="oc-finish"></span>
      <div class="grow" style="min-width:0">
        <div class="ord-title"><h1 class="page-title truncate">${o.name}</h1>${statusChip(o)}${alsoSentChip(o)}</div>
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
        { value: 'gelato', icon: 'gelato', tip: `Gelato · ${pagesText(o.pageOptions?.gelato)} стор.` }], f.chosen, { name: 'provider' })}</div>`);
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
  const thumb = (name, w) => media('/media/folder', { path: f.folder, file: name, w, ...(f.stamp ? { v: f.stamp } : {}) });
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
      <div class="row"><span class="step-no">1</span><h3 class="card-title grow">Файли з Canva</h3>
        ${o.items.length > 1 ? segHtml(o.items.map((x, i) => ({ value: String(i), label: `Книга ${i + 1}`, tip: x.childName || x.title })), String(pick), { name: 'book' }) : ''}${badge}</div>
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
  // While the check runs these are the findings it has already shared; the model is still on the rest.
  const openIssues = (w = f) => (w.check?.state === 'done' ? w.check.result.issues
    : w.check?.state === 'run' ? (w.check.partial?.issues || []) : []).filter((i) => !w.dismissed.has(i.id));
  const countOf = (level, w = f) => openIssues(w).filter((i) => i.level === level).length;

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

  const issueRow = (i) => html`<div class="tc-issue ${i.level} ${f.fresh ? 'enter' : ''}" data-lb="${viewerIndex(i.page)}">
      <span class="tc-where">${i.label}</span>
      <span class="tc-text">${quoteBold(i.text)}${i.note ? html`<span class="tc-note">${i.note}</span>` : ''}</span>
      ${ib('check', 'Це не помилка', `data-dismiss="${i.id}"`, { cls: 'sm' })}
    </div>`;

  function checkBody() {
    const c = f.check;
    // The pages already checked are shown at once, without waiting for the rest of the book.
    if (c?.state === 'run') {
      const running = openIssues();
      return running.length ? html`<div class="tc-list">${running.map(issueRow)}</div>` : '';
    }
    if (c?.state === 'error') {
      return html`<div class="notice notice-warn">${ic('alert')}<div class="grow">Текст не перевірено: ${c.message}</div>${ib('sync', 'Перевірити ще раз', 'data-act="recheck"', { cls: 'sm' })}</div>`;
    }
    if (c?.state !== 'done') return '';
    const r = c.result;
    const light = r.mode === 'light' ? html`<div class="row faint tc-light">${ic('info', 'icon-s')}<span>${LIGHT_TIP[r.light]}${r.bookId && r.light === 'noTexts' ? html` · <a href="#/book/${r.bookId}">паспорт книги</a>` : ''}</span></div>` : '';
    const list = openIssues();
    const learn = learnable();
    return html`${list.length ? html`<div class="tc-list">${list.map(issueRow)}</div>` : ''}${learn.length ? html`<div class="row tc-light faint">${ic('book', 'icon-s')}<span class="grow">Якщо в шаблоні Canva саме так — паспорт книги застарів</span>
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
    f.fresh = false;
    markPages();
  }

  // The check is no longer wanted (the card closes, other files, another book): the model stops on it.
  function dropCheck(w = f) {
    w.checkSeq++;
    const c = w.check;
    if (c?.state === 'run' && c.jobId) {
      api(`/api/orders/${o.receiptId}/textcheck/cancel`, { method: 'POST', body: { jobId: c.jobId } }).catch(() => {});
    }
  }

  // The model takes ~4 s to reach the graphics card (~70 s when it comes from disk): it is asked for while
  // the files are still being copied and checked, so the check right after them does not wait for it.
  const warmModel = () => { api('/api/textcheck/warm', { method: 'POST' }).catch(() => {}); };

  async function startCheck(w = f, at = w.seq) {
    const mine = ++w.checkSeq;
    const live = () => at === w.seq && mine === w.checkSeq;
    const paint = () => { if (showing(w)) paintCheck(); };
    w.check = { state: 'run', percent: 0, step: 'Перевірка тексту…' };
    paint();
    try {
      const start = await api(`/api/orders/${o.receiptId}/textcheck`, { method: 'POST', body: { folder: w.folder, pages: w.pages, pick: work.indexOf(w) } });
      if (!live()) return;
      if (start.off) { w.check = null; paint(); return; } // switched off in Settings
      w.check.jobId = start.jobId;
      const result = await runJob(Promise.resolve(start), (j) => {
        if (!live() || w.check?.state !== 'run') return;
        const had = openIssues(w).length;
        Object.assign(w.check, { percent: j.percent || 0, step: j.step || '', partial: j.partial || null });
        if (!showing(w)) return;
        const badge = view.querySelector('#oc-check-badge .v-badge.run');
        if (badge) { badge.querySelector('.num').textContent = `${Math.round(w.check.percent)}%`; badge.dataset.tip = w.check.step; }
        if (openIssues(w).length !== had) { setHtml($('#oc-check'), checkBody()); markPages(); }
      }, 700, live);
      if (!live()) return;
      w.check = { state: 'done', result };
      w.fresh = true;
    } catch (err) {
      if (!live()) return;
      w.check = { state: 'error', message: err.message };
    }
    paint();
  }

  // The viewer shows, with T, what the model read on a spread's pages and what they must say, and lets
  // a page be replaced by a file from the computer (the owner fixed it in Canva and downloaded it again).
  const pageNo = (file) => (/^cover/i.test(file) ? 0 : parseInt(file, 10));
  const pageWord = (file) => (pageNo(file) ? `сторінку ${pageNo(file)}` : 'обкладинку');

  function pageActions(w, item, again) {
    const acts = [];
    for (const file of item.files || []) {
      const num = pageNo(file) ? String(pageNo(file)) : '';
      acts.push({ icon: 'swap', label: num, tip: `Замінити ${pageWord(file)} — обрати файл на комп'ютері`,
        run: (lb) => replacePage(w, file, lb, again) });
      if (w.replaced.has(file.toLowerCase())) {
        acts.push({ icon: 'restore', label: num, on: true, tip: `Повернути попередню ${pageWord(file)}`,
          run: (lb) => restorePage(w, file, lb, again) });
      }
    }
    return acts;
  }

  function viewerItems(w = f, again = null) {
    const items = folderViewerItems(w.folder, w.pages, w.label, w.stamp);
    if (again) items.forEach((it) => { it.actions = pageActions(w, it, again); });
    for (const p of w.check?.state === 'done' ? w.check.result.pages : []) {
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
    const ready = readyBooks(p);
    // An order of several books: which of them this send takes, and what each one still waits for.
    const list = work.length > 1 ? html`<ul class="oc-books">${work.map((w, i) => {
      const its = ready.some((r) => r.i === i);
      const why = its ? 'готова' : !providerOf(i) ? 'не обрано друкарню' : providerOf(i) !== p ? `друкується в ${providerName(providerOf(i))}`
        : w.busy ? 'перевіряються файли' : w.folder ? 'файли не пройшли перевірку' : 'немає файлів';
      return html`<li class="${its ? 'is-ready' : 'faint'}">${ic(its ? 'check' : 'clock', 'icon-s')}<span class="grow truncate">Книга ${i + 1}${o.items[i]?.childName ? ` · ${o.items[i].childName}` : ''}</span><span>${why}</span></li>`;
    })}</ul>` : '';
    return html`<section class="card card-pad stack ${p === 'printify' ? 'tint-printify' : ''}" id="oc-print">
      <div class="row"><span class="step-no">3</span><h3 class="card-title grow">Друк</h3></div>
      ${list}
      ${done ? html`<div class="notice notice-success">${ic('checkCircle')}<div class="grow">${done.what}</div></div>
        <div class="row">${result ? html`<button class="btn btn-primary grow" data-act="to-creator">${ic('printer', 'icon-s')}Результат в Order Creator</button>` : ''}
          ${ib('send', 'Надіслати ще раз', 'data-act="print"')}</div>`
    : html`<button class="btn btn-xl btn-primary btn-block" data-act="print">${ic('send', 'icon-l')}До друку в ${providerName(p)}${ready.length > 1 ? html` · <span class="num">${ready.length}</span> книги` : ''}</button>`}
    </section>`;
  }

  // The cross beside the back arrow appears once the draft is made: «робота над цим замовленням
  // завершена» — the card and the Order Creator let go of it and the queue opens (owner, 20.09.2026).
  function renderFinish() {
    setHtml($('#oc-finish'), sentOf(o.receiptId)
      ? ib('x', 'Завершити роботу над замовленням', 'data-act="finish"', { cls: 'sm' }) : '');
  }

  function renderRight() {
    const ready = !!(f.folder && f.validation?.ok && !f.busy);
    renderFinish();
    setHtml($('#oc-flow'), [filesCard(), ready ? proofCard() : '', ready ? printCard() : '']);
    fadeImages($('#oc-flow'));
    requestAnimationFrame(() => syncSeg($('#oc-flow .seg')));
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
  async function arrange(path, w, my) {
    const i = work.indexOf(w);
    const res = await api(`/api/orders/${o.receiptId}/files`, { method: 'POST', body: { folder: path, provider: providerOf(i), format: plan(i).format || null } });
    if (my !== w.seq) return;
    Object.assign(w, { folder: res.path, note: res.note, pages: res.pageCount });
    if (showing(w)) renderPlan();
    const v = await runJob(api('/api/creator/validate', { method: 'POST', body: { mode: providerOf(i), folder: w.folder } }),
      (j) => { if (my === w.seq && showing(w)) setBusy(60 + (j.percent || 0) * 0.4); }, 300);
    if (my !== w.seq) return;
    Object.assign(w, { validation: v, busy: 0, check: null, replaced: restorable(v) });
    if (showing(w)) renderRight();
    if (v.ok) {
      if (showing(w)) requestAnimationFrame(() => $('#oc-proof')?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
      startCheck(w, my);
    }
  }
  const failed = (w, my, err) => {
    if (my !== w.seq) return;
    Object.assign(w, { busy: 0, error: err.message, validation: null, pages: 0 });
    if (showing(w)) { renderPlan(); renderRight(); }
  };

  async function takeDrop(dropped) {
    if (!provider()) { toast('Спершу оберіть друкарню', 'info'); return; }
    // A couple of loose pictures on a book that is already prepared is not a new export — most likely
    // one page fixed in Canva. The prepared work stays where it is; the viewer replaces that page.
    const zip = dropped.files.length === 1 && /\.zip$/i.test(dropped.files[0].name);
    const loose = !zip && !dropped.entries.some((x) => x.isDirectory);
    if (loose && dropped.files.length <= 3 && f.validation?.ok) {
      toast('Щоб замінити одну сторінку — відкрийте її в переглядачі (клік по сторінці) і натисніть «Замінити»', 'info', 7000);
      return;
    }
    const w = f;
    dropCheck(w);
    warmModel();
    const my = ++w.seq;
    Object.assign(w, { folder: '', label: dropLabel(dropped), note: '', pages: 0, validation: null, busy: 1, error: '', check: null,
      stamp: 0, replaced: new Set(), dismissed: new Set() });
    renderPlan(); renderRight();
    try {
      const path = await receiveDrop(dropped, (pct) => { if (my === w.seq && showing(w)) setBusy(pct * 0.6); });
      if (my === w.seq) await arrange(path, w, my);
    } catch (err) { failed(w, my, err); }
  }

  async function takeFolder() {
    let path;
    warmModel();
    try { path = (await api('/api/creator/pick-folder', { method: 'POST', body: { title: `Оберіть папку з обкладинкою і ${pagesText(pageOptions())} сторінками` } })).path; }
    catch (err) { toast(err.message, 'error'); return; }
    if (!path) return;
    const w = f;
    dropCheck(w);
    const my = ++w.seq;
    Object.assign(w, { folder: '', label: path.split(/[\\/]/).pop(), note: '', pages: 0, validation: null, busy: 1, error: '', check: null,
      stamp: 0, replaced: new Set(), dismissed: new Set() });
    renderPlan(); renderRight();
    try { await arrange(path, w, my); } catch (err) { failed(w, my, err); }
  }

  async function takeEarlier() {
    const e = earlier();
    if (!e) return;
    const w = f;
    dropCheck(w);
    warmModel();
    const my = ++w.seq;
    Object.assign(w, { folder: '', label: `Минула відправка · ${relTime(e.sentAt)}`, note: '', pages: 0, validation: null, busy: 1, error: '', check: null,
      stamp: 0, replaced: new Set(), dismissed: new Set() });
    renderPlan(); renderRight();
    try {
      const { path } = await api(`/api/archive/${e.id}/reuse`, { method: 'POST', body: {} });
      if (my === w.seq) await arrange(path, w, my);
    } catch (err) { failed(w, my, err); }
  }

  function resetFiles(w = f) {
    dropCheck(w);
    w.seq++;
    Object.assign(w, blank(), { chosen: w.chosen, seq: w.seq, checkSeq: w.checkSeq });
  }

  /** The books of this order that are ready for the printer now shown (files in, checked, not busy). */
  const readyBooks = (p = provider()) => work.map((w, i) => ({ w, i }))
    .filter(({ w, i }) => w.folder && w.validation?.ok && !w.busy && providerOf(i) === p);

  /** The viewer, with a live list of items: a replaced page rebuilds them and the viewer redraws. */
  function openViewer(start) {
    const w = f;
    const items = [];
    const again = (lb) => { items.splice(0, items.length, ...viewerItems(w, again)); lb.refresh(); };
    items.push(...viewerItems(w, again));
    openLightbox(items, start);
  }

  /** A page fixed in Canva takes the place of the old one; the old one waits for «Повернути». */
  async function replacePage(w, file, lb, again) {
    let path;
    try {
      path = (await api('/api/creator/pick-file', { method: 'POST',
        body: { title: `Оберіть ${pageWord(file)} (${file})`, initial: w.folder } })).path;
    } catch (err) { toast(err.message, 'error'); return; }
    if (!path) return;
    if (sentOf(o.receiptId) && !(await confirmBox({ title: 'Чернетку вже створено',
      text: 'У друкарні лежить стара сторінка. Замінити її тут і надіслати замовлення ще раз?',
      confirm: 'Замінити', cancel: 'Не чіпати' }))) return;
    let res;
    try {
      res = await api('/api/creator/replace-page', { method: 'POST', body: { folder: w.folder, file, path } });
    } catch (err) { toast(err.message, 'error'); return; }
    setRestorable(w, file, res.canRestore);
    pageChanged(w, file, lb, again, `Замінено ${pageWord(file)}`);
  }

  async function restorePage(w, file, lb, again) {
    let res;
    try {
      res = await api('/api/creator/restore-page', { method: 'POST', body: { folder: w.folder, file } });
    } catch (err) { toast(err.message, 'error'); return; }
    setRestorable(w, file, res.canRestore);   // an older version may still be there
    pageChanged(w, file, lb, again, `Повернено ${pageWord(file)}`);
  }

  /** The server says whether this page still has a previous version; the card only repeats it. */
  function setRestorable(w, file, can) {
    if (can) w.replaced.add(file.toLowerCase());
    else w.replaced.delete(file.toLowerCase());
  }

  /** After a page changed: new picture everywhere, files checked again, text checked again — and the
   *  «це не помилка» marks of that page forgotten, because it is a different page now. */
  function pageChanged(w, file, lb, again, message) {
    w.stamp++;
    for (const i of w.check?.state === 'done' ? w.check.result.issues : []) {
      if (i.page === pageNo(file)) w.dismissed.delete(i.id);
    }
    toast(message, 'success');
    again(lb);
    revalidate(w);
  }

  /** The same checks as after new files, but the folder stays as it is (only one page changed). The
   *  proof is not taken down while they run — it is redrawn once, when the new page is in it. */
  async function revalidate(w) {
    dropCheck(w);
    const my = ++w.seq;
    w.error = '';
    try {
      const v = await runJob(api('/api/creator/validate', { method: 'POST', body: { mode: providerOf(work.indexOf(w)), folder: w.folder } }),
        null, 300);
      if (my !== w.seq) return;
      Object.assign(w, { validation: v, busy: 0, check: null, replaced: restorable(v) });
      if (showing(w)) renderRight();
      if (v.ok) startCheck(w, my);
    } catch (err) { failed(w, my, err); }
  }

  // The text check never blocks printing — it asks once when it is still running or found mistakes.
  // Every ready book of the order goes in one draft to one address; the rest wait for another send.
  async function print() {
    const p = provider();
    const ready = readyBooks(p);
    if (!ready.length) { toast('Спершу розставте файли книги', 'info'); return; }
    const left = work.length - ready.length;
    if (left && !(await confirmBox({ title: 'Готові не всі книги замовлення',
      text: `Готов${ready.length > 1 ? 'і' : 'а'} ${ready.length} з ${work.length} книг замовлення. Відправити лише ${ready.length > 1 ? 'їх' : 'її'}? Решту можна надіслати пізніше — це буде окреме замовлення в друкарні.`,
      confirm: 'Відправити готові', cancel: 'Повернутись' }))) return;
    if (ready.some(({ w }) => w.check?.state === 'run') && !(await confirmBox({ title: 'Текст ще перевіряється',
      text: 'Відправити до друку, не дочекавшись перевірки тексту?', confirm: 'До друку', cancel: 'Зачекати' }))) return;
    const errors = ready.reduce((n, { w }) => n + (w.check?.state === 'done' ? countOf('error', w) : 0), 0);
    if (errors && !(await confirmBox({ title: 'У тексті є помилки', danger: true, confirm: 'Все одно до друку', cancel: 'Повернутись',
      text: `Перевірка знайшла ${errors} ${plural(errors, LEVEL_WORDS.error)} у тексті сторінок.` }))) return;
    const books = ready.map(({ w, i }) => ({ folder: w.folder, label: w.label, title: titleOf(i), format: plan(i).format || null }));
    give('creator', {
      receiptId: String(o.receiptId), // the Order Creator keeps its work (and result) for this order
      mode: p, books, ...books[0], address: addressFromEtsy(o),
    });
    location.hash = '#/creator';
  }

  // ---------------------------------------------------------------- events
  const offs = [
    on(view, 'click', '[data-act]', (e, t) => {
      const a = t.dataset.act;
      if (a === 'back') location.hash = '#/orders';
      else if (a === 'finish') { finished = true; finish(o.receiptId); location.hash = '#/orders'; }
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
    on(view, 'click', '[data-dismiss]', (e, b) => { f.dismissed.add(b.dataset.dismiss); paintCheck(); }),
    on(view, 'click', '[data-lb]', (e, c) => {
      if (e.target.closest('[data-dismiss]') || !f.folder || !f.pages) return;
      openViewer(+c.dataset.lb);
    }),
    on(view, 'click', '[data-seg="provider"] button', (e, b) => {
      f.chosen = b.dataset.value;
      setSeg(b.closest('.seg'), f.chosen);
      resetFiles();
      renderPlan(); renderRight();
    }),
    // Each book keeps its own work: switching simply shows another one, nothing is lost.
    on(view, 'click', '[data-seg="book"] button', (e, b) => {
      if (+b.dataset.value === pick) return;
      pick = +b.dataset.value;
      f = work[pick];
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
    keep: () => o.stage === 'new' && !finished,
    hidden() { keys(false); },
    async revive() {
      const fresh = await api(`/api/orders/${rid}`);
      if (fresh.stage !== 'new') return false;
      keys(true);
      const step = $('#oc-print');
      if (step) step.outerHTML = String(printCard());
      renderFinish();
      return true;
    },
    // Nothing but a position to remember: such cards give way first when many are kept (keep.js).
    idle: () => !(work.some((w) => w.folder || w.busy || w.label) || sentOf(o.receiptId)),
    unmount() { work.forEach((w) => { dropCheck(w); w.seq++; }); offs.forEach((fn) => fn()); keys(false); },
  };
}
