// Pieces shared by the order pipeline page, the order archive and the Order Creator: order stages,
// countries, the printer's status and tracking chips, the buyer's fields, the Etsy → Gelato address
// mapping, the sync, dropped folders/ZIPs and the page viewer of a print folder.
import { api, post, runJob, media, html, raw, ic, ib, copyText, syncSeg } from './lib.js';

export const COUNTRIES = [
  ['US', 'США'], ['CA', 'Канада'], ['GB', 'Велика Британія'], ['AU', 'Австралія'], ['NZ', 'Нова Зеландія'], ['IE', 'Ірландія'],
  ['DE', 'Німеччина'], ['FR', 'Франція'], ['IT', 'Італія'], ['ES', 'Іспанія'], ['PT', 'Португалія'], ['NL', 'Нідерланди'],
  ['BE', 'Бельгія'], ['LU', 'Люксембург'], ['AT', 'Австрія'], ['CH', 'Швейцарія'], ['PL', 'Польща'], ['CZ', 'Чехія'],
  ['SK', 'Словаччина'], ['HU', 'Угорщина'], ['RO', 'Румунія'], ['BG', 'Болгарія'], ['GR', 'Греція'], ['HR', 'Хорватія'],
  ['SI', 'Словенія'], ['DK', 'Данія'], ['SE', 'Швеція'], ['NO', 'Норвегія'], ['FI', 'Фінляндія'], ['EE', 'Естонія'],
  ['LV', 'Латвія'], ['LT', 'Литва'], ['UA', 'Україна'], ['IL', 'Ізраїль'], ['AE', 'ОАЕ'], ['SG', 'Сінгапур'],
  ['JP', 'Японія'], ['KR', 'Південна Корея'], ['MX', 'Мексика'], ['BR', 'Бразилія'], ['ZA', 'ПАР'],
];
export const countryName = (code) => COUNTRIES.find(([c]) => c === String(code || '').toUpperCase())?.[1] || code || '';

// Etsy keeps the seller's own "In Production" tab out of its API, so an order counts as in work
// once Printify or Gelato has a print order carrying its receipt number, and as sent once the printer
// has shipped it but Etsy is not told yet (all decided on the server).
// The queue's tabs in words (2026-09-30): the truck tab is the owner's to-do — "mark it shipped on Etsy" — and says so.
export const STAGES = [
  { value: 'new', icon: 'sparkle', label: 'Нові', tip: 'Нові — книгу ще не замовлено в друкарні' },
  { value: 'work', icon: 'hourglass', label: 'Друкуються', tip: 'Друкуються — книгу замовлено в друкарні' },
  { value: 'sent', icon: 'truck', label: 'Позначити в Etsy', tip: 'Позначити в Etsy — друкарня відправила, позначте замовлення відправленим в Etsy' },
  { value: 'shipped', icon: 'package', label: 'Відправлені', tip: 'Відправлені — позначені відправленими в Etsy' },
];
export const STAGE_EMPTY = {
  new: ['sparkle', 'Нових замовлень немає', 'Для всіх оплачених замовлень книгу вже замовлено в Printify або Gelato.'],
  work: ['hourglass', 'Зараз нічого не друкується', 'Тут будуть замовлення, для яких книгу вже замовлено в Printify або Gelato.'],
  sent: ['truck', 'Нічого не чекає позначки в Etsy', 'Тут з\'являться замовлення, які Printify або Gelato вже відправили, — поки ви не позначите їх відправленими в Etsy.'],
  shipped: ['package', 'Відправлених ще немає', ''],
};
export const STAGE_LABEL = { new: 'нове', work: 'друкується', sent: 'друкарня відправила', shipped: 'відправлено' };

export const providerName = (p) => (p === 'gelato' ? 'Gelato' : 'Printify');
export const variationsOf = (o) => (o.items || []).flatMap((i) => i.variations || []);
export const matchesOrder = (o, t) => !t || (o.name || '').toLowerCase().includes(t) || o.receiptId.includes(t);

