// Files and folders dragged into the window: what was dropped, read in full (a folder's tree, a ZIP), copied into the program — the order card, the Order Creator, the passport and the mockups take drops through here (out of order-bits.js on 27.09.2026).
import { post, upload } from './lib.js';

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
  return (await post('/api/drop/done', { session, whole: withText })).path;
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
