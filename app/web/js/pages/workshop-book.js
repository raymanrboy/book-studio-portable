// A book in the Workshop (the Listings mode). 17 rows — the cover, the dedication, spreads 2–15, the afterword —
// and every row a card of three, top to bottom (owner, 24.09.2026): the prompt for its picture, the 2:1 frame, the
// text. Prompts and texts come first (typed here, or one JSON from an agent); the pictures come last, dropped one
// per frame. «Передати в бібліотеку» gives the book its Etsy listing and sends it to the orders' library.
import {
  api, html, ic, ib, raw, setHtml, on, media, toast, menu, confirmBox, modal, upload, copyText, fadeImages,
  highlightTokens, el, plural,
} from '../lib.js';
import { openLightbox } from '../lightbox.js';
import { openAddBook } from './library.js';
import { copyGuide, saveGuide } from './workshop.js';

const SPREADS = Array.from({ length: 14 }, (_, i) => i + 2);
const pagesOf = (n) => [2 * n - 2, 2 * n - 1];
// shape: 'wide' — one 2:1 picture over the frame; 'right' / 'left' — a single page, the other half the endpaper.
const ROWS = [
  { key: 'cover', label: 'Обкладинка', short: 'обкладинка', shape: 'wide', halves: ['задня', 'лицьова'] },
  { key: 'page1', label: 'Сторінка 1 · присвята', short: 'сторінка 1', shape: 'right', halves: ['форзац', '1'] },
  ...SPREADS.map((n) => ({ key: `spread${n}`, label: `Розворот ${pagesOf(n).join('–')}`, short: pagesOf(n).join('–'),
    shape: 'wide', halves: pagesOf(n).map(String) })),
  { key: 'page30', label: 'Сторінка 30 · післяслово', short: 'сторінка 30', shape: 'left', halves: ['30', 'форзац'] },
];
const IMG_RE = /\.(png|jpe?g|webp)$/i;
const OFF = 0.04;  // a picture more than 4 % away from its frame's proportion gets the amber mark
const PROMPTS = ['промпт', 'промпти', 'промптів'];
const TEXTS = ['текст', 'тексти', 'текстів'];
// How the server names a missing piece of a JSON («cover», розвороту 5) in a sentence.
const HUMAN = { '«cover»': 'обкладинки', '«page1»': 'присвяти', '«page30»': 'післяслова' };