// Printer statuses by what they mean for the owner: trouble first (drafts and "on-hold" are the normal
// start, not a problem), then on its way, then not started yet; anything else is being made.
const STATUS_TONE = [
  [/issue|fail|return|unfulfillable|payment-not|declined|cancel/i, 'chip-amber'],
  [/fulfilled|shipped|transit|delivered/i, 'chip-green'],
  [/draft|hold|pending|created|uploading|approval/i, ''],
];
const statusTone = (s) => (STATUS_TONE.find(([re]) => re.test(s)) || [0, 'chip-accent'])[1];
/** "in_transit" / "has-issues" → "In transit" / "Has issues": the printer's word, kept in English, written for people. */
const statusText = (s) => String(s).replace(/[-_]+/g, ' ').trim().replace(/^./, (c) => c.toUpperCase());

/** Tracking numbers in the printer's colour, after its chip: carrier | number (one text line, so both sit
 * on the same baseline). A click on the carrier copies the carrier, anywhere else — the number (the owner,
 * 25.09.2026: he pastes them into Etsy's two fields). o: { provider, tracking }. */
const NUMBER_COPY = 'data-act="copy-text" data-done="Трек-номер скопійовано" data-tip="Копіювати трек-номер"';
export const trackChips = (o) => (o.tracking || []).map((t) => html`<span class="chip svc-${o.provider} ord-track ord-copy" role="button" tabindex="0" data-press
    ${raw(NUMBER_COPY)} data-text="${t.number}">${ic('truck', 'icon-s')}<span class="ord-track-text">${t.carrier
      ? html`<span class="ord-carrier" role="button" tabindex="0" data-press data-act="copy-text" data-text="${t.carrier}" data-done="Перевізника скопійовано" data-tip="Копіювати перевізника">${t.carrier}</span><span class="ord-track-sep"></span>` : ''}<span class="ord-track-no" ${raw(NUMBER_COPY)} data-text="${t.number}">${t.number}</span></span></span>`);

/** The printer's status (its own word, in English, as the owner asked); nothing before the book is ordered. */
export const statusChip = (o) => (o.printStatus
  ? html`<span class="chip ${statusTone(o.printStatus)}" data-tip="Статус у ${providerName(o.provider)}"><span class="dot"></span>${statusText(o.printStatus)}</span>`
  : '');

/** The stage tabs' counts for a search — the queue and the Order Creator's «Замовлення Etsy» list the same orders. */
export function countStages(seg, orders, term) {
  seg.querySelectorAll('button[data-value]').forEach((b) => {
    const n = orders.filter((o) => o.stage === b.dataset.value && matchesOrder(o, term)).length;
    b.querySelector('.seg-count').textContent = n;
    b.classList.toggle('has', n > 0 && b.dataset.value === 'sent'); // the owner's to-do: its count takes the ink
  });
  syncSeg(seg);
}

/** What an order list says when its tab shows nothing: the orders still loading, nothing found, or the stage's own
 *  words. `cls` — `empty-sm` in a dialog. */
export function emptyOrders(orders, term, stage, syncing, cls = '') {
  if (!orders.length && syncing) return html`<div class="empty ${cls}"><div class="empty-icon"><span class="spinner"></span></div><p>Завантаження замовлень з Etsy…</p></div>`;
  if (term) return html`<div class="empty ${cls}">Нічого не знайдено</div>`;
  const [icon, title, text] = STAGE_EMPTY[stage];
  return html`<div class="empty ${cls}"><div class="empty-icon">${ic(icon)}</div><h3>${title}</h3>${text ? html`<p>${text}</p>` : ''}</div>`;
}

/** A library book's picture at `w` px — the queue's row and the card's book. */
export const bookImage = (b, w) => media(`/media/book/${b.id}/${b.image}`, { w });

/** The printer's chip in its colour: `text` beside its logo, `tip` on hover, `lg` — the card's larger one. */
export const svcChip = (p, { tip = '', text = providerName(p), lg = false } = {}) => html`<span class="chip ${lg ? 'chip-lg ' : ''}svc-${p}"${
  tip ? html` data-tip="${tip}"` : ''}>${ic(p, 'icon-s')}${lg ? html`<span>${text}</span>` : text}</span>`;

