// One order's card: its book and Canva template, all the buyer wrote, the Canva export dropped in and put in page
// order, a proof of the first spread and every page with the text check by the local model, then the hand-over to
// the Order Creator. Nothing is saved to disk; while an order is new, its card is kept in memory when the owner steps
// to another tab and comes back as it was left (keep.js). The queue — orders.js.
import {
  api, post, html, ic, ib, raw, esc, setHtml, on, media, toast, segHtml, syncSeg, setSeg, relTime, dateTime, copyText,
  openExternal, runJob, fadeImages, plural, confirmBox, patch, escBack, notFound, stickyFit, replaceKeyed, BOOKS,
} from '../lib.js';
import { openFolderViewer, pageNo } from '../folder-viewer.js';
import {
  STAGE_LABEL, providerName, planText, pagesText, addressFromEtsy, smoothWheel, trackChips, statusChip, receiptCopy,
  copyChip, restorable, alsoSentChip, pageVersion, proofHtml, filesBadge, checkNotices, fieldsHtml, addressHtml,
  etsyAddressLines, svcChip, bookImage,
} from '../order-bits.js';
import { receiveDrop, dropLabel, wireFolderDrop } from '../drop.js';
import { give } from '../handoff.js';
import { offerModule } from '../modules-ui.js';
import { pathHtml } from '../path.js';
import { mountHistory } from '../order-history.js';
import { sentOf, keptOrder, finish, linkOf } from '../keep.js';
import { gelatoResultHtml, runCountdown, resultAction, linkAlive } from './gelato-result.js';

// Text check (textcheck/): how its findings are counted and why a check was only the light one.
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