export async function mount(view, [id]) {
  let book;
  try {
    book = await api(`/api/library/books/${id}`);
  } catch (err) {
    setHtml(view, html`<button class="back-link" onclick="location.hash='#/workshop'">${ic('arrowLeft', 'icon-s')}</button>
      <div class="empty"><div class="empty-icon">${ic('workshop')}</div><h3>Книгу не знайдено</h3><p>${err.message}</p></div>`);
    return null;
  }
  if (book.stage !== 'workshop') { location.replace(`#/book/${id}`); return null; } // already in the library

  const uploading = new Map(); // row key -> the share uploaded (0…1)
  const offs = [];
  const $ = (s) => view.querySelector(s);
  const row = (key) => ROWS.find((r) => r.key === key);
  const assetUrl = (a, w) => media(`/media/book/${id}/${a.file}`, w ? { w } : {});
  const field = (f) => (f === 'prompts' ? book.prompts : book.text) || {};

  /** What sits in a row's frame: one whole picture, or (from a library-style import) two pages. */
  function pictureOf(key) {
    if (key === 'cover') return { whole: book.cover };
    const s = book.slots[key] || {};
    return { whole: s.image, left: s.left, right: s.right };
  }
  const hasPicture = (key) => { const p = pictureOf(key); return !!(p.whole || p.left || p.right); };
  function offShape(r, a) {
    const want = r.shape === 'wide' ? 2 : 1;
    return a && a.width && a.height && Math.abs(a.width / a.height / want - 1) > OFF ? `не ${want}:1 · ${a.width}×${a.height}` : '';
  }

  setHtml(view, html`
    <div class="ws-page">
      <div class="page-head ws-head">
        <button class="back-link" data-act="back" aria-label="До Майстерні" data-tip="До Майстерні" data-kbd="Esc">${ic('arrowLeft')}</button>
        <textarea class="hero-title-input ws-title" id="ws-title" rows="1" spellcheck="false" aria-label="Назва книги">${book.title}</textarea>
        <div class="ws-head-tools">
          <span id="ws-ready"></span>
          <div class="tools">${ib('braces', 'Промпти й тексти (JSON)', 'data-act="json"')}${ib('more', 'Ще', 'data-act="more"')}</div>
          <button class="btn btn-primary" data-act="transfer">${ic('shelf')}Передати в бібліотеку</button>
        </div>
      </div>
      <div class="ws-rows" id="ws-rows"></div>
    </div>
    <input type="file" id="ws-file" accept=".png,.jpg,.jpeg,.webp" hidden>
    <input type="file" id="ws-json-file" accept=".json,application/json" hidden>`);

  // ---------------------------------------------------------------- painting
  function paintReady() {
    const c = book.completeness;
    const part = (name, label, n, total) => {
      const p = n / total;
      const tip = `${label}: ${n} з ${total}`;
      return html`<i class="${p >= 1 ? 'ok' : p > 0 ? 'part' : ''}" style="--p:${Math.round(p * 100)}%" data-tip="${tip}" aria-label="${tip}">${ic(name)}</i>`;
    };
    setHtml($('#ws-ready'), html`<div class="ready" role="list">
      ${part('prompt', 'Промпти', c.prompts, c.promptsTotal)}${part('text', 'Тексти', c.texts, c.textsTotal)}${part('image', 'Картинки', c.pictures, c.picturesTotal)}</div>`);
  }

  function blockHtml(f, key) {
    const value = field(f)[key] || '';
    const prompt = f === 'prompts';
    const what = prompt ? 'Промпт' : 'Текст';
    return html`<div class="ws-block ${prompt ? 'ws-prompt' : 'ws-text'}" data-field="${f}" data-key="${key}">
      <div class="ws-block-head">${ic(prompt ? 'prompt' : 'text', 'icon-s')}<span class="eyebrow">${what}</span><span class="spacer"></span>
        ${ib('copy', prompt ? 'Скопіювати промпт' : 'Скопіювати текст', `data-act="copy" ${value ? '' : 'disabled'}`, { cls: 'sm' })}
        ${ib('edit', 'Редагувати', 'data-act="edit"', { cls: 'sm' })}</div>
      <div class="ws-body ${value ? '' : 'empty-text'}" data-act="edit">${value ? (prompt ? value : highlightTokens(value))
        : `${what} ще не написано — клацніть, щоб написати`}</div>
    </div>`;
  }

  /** An empty frame: dashed, the fold in the middle, the page numbers on its halves; a drop or a click fills it. */
  function placeholder(r, half = null) {
    const what = r.key === 'cover' ? 'обкладинку 2:1' : r.shape === 'wide' ? 'розворот 2:1' : 'сторінку';
    return html`<button type="button" class="ws-ph" data-act="pick" data-key="${r.key}">
      ${half === null ? html`<span class="ws-half">${r.halves[0]}</span><span class="ws-half">${r.halves[1]}</span>` : html`<span class="ws-half ws-one">${half}</span>`}
      <span class="ws-ph-text">${ic('upload')}<b>Перетягніть ${what}</b><span>або клацніть, щоб обрати файл</span></span>
    </button>`;
  }

  function artHtml(r, a, extra = '') {
    const mark = offShape(r, a);
    return html`<div class="ws-art ${a.lqip ? 'lqip' : ''} ${extra}" ${a.lqip ? raw(`style="background-image:url(${a.lqip})"`) : ''}>
      <img data-fade decoding="async" src="${assetUrl(a, 1400)}" alt="${r.label}" data-act="zoom" data-key="${r.key}">
      ${r.shape === 'wide' && r.key !== 'cover' ? html`<div class="gutter"></div>` : ''}
      ${mark ? html`<span class="chip chip-amber ws-mark" data-tip="Рамка чекає пропорцію ${r.shape === 'wide' ? '2:1' : '1:1'}">${ic('alert', 'icon-s')}${mark}</span>` : ''}
      <div class="img-actions">
        ${ib('expand', 'Переглянути', `data-act="zoom" data-key="${r.key}"`, { cls: 'sm' })}
        ${ib('upload', 'Замінити картинку', `data-act="pick" data-key="${r.key}"`, { cls: 'sm' })}
        ${ib('trash', 'Прибрати картинку', `data-act="remove" data-key="${r.key}"`, { cls: 'sm danger' })}
      </div>
      <i class="crops"></i>
    </div>`;
  }

  function frameHtml(r) {
    const p = pictureOf(r.key);
    const up = uploading.get(r.key);
    const busy = up === undefined ? '' : html`<div class="busy-overlay"><div class="ws-up"><i style="transform:scaleX(${up})"></i></div></div>`;
    if (r.shape === 'wide') {
      const inner = p.whole ? artHtml(r, p.whole)
        : p.left || p.right ? html`<div class="ws-pair">${[p.left, p.right].map((a) => (a ? artHtml(r, a, 'ws-halfart') : html`<div class="ws-endpaper"></div>`))}</div>`
          : placeholder(r);
      return html`<div class="ws-frame" data-drop="${r.key}">${inner}${busy}</div>`;
    }
    // A single page: the endpaper on one side, the page (the drop target) on the other.
    const page = html`<div class="ws-pagehalf" data-drop="${r.key}">${p.whole ? artHtml(r, p.whole) : placeholder(r, r.shape === 'right' ? r.halves[1] : r.halves[0])}${busy}</div>`;
    const endpaper = html`<div class="ws-endpaper"><span>форзац</span></div>`;
    return html`<div class="ws-frame ws-single">${r.shape === 'right' ? html`${endpaper}${page}` : html`${page}${endpaper}`}</div>`;
  }

  function rowDots(key) {
    const has = [!!(book.prompts[key] || '').trim(), hasPicture(key), !!(book.text[key] || '').trim()];
    const tip = ['промпт', 'картинка', 'текст'].map((w, i) => `${w} ${has[i] ? '✓' : '—'}`).join(' · ');
    return html`<span class="ws-dots" data-tip="${tip}">${has.map((ok) => html`<i class="${ok ? 'ok' : ''}"></i>`)}</span>`;
  }

  function rowHtml(r) {
    return html`<section class="ws-row" data-row="${r.key}">
      <div class="ws-row-head"><span class="section-title">${r.label}</span><span class="spacer"></span>${rowDots(r.key)}</div>
      ${blockHtml('prompts', r.key)}
      ${frameHtml(r)}
      ${blockHtml('text', r.key)}
    </section>`;
  }

  function paintRows() {
    setHtml($('#ws-rows'), ROWS.map(rowHtml));
    fadeImages($('#ws-rows'));
  }
  /** Only the frame and the row's dots: a prompt or a text being typed in the same row stays as it is. */
  function paintFrame(key) {
    const rowEl = view.querySelector(`[data-row="${key}"]`);
    const old = rowEl?.querySelector('.ws-frame');
    if (!old) return;
    const next = el(frameHtml(row(key)));
    old.replaceWith(next);
    fadeImages(next);
    rowEl.querySelector('.ws-dots')?.replaceWith(el(rowDots(key)));
  }
  function paintProgress(key) {
    const bar = view.querySelector(`[data-row="${key}"] .ws-up > i`);
    if (bar) bar.style.transform = `scaleX(${uploading.get(key) || 0})`;
  }

  paintReady();
  paintRows();

  // ---------------------------------------------------------------- saving
  async function patch(body) {
    try {
      book = await api(`/api/library/books/${id}`, { method: 'PATCH', body: { ...body, rev: book.rev } });
      paintReady();
      return true;
    } catch (err) {
      toast(err.message, 'error');
      return false;
    }
  }

  /** A prompt or a text edited in place: saved on leaving the field or Ctrl+Enter; Esc gives the old one back. */
  function edit(f, key) {
    const block = view.querySelector(`.ws-block[data-field="${f}"][data-key="${key}"]`);
    if (!block || block.querySelector('textarea')) return;
    const ta = el(html`<textarea class="textarea ws-edit" spellcheck="${f === 'text' ? 'true' : 'false'}"
      placeholder="${f === 'prompts' ? 'Опис ілюстрації для генератора' : 'Текст сторінки. {Name} і {Gifter} — місця для персоналізації.'}"></textarea>`);
    ta.value = field(f)[key] || '';
    block.querySelector('.ws-body').replaceWith(ta);
    const foot = el(html`<div class="ws-edit-foot"><span class="faint">Ctrl+Enter — зберегти · Esc — скасувати</span><span class="spacer"></span>
      ${ib('x', 'Скасувати', 'data-x="cancel"', { cls: 'sm', kbd: 'Esc' })}${ib('check', 'Зберегти', 'data-x="save"', { cls: 'sm primary', kbd: 'Ctrl+Enter' })}</div>`);
    block.appendChild(foot);
    ta.focus();
    ta.setSelectionRange(ta.value.length, ta.value.length);
    let finished = false;
    const finish = async (save) => {
      if (finished) return;
      finished = true;
      const value = ta.value.trim();
      if (save && value !== (field(f)[key] || '').trim()) {
        if (await patch({ [f]: { [key]: value } })) toast(f === 'prompts' ? 'Промпт збережено' : 'Текст збережено', 'success', 1400);
      }
      block.replaceWith(el(blockHtml(f, key)));
      const dots = view.querySelector(`[data-row="${key}"] .ws-dots`);
      if (dots) dots.replaceWith(el(rowDots(key)));
    };
    ta.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); finish(true); }
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); finish(false); }
    });
    ta.addEventListener('blur', () => setTimeout(() => { if (!block.contains(document.activeElement)) finish(true); }, 120));
    foot.addEventListener('mousedown', (e) => e.preventDefault());
    foot.addEventListener('click', (e) => { const b = e.target.closest('[data-x]'); if (b) finish(b.dataset.x === 'save'); });
  }

  // ---------------------------------------------------------------- pictures, one per frame
  let pickKey = null;
  async function uploadTo(key, file) {
    if (!IMG_RE.test(file.name)) { toast(`«${file.name}» — не картинка (PNG, JPG, WEBP)`, 'error'); return; }
    if (uploading.has(key)) { toast(`${row(key).label}: попередня картинка ще вантажиться`, 'info'); return; }
    uploading.set(key, 0);
    paintFrame(key);
    try {
      const q = new URLSearchParams({ slot: key, name: file.name });
      book = await upload(`/api/library/books/${id}/assets?${q}`, file, (p) => { uploading.set(key, p); paintProgress(key); });
      uploading.delete(key);
      paintFrame(key);
      paintReady();
      const mark = offShape(row(key), pictureOf(key).whole);
      if (mark) toast(`${row(key).label}: картинка ${mark} — поставлено, але перевірте пропорцію`, 'info', 5000);
    } catch (err) {
      uploading.delete(key);
      paintFrame(key);
      toast(err.message, 'error');
    }
  }

  async function removePicture(key) {
    const r = row(key);
    const ok = await confirmBox({ title: 'Прибрати картинку?', text: `${r.label}: картинку буде видалено з Майстерні. Файл на вашому диску не зміниться.`, confirm: 'Прибрати', danger: true });
    if (!ok) return;
    const p = pictureOf(key);
    const slots = p.whole ? [key] : [p.left && `${key}:left`, p.right && `${key}:right`].filter(Boolean);
    try {
      for (const slot of slots) book = await api(`/api/library/books/${id}/assets?slot=${encodeURIComponent(slot)}`, { method: 'DELETE' });
      paintFrame(key);
      paintReady();
    } catch (err) { toast(err.message, 'error'); }
  }

  function lightboxItems() {
    return ROWS.filter((r) => pictureOf(r.key).whole).map((r) => {
      const a = pictureOf(r.key).whole;
      return {
        key: r.key, src: assetUrl(a, 1400), full: assetUrl(a, 2600), title: r.label,
        sub: `${a.width}×${a.height}${offShape(r, a) ? ' · не та пропорція' : ''}`, text: book.text[r.key] || '',
        onOriginal: () => api(`/api/library/books/${id}/open-original`, { method: 'POST', body: { file: a.file } }).catch((err) => toast(err.message, 'error')),
      };
    });
  }
  function zoom(key) {
    const items = lightboxItems();
    if (items.length) openLightbox(items, Math.max(0, items.findIndex((it) => it.key === key)));
  }

  // ---------------------------------------------------------------- prompts and texts in one JSON
  async function importJson(raw) {
    let check;
    try { check = await api(`/api/workshop/books/${id}/json`, { method: 'POST', body: { json: raw, dryRun: true } }); }
    catch (err) { toast(err.message, 'error', 6500); return false; }
    const r = check.replaces;
    if (r.prompts || r.texts) {
      const what = [r.prompts && `${r.prompts} ${plural(r.prompts, PROMPTS)}`, r.texts && `${r.texts} ${plural(r.texts, TEXTS)}`].filter(Boolean).join(' і ');
      const ok = await confirmBox({ title: `Замінити ${what}, які вже є?`, text: 'У JSON для них інакше, ніж уже написано в книзі. Решта просто заповниться.', confirm: 'Замінити' });
      if (!ok) return false;
    }
    try {
      const res = await api(`/api/workshop/books/${id}/json`, { method: 'POST', body: { json: raw } });
      book = res.book;
      paintReady();
      paintRows();
      toast(`Заповнено: ${res.prompts} ${plural(res.prompts, PROMPTS)}, ${res.texts} ${plural(res.texts, TEXTS)}`, 'success');
      // A few are named, many only counted: "немає промптів (присвяти, розвороту 9)" / "немає 15 промптів".
      const gap = (list, words) => (list.length > 3 ? `${list.length} ${plural(list.length, words)}`
        : `${words[2]} (${list.map((n) => HUMAN[n] || n).join(', ')})`);
      const gaps = [[res.missing.prompts, PROMPTS], [res.missing.texts, TEXTS]].filter(([list]) => list.length).map(([l, w]) => gap(l, w));
      if (gaps.length) toast(`У JSON немає ${gaps.join(' і ')} — там лишилось, як було`, 'info', 7000);
      return true;
    } catch (err) { toast(err.message, 'error', 6500); return false; }
  }

  function pasteJson() {
    const m = modal({
      title: 'Промпти й тексти з JSON',
      sub: 'Вставте відповідь агента — усе розкладеться по рядках книги.',
      body: html`<textarea class="textarea mono ws-json" id="ws-json" rows="14" spellcheck="false" placeholder='{ "cover": {"prompt": "…", "text": "…"}, "page1": …, "spreads": {"2": …}, "page30": … }'></textarea>`,
      foot: html`<button class="btn btn-ghost" data-no>Скасувати</button><button class="btn btn-primary" data-yes>${ic('braces')}Заповнити</button>`,
      size: 'l',
    });
    const ta = m.el.querySelector('#ws-json');
    m.foot.querySelector('[data-no]').onclick = () => m.close();
    m.foot.querySelector('[data-yes]').onclick = async () => {
      if (!ta.value.trim()) { toast('Вставте JSON', 'error'); return; }
      if (await importJson(ta.value)) m.close();
    };
    setTimeout(() => ta.focus(), 30);
  }

  async function copyJson() {
    try { copyText(JSON.stringify(await api(`/api/workshop/books/${id}/json`), null, 2), 'Промпти й тексти скопійовано як JSON'); }
    catch (err) { toast(err.message, 'error'); }
  }

  // ---------------------------------------------------------------- «Передати в бібліотеку»
  async function transfer() {
    let existing;
    try { existing = (await api('/api/library/books')).books; } catch (err) { toast(err.message, 'error'); return; }
    const noPicture = ROWS.filter((r) => !hasPicture(r.key)).map((r) => r.short);
    const noText = ROWS.filter((r) => !(book.text[r.key] || '').trim()).map((r) => r.short);
    const gaps = [noPicture.length && `картинок — ${noPicture.join(', ')}`, noText.length && `текстів — ${noText.join(', ')}`].filter(Boolean);
    const summary = gaps.length
      ? html`<div class="notice notice-warn">${ic('alert')}<div>Бракує ${gaps.join('; ')}. У бібліотеці їх можна докласти пізніше.</div></div>`
      : html`<div class="notice notice-success">${ic('checkCircle')}<div>Усі картинки й тексти на місці.</div></div>`;
    openAddBook(existing, {
      book, summary,
      done: (b) => { toast(`«${b.title}» — у бібліотеці замовлень`, 'success'); location.hash = '#/workshop'; },
    });
  }

  // ---------------------------------------------------------------- events
  offs.push(on(view, 'click', '[data-act]', (e, t) => {
    const act = t.dataset.act;
    if (act === 'back') { location.hash = '#/workshop'; return; }
    if (act === 'transfer') { transfer(); return; }
    if (act === 'json') {
      menu(t, [
        { label: 'Вставити JSON…', icon: 'braces', onClick: pasteJson },
        { label: 'Завантажити JSON-файл…', icon: 'fileOpen', onClick: () => $('#ws-json-file').click() },
        { label: 'Скопіювати промпти й тексти як JSON', icon: 'copy', onClick: copyJson },
        '-',
        { label: 'Скопіювати інструкцію для агента', icon: 'guide', onClick: copyGuide },
        { label: 'Зберегти інструкцію у файл…', icon: 'download', onClick: saveGuide },
      ]);
      return;
    }
    if (act === 'more') {
      menu(t, [
        { label: 'Відкрити папку книги', icon: 'folderOpen', onClick: () => api(`/api/library/books/${id}/open-folder`, { method: 'POST', body: {} }).catch((err) => toast(err.message, 'error')) },
        '-',
        { label: 'Видалити книгу', icon: 'trash', danger: true, onClick: deleteBook },
      ]);
      return;
    }
    const key = t.dataset.key || t.closest('[data-key]')?.dataset.key;
    if (act === 'pick') { pickKey = key; $('#ws-file').click(); return; }
    if (act === 'zoom') { e.stopPropagation(); zoom(key); return; }
    if (act === 'remove') { e.stopPropagation(); removePicture(key); return; }
    const block = t.closest('.ws-block');
    if (act === 'copy' && block) { copyText(field(block.dataset.field)[block.dataset.key] || '', block.dataset.field === 'prompts' ? 'Промпт скопійовано' : 'Текст скопійовано'); return; }
    if (act === 'edit' && block) edit(block.dataset.field, block.dataset.key);
  }));

  async function deleteBook() {
    const ok = await confirmBox({ title: `Видалити «${book.title}»?`, text: 'Книга піде в кошик бібліотеки (app/data/library/trash) — звідти її можна повернути вручну.', confirm: 'Видалити', danger: true });
    if (!ok) return;
    try {
      await api(`/api/library/books/${id}`, { method: 'DELETE' });
      toast('Книгу видалено', 'success');
      location.hash = '#/workshop';
    } catch (err) { toast(err.message, 'error'); }
  }

  $('#ws-file').addEventListener('change', (e) => {
    const f = e.target.files[0];
    e.target.value = '';
    if (f && pickKey) uploadTo(pickKey, f);
  });
  $('#ws-json-file').addEventListener('change', async (e) => {
    const f = e.target.files[0];
    e.target.value = '';
    if (f) importJson(await f.text());
  });

  // The title, edited in place like the passport's.
  const title = $('#ws-title');
  title.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); title.blur(); } });
  title.addEventListener('blur', async () => {
    const v = title.value.trim();
    if (!v) { title.value = book.title; return; }
    if (v !== book.title && await patch({ title: v })) toast('Назву збережено', 'success', 1400);
  });

  // Dragging files in: a picture onto its frame (one per frame), a JSON anywhere on the page.
  const files = (e) => [...(e.dataTransfer?.types || [])].includes('Files');
  const mark = (target) => {
    view.querySelectorAll('.drop-hot').forEach((x) => x.classList.remove('drop-hot'));
    target?.classList.add('drop-hot');
  };
  const onOver = (e) => {
    if (!files(e)) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    mark(e.target.closest('[data-drop]'));
  };
  const onLeave = (e) => { if (!e.relatedTarget || !view.contains(e.relatedTarget)) mark(null); };
  const onDrop = async (e) => {
    if (!files(e)) return;
    e.preventDefault();
    mark(null);
    const dropped = [...e.dataTransfer.files];
    const target = e.target.closest('[data-drop]');
    const json = dropped.filter((f) => /\.json$/i.test(f.name));
    if (dropped.length === 1 && json.length === 1) { importJson(await json[0].text()); return; }
    if (!target) { toast('Перетягніть картинку на її рамку (або JSON — будь-куди на сторінку)', 'info'); return; }
    if (dropped.length !== 1) { toast('Одна картинка — в одну рамку', 'error'); return; }
    uploadTo(target.dataset.drop, dropped[0]);
  };
  view.addEventListener('dragover', onOver);
  view.addEventListener('dragleave', onLeave);
  view.addEventListener('drop', onDrop);

  const onKey = (e) => {
    if (e.key !== 'Escape' || document.querySelector('.modal-root, .lightbox, .menu')) return;
    if (/^(INPUT|TEXTAREA)$/.test(document.activeElement?.tagName || '')) return;
    location.hash = '#/workshop';
  };
  document.addEventListener('keydown', onKey);

  return {
    unmount() {
      offs.forEach((off) => off());
      document.removeEventListener('keydown', onKey);
    },
  };
}