/** A book's file check as a badge: running (`busy` — the percent; `id` lets the progress land on it), passed, or
 *  failed (`failed` — an error before any check result). The order card and the Order Creator show the same one. */
export function filesBadge(v, { busy = 0, failed = false, id = '' } = {}) {
  if (busy) return html`<span class="v-badge run"${id ? html` id="${id}"` : ''}><span class="spinner"></span><span class="num">${Math.round(busy)}%</span></span>`;
  if (v?.ok) return html`<span class="v-badge ok" data-tip="Усі PNG повністю прочитано й перевірено">${ic('check')}<span class="num">${v.found}/${v.expected}</span></span>`;
  return failed || v ? html`<span class="v-badge bad">${ic('x')}Є проблеми</span>` : '';
}

/** What a file check found: the first dozen errors (under `title`, if given) and every warning. */
export function checkNotices(errors = [], warnings = [], title = '') {
  return html`${errors.length ? html`<div class="notice notice-error">${ic('alertCircle')}<div>${title ? html`<b>${title}</b>` : ''}<ul>${
    errors.slice(0, 12).map((e) => html`<li>${e}</li>`)}</ul>${errors.length > 12 ? html`<div>…та ще ${errors.length - 12}</div>` : ''}</div></div>` : ''}
    ${warnings.length ? html`<div class="notice notice-warn">${ic('alert')}<div>${warnings.map((w) => html`<div>${w}</div>`)}</div></div>` : ''}`;
}

/** What the buyer filled in, each value with its copy button (`data-copy` = its index; the page copies it) — the
 *  order card and the archive. */
export const fieldsHtml = (vars = []) => (vars.length ? html`<dl class="ord-fields">${vars.map((v, i) => html`
    <dt>${v.name}${isCustomText(v) ? html`<span class="chip chip-amber">свій текст</span>` : ''}</dt>
    <dd class="${isCustomText(v) ? 'custom' : ''} ${isNameField(v) ? 'is-name' : ''}"><span>${v.value}</span>${isFormatField(v) ? '' : ib('copy', 'Копіювати', `data-copy="${i}"`, { cls: 'sm' })}</dd>`)}</dl>`
  : html`<div class="faint">Покупець нічого не вказав.</div>`);

/** The lines of an Etsy address, and any address's lines as the card shows them. */
export const etsyAddressLines = (a = {}) => [a.name, a.first_line, a.second_line, [a.city, a.state, a.zip].filter(Boolean).join(', '),
  countryName(a.country_iso)];
export const addressHtml = (lines) => html`<div class="ord-address">${lines.filter(Boolean).map((line) => html`<div>${line}</div>`)}</div>`;

/** The proof of a book's print files — the cover, the first spread with what the buyer wrote beside page 1, a strip
 *  of every spread: the order card's «Вичитка» (named «Звірка» until 30.09.2026) and the archive's «Що пішло в друк» (written in both until 27.09.2026).
 *  `src(file, side)` — a picture's address; `marks` tags each page (`data-page`) for the text check's findings. */