// ==================================================================== one order
export async function mountCard(view, rid) {
  let o;
  try { o = await api(`/api/orders/${rid}`); }
  catch (err) {
    notFound(view, { back: '#/orders', backLabel: 'До замовлень', icon: 'receipt', title: 'Замовлення не відкрилось', text: err.message });
    return null;
  }
  let pick = 0;        // which book of the order this pass is for (most orders hold one)
  // A printed order whose files are in the archive: the flow for a send by hand stays folded (2026-09-30).
  let manual = o.stage === 'new' || !(o.printed || []).length;
  let finished = false; // «Завершити»: this card is not kept when the owner leaves it
  // Every book of the order goes its own way — its own files, proof and text check — and they all leave
  // for the printer together, in one draft to one address (owner, 20.09.2026).
  // check: null (none yet / switched off) | {state:'run', percent, step} | {state:'done', result} | {state:'error', message}
  const blank = () => ({ folder: '', label: '', note: '', pages: 0, validation: null, busy: 0, error: '', check: null,
    chosen: null,        // printer picked by hand when the cover type could not be read
    decided: null,       // a hardcover's printer, as its files decided it (24 pages → Printify, 28/30 → Gelato)
    seq: 0, checkSeq: 0, // a flow whose number moved on is no longer this book's newest
    seen: { seq: -1, ids: new Set() }, // the findings already shown for the check number `seq` (markSeen())
    versions: {},        // page file -> how often it was replaced or put back: only its own pictures are fetched anew
    replaced: new Set(), // pages a new file was put over — they can be put back
    dismissed: new Set() }); // findings the owner marked «це не помилка» (kept for the card's life)
  const work = (o.items.length ? o.items : [{}]).map(blank);
  let f = work[pick];
  const showing = (w) => w === f;
  const item = () => o.items[pick] || {};
  const plan = (i = pick) => o.items[i]?.plan || {};
  // A hardcover's printer is decided by its files for now (owner, 25.09.2026 — Printify prints faulty books):
  // until they are in, the rule's printer is only the suggestion.
  const byFiles = (i = pick) => !!plan(i).choice;
  const providerOf = (i) => work[i].decided || plan(i).provider || work[i].chosen;
  const provider = () => providerOf(pick);
  // Printify takes 24 pages; Gelato as many as were downloaded (28 or 30) — known once the files are in (f.pages).
  const pageOptions = () => (plan().provider ? plan().pages : (o.pageOptions || {})[provider()]) || [];
  // «4100000001 - Emma»; two books for children of the same name are told apart by a number.
  const titleOf = (i) => {
    const name = o.items[i]?.childName || o.childName || '';
    const same = o.items.filter((x, j) => j < i && (x.childName || '') === (o.items[i]?.childName || ''));
    return (name ? `${o.receiptId} - ${name}` : String(o.receiptId)) + (same.length ? ` (${same.length + 1})` : '');
  };
  const pagesLabel = () => (f.pages ? String(f.pages) : pagesText(byFiles() ? plan().choice[provider()] : pageOptions()));

  // A printed order (2026-09-30): what went to print and the reprint, here — the order in one place. The files
  // below stay for a send made again by hand (files no longer in the archive).
  function printedHtml() {
    const last = (o.printed || [])[0];
    // Data and two quiet icon buttons — no sentence telling what to do: the path above and the status chip say where
    // the order is (2026-09-30).
    return html`<section class="card card-pad oc-printed">
      <span class="oc-printed-icon">${ic(o.stage === 'sent' ? 'truck' : o.stage === 'work' ? 'hourglass' : 'package')}</span>
      <div class="grow">${last ? html`<span class="faint">${dateTime(last.sentAt)}${last.pageCount ? ` · ${last.pageCount} стор.` : ''}${last.formatLabel ? ` · ${last.formatLabel}` : ''}${(o.printed || []).length > 1 ? ` · відправок: ${o.printed.length}` : ''}</span>`
          : html`<span class="faint">Файлів цієї відправки в архіві друку немає</span>`}</div>
      ${last ? ib('orderArchive', 'Що пішло в друк · передрук', `data-href="#/archive/${last.id}"`) : ''}
      ${last ? ib('upload', 'Покласти інші файли й надіслати ще раз', 'data-act="manual" id="oc-manual"') : ''}
    </section>`;
  }

  const atGelato = o.stage !== 'new' && o.provider === 'gelato';
  setHtml(view, html`
    <div class="page-head">
      <button class="back-link" data-act="back" aria-label="До замовлень" data-tip="До замовлень" data-kbd="Esc">${ic('arrowLeft')}</button>
      <span id="oc-finish"></span>
      <div class="grow">
        <div class="ord-title"><h1 class="page-title truncate">${o.name}</h1>${statusChip(o)}${alsoSentChip(o)}</div>
        <div class="page-sub ord-sub">${receiptCopy(o, 'mono')} · <span data-tip="${dateTime(o.createdAt)}">${relTime(o.createdAt)}</span> · ${STAGE_LABEL[o.stage] || ''}${trackChips(o)}</div>
      </div>
      <div id="oc-plan"></div>
    </div>
    <div class="ord-path-slot" id="oc-path"></div>
    <div id="oc-link"></div>
    ${o.stage !== 'new' ? printedHtml() : ''}
    <div class="ord-grid${atGelato ? ' ord-hist' : ''}">
      <div class="stack-l" id="oc-flow"></div>
      <div class="stack-l ord-side" id="oc-data"></div>
      ${atGelato ? html`<div class="ord-history" id="oc-history"></div>` : ''}
    </div>`);
  const $ = (s) => view.querySelector(s);
  // A placed Gelato order's history, asked for now that the card is open (never for the whole queue).
  const stopHistory = atGelato ? mountHistory($('#oc-history'), o) : () => {};

  // ---------------------------------------------------------------- header: where it is printed
  function renderPlan() {
    // A placed order shows where it really went — not where the printer rule would send it (a Gelato order said
    // «Printify · 24 стор.», 2026-09-30).
    if (o.stage !== 'new' && o.provider) {
      const sent = (o.printed || []).find((e) => e.provider === o.provider);
      setHtml($('#oc-plan'), svcChip(o.provider, { tip: `Замовлено в ${providerName(o.provider)}`, lg: true,
        text: `${providerName(o.provider)}${sent?.pageCount ? ` · ${sent.pageCount} стор.` : ''}` }));
      return;
    }
    const p = provider();
    const tip = f.decided ? `Файли вирішили: ${f.pages} стор. — ${providerName(p)}` : planText(plan());
    setHtml($('#oc-plan'), plan().provider
      ? svcChip(p, { tip, lg: true, text: `${providerName(p)} · ${pagesLabel()} стор.` })
      : html`<div class="row" style="gap:10px"><span class="faint" style="font-size: var(--fs)">Друкарня</span>${segHtml([
        { value: 'printify', icon: 'printify', tip: `Printify · ${pagesText(o.pageOptions?.printify)} стор.` },
        { value: 'gelato', icon: 'gelato', tip: `Gelato · ${pagesText(o.pageOptions?.gelato)} стор.` }], f.chosen, { name: 'provider' })}</div>`);
    requestAnimationFrame(() => syncSeg($('#oc-plan .seg')));
  }

  // ---------------------------------------------------------------- the order's path (2026-09-30)
  // Canva → Файли → Вичитка → Друк → Відправка for the book shown; a printed order has its first four behind it.
  function pathSteps() {
    const printed = o.stage !== 'new';
    const drafted = printed || !!sentOf(o.receiptId);
    const v = f.validation;
    const filesOk = !!(f.folder && v?.ok && !f.busy);
    const bad = !!(f.error || (v && !v.ok && !f.busy));
    const c = f.check;
    const errors = c?.state === 'done' ? countOf('error') + (alarmOf() ? 1 : 0) : 0;
    const proof = printed || drafted ? 'done' : !filesOk ? 'todo' : c?.state === 'run' ? 'part' : 'done';
    return [
      { key: 'canva', label: 'Canva', icon: 'canva', state: printed || f.folder || f.busy ? 'done' : 'todo',
        tip: item().book?.canvaUrl ? 'Canva: відкрити шаблон книги' : 'Canva: у паспорті книги немає посилання' },
      { key: 'files', label: 'Файли', icon: 'folderIn', state: printed || filesOk ? 'done' : f.busy ? 'part' : 'todo', nogo: bad,
        count: bad ? 'помилка' : f.busy ? `${Math.round(f.busy)}%` : filesOk ? `${f.pages} стор.` : '' },
      { key: 'proof', label: 'Вичитка', icon: 'textScan', state: proof, nogo: !printed && errors > 0,
        count: printed ? '' : c?.state === 'run' ? 'перевірка' : errors ? `${errors} ${plural(errors, LEVEL_WORDS.error)}` : c?.state === 'done' ? 'текст збігся' : '' },
      { key: 'print', label: 'Друк', icon: 'printer', state: printed ? 'done' : drafted ? 'part' : 'todo',
        count: printed ? providerName(o.provider) : drafted ? 'підтвердіть' : '',
        tip: drafted && !printed ? 'Чернетку створено — підтвердіть і оплатіть її в друкарні, потім «Оновити» в черзі' : 'Друк: чернетка в друкарні' },
      { key: 'ship', label: 'Відправка', icon: 'truck', state: o.stage === 'shipped' ? 'done' : printed ? 'part' : 'todo',
        count: o.stage === 'sent' ? 'позначте в Etsy' : o.stage === 'work' ? 'друкується' : '' },
    ];
  }
  const renderPath = () => setHtml($('#oc-path'), pathHtml(pathSteps(), { label: 'Шлях замовлення' }));
  function goStep(key) {
    const to = { files: '#oc-flow', proof: '#oc-proof', print: '#oc-print' }[key];
    if (key === 'canva') {
      if (item().book?.canvaUrl) openExternal(item().book.canvaUrl);
      else toast('У паспорті книги немає посилання на Canva', 'info');
    } else if (to && $(to)) $(to).scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // ---------------------------------------------------------------- right (stays in view): book, personalization, delivery
  function renderLeft() {
    const it = item();
    const b = it.book;
    setHtml($('#oc-data'), html`
      <section class="card card-pad ord-book">
        <div class="ord-book-art ${b?.lqip ? 'lqip' : ''}" ${b?.lqip ? raw(`style="background-image:url(${b.lqip})"`) : ''}>
          ${b?.image ? html`<img data-fade decoding="async" src="${bookImage(b, 360)}" alt="">` : ic('book')}</div>
        <div class="stack-s grow">
          ${b ? html`<a class="ord-book-title" href="#/book/${b.id}" data-tip="Паспорт книги">${b.title}</a>`
            : html`<b>Книги немає в бібліотеці</b><span class="faint mono" style="font-size: var(--fs-s)">лістинг #${it.listingId || '—'}</span>`}
          ${b?.canvaUrl ? html`<button class="btn ${f.folder || f.busy || (o.printed || []).length ? '' : 'btn-primary'}" data-act="canva">${ic('canva')}Відкрити шаблон у Canva</button>`
            : b ? html`<a class="btn" href="#/book/${b.id}">${ic('link')}Додати посилання на Canva</a>`
              : html`<a class="btn" href="#/books/shop">${ic('shelf')}До книг</a>`}
        </div>
      </section>
      <section class="card card-pad stack">
        <div class="row"><h3 class="card-title grow">Персоналізація</h3>
          ${o.items.length > 1 ? segHtml(o.items.map((x, i) => ({ value: String(i), label: `Книга ${i + 1}`, tip: x.title })), String(pick), { name: 'book' }) : ''}</div>
        ${fieldsHtml(it.variations)}
        ${o.buyerMessage ? html`<div class="ord-message"><span class="eyebrow">Повідомлення покупця</span><div>${o.buyerMessage}</div></div>` : ''}
      </section>
      <section class="card card-pad stack-s">
        <h3 class="card-title">Доставка</h3>
        ${addressHtml(etsyAddressLines(o.address))}
      </section>`);
    fadeImages($('#oc-data'));
    requestAnimationFrame(() => syncSeg($('#oc-data .seg')));
  }

  // ---------------------------------------------------------------- left: files → proof → print
  const thumb = (name, w) => media('/media/folder', { path: f.folder, file: name, w, ...pageVersion(f.versions, name) });
  // The newest send of this order to the chosen printer that never went to print (a cancelled order, a
  // deleted or unconfirmed draft): its archived files can be taken instead of downloading them again.
  const earlier = () => (o.earlierSends || []).find((e) => byFiles() || e.provider === provider());

  function filesCard() {
    const v = f.validation;
    const badge = filesBadge(v, { busy: f.busy, failed: !!f.error });
    const errors = f.error ? [f.error] : (v?.errors || []);
    return html`<section class="card card-pad stack" data-folder-drop>
      <div class="row"><span class="step-no">2</span><h3 class="card-title grow">Файли з Canva</h3>
        ${o.items.length > 1 ? segHtml(o.items.map((x, i) => ({ value: String(i), label: `Книга ${i + 1}`, tip: x.childName || x.title })), String(pick), { name: 'book' }) : ''}${badge}</div>
      <div class="input-group">
        <input class="input path-input" id="oc-folder" readonly value="${f.label}" title="${f.folder}" aria-label="Файли з Canva"
          placeholder="${provider() ? `ZIP або папка · обкладинка і ${pagesText(pageOptions())} ${plural(pageOptions().at(-1) || 0, ['сторінка', 'сторінки', 'сторінок'])}` : 'Спершу оберіть друкарню'}">
        ${ib('folderPick', 'Обрати папку', `data-act="browse" ${provider() ? '' : 'disabled'}`)}
      </div>
      ${!f.folder && !f.busy && earlier() ? html`<button class="btn btn-sm btn-ghost" style="align-self:flex-start" data-act="earlier"
        data-tip="Ці файли вже відправлялись ${dateTime(earlier().sentAt)}, але замовлення в друкарні не оформлене чи скасоване">${ic('orderArchive', 'icon-s')}Взяти файли минулої відправки · ${relTime(earlier().sentAt)}</button>` : ''}
      ${f.note && !f.busy ? html`<div class="row faint" style="font-size: var(--fs)">${ic('swap', 'icon-s')}<span>${f.note}</span></div>` : ''}
      ${f.busy ? '' : checkNotices(errors, v?.warnings)}
    </section>`;
  }

  function proofCard() {
    const it = item();
    const cover = f.validation.files.find((r) => r.position === 'cover') || {};
    return html`<section class="card card-pad stack-l" id="oc-proof">
      <div class="row"><span class="step-no">3</span><h3 class="card-title grow">Вичитка</h3><span class="row tc-head" id="oc-check-badge">${checkBadge()}</span></div>
      <div id="oc-check">${checkBody()}</div>
      ${proofHtml({ src: thumb, pages: f.pages, ratio: cover.width ? cover.width / cover.height : 1.9, name: it.childName,
        variations: it.variations, stripId: 'oc-strip', marks: true })}
    </section>`;
  }

  // ---------------------------------------------------------------- text check (the local model reads every page)
  // Starts by itself once the files are in; the proof stays usable meanwhile. Red — certain mistakes,
  // amber — worth a look; «це не помилка» hides a finding (a deliberate edit) for as long as the card lives.
  // While the check runs these are the findings it has already shared; the model is still on the rest.
  const openIssues = (w = f) => (w.check?.state === 'done' ? w.check.result.issues
    : w.check?.state === 'run' ? (w.check.partial?.issues || []) : []).filter((i) => !w.dismissed.has(i.id));
  const countOf = (level, w = f) => openIssues(w).filter((i) => i.level === level).length;
  // Most story pages unlike the book's passport: the pages of another book (the owner once laid out the order's
  // other book from its Canva template). One alarm instead of a row per page — a red banner nobody can miss.
  const alarmOf = (w = f) => openIssues(w).find((i) => i.kind === 'book');
  // A finding slides in once: one already shown for this check doesn't again — not when the check ends after showing
  // it while it ran, nor on a repaint (every row faded in a second time at the end, 26.09.2026).
  const isNew = (id, w = f) => w.seen.seq !== w.checkSeq || !w.seen.ids.has(id);
  function markSeen(w = f) {
    if (w.seen.seq !== w.checkSeq) w.seen = { seq: w.checkSeq, ids: new Set() };
    for (const i of openIssues(w)) w.seen.ids.add(i.id);
  }

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
      return html`<span class="v-badge run" data-tip="${c.step || 'Перевірка тексту…'}"><span class="spinner"></span>${ic('textScan')}<span class="num">${Math.round(c.percent)}%</span></span>`;
    }
    if (c.state === 'module') return html`<span class="v-badge" data-tip="Розумна вичитка — додатковий модуль, ще не встановлений">${ic('textScan')}Вичитка не встановлена</span>${ib('download', 'Встановити модуль «Розумна вичитка тексту» (≈ 9 ГБ) — тоді текст перевірятиметься сам', 'data-act="install-module"', { cls: 'sm' })}`;
    const again = ib('sync', 'Перевірити текст ще раз', 'data-act="recheck"', { cls: 'sm' });
    if (c.state === 'error') return html`<span class="v-badge" data-tip="${c.message}">${ic('textScan')}Текст не перевірено</span>`;
    const tip = checkTip(c.result);
    const errors = countOf('error'), warns = countOf('warn');
    if (alarmOf()) return html`<span class="v-badge bad" data-tip="${tip}">${ic('alertCircle')}Не та книга</span>${again}`;
    if (errors) return html`<span class="v-badge bad" data-tip="${tip}">${ic('textScan')}<span class="num">${errors}</span>${plural(errors, LEVEL_WORDS.error)}</span>${again}`;
    if (warns) return html`<span class="v-badge warn" data-tip="${tip}">${ic('textScan')}<span class="num">${warns}</span>${plural(warns, LEVEL_WORDS.warn)}</span>${again}`;
    return html`<span class="v-badge ok" data-tip="${tip}">${ic('textScan')}Текст збігається</span>${again}`;
  }

  const issueRow = (i) => html`<div class="tc-issue ${i.level} ${isNew(i.id) ? 'enter' : ''}" data-lb="${viewerIndex(i.page)}" role="button" tabindex="0" data-press>
      <span class="tc-where">${i.label}</span>
      <span class="tc-text">${quoteBold(i.text)}${i.note ? html`<span class="tc-note">${i.note}</span>` : ''}</span>
      ${ib('check', 'Це не помилка', `data-dismiss="${i.id}"`, { cls: 'sm' })}
    </div>`;

  function wrongBook(i) {
    const fresh = isNew(i.id); // it shakes once, not on every repaint of the list
    const cover = (b, what) => html`<figure class="tc-alarm-book">${b.image ? html`<img decoding="async" src="${bookImage(b, 160)}" alt="">` : ic('book')}
      <figcaption><span>${what}</span>${b.title}</figcaption></figure>`;
    const mine = item().book;
    return html`<div class="tc-alarm ${fresh ? 'enter' : ''}" data-lb="${viewerIndex(i.page)}" role="alert" tabindex="0" data-press>
      <div class="tc-alarm-head">${ic('alertCircle')}<span class="grow">Це не та книга!</span>
        <button class="btn btn-sm tc-alarm-dismiss" data-dismiss="${i.id}" data-tip="Сторінки правильні — прибрати попередження">Це та книга</button></div>
      <div>Сторінки не з книги, яку замовили: ${i.note}. Мабуть, у Canva відкрито шаблон іншої книги.</div>
      ${i.like && mine ? html`<div class="tc-alarm-books">${cover(mine, 'Замовлено')}${cover(i.like, 'А сторінки схожі на')}</div>` : ''}
    </div>`;
  }

  // The alarm first, then a row per finding.
  const findingsHtml = (list) => {
    const alarm = list.find((i) => i.kind === 'book'), rows = list.filter((i) => i.kind !== 'book');
    return html`${alarm ? wrongBook(alarm) : ''}${rows.length ? html`<div class="tc-list">${rows.map(issueRow)}</div>` : ''}`;
  };

  function checkBody() {
    const c = f.check;
    // The pages already checked are shown at once, without waiting for the rest of the book.
    if (c?.state === 'run') return findingsHtml(openIssues());
    if (c?.state === 'error') {
      return html`<div class="notice notice-warn">${ic('alert')}<div class="grow">Текст не перевірено: ${c.message}</div>${ib('sync', 'Перевірити ще раз', 'data-act="recheck"', { cls: 'sm' })}</div>`;
    }
    if (c?.state !== 'done') return '';
    const r = c.result;
    const light = r.mode === 'light' ? html`<div class="row faint tc-light">${ic('info', 'icon-s')}<span>${LIGHT_TIP[r.light]}${r.bookId && r.light === 'noTexts' ? html` · <a href="#/book/${r.bookId}">паспорт книги</a>` : ''}</span></div>` : '';
    const list = openIssues();
    const learn = learnable();
    return html`${findingsHtml(list)}${learn.length ? html`<div class="row tc-light faint">${ic('book', 'icon-s')}<span class="grow">Якщо в шаблоні Canva саме так — паспорт книги застарів</span>
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
    const w = f; // the book this passport is for: the tab may switch while the dialog is open
    const r = f.check.result, pages = learnable();
    const body = { bookId: r.bookId, child: r.child, pages: pages.map((p) => ({ key: p.learn, text: p.text })) };
    let texts;
    try { ({ texts } = await post('/api/textcheck/passport', { ...body, preview: true })); }
    catch (err) { toast(err.message, 'error'); return; }
    // What exactly the passport will keep: {Name} stands out, so a name caught inside a word would show.
    const shownText = (t) => html`${t.split(/(\{Name\})/).map((part) => part === '{Name}' ? html`<b class="tc-slot">{Name}</b>` : part)}`;
    const ok = await confirmBox({
      title: 'Оновити паспорт книги?', confirm: 'Оновити паспорт',
      text: `Тексти ${pages.length} ${plural(pages.length, ['сторінки', 'сторінок', 'сторінок'])} у паспорті книги стануть такими, як нижче: як у цьому друці, а ім'я дитини — знову {Name}.\n\nРобіть це, лише якщо ці сторінки в шаблоні Canva правильні — тоді наступні замовлення цієї книги звірятимуться вже з ними.`,
      extra: html`<div class="tc-passport">${pages.map((p) => html`<div class="tc-where">${p.label}</div><div class="tc-text">${shownText(texts[p.learn] || '')}</div>`)}</div>`,
    });
    if (!ok) return;
    try {
      await post('/api/textcheck/passport', body);
      toast('Паспорт книги оновлено', 'success');
      startCheck(w);
    } catch (err) { toast(err.message, 'error'); }
  }

  // Red / amber outline on the pages with findings: the big cover and page 1, and the strip.
  function markPages() {
    const worst = {};
    for (const i of openIssues()) for (const p of i.pages || [i.page]) if (worst[p] !== 'error') worst[p] = i.level;
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
    markSeen();
    markPages();
    renderPath();
  }

  // The check is no longer wanted (the card closes, other files, another book): the model stops on it.
  function dropCheck(w = f) {
    w.checkSeq++;
    const c = w.check;
    if (c?.state === 'run' && c.jobId) {
      post(`/api/orders/${o.receiptId}/textcheck/cancel`, { jobId: c.jobId }).catch(() => {});
    }
  }

  // «Це не помилка» also goes into that check's journal: the next calibration of what the check shows is then
  // made on the owner's own answers (25.09.2026).
  function keepMark(w, id) {
    const journal = w.check?.state === 'done' && w.check.result.journal;
    if (journal) post('/api/textcheck/mark', { journal, id }).catch(() => {});
  }

  // The model takes ~4 s to reach the graphics card (~70 s when it comes from disk): it is asked for while
  // the files are still being copied and checked, so the check right after them does not wait for it.
  // When Ollama is not running yet, it is started now (no console window): the owner is told, and told when it is ready.
  const warmModel = async () => {
    let r;
    try { r = await post('/api/textcheck/warm'); } catch { return; }
    if (!r?.starting) return;
    toast('Запускається Ollama… це кілька секунд', 'info', 5000);
    for (let i = 0; i < 40; i++) {
      await new Promise((ok) => setTimeout(ok, 1500));
      let s;
      try { s = await api('/api/textcheck/status'); } catch { return; }
      if (s.running) { toast('Ollama запущено', 'success', 3000); return; }
      if (!s.starting && i > 2) return;
    }
  };

  async function startCheck(w = f, at = w.seq) {
    const mine = ++w.checkSeq;
    const live = () => at === w.seq && mine === w.checkSeq;
    const paint = () => { if (showing(w)) paintCheck(); };
    w.check = { state: 'run', percent: 0, step: 'Перевірка тексту…' };
    paint();
    try {
      const start = await post(`/api/orders/${o.receiptId}/textcheck`, { folder: w.folder, pages: w.pages, pick: work.indexOf(w) });
      if (!live()) return;
      if (start.off) { w.check = start.module ? { state: 'module', module: start.module } : null; paint(); return; } // switched off in Settings, or its module is not installed
      w.check.jobId = start.jobId;
      const result = await runJob(Promise.resolve(start), (j) => {
        if (!live() || w.check?.state !== 'run') return;
        const had = openIssues(w).length;
        Object.assign(w.check, { percent: j.percent || 0, step: j.step || '', partial: j.partial || null });
        if (!showing(w)) return;
        const badge = view.querySelector('#oc-check-badge .v-badge.run');
        if (badge) { badge.querySelector('.num').textContent = `${Math.round(w.check.percent)}%`; badge.dataset.tip = w.check.step; }
        if (openIssues(w).length !== had) { setHtml($('#oc-check'), checkBody()); markSeen(w); markPages(); }
      }, 700, live);
      if (!live()) return;
      w.check = { state: 'done', result };
      for (const i of result.issues) if (w.dismissed.has(i.id)) keepMark(w, i.id); // marked while it still ran
    } catch (err) {
      if (!live()) return;
      w.check = { state: 'error', message: err.message };
    }
    paint();
  }

  // The viewer (folder-viewer.js) shows, with T, what the model read on a spread's pages and what they must say.
  function readings(w, items) {
    for (const p of w.check?.state === 'done' ? w.check.result.pages : []) {
      const item = items[viewerIndex(p.page)];
      if (!item || (!p.text && !p.expected)) continue;
      const block = [`${p.label} — надруковано:`, p.text || '—', ...(p.expected ? ['', 'Має бути:', p.expected] : [])].join('\n');
      item.text = item.text ? `${item.text}\n\n${block}` : block;
    }
  }

  // Once the Order Creator has made the draft for this order, the step says so instead of offering
  // «До друку» again (the order stays in «Нові» until the next sync finds it at the printer).
  function printCard() {
    const p = provider();
    const done = sentOf(o.receiptId);
    const result = keptOrder('#/creator') === String(o.receiptId);
    // A Gelato draft's green card stays here, whole, while the temporary link to its files lives (owner, 01.10.2026).
    const shown = done?.result || linkOf(o.receiptId);          // a finished order keeps its link here while it lives
    const live = shown && linkAlive(shown) ? shown : null;
    const ready = readyBooks(p);
    // An order of several books: which of them this send takes, and what each one still waits for.
    const list = work.length > 1 ? html`<ul class="oc-books">${work.map((w, i) => {
      const its = ready.some((r) => r.i === i);
      const why = its ? 'готова' : !providerOf(i) ? 'не обрано друкарню' : providerOf(i) !== p ? `друкується в ${providerName(providerOf(i))}`
        : w.busy ? 'перевіряються файли' : w.folder ? 'файли не пройшли перевірку' : 'немає файлів';
      return html`<li class="${its ? 'is-ready' : 'faint'}">${ic(its ? 'check' : 'clock', 'icon-s')}<span class="grow truncate">Книга ${i + 1}${o.items[i]?.childName ? ` · ${o.items[i].childName}` : ''}</span><span>${why}</span></li>`;
    })}</ul>` : '';
    return html`<section class="card card-pad stack ${p === 'printify' ? 'tint-printify' : ''}" id="oc-print">
      <div class="row"><span class="step-no">4</span><h3 class="card-title grow">Друк</h3></div>
      ${list}
      ${live ? html`${gelatoResultHtml(live)}<div class="row" style="justify-content:flex-end">${ib('send', 'Надіслати ще раз', 'data-act="print"')}</div>`
    : done ? html`<div class="notice notice-success">${ic('checkCircle')}<div class="grow">${done.what}</div></div>
        <div class="row">${result ? html`<button class="btn btn-primary grow" data-act="to-creator">${ic('printer', 'icon-s')}Результат в Order Creator</button>` : ''}
          ${ib('send', 'Надіслати ще раз', 'data-act="print"')}</div>`
    : html`<button class="btn btn-xl btn-primary btn-block" data-act="print">${ic('send', 'icon-l')}До друку в ${providerName(p)}${ready.length > 1 ? html` · <span class="num">${ready.length}</span> ${plural(ready.length, BOOKS)}` : ''}</button>`}
    </section>`;
  }

  // The cross beside the back arrow appears once the draft is made: «робота над цим замовленням
  // завершена» — the card and the Order Creator let go of it and the queue opens (owner, 20.09.2026).
  function renderFinish() {
    setHtml($('#oc-finish'), sentOf(o.receiptId)
      ? ib('checkCircle', 'Завершити роботу над замовленням', 'data-act="finish"', { cls: 'sm' }) : '');
  }

  // The temporary link to this order's files for Gelato (a Cloudflare tunnel) is still open: said here, at the top, whatever the step —
  // also after «Завершити» and when the card is opened again (the server knows: `links`, from the archive's sends and the open
  // tunnels; the owner, 04.10.2026 — Gelato may still be fetching the PDFs). The print step's own green card, when it is on screen, says it too.
  let stopPlaque = () => {};
  let plaqueR = null;                                  // the one countdown of this link: a redraw must not start it over
  function renderLink() {
    stopPlaque();
    const slot = $('#oc-link');
    const link = (o.links || [])[0];
    if (!slot) return;
    if (!link || $('#oc-print .result-card')) { setHtml(slot, ''); return; }
    if (!plaqueR || plaqueR.orderId !== link.orderId) plaqueR = { orderId: link.orderId, keepAliveSeconds: link.secondsLeft };
    setHtml(slot, html`<div class="notice notice-success">${ic('link')}<div class="grow">Тимчасове посилання на файли для Gelato ще працює —
      <b class="num" data-countdown>--:--</b>. Gelato забирає файли сам, зазвичай за хвилину.</div>
      ${ib('unlink', 'Файли забрано — закрити посилання', 'data-act="link-close"', { cls: 'sm' })}</div>`);
    stopPlaque = runCountdown(slot, plaqueR, () => { o.links = []; setHtml(slot, ''); });
  }

  // The flow is redrawn in place (patch()): a card whose markup didn't change stays, and a changed one keeps every
  // picture it already showed — after a replaced page only that page loads, and the strip stays where it was (the
  // whole flow was redrawn, every picture faded in again and the strip jumped back to the first spread, 26.09.2026).
  // The green card's countdown; when the link closes, the step shows the short «created» line again.
  let stopLink = () => {};
  function linkTimer() {
    stopLink();
    const card = $('#oc-print .result-card'), r = sentOf(o.receiptId)?.result || linkOf(o.receiptId);
    if (card && r) stopLink = runCountdown(card, r, redrawPrint);
  }
  function redrawPrint() {
    const step = $('#oc-print');
    if (step) replaceKeyed(step, printCard()); // keeps its key: the next patch() does not make the print card again
    linkTimer();
  }

  function renderRight() {
    const ready = !!(f.folder && f.validation?.ok && !f.busy);
    renderFinish();
    renderPath();
    const scrolled = $('#oc-strip')?.scrollLeft || 0;
    view.querySelector('.ord-grid').classList.toggle('ord-solo', !manual); // a printed order: its data alone
    patch($('#oc-flow'), manual ? [['files', filesCard()], ...(ready ? [['proof', proofCard()], ['print', printCard()]] : [])] : []);
    fadeImages($('#oc-flow'));
    linkTimer();
    renderLink();
    requestAnimationFrame(() => syncSeg($('#oc-flow .seg')));
    if ($('#oc-check')) markSeen();
    const strip = $('#oc-strip');
    if (strip) {
      strip.scrollLeft = scrolled;
      if (!strip.dataset.wheel) { smoothWheel(strip); strip.dataset.wheel = '1'; }
    }
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
    const res = await post(`/api/orders/${o.receiptId}/files`, { folder: path, provider: byFiles(i) ? 'files' : providerOf(i), format: plan(i).format || null });
    if (my !== w.seq) return;
    Object.assign(w, { folder: res.path, note: res.note, pages: res.pageCount, decided: byFiles(i) ? res.provider : null });
    if (showing(w)) renderPlan();
    const v = await runJob(post('/api/creator/validate', { mode: providerOf(i), folder: w.folder }),
      (j) => { if (my === w.seq && showing(w)) setBusy(60 + (j.percent || 0) * 0.4); }, 300, () => my === w.seq);
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
    Object.assign(w, { busy: 0, error: err.message, validation: null, pages: 0, decided: null });
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
      decided: null, versions: {}, replaced: new Set(), dismissed: new Set() });
    renderPlan(); renderRight();
    try {
      const path = await receiveDrop(dropped, (pct) => { if (my === w.seq && showing(w)) setBusy(pct * 0.6); });
      if (my === w.seq) await arrange(path, w, my);
    } catch (err) { failed(w, my, err); }
  }

  async function takeFolder() {
    let path;
    warmModel();
    try { path = (await post('/api/creator/pick-folder', { title: `Оберіть папку з обкладинкою і ${pagesText(pageOptions())} сторінками` })).path; }
    catch (err) { toast(err.message, 'error'); return; }
    if (!path) return;
    const w = f;
    dropCheck(w);
    const my = ++w.seq;
    Object.assign(w, { folder: '', label: path.split(/[\\/]/).pop(), note: '', pages: 0, validation: null, busy: 1, error: '', check: null,
      decided: null, versions: {}, replaced: new Set(), dismissed: new Set() });
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
      decided: null, versions: {}, replaced: new Set(), dismissed: new Set() });
    renderPlan(); renderRight();
    try {
      const { path } = await post(`/api/archive/${e.id}/reuse`, {});
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

  /** The viewer of the shown book's folder; a page replaced or put back there is checked again. */
  function openViewer(start) {
    const w = f;
    openFolderViewer(w, start, {
      total: w.pages, label: w.label,
      sent: () => !!(sentOf(o.receiptId) || o.atPrinter),
      again: 'надіслати замовлення ще раз?',
      decorate: (items) => readings(w, items),
      changed: (file) => pageChanged(w, file),
    });
  }

  /** After a page changed: files checked again, text checked again — and the «це не помилка» marks of that page
   *  forgotten, because it is a different page now. */
  function pageChanged(w, file) {
    for (const i of w.check?.state === 'done' ? w.check.result.issues : []) {
      if (i.page === pageNo(file)) w.dismissed.delete(i.id);
    }
    revalidate(w);
  }

  /** The same checks as after new files, but the folder stays as it is (only one page changed). The
   *  proof is not taken down while they run — it is redrawn once, when the new page is in it. */
  async function revalidate(w) {
    warmModel(); // the re-check after a fixed page starts at once, the model loaded meanwhile
    dropCheck(w);
    const my = ++w.seq;
    w.error = '';
    try {
      const v = await runJob(post('/api/creator/validate', { mode: providerOf(work.indexOf(w)), folder: w.folder }),
        null, 300, () => my === w.seq); // other files or the card closed (w.seq moves on): the poll stops
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
    const wrong = ready.filter(({ w }) => w.check && alarmOf(w));
    const errors = wrong.length ? 0 : ready.reduce((n, { w }) => n + (w.check?.state === 'done' ? countOf('error', w) : 0), 0);
    const checking = ready.some(({ w }) => w.check?.state === 'run');
    // One review before the send instead of up to four questions in a row (2026-09-30): everything the program noticed, in
    // one place, most serious first; nothing is asked when nothing was noticed.
    const notes = [
      wrong.length && `${work.length > 1 ? `Книга ${wrong.map(({ i }) => i + 1).join(', ')}: с` : 'С'}торінки не схожі на тексти книги, яку замовили — мабуть, у Canva відкрито шаблон іншої книги. Перевірте, що саме замовив покупець.`,
      errors && `Перевірка знайшла ${errors} ${plural(errors, LEVEL_WORDS.error)} у тексті сторінок.`,
      checking && 'Текст ще перевіряється — відправлю, не дочекавшись.',
      left && `Готов${ready.length > 1 ? 'і' : 'а'} ${ready.length} з ${work.length} книг: піде лише ${ready.length > 1 ? 'вони' : 'вона'}, решту можна надіслати пізніше окремим замовленням.`,
    ].filter(Boolean);
    const serious = !!(wrong.length || errors);
    if (notes.length && !(await confirmBox({
      title: wrong.length ? 'Це не та книга!' : serious ? 'У тексті є помилки' : 'Перед друком',
      text: notes.join('\n\n'), danger: serious, cancel: checking && !serious && !left ? 'Зачекати' : 'Повернутись',
      confirm: serious ? 'Все одно до друку' : left ? 'Відправити готові' : 'До друку' }))) return;
    const books = ready.map(({ w, i }) => ({ folder: w.folder, label: w.label, title: titleOf(i), format: (p === 'gelato' && plan(i).format) || null }));
    give('creator', {
      receiptId: String(o.receiptId), // the Order Creator keeps its work (and result) for this order
      buyer: o.name,                  // its head: the order it prints (2026-09-30)
      mode: p, books, address: addressFromEtsy(o),
    });
    location.hash = '#/creator';
  }

  // ---------------------------------------------------------------- events
  const stopFit = stickyFit(view.querySelector('#oc-data'));
  const offs = [
    on(view, 'click', '[data-act]', async (e, t) => {
      const a = t.dataset.act;
      if (a === 'link-close') {
        try { await post('/api/creator/gelato/close-tunnel', { orderId: o.links?.[0]?.orderId }); }
        catch (er) { toast(`Посилання не закрилося: ${er.message}`, 'error'); return; }
        stopPlaque(); o.links = []; setHtml($('#oc-link'), '');
        toast('Посилання закрито', 'success', 2200);
        return;
      }
      const sent = sentOf(o.receiptId)?.result || linkOf(o.receiptId);
      if (sent && t.closest('.result-card') && await resultAction(a, sent, t)) { if (a === 'close-tunnel') redrawPrint(); return; }
      if (a === 'back') location.hash = '#/orders';
      else if (a === 'finish') { finished = true; finish(o.receiptId); toast('Роботу над замовленням завершено', 'success'); location.hash = '#/orders'; }
      else if (a === 'canva') openExternal(item().book?.canvaUrl);
      else if (a === 'browse') takeFolder();
      else if (a === 'earlier') takeEarlier();
      else if (a === 'print') print();
      else if (a === 'to-creator') location.hash = '#/creator';
      else if (a === 'copy-text') copyChip(e, t);
      else if (a === 'recheck') startCheck();
      else if (a === 'install-module') offerModule('textcheck').then((ok) => { if (ok) startCheck(); });
      else if (a === 'path') goStep(t.dataset.step);
      else if (a === 'manual') { manual = true; t.remove(); renderRight(); $('#oc-flow')?.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
      else if (a === 'learn') learnPassport();
    }),
    on(view, 'click', '[data-href]', (e, b) => { location.hash = b.dataset.href; }),
    on(view, 'click', '[data-copy]', (e, b) => copyText(item().variations?.[+b.dataset.copy]?.value || '', 'Скопійовано')),
    on(view, 'click', '[data-dismiss]', (e, b) => { f.dismissed.add(b.dataset.dismiss); keepMark(f, b.dataset.dismiss); paintCheck(); }),
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

  const listenEsc = escBack('#/orders'); // Esc steps back to the queue (not named esc: that is the HTML escape imported above)

  renderPlan(); renderLeft(); renderRight();
  // A new order's card is kept when the owner steps to another tab (keep.js): hidden, it lets go of Esc;
  // brought back, it first asks whether the order is still new, then shows a draft made meanwhile.
  return {
    receiptId: String(o.receiptId),
    keep: () => o.stage === 'new' && !finished,
    hidden() { listenEsc(false); stopLink(); stopPlaque(); },
    async revive() {
      const fresh = await api(`/api/orders/${rid}`);
      if (fresh.stage !== 'new') return false;
      listenEsc(true);
      o.links = fresh.links || [];
      redrawPrint();
      renderLink();
      renderFinish();
      renderPath();
      return true;
    },
    // Nothing but a position to remember: such cards give way first when many are kept (keep.js).
    idle: () => !(work.some((w) => w.folder || w.busy || w.label) || sentOf(o.receiptId)),
    unmount() { work.forEach((w) => { dropCheck(w); w.seq++; }); offs.forEach((fn) => fn()); stopHistory(); stopFit(); listenEsc(false); stopLink(); stopPlaque(); },
  };
}
