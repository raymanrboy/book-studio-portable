// The book passport's dialogs: «Імпорт з папки» (a folder, or a dropped ZIP — laid out by library.scan_folder),
// the book's text as JSON, the Canva link; the whole text in one piece; the slots' layout the page shares (out of
// book.js on 27.09.2026).
import { api, post, html, ic, modal, toast, runJob, setProgress } from '../lib.js';
import { refreshInfo } from '../info.js';

const SPREADS = Array.from({ length: 14 }, (_, i) => i + 2);
export const SLOT_KEYS = ['page1', ...SPREADS.map((n) => `spread${n}`), 'page30'];
export const pagesOf = (n) => [2 * n - 2, 2 * n - 1];

function slotName(slot) {
  const [base, part] = slot.split(':');
  if (base === 'cover') return 'Обкладинка';
  if (base === 'thumbnail') return 'Заставка';
  if (base === 'page1') return 'Сторінка 1 · присвята';
  if (base === 'page30') return 'Сторінка 30 · післяслово';
  const [a, b] = pagesOf(+base.slice(6));
  return `Розворот ${base.slice(6)} · ${part === 'left' ? `ліва (${a})` : part === 'right' ? `права (${b})` : `стор. ${a}–${b}`}`;
}
const slotOrder = (s) => {
  const base = s.split(':')[0];
  if (base === 'cover') return 0; if (base === 'thumbnail') return 1; if (base === 'page1') return 2; if (base === 'page30') return 99;
  return +base.slice(6) * 3 + (s.endsWith(':right') ? 1 : 0);
};

function hasAsset(book, slot) {
  const [base, part] = slot.split(':');
  if (base === 'cover' || base === 'thumbnail') return !!book[base];
  const s = book.slots[base];
  return part ? !!(s[part] || s.image) : !!(s.image || s.left || s.right);
}

// ---------------------------------------------------------------- folder import (native dialog, or a dropped ZIP)
export async function importFolder(path, { id, current, onBook }) {
  if (!path) {
    try { path = (await post('/api/app/pick-folder', { title: 'Оберіть папку з файлами книги' })).path; }
    catch (err) { toast(err.message, 'error'); return; }
  }
  if (!path) return;
  let scan;
  try { scan = await post(`/api/library/books/${id}/folder-scan`, { path }); }
  catch (err) { toast(err.message, 'error'); return; }
  const slots = Object.keys(scan.mapping).sort((a, b) => slotOrder(a) - slotOrder(b));
  const m = modal({
    title: 'Імпорт з папки',
    sub: scan.folder,
    size: 'l',
    body: html`<div class="stack">
      <div class="row-wrap">
        ${scan.mapping.cover ? html`<span class="chip chip-green">${ic('check', 'icon-s')}Обкладинка</span>` : html`<span class="chip">без обкладинки</span>`}
        <span class="chip ${slots.length ? 'chip-green' : ''}"><span class="num">${slots.length}</span> ${slots.length === 1 ? 'зображення' : 'зображень'}</span>
        ${scan.text ? html`<span class="chip chip-green">${ic('check', 'icon-s')}Текст ${scan.text.name}</span>` : html`<span class="chip">без тексту</span>`}
      </div>
      ${slots.length ? html`<div class="card-soft" style="max-height:300px;overflow:auto;padding:4px 12px">${slots.map((s) => html`<div class="row" style="padding:7px 0;border-bottom:1px solid var(--border)">
        <label class="check grow"><input type="checkbox" data-slot-cb="${s}" checked><span>${slotName(s)}</span></label><span class="mono faint">${scan.mapping[s].name}</span>${hasAsset(current(), s) ? html`<span class="chip chip-amber">замінить</span>` : ''}</div>`)}</div>` : ''}
      ${scan.issues.map((t) => html`<div class="notice notice-warn">${ic('alert')}<div>${t}</div></div>`)}
      ${scan.text ? html`<label class="check"><input type="checkbox" id="fi-text" checked><span>Імпортувати текст із <b>${scan.text.name}</b> (замінить наявні тексти)</span></label>` : ''}
      ${scan.ignored.length ? html`<div class="faint" style="font-size: var(--fs)">Не розпізнано: ${scan.ignored.join(', ')}</div>` : ''}
      <div id="fi-progress" hidden><div class="row" style="margin-bottom:6px"><span id="fi-step" class="grow" style="font-weight:600;font-size: var(--fs)"></span><span id="fi-pct" class="mono faint"></span></div><div class="progress"><i id="fi-bar"></i></div></div>
    </div>`,
    foot: html`<button class="btn btn-ghost" data-c>Скасувати</button><button class="btn btn-primary" data-go>${ic('download', 'icon-s')}Імпортувати</button>`,
  });
  m.foot.querySelector('[data-c]').onclick = () => m.close();
  m.foot.querySelector('[data-go]').onclick = async () => {
    const selected = [...m.el.querySelectorAll('[data-slot-cb]')].filter((c) => c.checked).map((c) => c.dataset.slotCb);
    // The button always answers (2026-09-30): nothing to take in is said, not a grey button.
    if (!selected.length && !m.el.querySelector('#fi-text')?.checked) {
      toast(slots.length || scan.text ? 'Позначте, що імпортувати' : 'У папці немає картинок чи тексту для цієї книги', 'info');
      return;
    }
    m.foot.querySelectorAll('button').forEach((b) => { b.disabled = true; });
    m.el.querySelector('#fi-progress').hidden = false;
    try {
      const res = await runJob(post(`/api/library/books/${id}/folder-import`,
        { path: scan.folder, slots: selected, includeText: !!m.el.querySelector('#fi-text')?.checked }), (j) => {
        m.el.querySelector('#fi-step').textContent = `${j.step} ${j.detail || ''}`;
        m.el.querySelector('#fi-pct').textContent = `${Math.round(j.percent)}%`;
        setProgress(m.el.querySelector('#fi-bar'), j.percent);
      });
      m.close();
      onBook(await api(`/api/library/books/${id}`));
      refreshInfo();
      if (res.errors?.length) toast(`Імпорт із зауваженнями:\n${res.errors.slice(0, 4).join('\n')}`, 'error', 9000);
      else toast(`Імпортовано ${res.images} зображень${res.text ? ' і текст' : ''}`, 'success');
    } catch (err) {
      toast(err.message, 'error');
      m.foot.querySelectorAll('button').forEach((b) => { b.disabled = false; });
    }
  };
}