export const STRIP_THUMB = 360; // the strip's previews: the side the file check makes them at (images.VIEW_SIDES)
export function proofHtml({ src, pages, ratio, name, variations, stripId, marks = false }) {
  const at = (n) => (marks ? html` data-page="${n}"` : '');
  const half = (n) => (n === null ? html`<div class="half blank"></div>`
    : html`<div class="half"${at(n)}><img data-fade loading="lazy" decoding="async" src="${src(`${n}.png`, STRIP_THUMB)}" alt=""></div>`);
  const notes = (variations || []).filter((v) => !isNameField(v) && !isFormatField(v)); // only what the page itself says
  return html`<div class="proof">
      <div class="structure-cover" data-lb="0"${at(0)} role="button" tabindex="0" data-press aria-label="Відкрити обкладинку" style="aspect-ratio:${ratio}">
        <img data-fade decoding="async" src="${src('Cover.png', 1400)}" alt="Обкладинка"><div class="gutter"></div><i class="crops"></i>
      </div>
      <div class="spread-view proof-spread" data-lb="1" role="button" tabindex="0" data-press aria-label="Відкрити першу сторінку">
        <div class="half proof-note">
          ${name ? html`<div class="proof-name">${name}</div>` : ''}
          <dl>${notes.map((v) => html`<dt>${v.name}</dt><dd>${v.value}</dd>`)}</dl>
        </div>
        <div class="half"${at(1)}><img data-fade decoding="async" src="${src('1.png', 1400)}" alt="Сторінка 1"></div>
        <div class="gutter-s"></div><i class="crops"></i>
      </div>
    </div>
    <div class="strip" id="${stripId}">
      <div class="strip-item" data-lb="0" role="button" tabindex="0" data-press aria-label="Відкрити обкладинку" style="width:${Math.round(110 * ratio)}px">
        <div class="structure-cover"${at(0)} style="height:110px"><img data-fade loading="lazy" decoding="async" src="${src('Cover.png', STRIP_THUMB)}" alt=""></div>
        <span class="strip-no">обкладинка</span></div>
      ${spreadsOf(pages).map((sp, i) => html`<div class="strip-item" data-lb="${i + 1}" role="button" tabindex="0" data-press aria-label="Відкрити розворот ${[sp.left, sp.right].filter(Boolean).join('–')}">
        <div class="spread-view">${half(sp.left)}${half(sp.right)}<div class="gutter-s"></div></div>
        <span class="strip-no num">${[sp.left, sp.right].filter(Boolean).join('–')}</span></div>`)}
    </div>`;
}

/** Books of this order sent in another go, or to the other printer: the status chip beside it describes
 *  only the first print order, so this says how many more there are. o: { alsoSent }. */
export const alsoSentChip = (o) => {
  const more = o.alsoSent || [];
  if (!more.length) return '';
  const where = [...new Set(more.map((m) => providerName(m.provider)))].join(' і ');
  return html`<span class="chip" data-tip="Ще ${more.length === 1 ? 'одне замовлення друку' : `${more.length} замовлення друку`} цього чека — у ${where}">+${more.length} у друці</span>`;
};

/** The receipt number without "#": a click copies it (in the queue, the card header and the archive). */
export const receiptCopy = (o, cls) => html`<span class="${cls} ord-copy" role="button" tabindex="0" data-press data-act="copy-text" data-text="${o.receiptId}"
    data-done="Номер замовлення скопійовано" data-tip="Копіювати номер замовлення">#${o.receiptId}</span>`;

/** Receipt and tracking numbers may sit inside a row link: copy without opening it. */
export function copyChip(e, el) {
  e.preventDefault();
  e.stopPropagation();
  copyText(el.dataset.text, el.dataset.done);
}

// The receipt number in front of a title "4100000001 - Emma", and the child's name after it ('' without a
// number) — read the same way as the server's archive.receipt_of / child_of. A send names its receipt itself.
const TITLE_RE = /^\s*(\d{6,20})\s*-\s*([\s\S]*)$/;
export const receiptOfTitle = (title) => /^\s*(\d{6,20})(?!\d)/.exec(title || '')?.[1] || '';
export const childOf = (title) => (TITLE_RE.exec(title || '')?.[2] || '').trim();

// The buyer's fields: a dedication of their own, the child's name, and the cover format (which only
// decides the printer — it is never typed into Canva, so it gets no copy button).
// «свій текст»: decided by the server (wording.custom_text), the same rule the text check uses.
export const isCustomText = (v) => !!v.custom;
export const isNameField = (v) => !!v.isName; // the field the child's name came from (orders.enrich)
export const isFormatField = (v) => /cover|size|format|binding|обкладинк|розмір/i.test(v.name || '')
  || /hard\s?cover|soft\s?cover|hardback|paperback/i.test(v.value || '');

/** [28, 30] → "28 або 30", [24, 28, 30] → "24, 28 або 30": the book lengths a printer takes (Gelato: as many pages as were downloaded). */
export const pagesText = (options) => {
  const list = [].concat(options || []);
  return list.length > 1 ? `${list.slice(0, -1).join(', ')} або ${list.at(-1)}` : list.join('');
};

