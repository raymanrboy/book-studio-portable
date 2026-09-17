// Pieces shared by the order pipeline page and the Order Creator: order stages, countries, the
// Etsy → Gelato address mapping, the sync, dropped folders/ZIPs and the page viewer of a print folder.
import { api, runJob, upload, media } from './lib.js';

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
// once Printify or Gelato has a print order carrying its receipt number (decided on the server).
export const STAGES = [
  { value: 'new', icon: 'sparkle', tip: 'Нові — книгу ще не замовлено ні в Printify, ні в Gelato' },
  { value: 'work', icon: 'hourglass', tip: 'В роботі — книгу вже замовлено в Printify або Gelato' },
  { value: 'shipped', icon: 'package', tip: 'Відправлені покупцю' },
];
export const STAGE_EMPTY = {
  new: ['sparkle', 'Нових замовлень немає', 'Для всіх оплачених замовлень книгу вже замовлено в Printify або Gelato.'],
  work: ['hourglass', 'Зараз нічого не друкується', 'Тут будуть замовлення, для яких книгу вже замовлено в Printify або Gelato.'],
  shipped: ['package', 'Відправлених ще немає', ''],
};

export const providerName = (p) => (p === 'gelato' ? 'Gelato' : 'Printify');
export const variationsOf = (o) => (o.items || []).flatMap((i) => i.variations || []);
export const matchesOrder = (o, t) => !t || (o.name || '').toLowerCase().includes(t) || o.receiptId.includes(t);

/** "Hardcover · США → Printify · 24 стор." — why this printer was chosen. */
export function planText(plan) {
  if (!plan?.provider) return 'Тип обкладинки не вдалося визначити — оберіть друкарню';
  const binding = plan.binding === 'hardcover' ? 'Hardcover' : 'Softcover';
  return `${binding} · ${countryName(plan.country)} → ${providerName(plan.provider)} · ${plan.pages} стор.`;
}

/** Etsy shipping address → the Order Creator's Gelato address fields. */
export function addressFromEtsy(o) {
  const a = o.address || {};
  const parts = (a.name || o.name || '').trim().split(/\s+/);
  return {
    firstName: parts[0] || '', lastName: parts.slice(1).join(' ') || '',
    addressLine1: a.first_line || '', addressLine2: a.second_line || '', city: a.city || '',
    state: a.state || '', postCode: a.zip || '', country: (a.country_iso || 'US').toUpperCase(),
  };
}

// Orders are pulled from Etsy, Printify and Gelato only twice over: once when the program starts
// (on the server) and whenever the refresh button is pressed. Pages never start a sync on their own.

/** Pulls the latest orders now (the refresh button; a few seconds). */
export async function syncOrders(onStep) {
  await runJob(api('/api/profit/sync', { method: 'POST', body: {} }), (j) => { if (j.step) onStep?.(j.step); });
}

/** The sync already running (usually the start-up one): its job id, or null. */
export async function runningSync() {
  try { return (await api('/api/profit/sync')).jobId || null; } catch { return null; }
}

/** Waits for a running sync to end, reporting its steps. */
export async function watchSync(jobId, onStep) {
  await runJob(Promise.resolve({ jobId }), (j) => { if (j.step) onStep?.(j.step); });
}

// ------------------------------------------------------------------ print folder: spreads and viewer
/** Spreads of a book with `total` pages: page numbers, null = the blank endpaper. */
export function spreadsOf(total) {
  const list = [{ left: null, right: 1 }];
  for (let f = 2; f <= total; f += 2) list.push({ left: f, right: f + 1 <= total ? f + 1 : null });
  return list;
}