// ---------------------------------------------------------------- text JSON
export async function importTextJson(id, text, onBook) {
  try {
    const res = await post(`/api/library/books/${id}/text`, { json: text });
    onBook(res.book);
    // Missing texts are fine: those places simply stay empty.
    toast(res.problems.length ? `Імпортовано ${res.imported} з ${res.imported + res.problems.length} текстів` : 'Текст книги імпортовано повністю', 'success');
  } catch (err) { toast(err.message, 'error', 8000); }
}
export function pasteJsonDialog(id, onBook) {
  const m = modal({
    title: 'Вставити текст книги (JSON)',
    sub: 'Формат: { "cover", "page1", "spreads": { "2" … "15" }, "page30" }',
    size: 'l',
    body: html`<textarea class="textarea mono" id="pj" style="min-height:320px" placeholder='{"cover": "...", "page1": "...", "spreads": {"2": "..."}, "page30": "..."}' autofocus></textarea>`,
    foot: html`<button class="btn btn-ghost" data-c>Скасувати</button><button class="btn btn-primary" data-go>Імпортувати</button>`,
  });
  m.foot.querySelector('[data-c]').onclick = () => m.close();
  m.foot.querySelector('[data-go]').onclick = async () => { const v = m.el.querySelector('#pj').value; m.close(); await importTextJson(id, v, onBook); };
}
export function canvaDialog(book, saveBook) {
  const m = modal({
    title: 'Макет у Canva',
    sub: 'Canva → Поділитися → Копіювати посилання',
    body: html`<input class="input" id="cv-url" placeholder="https://www.canva.com/design/…" value="${book.canvaUrl || ''}" autocomplete="off" spellcheck="false" aria-label="Посилання на макет у Canva" autofocus>`,
    foot: html`${book.canvaUrl ? html`<button class="btn btn-ghost danger" data-rm>Прибрати</button><span class="spacer"></span>` : ''}
      <button class="btn btn-ghost" data-c>Скасувати</button><button class="btn btn-primary" data-go>Зберегти</button>`,
  });
  const input = m.el.querySelector('#cv-url');
  const save = async (v) => {
    if (v && !/^https?:\/\//i.test(v)) { toast('Посилання має починатися з https://', 'error'); input.focus(); return; }
    m.close();
    if (v !== (book.canvaUrl || '') && await saveBook({ canvaUrl: v })) toast(v ? 'Посилання на Canva збережено' : 'Посилання на Canva прибрано', 'success', 1400);
  };
  m.foot.querySelector('[data-c]').onclick = () => m.close();
  m.foot.querySelector('[data-go]').onclick = () => save(input.value.trim());
  m.foot.querySelector('[data-rm]')?.addEventListener('click', () => save(''));
  input.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); save(input.value.trim()); } });
  input.select();
}
export function bookText(book) {
  const parts = [];
  if (book.text.cover) parts.push(`[Обкладинка]\n${book.text.cover}`);
  for (const k of SLOT_KEYS) {
    const t = book.text[k];
    if (!t) continue;
    const label = k === 'page1' ? 'Сторінка 1' : k === 'page30' ? 'Сторінка 30' : `Розворот ${k.slice(6)} (стор. ${pagesOf(+k.slice(6)).join('–')})`;
    parts.push(`[${label}]\n${t}`);
  }
  return parts.join('\n\n');
}
