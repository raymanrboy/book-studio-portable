// Pieces shared by the order pipeline page, the order archive and the Order Creator: order stages,
// countries, the printer's status and tracking chips, the buyer's fields, the Etsy → Gelato address
// mapping, the sync, dropped folders/ZIPs and the page viewer of a print folder.
import { api, runJob, upload, media, html, raw, ic, copyText } from './lib.js';

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
export const STAGES = [
  { value: 'new', icon: 'sparkle', tip: 'Нові — книгу ще не замовлено ні в Printify, ні в Gelato' },
  { value: 'work', icon: 'hourglass', tip: 'В роботі — книгу вже замовлено в Printify або Gelato' },
  { value: 'sent', icon: 'truck', tip: 'Друкарня відправила — можна позначати відправленими в Etsy' },
  { value: 'shipped', icon: 'package', tip: 'Відправлені — позначені відправленими в Etsy' },
];
export const STAGE_EMPTY = {
  new: ['sparkle', 'Нових замовлень немає', 'Для всіх оплачених замовлень книгу вже замовлено в Printify або Gelato.'],
  work: ['hourglass', 'Зараз нічого не друкується', 'Тут будуть замовлення, для яких книгу вже замовлено в Printify або Gelato.'],
  sent: ['truck', 'Нічого не чекає позначки в Etsy', 'Тут з\'являться замовлення, які Printify або Gelato вже відправили, — поки ви не позначите їх відправленими в Etsy.'],
  shipped: ['package', 'Відправлених ще немає', ''],
};
export const STAGE_LABEL = { new: 'нове', work: 'в роботі', sent: 'відправлено друкарнею', shipped: 'відправлено' };

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
export const trackChips = (o) => (o.tracking || []).map((t) => html`<span class="chip svc-${o.provider} ord-track ord-copy" role="button"
    ${raw(NUMBER_COPY)} data-text="${t.number}">${ic('truck', 'icon-s')}<span class="ord-track-text">${t.carrier
      ? html`<span class="ord-carrier" data-act="copy-text" data-text="${t.carrier}" data-done="Перевізника скопійовано" data-tip="Копіювати перевізника">${t.carrier}</span><span class="ord-track-sep"></span>` : ''}<span class="ord-track-no" ${raw(NUMBER_COPY)} data-text="${t.number}">${t.number}</span></span></span>`);

/** The printer's status (its own word, in English, as the owner asked); nothing before the book is ordered. */
export const statusChip = (o) => (o.printStatus
  ? html`<span class="chip ${statusTone(o.printStatus)} ord-status" data-tip="Статус у ${providerName(o.provider)}"><span class="dot"></span>${statusText(o.printStatus)}</span>`
  : '');

/** Books of this order sent in another go, or to the other printer: the status chip beside it describes
 *  only the first print order, so this says how many more there are. o: { alsoSent }. */
export const alsoSentChip = (o) => {
  const more = o.alsoSent || [];
  if (!more.length) return '';
  const where = [...new Set(more.map((m) => providerName(m.provider)))].join(' і ');
  return html`<span class="chip ord-status" data-tip="Ще ${more.length === 1 ? 'одне замовлення друку' : `${more.length} замовлення друку`} цього чека — у ${where}">+${more.length} у друці</span>`;
};