/** "Hardcover · США → Printify · 24 стор." — why this printer was chosen. A hardcover's printer is decided
 *  by its files for now (owner, 25.09.2026): the rule's one is only the suggestion. */
export function planText(plan) {
  if (!plan?.provider) return 'Тип обкладинки не вдалося визначити — оберіть друкарню';
  // From 1 October only Gelato prints: a book of an unknown cover type goes there too, its format picked in the Order Creator.
  if (!plan.binding) return `Тип обкладинки не визначено → ${providerName(plan.provider)} · ${pagesText(plan.pages)} стор. Формат — в Order Creator`;
  const binding = plan.binding === 'hardcover' ? 'Hardcover' : 'Softcover';
  if (plan.choice) {
    return `${binding} · ${countryName(plan.country)} → зазвичай ${providerName(plan.provider)}. Друкарню визначать файли: `
      + `${pagesText(plan.choice.printify)} стор. — Printify, ${pagesText(plan.choice.gelato)} — Gelato`;
  }
  return `${binding} · ${countryName(plan.country)} → ${providerName(plan.provider)} · ${pagesText(plan.pages)} стор.`;
}

/** Etsy shipping address → the Order Creator's Gelato address fields. */
export function addressFromEtsy(o) {
  const a = o.address || {};
  const parts = (a.name || o.name || '').trim().split(/\s+/);
  return {
    firstName: parts[0] || '', lastName: parts.slice(1).join(' ') || '',
    addressLine1: a.first_line || '', addressLine2: a.second_line || '', city: a.city || '',
    state: a.state || '', postCode: a.zip || '', country: (a.country_iso || '').toUpperCase(),
  };
}

// Orders are pulled from Etsy, Printify and Gelato only twice over: once when the program starts
// (on the server) and whenever the refresh button is pressed. Pages never start a sync on their own.

/** Pulls the latest orders now (the refresh button; a few seconds). */
async function syncOrders(onStep) {
  await runJob(post('/api/profit/sync', {}), (j) => { if (j.step) onStep?.(j.step); });
}

/** The sync already running (usually the start-up one): its job id, or null. */
async function runningSync() {
  try { return (await api('/api/profit/sync')).jobId || null; } catch { return null; }
}

/** Waits for a running sync to end, reporting its steps. */
async function watchSync(jobId, onStep) {
  await runJob(Promise.resolve({ jobId }), (j) => { if (j.step) onStep?.(j.step); });
}

/** The rows of a list just moved: its clicks are ignored a moment, so a click aimed at one buyer never
 *  lands on another. */
export function holdClicks(list) {
  list.inert = true;
  clearTimeout(list.holdTimer);
  list.holdTimer = setTimeout(() => { list.inert = false; }, 450);
}

/** The refresh of an order list (the queue, the Order Creator's picker): the button pulls the latest orders;
 *  a page only follows a sync already running (the program's start-up one) and never starts one itself.
 *  fetch() gives the orders, alive() says the page is still there, onFresh(data) shows them. */
export function orderSync({ fetch, alive, setSub, syncedText, button, onStart, onFresh }) {
  const sync = { syncing: false };
  sync.refresh = async (pull = () => syncOrders(setSub)) => {
    if (sync.syncing) return;
    sync.syncing = true;
    button.disabled = true; button.firstElementChild?.classList.add('spin');
    setSub('Оновлення…');
    onStart?.();
    try {
      await pull();
      const next = await fetch();
      if (!alive()) return;
      onFresh(next);
    } catch (err) {
      if (alive()) setSub(`${syncedText()} · не вдалося оновити: ${err.message}`);
    } finally {
      sync.syncing = false;
      button.disabled = false; button.firstElementChild?.classList.remove('spin');
    }
  };
  sync.follow = () => runningSync().then((jobId) => { if (jobId && alive()) sync.refresh(() => watchSync(jobId, setSub)); });
  return sync;
}

/** Pages that still have a previous version on disk, from the files check — so «Повернути» is offered
 *  again after leaving the card, reopening it or restarting the program. */