/** Viewer items for a folder of Cover.png + 1..total.png: the cover, then every spread. */
export function folderViewerItems(folder, total, sub = '') {
  const items = [{ src: media('/media/folder', { path: folder, file: 'Cover.png', w: 2600 }),
    full: media('/media/folder', { path: folder, file: 'Cover.png', w: 4096 }), title: 'Обкладинка', sub }];
  spreadsOf(total).forEach((sp, i) => {
    const q = { path: folder, h: 1400 };
    if (sp.left) q.left = `${sp.left}.png`;
    if (sp.right) q.right = `${sp.right}.png`;
    const lp = i === 0 ? 1 : sp.left + 1;
    items.push({ src: media('/media/folder-spread', q), full: media('/media/folder-spread', { ...q, h: 2400 }),
      title: `Розворот ${i + 1} · стор. ${lp}–${lp + 1}`, sub: `${sp.left ? `${sp.left}.png` : 'форзац'} · ${sp.right ? `${sp.right}.png` : 'нахзац'}` });
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

export const isZipDrop = ({ files }) => files.length === 1 && /\.zip$/i.test(files[0].name);
export const isFolderDrop = ({ entries }) => entries.some((e) => e.isDirectory);

/** Pictures and text files inside dropped folders (any depth up to four levels), as plain File objects. */
export async function filesInDrop({ entries }) {
  const list = [];
  for (const e of entries) await collect(e, list, 0, IMG_OR_TEXT);
  return list.map((x) => x.file);
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
 *  withText also keeps the book-text JSON found in a ZIP (the library import reads it). */
export async function receiveDrop({ entries, files }, onProgress, { withText = false } = {}) {
  const zip = files.length === 1 && /\.zip$/i.test(files[0].name) ? files[0] : null;
  const list = [];
  if (!zip) {
    if (entries.length) { try { for (const e of entries) await collect(e, list); } catch { /* unreadable entry: handled below */ } }
    else files.filter((f) => IMG_FILE.test(f.name)).forEach((f) => list.push({ name: f.name, file: f }));
    if (!list.length) throw new Error('Перетягніть папку з Cover.png і сторінками або ZIP-архів');
    if (!entries.some((e) => e.isDirectory)) list.forEach((x) => { x.name = `Файли/${x.name}`; }); // loose pictures get a folder of their own
  }
  const session = crypto.randomUUID().replace(/-/g, '');
  const total = (zip ? zip.size : list.reduce((sum, x) => sum + x.file.size, 0)) || 1;
  let sent = 0;
  const report = () => onProgress?.(Math.max(1, Math.min(99, (sent / total) * 100)));
  if (zip) await upload(`/api/creator/drop/zip?${new URLSearchParams({ session, name: zip.name, ...(withText ? { text: '1' } : {}) })}`, zip, (p) => { sent = p * total; report(); });
  else {
    let next = 0;
    const worker = async () => {
      while (next < list.length) {
        const x = list[next++];
        let done = 0;
        await upload(`/api/creator/drop/file?${new URLSearchParams({ session, name: x.name })}`, x.file, (p) => { sent += p * x.file.size - done; done = p * x.file.size; report(); });
        sent += x.file.size - done; report();
      }
    };
    await Promise.all([worker(), worker(), worker()]);
  }
  return (await api('/api/creator/drop/done', { method: 'POST', body: { session } })).path;
}

/** Lights `input` while files are dragged over `[data-folder-drop]` inside `root`; calls onDrop(contents). */
export function wireFolderDrop(root, input, onDrop) {
  const zone = (e) => e.target.closest?.('[data-folder-drop]');
  const mark = (on) => input()?.classList.toggle('drop-hot', on);
  root.addEventListener('dragover', (e) => {
    if (!e.dataTransfer?.types?.includes('Files')) return;
    const z = zone(e);
    mark(!!z);
    if (z) { e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; }
  });
  root.addEventListener('dragleave', (e) => { if (!e.relatedTarget || !e.relatedTarget.closest?.('[data-folder-drop]')) mark(false); });
  root.addEventListener('drop', (e) => {
    mark(false);
    if (!zone(e) || !e.dataTransfer?.files?.length) return;
    e.preventDefault();
    onDrop(dropContents(e));
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