/** The receipt number without "#": a click copies it (in the queue, the card header and the archive). */
export const receiptCopy = (o, cls) => html`<span class="${cls} ord-copy" role="button" data-act="copy-text" data-text="${o.receiptId}"
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
  await runJob(api('/api/profit/sync', { method: 'POST', body: {} }), (j) => { if (j.step) onStep?.(j.step); });
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

// ------------------------------------------------------------------ dropped folders and archives
// The window cannot see where a dragged folder lives, so its pictures (or a ZIP) are copied into
// the program first (a scratch folder wiped at start-up).
const IMG_FILE = /\.(png|jpe?g|webp)$/i;
const IMG_OR_TEXT = /\.(png|jpe?g|webp|json)$/i;
const readEntries = (dir) => new Promise((resolve, reject) => {
  const reader = dir.createReader();
  const all = [];
  const next = () => reader.readEntries((batch) => { if (!batch.length) resolve(all); else { all.push(...batch); next(); } }, reject);
  next();
});
const entryFile = (entry) => new Promise((resolve, reject) => entry.file(resolve, reject));
async function collect(entry, out, depth = 0, accept = IMG_FILE) {
  if (entry.isFile) { if (accept.test(entry.name)) out.push({ name: entry.fullPath.replace(/^\/+/, ''), file: await entryFile(entry) }); return; }
  if (entry.isDirectory && depth < 4) for (const e of await readEntries(entry)) await collect(e, out, depth + 1, accept);
}

/** What was dropped, read while the drop event still runs (entries expire right after it). */
export function dropContents(e) {
  const dt = e.dataTransfer;
  return {
    entries: [...dt.items].filter((i) => i.kind === 'file').map((i) => i.webkitGetAsEntry?.()).filter(Boolean),
    files: [...dt.files],
  };
}

/** Name to show for a drop before it is copied: the folder's or the archive's own name. */
export function dropLabel({ entries, files }) {
  const zip = files.length === 1 && /\.zip$/i.test(files[0].name) ? files[0] : null;
  return zip ? zip.name.replace(/\.zip$/i, '') : entries.find((e) => e.isDirectory)?.name || 'Файли';
}

/** Copies a dropped folder, loose pictures or a ZIP into the program; resolves to the folder path.
 *  withText — the library's import: the book-text JSON comes too, and the path given back is the dropped
 *  folder itself (the importer reads its generated/ and pages/ as well), not the one with Cover.png. */
export async function receiveDrop({ entries, files }, onProgress, { withText = false } = {}) {
  const zip = files.length === 1 && /\.zip$/i.test(files[0].name) ? files[0] : null;
  const accept = withText ? IMG_OR_TEXT : IMG_FILE;
  const list = [];
  if (!zip) {
    if (entries.length) { try { for (const e of entries) await collect(e, list, 0, accept); } catch { /* unreadable entry: handled below */ } }
    else files.filter((f) => accept.test(f.name)).forEach((f) => list.push({ name: f.name, file: f }));
    if (!list.length) throw new Error('Перетягніть папку з Cover.png і сторінками або ZIP-архів');
    if (!entries.some((e) => e.isDirectory)) list.forEach((x) => { x.name = `Файли/${x.name}`; }); // loose pictures get a folder of their own
  }
  const session = crypto.randomUUID().replace(/-/g, '');
  const total = (zip ? zip.size : list.reduce((sum, x) => sum + x.file.size, 0)) || 1;
  let sent = 0;
  const report = () => onProgress?.(Math.max(1, Math.min(99, (sent / total) * 100)));
  if (zip) await upload(`/api/drop/zip?${new URLSearchParams({ session, name: zip.name, ...(withText ? { text: '1' } : {}) })}`, zip, (p) => { sent = p * total; report(); });
  else {
    let next = 0;
    const worker = async () => {
      while (next < list.length) {
        const x = list[next++];
        let done = 0;
        await upload(`/api/drop/file?${new URLSearchParams({ session, name: x.name, ...(withText ? { text: '1' } : {}) })}`, x.file, (p) => { sent += p * x.file.size - done; done = p * x.file.size; report(); });
        sent += x.file.size - done; report();
      }
    };
    await Promise.all([worker(), worker(), worker()]);
  }
  return (await api('/api/drop/done', { method: 'POST', body: { session, whole: withText } })).path;
}

/** Lights `input` while files are dragged over `[data-folder-drop]` inside `root`; calls onDrop(contents). */
export function wireFolderDrop(root, input, onDrop) {
  const zone = (e) => e.target.closest?.('[data-folder-drop]');
  // With several books each folder block is its own drop zone: the one under the cursor lights up, and
  // the drop tells the page which book it was meant for.
  const mark = (on, z) => {
    root.querySelectorAll('.drop-hot').forEach((el) => el.classList.remove('drop-hot'));
    if (on) input(z)?.classList.add('drop-hot');
  };
  root.addEventListener('dragover', (e) => {
    if (!e.dataTransfer?.types?.includes('Files')) return;
    const z = zone(e);
    mark(!!z, z);
    if (z) { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; }
  });
  root.addEventListener('dragleave', (e) => { if (!e.relatedTarget || !e.relatedTarget.closest?.('[data-folder-drop]')) mark(false); });
  root.addEventListener('drop', (e) => {
    mark(false);
    if (!zone(e) || !e.dataTransfer?.files?.length) return;
    e.preventDefault();
    onDrop(dropContents(e), zone(e));
  });
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