export function restorable(validation) {
  return new Set((validation?.files || []).filter((r) => r.replaced).map((r) => r.file.toLowerCase()));
}

// ------------------------------------------------------------------ print folder: spreads and viewer
/** Spreads of a book with `total` pages: page numbers, null = the blank endpaper. */
export function spreadsOf(total) {
  const list = [{ left: null, right: 1 }];
  for (let f = 2; f <= total; f += 2) list.push({ left: f, right: f + 1 <= total ? f + 1 : null });
  return list;
}

/** Viewer items for a folder of Cover.png + 1..total.png: the cover, then every spread. */
// `v` changes whenever a page of the folder was replaced: the address changes with it, so the viewer
// shows the new picture instead of the one the browser kept (previews are cached for ten minutes).
/** A page's version in a picture's address: grows each time that page is replaced or put back, so only its own
 *  pictures are fetched again (one number for the whole folder reloaded all ~33 of them, 26.09.2026). */
export const pageVersion = (versions, ...files) => {
  const v = files.map((f) => (f && versions?.[f]) || 0).join('.');
  return /[1-9]/.test(v) ? { v } : {};
};

export function folderViewerItems(folder, total, sub = '', versions = {}) {
  const cover = pageVersion(versions, 'Cover.png');
  const items = [{ src: media('/media/folder', { path: folder, file: 'Cover.png', w: 2600, ...cover }),
    full: media('/media/folder', { path: folder, file: 'Cover.png', w: 4096, ...cover }), title: 'Обкладинка', sub,
    files: ['Cover.png'] }];
  spreadsOf(total).forEach((sp, i) => {
    const q = { path: folder, h: 1400, ...pageVersion(versions, sp.left && `${sp.left}.png`, sp.right && `${sp.right}.png`) };
    if (sp.left) q.left = `${sp.left}.png`;
    if (sp.right) q.right = `${sp.right}.png`;
    const lp = i === 0 ? 1 : sp.left + 1;
    items.push({ src: media('/media/folder-spread', q), full: media('/media/folder-spread', { ...q, h: 2400 }),
      title: `Розворот ${i + 1} · стор. ${lp}–${lp + 1}`, sub: `${sp.left ? `${sp.left}.png` : 'форзац'} · ${sp.right ? `${sp.right}.png` : 'нахзац'}`,
      files: [sp.left, sp.right].filter(Boolean).map((n) => `${n}.png`) });
  });
  return items;
}


/** Mouse wheel scrolls a horizontal strip sideways with eased intermediate frames; at either end the page scrolls on.
 *  The eased position is kept here (not read back from the element), so sub-pixel steps never stall the
 *  animation, and a scroll made any other way (scrollbar, touchpad) simply takes over. */
export function smoothWheel(el, speed = 1.6) {
  let pos = 0, target = 0, raf = 0, last = 0, written = null;
  const stop = () => { raf = 0; last = 0; written = null; };
  const step = (t) => {
    if (written !== null && Math.abs(el.scrollLeft - written) > 2) { stop(); return; } // moved by something else
    const dt = Math.min(64, t - (last || t));
    last = t;
    pos += (target - pos) * (1 - Math.exp(-dt / 90));
    if (Math.abs(target - pos) < 0.5) pos = target;
    el.scrollLeft = pos;
    written = el.scrollLeft;
    if (pos !== target) raf = requestAnimationFrame(step); else stop();
  };
  el.addEventListener('wheel', (e) => {
    if (Math.abs(e.deltaY) <= Math.abs(e.deltaX)) return; // touchpads already scroll sideways
    const max = el.scrollWidth - el.clientWidth;
    if (!raf) pos = target = el.scrollLeft;
    if (max <= 0 || (e.deltaY > 0 && target >= max - 0.5) || (e.deltaY < 0 && target <= 0.5)) return;
    e.preventDefault();
    target = Math.max(0, Math.min(max, target + (e.deltaMode === 1 ? e.deltaY * 32 : e.deltaY) * speed));
    if (!raf) raf = requestAnimationFrame(step);
  }, { passive: false });
}
