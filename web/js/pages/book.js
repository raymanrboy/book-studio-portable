// Book passport: cover, 16 page slots (dedication, 14 spreads, afterword), texts, files.
import {
  api, html, ic, raw, setHtml, on, media, modal, toast, menu, confirmBox, upload, runJob, copyText,
  openExternal, fadeImages, highlightTokens, debounce, dateTime, bytes, segHtml, syncSeg, setSeg, naturalCompare, el,
} from '../lib.js';
import { openLightbox } from '../lightbox.js';
import { refreshInfo } from '../app.js';

const SPREADS = Array.from({ length: 14 }, (_, i) => i + 2);
const SLOT_KEYS = ['page1', ...SPREADS.map((n) => `spread${n}`), 'page30'];
const pagesOf = (n) => [2 * n - 2, 2 * n - 1];
const IMG_RE = /\.(png|jpe?g|webp)$/i;

export async function mount(view, [id]) {
  let book;
  try {
    book = await api(`/api/library/books/${id}`);
  } catch (err) {
    setHtml(view, html`<button class="back-link" onclick="location.hash='#/library'">${ic('arrowLeft', 'icon-s')}Бібліотека</button>
      <div class="empty"><div class="empty-icon">${ic('book')}</div><h3>Книгу не знайдено</h3><p>${err.message}</p></div>`);
    return null;
  }
  let filter = 'all';
  const busy = new Set();

  const assetUrl = (a, w) => media(`/media/book/${id}/${a.file}`, w ? { w } : {});

  // ---------------------------------------------------------------- skeleton
  setHtml(view, html`
    <div class="row" style="margin-bottom:6px">
      <button class="back-link" data-act="back" style="margin:0">${ic('arrowLeft', 'icon-s')}Бібліотека</button>
      <span class="spacer"></span>
      <div class="row-wrap" id="bk-actions"></div>
    </div>
    <div id="bk-hero"></div>
    <div class="section-head"><div><div class="section-title">Обкладинка</div><div class="section-sub">Повний розворот обкладинки та її текст</div></div></div>
    <div id="bk-cover"></div>
    <div class="section-head" id="bk-pages-head"></div>
    <div class="slots" id="bk-slots"></div>
    <input type="file" id="bk-file" accept=".png,.jpg,.jpeg,.webp" hidden>
    <input type="file" id="bk-json" accept=".json,application/json" hidden>
    <input type="file" id="bk-many" accept=".png,.jpg,.jpeg,.webp,.json" multiple hidden>`);

  const $ = (s) => view.querySelector(s);

  // ---------------------------------------------------------------- render parts
  function renderActions() {
    setHtml($('#bk-actions'), html`
      <button class="btn btn-sm" data-act="import-folder">${ic('folder', 'icon-s')}Імпорт з папки</button>
      <button class="btn btn-sm" data-act="add-files">${ic('upload', 'icon-s')}Додати файли</button>
      <button class="btn btn-sm" data-act="text-menu">${ic('text', 'icon-s')}Текст JSON</button>
      ${book.listing?.url ? html`<button class="btn btn-sm" data-act="open-etsy">${ic('external', 'icon-s')}Etsy</button>` : ''}
      ${book.canvaUrl ? html`<button class="btn btn-sm btn-primary" data-act="open-canva">${ic('sparkle', 'icon-s')}Відкрити в Canva</button>` : ''}
      <button class="btn btn-sm btn-icon" data-act="more" title="Ще">${ic('more')}</button>`);
  }

  function renderHero() {
    const c = book.completeness;
    const l = book.listing || {};
    const thumb = book.thumbnail;
    const checks = [
      ['Обкладинка', c.cover],
      ['Заставка в галереї', c.thumbnail],
      ['Ілюстрації', c.illustrations === c.illustrationsTotal, `${c.illustrations}/${c.illustrationsTotal}`, c.illustrations / c.illustrationsTotal],
      ['Тексти', c.texts === c.textsTotal, `${c.texts}/${c.textsTotal}`, c.texts / c.textsTotal],
      ['Посилання на Canva', c.canva],
    ];
    setHtml($('#bk-hero'), html`<div class="card card-pad book-hero">
      <div class="hero-thumb ${thumb?.lqip ? 'lqip' : ''}" ${thumb?.lqip ? raw(`style="background-image:url(${thumb.lqip})"`) : ''} data-drop="thumbnail" data-act="${thumb ? 'zoom-thumb' : 'pick'}" data-slot="thumbnail" title="Заставка книги в галереї">
        ${thumb ? html`<img decoding="async" src="${assetUrl(thumb, 720)}" alt="">
          <div class="thumb-actions"><button class="btn btn-xs" data-act="pick" data-slot="thumbnail">${ic('upload', 'icon-s')}Замінити</button>
          <button class="btn btn-xs btn-icon" data-act="remove" data-slot="thumbnail" title="Прибрати">${ic('trash', 'icon-s')}</button></div>`
          : html`<div class="drop-ph"><div class="drop-ico">${ic('image')}</div><b>Заставка</b><span>Перетягніть фото або натисніть</span>
            ${l.id ? html`<button class="btn btn-xs" data-act="thumb-etsy">${ic('download', 'icon-s')}Фото з Etsy</button>` : ''}</div>`}
        ${busy.has('thumbnail') ? html`<div class="busy-overlay"><div class="spinner spinner-l"></div></div>` : ''}
      </div>
      <div class="stack" style="min-width:0">
        <textarea class="hero-title-input" id="bk-title" rows="1" spellcheck="false">${book.title}</textarea>
        <div class="hero-meta">
          ${l.id ? html`<a href="#" data-act="open-etsy" class="chip chip-accent chip-mono">${ic('external', 'icon-s')}Etsy #${l.id}</a>` : html`<span class="chip chip-amber">без лістингу</span>`}
          ${l.state ? html`<span class="chip ${l.state === 'active' ? 'chip-green' : 'chip-amber'}">${l.state}</span>` : ''}
          ${l.verifiedAt ? html`<span class="faint">перевірено ${dateTime(l.verifiedAt)}</span>` : l.id ? html`<span class="chip chip-amber">${ic('alert', 'icon-s')}не перевірено</span>` : ''}
          ${book.archived ? html`<span class="chip chip-purple">${ic('archive', 'icon-s')}в архіві</span>` : ''}
        </div>
        ${l.title && l.title !== book.title ? html`<div class="faint" style="font-size:12.5px">Назва на Etsy: ${l.title}</div>` : ''}
        <div class="field" style="margin-top:4px">
          <label class="field-label">${ic('sparkle', 'icon-s')}Макет у Canva</label>
          <div class="row"><input class="input" id="bk-canva" placeholder="Вставте посилання на дизайн у Canva…" value="${book.canvaUrl || ''}" autocomplete="off">
          <button class="btn" data-act="open-canva" ${book.canvaUrl ? '' : 'disabled'}>${ic('external', 'icon-s')}Відкрити</button></div>
        </div>
        <div class="field">
          <label class="field-label">Нотатки</label>
          <textarea class="textarea" id="bk-notes" rows="2" style="min-height:64px" placeholder="Особливості книги, шрифти, варіанти персоналізації…">${book.notes || ''}</textarea>
        </div>
      </div>
      <div class="card-soft" style="padding:16px">
        <div style="font-weight:650;margin-bottom:12px">Готовність книги</div>
        <div class="check-list">${checks.map(([label, ok, num, frac]) => html`<div>
          <div class="check-row"><span class="check-ico ${ok ? 'ok' : ''}">${ic(ok ? 'check' : 'x', 'icon-s')}</span>${label}${num ? html`<span class="num">${num}</span>` : ''}</div>
          ${frac !== undefined ? html`<div class="bar-mini" style="margin:6px 0 0 32px"><i style="width:${Math.round(frac * 100)}%"></i></div>` : ''}
        </div>`)}</div>
        <div class="faint" style="font-size:11.5px;margin-top:14px">Додано ${dateTime(book.createdAt)}<br>Змінено ${dateTime(book.updatedAt)}</div>
      </div>
    </div>`);
    autosize($('#bk-title'));
  }

  function renderCover() {
    const cover = book.cover;
    setHtml($('#bk-cover'), html`<div class="stack">
      <div class="cover-box ${cover?.lqip ? 'lqip' : ''}" data-drop="cover" style="${cover ? `aspect-ratio:${cover.width} / ${cover.height}${cover.lqip ? `;background-image:url(${cover.lqip})` : ''}` : 'min-height:220px'}">
        ${cover ? html`<img data-fade decoding="async" src="${assetUrl(cover, 1400)}" alt="" data-zoom="cover"><div class="gutter"></div>
          <div class="img-actions">
            <button class="btn btn-xs" data-act="zoom" data-key="cover">${ic('zoomIn', 'icon-s')}</button>
            <button class="btn btn-xs" data-act="pick" data-slot="cover">${ic('upload', 'icon-s')}Замінити</button>
            <button class="btn btn-xs btn-icon" data-act="remove" data-slot="cover" title="Видалити">${ic('trash', 'icon-s')}</button>
          </div>
          <span class="page-tag">${cover.width}×${cover.height} · ${bytes(cover.bytes)}</span>`
          : html`<div class="drop-ph" data-act="pick" data-slot="cover" style="min-height:220px"><div class="drop-ico">${ic('image')}</div><b>Обкладинка</b><span>Перетягніть файл обкладинки сюди або натисніть</span></div>`}
        ${busy.has('cover') ? html`<div class="busy-overlay"><div class="spinner spinner-l"></div></div>` : ''}
      </div>
      ${textBlock('cover', 'Текст обкладинки')}
    </div>`);
    fadeImages($('#bk-cover'));
  }

  function textBlock(key, label) {
    const t = book.text[key] || '';
    return html`<div class="text-block" data-textblock="${key}">
      <div class="row" style="margin-bottom:8px"><span style="font-weight:650;font-size:13px">${label}</span><span class="spacer"></span>
        <button class="btn btn-ghost btn-xs" data-act="copy-text" data-key="${key}" ${t ? '' : 'disabled'}>${ic('copy', 'icon-s')}Копіювати</button>
        <button class="btn btn-ghost btn-xs" data-act="edit-text" data-key="${key}">${ic('edit', 'icon-s')}Редагувати</button></div>
      <div class="text-body ${t ? '' : 'empty-text'}" data-act="edit-text" data-key="${key}">${t ? highlightTokens(t) : 'Текст ще не додано — натисніть, щоб написати.'}</div>
    </div>`;
  }

  function renderPagesHead() {
    const c = book.completeness;
    setHtml($('#bk-pages-head'), html`
      <div><div class="section-title">Сторінки й розвороти</div>
        <div class="section-sub">Присвята, 14 розворотів, післяслово · ${c.illustrations}/16 з ілюстраціями · перетягніть файли прямо на потрібне місце</div></div>
      <span class="spacer"></span>
      ${segHtml([{ value: 'all', label: 'Усі' }, { value: 'noimg', label: 'Без ілюстрацій' }, { value: 'notext', label: 'Без тексту' }], filter, { name: 'filter' })}
      <button class="btn btn-sm" data-act="copy-all">${ic('copy', 'icon-s')}Весь текст</button>`);
    requestAnimationFrame(() => syncSeg($('#bk-pages-head .seg')));
  }

  function slotHasImage(key) {
    const s = book.slots[key];
    return !!(s.image || (s.left && s.right));
  }

  function rowHtml(key, i) {
    const s = book.slots[key];
    const label = key === 'page1' ? 'Сторінка 1' : key === 'page30' ? 'Сторінка 30' : `Розворот ${key.slice(6)}`;
    const pages = key === 'page1' ? 'присвята' : key === 'page30' ? 'післяслово' : `стор. ${pagesOf(+key.slice(6)).join('–')}`;
    const t = book.text[key] || '';
    const textCol = html`<div class="slot-text" data-textcol="${key}">
      <div class="slot-text-head"><span class="slot-label">${label}</span><span class="slot-pages">${pages}</span><span class="spacer"></span>
        <button class="btn btn-ghost btn-xs btn-icon" data-act="copy-text" data-key="${key}" title="Копіювати текст" ${t ? '' : 'disabled'}>${ic('copy', 'icon-s')}</button>
        <button class="btn btn-ghost btn-xs btn-icon" data-act="edit-text" data-key="${key}" title="Редагувати">${ic('edit', 'icon-s')}</button></div>
      <div class="slot-text-body ${t ? '' : 'empty-text'}" data-act="edit-text" data-key="${key}">${t ? highlightTokens(t) : 'Текст ще не додано'}</div>
    </div>`;
    const busyOv = (slot) => busy.has(slot) ? html`<div class="busy-overlay"><div class="spinner spinner-l"></div></div>` : '';
    const bg = (asset) => (asset?.lqip ? raw(`style="background-image:url(${asset.lqip})"`) : '');
    const pageSq = (slot, asset, tag, hint) => html`<div class="page-sq ${asset?.lqip ? 'lqip' : ''}" data-drop="${slot}" ${slot.includes(':') ? 'data-auto="1"' : ''} ${bg(asset)}>
      ${asset ? html`<img data-fade decoding="async" src="${assetUrl(asset, 720)}" alt="" data-zoom="${slot}" loading="lazy">
        <div class="img-actions"><button class="btn btn-xs btn-icon" data-act="zoom" data-key="${slot}" title="Збільшити">${ic('zoomIn', 'icon-s')}</button>
        <button class="btn btn-xs btn-icon" data-act="pick" data-slot="${slot}" title="Замінити">${ic('upload', 'icon-s')}</button>
        ${slot.includes(':') && s.left && s.right ? html`<button class="btn btn-xs btn-icon" data-act="swap" data-key="${key}" title="Поміняти сторінки місцями">${ic('swap', 'icon-s')}</button>` : ''}
        <button class="btn btn-xs btn-icon" data-act="remove" data-slot="${slot}" title="Видалити">${ic('trash', 'icon-s')}</button></div>
        <span class="page-tag">${tag}</span>`
        : html`<div class="drop-ph" data-act="pick" data-slot="${slot}"><div class="drop-ico">${ic('upload')}</div><b>${hint}</b><span>стор. ${tag}</span></div>`}
      ${busyOv(slot)}</div>`;
    const blank = (text) => html`<div class="page-sq blank"><span>${text}</span></div>`;

    let images;
    if (key === 'page1') images = html`${blank('Форзац')}${pageSq('page1', s.image, '1', 'Присвята')}`;
    else if (key === 'page30') images = html`${pageSq('page30', s.image, '30', 'Післяслово')}${blank('Нахзац')}`;
    else {
      const [lp, rp] = pagesOf(+key.slice(6));
      if (s.image) {
        images = html`<div class="spread-img ${s.image.lqip ? 'lqip' : ''}" data-drop="${key}" ${bg(s.image)}>
          <img data-fade decoding="async" src="${assetUrl(s.image, 1400)}" alt="" data-zoom="${key}" loading="lazy"><div class="gutter"></div>
          <div class="img-actions"><button class="btn btn-xs btn-icon" data-act="zoom" data-key="${key}" title="Збільшити">${ic('zoomIn', 'icon-s')}</button>
            <button class="btn btn-xs" data-act="pick" data-slot="${key}">${ic('upload', 'icon-s')}Замінити</button>
            <button class="btn btn-xs btn-icon" data-act="remove" data-slot="${key}" title="Видалити">${ic('trash', 'icon-s')}</button></div>
          <span class="page-tag">${lp}–${rp}</span>${busyOv(key)}</div>`;
      } else {
        images = html`${pageSq(`${key}:left`, s.left, String(lp), 'Ліва сторінка')}${pageSq(`${key}:right`, s.right, String(rp), 'Права сторінка')}`;
      }
    }
    const hidden = (filter === 'noimg' && slotHasImage(key)) || (filter === 'notext' && t.trim());
    // Entrance animation only on first paint (i >= 0); re-rendered rows just swap in place.
    return html`<div class="slot-row ${i >= 0 ? 'enter' : ''}" data-row="${key}" ${hidden ? 'hidden' : ''} ${i >= 0 ? raw(`style="animation-delay:${Math.min(i * 30, 300)}ms"`) : ''}>${textCol}${images}</div>`;
  }

  function renderSlots() {
    setHtml($('#bk-slots'), SLOT_KEYS.map((k, i) => rowHtml(k, i)));
    fadeImages($('#bk-slots'));
  }
  function renderRow(key) {
    const old = view.querySelector(`[data-row="${key}"]`);
    if (!old) return;
    const fresh = el(rowHtml(key, -1));
    old.replaceWith(fresh);
    fadeImages(fresh);
  }
  function renderAll() {
    renderActions(); renderHero(); renderCover(); renderPagesHead(); renderSlots();
  }
  function applyBook(next, touched) {
    book = next;
    renderActions();
    renderHero();
    renderPagesHead();
    if (!touched || touched === 'cover') renderCover();
    if (!touched) renderSlots();
    else if (touched !== 'cover' && touched !== 'thumbnail' && touched !== 'meta') renderRow(touched.split(':')[0]);
  }

  // ---------------------------------------------------------------- saving fields
  async function patch(body, touched = 'meta') {
    try {
      const next = await api(`/api/library/books/${id}`, { method: 'PATCH', body: { ...body, rev: book.rev } });
      book = next;
      if (touched === 'meta') { renderActions(); refreshChecklist(); }
      return true;
    } catch (err) {
      toast(err.message, 'error');
      return false;
    }
  }
  function refreshChecklist() {
    // Re-render hero but keep focus/caret where the user is typing.
    const focused = document.activeElement?.id;
    const caret = focused ? [document.activeElement.selectionStart, document.activeElement.selectionEnd] : null;
    renderHero();
    renderPagesHead();
    if (focused) { const f = document.getElementById(focused); if (f) { f.focus(); try { f.setSelectionRange(...caret); } catch {} } }
  }
  const saveNotes = debounce(async (value) => { await patch({ notes: value }, 'notes'); }, 700);

  function autosize(ta) {
    if (!ta || CSS.supports('field-sizing', 'content')) return; // CSS sizes the title itself
    ta.style.height = 'auto';
    ta.style.height = `${ta.scrollHeight}px`;
  }

  // ---------------------------------------------------------------- text editing
  function editText(key) {
    const container = key === 'cover' ? view.querySelector('[data-textblock="cover"]') : view.querySelector(`[data-textcol="${key}"]`);
    if (!container || container.querySelector('textarea')) return;
    const bodyEl = container.querySelector(key === 'cover' ? '.text-body' : '.slot-text-body');
    const ta = document.createElement('textarea');
    ta.className = key === 'cover' ? 'textarea' : '';
    ta.value = book.text[key] || '';
    ta.placeholder = 'Текст сторінки. {Name} та {Gifter} — місця для персоналізації.';
    bodyEl.replaceWith(ta);
    const foot = el(html`<div class="slot-text-foot" ${key === 'cover' ? 'style="background:none;border:0;padding:8px 0 0"' : ''}>
      <span class="faint" style="font-size:11.5px;align-self:center">Ctrl+Enter — зберегти, Esc — скасувати</span><span class="spacer"></span>
      <button class="btn btn-ghost btn-xs" data-x="cancel">Скасувати</button><button class="btn btn-primary btn-xs" data-x="save">Зберегти</button></div>`);
    container.appendChild(foot);
    ta.focus();
    ta.setSelectionRange(ta.value.length, ta.value.length);
    let finished = false;
    const finish = async (save) => {
      if (finished) return; finished = true;
      if (save && ta.value !== (book.text[key] || '')) {
        const ok = await patch({ text: { [key]: ta.value } }, key);
        if (ok) toast('Текст збережено', 'success', 1400);
      }
      if (key === 'cover') renderCover(); else renderRow(key);
      renderHero(); renderPagesHead();
    };
    ta.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); finish(true); }
      if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); finish(false); }
    });
    ta.addEventListener('blur', () => setTimeout(() => { if (!container.contains(document.activeElement)) finish(true); }, 120));
    foot.addEventListener('mousedown', (e) => e.preventDefault());
    foot.addEventListener('click', (e) => {
      const b = e.target.closest('[data-x]');
      if (b) finish(b.dataset.x === 'save');
    });
  }

  // ---------------------------------------------------------------- uploads
  let pickSlot = null;
  async function uploadTo(slot, file, auto = false) {
    if (!IMG_RE.test(file.name)) { toast(`«${file.name}» — не зображення (PNG, JPG, WEBP)`, 'error'); return; }
    const base = slot.split(':')[0];
    busy.add(slot);
    rerenderSlot(slot);
    try {
      const q = new URLSearchParams({ slot, name: file.name, ...(auto ? { auto: '1' } : {}) });
      const next = await upload(`/api/library/books/${id}/assets?${q}`, file);
      busy.delete(slot);
      applyBook(next, base);
      refreshInfo();
    } catch (err) {
      busy.delete(slot);
      rerenderSlot(slot);
      toast(err.message, 'error');
    }
  }
  function rerenderSlot(slot) {
    const base = slot.split(':')[0];
    if (base === 'cover') renderCover();
    else if (base === 'thumbnail') renderHero();
    else renderRow(base);
  }
  async function removeAsset(slot) {
    const ok = await confirmBox({ title: 'Видалити зображення?', text: 'Файл буде видалено з бібліотеки. Оригінал на вашому диску не зміниться.', confirm: 'Видалити', danger: true });
    if (!ok) return;
    try {
      const next = await api(`/api/library/books/${id}/assets?slot=${encodeURIComponent(slot)}`, { method: 'DELETE' });
      applyBook(next, slot.split(':')[0]);
    } catch (err) { toast(err.message, 'error'); }
  }

  // ---------------------------------------------------------------- smart multi-file mapping
  function mapFiles(files) {
    const mapping = {}; const ignored = []; let text = null;
    const singles = {}, pairs = {};
    let cover = null, thumb = null;
    for (const f of files) {
      const stem = f.name.replace(/\.[^.]+$/, '').trim().toLowerCase();
      if (/\.json$/i.test(f.name)) { text = f; continue; }
      if (!IMG_RE.test(f.name)) { ignored.push(f.name); continue; }
      if (/cover|cober|обкладин/.test(stem)) { if (!cover || /\.png$/i.test(f.name)) cover = f; continue; }
      if (/thumb|заставк|preview|gallery/.test(stem)) { thumb = f; continue; }
      const m = stem.match(/^(\d+)(?:\s*[-–_]\s*(\d+))?$/);
      if (!m) { ignored.push(f.name); continue; }
      if (m[2]) pairs[`${+m[1]}-${+m[2]}`] = f; else singles[+m[1]] = f;
    }
    if (cover) mapping.cover = cover;
    if (thumb) mapping.thumbnail = thumb;
    if (singles[1]) mapping.page1 = singles[1];
    if (singles[30]) mapping.page30 = singles[30];
    for (const n of SPREADS) {
      const [a, b] = pagesOf(n);
      if (pairs[`${a}-${b}`]) mapping[`spread${n}`] = pairs[`${a}-${b}`];
      else { if (singles[a]) mapping[`spread${n}:left`] = singles[a]; if (singles[b]) mapping[`spread${n}:right`] = singles[b]; }
    }
    const used = new Set(Object.values(mapping));
    for (const f of files) if (IMG_RE.test(f.name) && !used.has(f) && !ignored.includes(f.name)) ignored.push(f.name);
    return { mapping, ignored, text };
  }

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

  async function importFiles(files) {
    const { mapping, ignored, text } = mapFiles(files);
    const slots = Object.keys(mapping).sort((a, b) => slotOrder(a) - slotOrder(b));
    if (!slots.length && !text) {
      toast('Не вдалося розпізнати файли. Назвіть їх як 1.png, 2-3.png … 30.png, Cover.png', 'error', 6000);
      return;
    }
    const m = modal({
      title: 'Розкласти файли по книзі',
      sub: `${slots.length} ${slots.length === 1 ? 'зображення' : 'зображень'}${text ? ' + текст' : ''}`,
      size: 'l',
      body: html`<div class="stack">
        ${slots.length ? html`<div class="card-soft" style="max-height:340px;overflow:auto;padding:4px 12px">${slots.map((s) => html`<div class="row" style="padding:7px 0;border-bottom:1px solid var(--border)">
          <span class="grow">${slotName(s)}</span><span class="mono faint">${mapping[s].name}</span>${hasAsset(s) ? html`<span class="chip chip-amber">замінить</span>` : ''}</div>`)}</div>` : ''}
        ${text ? html`<div class="notice notice-info">${ic('text')}<div>Текст книги з <b>${text.name}</b> буде імпортовано (замінить наявні тексти).</div></div>` : ''}
        ${ignored.length ? html`<div class="faint" style="font-size:12.5px">Пропущено: ${ignored.sort(naturalCompare).join(', ')}</div>` : ''}
        <div id="imp-progress" hidden><div class="row" style="margin-bottom:6px"><span id="imp-step" class="grow" style="font-weight:600;font-size:13px"></span><span id="imp-pct" class="mono faint"></span></div><div class="progress"><i id="imp-bar"></i></div></div>
      </div>`,
      foot: html`<button class="btn btn-ghost" data-c>Скасувати</button><button class="btn btn-primary" data-go>${ic('upload', 'icon-s')}Імпортувати</button>`,
    });
    m.foot.querySelector('[data-c]').onclick = () => m.close();
    m.foot.querySelector('[data-go]').onclick = async () => {
      m.foot.querySelectorAll('button').forEach((b) => { b.disabled = true; });
      m.el.querySelector('#imp-progress').hidden = false;
      const total = slots.length + (text ? 1 : 0);
      let done = 0; const errors = [];
      const step = (label) => {
        m.el.querySelector('#imp-step').textContent = label;
        m.el.querySelector('#imp-pct').textContent = `${done}/${total}`;
        m.el.querySelector('#imp-bar').style.width = `${(done / total) * 100}%`;
      };
      for (const s of slots) {
        step(`Завантаження: ${slotName(s)}`);
        try {
          const q = new URLSearchParams({ slot: s, name: mapping[s].name });
          book = await upload(`/api/library/books/${id}/assets?${q}`, mapping[s], (p) => {
            m.el.querySelector('#imp-bar').style.width = `${((done + p) / total) * 100}%`;
          });
        } catch (err) { errors.push(`${mapping[s].name}: ${err.message}`); }
        done++;
      }
      if (text) {
        step('Імпорт тексту…');
        try { const res = await api(`/api/library/books/${id}/text`, { method: 'POST', body: { json: await text.text() } }); book = res.book; }
        catch (err) { errors.push(`${text.name}: ${err.message}`); }
        done++;
      }
      step('Готово');
      m.close();
      renderAll();
      refreshInfo();
      if (errors.length) toast(`Імпортовано з помилками:\n${errors.slice(0, 4).join('\n')}`, 'error', 9000);
      else toast('Файли розкладено по книзі', 'success');
    };
  }
  function hasAsset(slot) {
    const [base, part] = slot.split(':');
    if (base === 'cover' || base === 'thumbnail') return !!book[base];
    const s = book.slots[base];
    return part ? !!(s[part] || s.image) : !!(s.image || s.left || s.right);
  }

  // ---------------------------------------------------------------- folder import (native dialog)
  async function importFolder() {
    let path;
    try { path = (await api('/api/app/pick-folder', { method: 'POST', body: { title: 'Оберіть папку з файлами книги' } })).path; }
    catch (err) { toast(err.message, 'error'); return; }
    if (!path) return;
    let scan;
    try { scan = await api(`/api/library/books/${id}/folder-scan`, { method: 'POST', body: { path } }); }
    catch (err) { toast(err.message, 'error'); return; }
    const slots = Object.keys(scan.mapping).sort((a, b) => slotOrder(a) - slotOrder(b));
    const m = modal({
      title: 'Імпорт з папки',
      sub: scan.folder,
      size: 'l',
      body: html`<div class="stack">
        <div class="row-wrap">
          <span class="chip ${scan.mapping.cover ? 'chip-green' : ''}">${ic(scan.mapping.cover ? 'check' : 'x', 'icon-s')}Обкладинка</span>
          <span class="chip ${scan.slotsFound === scan.slotsTotal ? 'chip-green' : scan.slotsFound ? 'chip-amber' : ''}">Сторінки ${scan.slotsFound}/${scan.slotsTotal}</span>
          <span class="chip ${scan.text ? 'chip-green' : ''}">${ic(scan.text ? 'check' : 'x', 'icon-s')}Текст ${scan.text ? scan.text.name : ''}</span>
        </div>
        ${slots.length ? html`<div class="card-soft" style="max-height:300px;overflow:auto;padding:4px 12px">${slots.map((s) => html`<div class="row" style="padding:7px 0;border-bottom:1px solid var(--border)">
          <label class="check grow"><input type="checkbox" data-slot-cb="${s}" checked><span>${slotName(s)}</span></label><span class="mono faint">${scan.mapping[s].name}</span>${hasAsset(s) ? html`<span class="chip chip-amber">замінить</span>` : ''}</div>`)}</div>` : ''}
        ${scan.issues.map((t) => html`<div class="notice notice-warn">${ic('alert')}<div>${t}</div></div>`)}
        ${scan.text ? html`<label class="check"><input type="checkbox" id="fi-text" checked><span>Імпортувати текст із <b>${scan.text.name}</b> (замінить наявні тексти)</span></label>` : ''}
        ${scan.ignored.length ? html`<div class="faint" style="font-size:12.5px">Не розпізнано: ${scan.ignored.join(', ')}</div>` : ''}
        <div id="fi-progress" hidden><div class="row" style="margin-bottom:6px"><span id="fi-step" class="grow" style="font-weight:600;font-size:13px"></span><span id="fi-pct" class="mono faint"></span></div><div class="progress"><i id="fi-bar"></i></div></div>
      </div>`,
      foot: html`<button class="btn btn-ghost" data-c>Скасувати</button><button class="btn btn-primary" data-go ${slots.length || scan.text ? '' : 'disabled'}>${ic('download', 'icon-s')}Імпортувати</button>`,
    });
    m.foot.querySelector('[data-c]').onclick = () => m.close();
    m.foot.querySelector('[data-go]').onclick = async () => {
      const selected = [...m.el.querySelectorAll('[data-slot-cb]')].filter((c) => c.checked).map((c) => c.dataset.slotCb);
      m.foot.querySelectorAll('button').forEach((b) => { b.disabled = true; });
      m.el.querySelector('#fi-progress').hidden = false;
      try {
        const res = await runJob(api(`/api/library/books/${id}/folder-import`, {
          method: 'POST', body: { path: scan.folder, slots: selected, includeText: !!m.el.querySelector('#fi-text')?.checked },
        }), (j) => {
          m.el.querySelector('#fi-step').textContent = `${j.step} ${j.detail || ''}`;
          m.el.querySelector('#fi-pct').textContent = `${Math.round(j.percent)}%`;
          m.el.querySelector('#fi-bar').style.width = `${j.percent}%`;
        });
        m.close();
        book = await api(`/api/library/books/${id}`);
        renderAll();
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
  async function importTextJson(raw) {
    try {
      const res = await api(`/api/library/books/${id}/text`, { method: 'POST', body: { json: raw } });
      book = res.book;
      renderAll();
      if (res.problems.length) toast(`Імпортовано ${res.imported} текстів. Не вистачає: ${res.problems.length}`, 'info', 6000);
      else toast('Текст книги імпортовано повністю', 'success');
    } catch (err) { toast(err.message, 'error', 8000); }
  }
  function pasteJsonDialog() {
    const m = modal({
      title: 'Вставити текст книги (JSON)',
      sub: 'Формат: { "cover", "page1", "spreads": { "2" … "15" }, "page30" }',
      size: 'l',
      body: html`<textarea class="textarea mono" id="pj" style="min-height:320px" placeholder='{"cover": "...", "page1": "...", "spreads": {"2": "..."}, "page30": "..."}' autofocus></textarea>`,
      foot: html`<button class="btn btn-ghost" data-c>Скасувати</button><button class="btn btn-primary" data-go>Імпортувати</button>`,
    });
    m.foot.querySelector('[data-c]').onclick = () => m.close();
    m.foot.querySelector('[data-go]').onclick = async () => { const v = m.el.querySelector('#pj').value; m.close(); await importTextJson(v); };
  }
  function allText() {
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

  // ---------------------------------------------------------------- lightbox
  function lightboxItems() {
    const items = [];
    const orig = (a) => () => api(`/api/library/books/${id}/open-original`, { method: 'POST', body: { file: a.file } }).catch((e) => toast(e.message, 'error'));
    const push = (key, a, title, text) => items.push({
      key, src: assetUrl(a, 2400), full: Math.max(a.width, a.height) > 2400 ? assetUrl(a, 4096) : null,
      title, sub: `${book.title} · ${a.width}×${a.height}`, text, onOriginal: orig(a),
    });
    if (book.cover) push('cover', book.cover, 'Обкладинка', book.text.cover);
    for (const k of SLOT_KEYS) {
      const s = book.slots[k];
      const t = book.text[k];
      if (k === 'page1' && s.image) push('page1', s.image, 'Сторінка 1 · присвята', t);
      else if (k === 'page30' && s.image) push('page30', s.image, 'Сторінка 30 · післяслово', t);
      else if (k.startsWith('spread')) {
        const [a, b] = pagesOf(+k.slice(6));
        if (s.image) push(k, s.image, `Розворот ${k.slice(6)} · стор. ${a}–${b}`, t);
        if (s.left) push(`${k}:left`, s.left, `Розворот ${k.slice(6)} · ліва сторінка ${a}`, t);
        if (s.right) push(`${k}:right`, s.right, `Розворот ${k.slice(6)} · права сторінка ${b}`, t);
      }
    }
    if (book.thumbnail) push('thumbnail', book.thumbnail, 'Заставка', '');
    return items;
  }
  function zoom(key) {
    const items = lightboxItems();
    const i = Math.max(0, items.findIndex((it) => it.key === key));
    openLightbox(items, i);
  }

  // ---------------------------------------------------------------- events
  renderAll();

  const offs = [
    on(view, 'click', '[data-act]', async (e, t) => {
      const act = t.dataset.act;
      if (act === 'back') { location.hash = '#/library'; return; }
      if (act === 'pick') { e.stopPropagation(); pickSlot = t.dataset.slot; $('#bk-file').click(); return; }
      if (act === 'remove') { e.stopPropagation(); removeAsset(t.dataset.slot); return; }
      if (act === 'zoom') { e.stopPropagation(); zoom(t.dataset.key); return; }
      if (act === 'zoom-thumb') { zoom('thumbnail'); return; }
      if (act === 'swap') {
        e.stopPropagation();
        try { applyBook(await api(`/api/library/books/${id}/swap`, { method: 'POST', body: { slot: t.dataset.key } }), t.dataset.key); }
        catch (err) { toast(err.message, 'error'); }
        return;
      }
      if (act === 'copy-text') { copyText(book.text[t.dataset.key] || '', 'Текст скопійовано'); return; }
      if (act === 'edit-text') { editText(t.dataset.key); return; }
      if (act === 'copy-all') { const all = allText(); if (all) copyText(all, 'Увесь текст книги скопійовано'); else toast('У книзі ще немає тексту', 'info'); return; }
      if (act === 'open-etsy') { e.preventDefault(); openExternal(book.listing?.url); return; }
      if (act === 'open-canva') { openExternal(book.canvaUrl); return; }
      if (act === 'import-folder') { importFolder(); return; }
      if (act === 'add-files') { $('#bk-many').click(); return; }
      if (act === 'thumb-etsy') { e.stopPropagation(); thumbFromEtsy(); return; }
      if (act === 'text-menu') {
        menu(t, [
          { label: 'Завантажити файл JSON…', icon: 'upload', onClick: () => $('#bk-json').click() },
          { label: 'Вставити JSON вручну', icon: 'text', onClick: pasteJsonDialog },
          '-',
          { label: 'Скопіювати як JSON', icon: 'copy', onClick: async () => copyText(JSON.stringify(await api(`/api/library/books/${id}/text.json`), null, 2), 'JSON скопійовано') },
          { label: 'Скопіювати весь текст', icon: 'copy', onClick: () => { const a = allText(); a ? copyText(a) : toast('У книзі ще немає тексту'); } },
        ]);
        return;
      }
      if (act === 'more') {
        menu(t, [
          ...(book.listing?.id ? [{ label: 'Оновити дані з Etsy', icon: 'refresh', onClick: refreshListing },
            { label: 'Фото лістингу як заставка', icon: 'image', onClick: thumbFromEtsy }] : []),
          { label: 'Експорт файлів у папку…', icon: 'download', onClick: exportBook },
          { label: 'Відкрити папку книги', icon: 'folder', onClick: () => api(`/api/library/books/${id}/open-folder`, { method: 'POST', body: {} }).catch((er) => toast(er.message, 'error')) },
          '-',
          book.archived ? { label: 'Відновити з архіву', icon: 'restore', onClick: () => setArchived(false) } : { label: 'Перенести в архів', icon: 'archive', onClick: () => setArchived(true) },
          { label: 'Видалити книгу…', icon: 'trash', danger: true, onClick: deleteBook },
        ]);
      }
    }),
    on(view, 'click', '[data-zoom]', (e, img) => zoom(img.dataset.zoom)),
    on(view, 'click', '[data-seg="filter"] button', (e, b) => {
      filter = b.dataset.value; setSeg(b.closest('.seg'), filter);
      SLOT_KEYS.forEach((k) => {
        const row = view.querySelector(`[data-row="${k}"]`);
        if (row) row.hidden = (filter === 'noimg' && slotHasImage(k)) || (filter === 'notext' && (book.text[k] || '').trim());
      });
    }),
  ];

  async function thumbFromEtsy() {
    busy.add('thumbnail'); renderHero();
    try { applyBook(await api(`/api/library/books/${id}/thumbnail-from-listing`, { method: 'POST', body: {} }), 'thumbnail'); toast('Заставку взято з Etsy', 'success'); refreshInfo(); }
    catch (err) { toast(err.message, 'error'); }
    finally { busy.delete('thumbnail'); renderHero(); }
  }
  async function refreshListing() {
    try { applyBook(await api(`/api/library/books/${id}/refresh-listing`, { method: 'POST', body: {} }), 'meta'); toast('Дані лістингу оновлено', 'success'); }
    catch (err) { toast(err.message, 'error'); }
  }
  async function setArchived(archived) {
    try {
      applyBook(await api(`/api/library/books/${id}/archive`, { method: 'POST', body: { archived } }), 'meta');
      toast(archived ? 'Книгу перенесено в архів' : 'Книгу відновлено', 'success');
      refreshInfo();
    } catch (err) { toast(err.message, 'error'); }
  }
  async function deleteBook() {
    const ok = await confirmBox({
      title: 'Видалити книгу?',
      text: `«${book.title}» разом з усіма ілюстраціями буде прибрано з бібліотеки.\nФайли перемістяться в папку data/library/trash, звідки їх можна повернути вручну.`,
      confirm: 'Видалити', danger: true,
    });
    if (!ok) return;
    try { await api(`/api/library/books/${id}`, { method: 'DELETE' }); toast('Книгу видалено', 'success'); refreshInfo(); location.hash = '#/library'; }
    catch (err) { toast(err.message, 'error'); }
  }
  async function exportBook() {
    let path;
    try { path = (await api('/api/app/pick-folder', { method: 'POST', body: { title: 'Куди зберегти файли книги?' } })).path; }
    catch (err) { toast(err.message, 'error'); return; }
    if (!path) return;
    toast('Експорт розпочато…', 'info', 1800);
    try {
      const res = await runJob(api(`/api/library/books/${id}/export`, { method: 'POST', body: { path } }));
      toast(`Збережено ${res.files} файлів у ${res.folder}`, 'success', 6000);
      api('/api/creator/open-folder', { method: 'POST', body: { path: res.folder } }).catch(() => {});
    } catch (err) { toast(err.message, 'error'); }
  }

  // Inputs
  view.addEventListener('input', (e) => {
    if (e.target.id === 'bk-title') autosize(e.target);
    if (e.target.id === 'bk-notes') saveNotes(e.target.value);
  });
  view.addEventListener('keydown', (e) => {
    if ((e.target.id === 'bk-title' || e.target.id === 'bk-canva') && e.key === 'Enter') { e.preventDefault(); e.target.blur(); }
  });
  view.addEventListener('focusout', async (e) => {
    if (e.target.id === 'bk-title') {
      const v = e.target.value.trim();
      if (!v) { e.target.value = book.title; autosize(e.target); return; }
      if (v !== book.title && await patch({ title: v })) { toast('Назву збережено', 'success', 1400); refreshInfo(); }
    }
    if (e.target.id === 'bk-canva') {
      const v = e.target.value.trim();
      if (v !== (book.canvaUrl || '')) { if (v && !/^https?:\/\//i.test(v)) { toast('Посилання має починатися з https://', 'error'); return; } if (await patch({ canvaUrl: v })) toast('Посилання на Canva збережено', 'success', 1400); }
    }
    if (e.target.id === 'bk-notes') saveNotes.flush(e.target.value);
  });

  // File inputs
  $('#bk-file').addEventListener('change', (e) => {
    const f = e.target.files[0]; e.target.value = '';
    if (f && pickSlot) uploadTo(pickSlot, f, pickSlot.includes(':'));
  });
  $('#bk-json').addEventListener('change', async (e) => {
    const f = e.target.files[0]; e.target.value = '';
    if (f) importTextJson(await f.text());
  });
  $('#bk-many').addEventListener('change', (e) => {
    const files = [...e.target.files]; e.target.value = '';
    if (files.length) importFiles(files);
  });

  // Drag & drop: onto a slot = that slot; several files anywhere = smart mapping.
  let hot = null;
  const setHot = (node) => { if (hot === node) return; hot?.classList.remove('drop-hot'); hot = node; hot?.classList.add('drop-hot'); };
  const onDragOver = (e) => {
    if (!e.dataTransfer?.types?.includes('Files')) return;
    e.preventDefault();
    setHot(e.target.closest('[data-drop]'));
  };
  const onDragLeave = (e) => { if (!e.relatedTarget || !view.contains(e.relatedTarget)) setHot(null); };
  const onDrop = async (e) => {
    if (!e.dataTransfer?.files?.length) return;
    e.preventDefault();
    const target = e.target.closest('[data-drop]');
    setHot(null);
    const files = [...e.dataTransfer.files];
    if (files.length === 1 && /\.json$/i.test(files[0].name)) { importTextJson(await files[0].text()); return; }
    if (target && files.length === 1) { uploadTo(target.dataset.drop, files[0], !!target.dataset.auto); return; }
    if (target && files.length === 2 && /^spread\d+/.test(target.dataset.drop)) {
      const base = target.dataset.drop.split(':')[0];
      const [a, b] = files.sort((x, y) => naturalCompare(x.name, y.name));
      await uploadTo(`${base}:left`, a); await uploadTo(`${base}:right`, b);
      return;
    }
    importFiles(files);
  };
  view.addEventListener('dragover', onDragOver);
  view.addEventListener('dragleave', onDragLeave);
  view.addEventListener('drop', onDrop);

  // Keyboard: Ctrl+V with an image in clipboard is not supported by design (use files).
  return {
    unmount() {
      offs.forEach((f) => f());
      saveNotes.cancel();
    },
  };
}
