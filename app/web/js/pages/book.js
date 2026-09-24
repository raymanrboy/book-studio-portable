// Book passport: cover, 16 page slots (dedication, 14 spreads, afterword), texts, files.
import {
  api, html, ic, ib, raw, setHtml, on, media, modal, toast, menu, confirmBox, upload, runJob, copyText,
  openExternal, fadeImages, highlightTokens, dateTime, bytes, naturalCompare, el,
} from '../lib.js';
import { openLightbox } from '../lightbox.js';
import { refreshInfo } from '../info.js';
import { dropContents, receiveDrop } from '../order-bits.js';

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
  if (book.stage === 'workshop') { location.replace(`#/workshop/${id}`); return null; } // still in development
  const busy = new Set();

  const assetUrl = (a, w) => media(`/media/book/${id}/${a.file}`, w ? { w } : {});

  // ---------------------------------------------------------------- skeleton
  setHtml(view, html`
    <div class="page-head" style="margin-bottom:14px">
      <button class="back-link" data-act="back" aria-label="До бібліотеки" data-tip="До бібліотеки" data-kbd="Esc">${ic('arrowLeft')}</button>
      <span class="spacer"></span>
      <div id="bk-actions"></div>
    </div>
    <div id="bk-hero"></div>
    <div class="section-head" id="bk-cover-head"></div>
    <div id="bk-cover"></div>
    <div class="section-head" id="bk-pages-head"></div>
    <div class="slots" id="bk-slots"></div>
    <input type="file" id="bk-file" accept=".png,.jpg,.jpeg,.webp" hidden>
    <input type="file" id="bk-json" accept=".json,application/json" hidden>
    <input type="file" id="bk-many" accept=".png,.jpg,.jpeg,.webp,.json" multiple hidden>`);

  const $ = (s) => view.querySelector(s);

  // ---------------------------------------------------------------- render parts
  function renderActions() {
    setHtml($('#bk-actions'), html`<div class="tools">
      ${ib('folderIn', 'Імпорт з папки', 'data-act="import-folder"')}
      ${ib('filesPlus', 'Додати файли', 'data-act="add-files"')}
      ${ib('braces', 'Текст книги', 'data-act="text-menu"')}
      <span class="sep"></span>
      ${ib('more', 'Ще', 'data-act="more"')}
    </div>`);
  }

  // The parts of a finished book, lit when done; a thin ink line shows partial progress.
  // (The Canva link has its own button in the same row, so it is not repeated here.)
  function readiness() {
    const c = book.completeness;
    const part = (iconName, label, done, n, total) => {
      const p = total ? n / total : done ? 1 : 0;
      const tip = total ? `${label}: ${n} з ${total}` : `${label}: ${done ? 'є' : 'немає'}`;
      return html`<i class="${p >= 1 ? 'ok' : p > 0 ? 'part' : ''}" style="--p:${Math.round(p * 100)}%" data-tip="${tip}" aria-label="${tip}">${ic(iconName)}</i>`;
    };
    return html`<div class="ready" role="list">
      ${part('book', 'Обкладинка', c.cover)}
      ${part('image', 'Заставка в галереї', c.thumbnail)}
      ${part('images', 'Ілюстрації', null, c.illustrations, c.illustrationsTotal)}
      ${part('text', 'Тексти', null, c.texts, c.textsTotal)}
    </div>`;
  }

  function renderHero() {
    const l = book.listing || {};
    const thumb = book.thumbnail;
    setHtml($('#bk-hero'), html`<div class="book-hero">
      <div class="hero-thumb ${thumb?.lqip ? 'lqip' : ''}" ${thumb?.lqip ? raw(`style="background-image:url(${thumb.lqip})"`) : ''} data-drop="thumbnail" ${thumb ? raw('data-act="zoom-thumb"') : ''}>
        ${thumb ? html`<img data-fade decoding="async" src="${assetUrl(thumb, 720)}" alt="Заставка книги">
            <div class="img-actions">
              ${ib('upload', 'Замінити заставку', 'data-act="pick" data-slot="thumbnail"', { cls: 'sm' })}
              ${ib('trash', 'Прибрати заставку', 'data-act="remove" data-slot="thumbnail"', { cls: 'sm danger' })}
            </div>
            <i class="crops"></i>`
          : html`<div class="drop-ph" data-act="pick" data-slot="thumbnail"><div class="drop-ico">${ic('image')}</div><b>Заставка</b>
              ${l.id ? ib('imageDown', 'Взяти головне фото лістингу', 'data-act="thumb-etsy"', { cls: 'sm' }) : ''}</div>`}
        ${busy.has('thumbnail') ? html`<div class="busy-overlay"><div class="spinner spinner-l"></div></div>` : ''}
      </div>
      <div class="hero-main">
        <textarea class="hero-title-input" id="bk-title" rows="1" spellcheck="false" aria-label="Назва книги">${book.title}</textarea>
        <div class="hero-meta">
          ${l.id ? html`<span class="chip chip-lg chip-mono" data-tip="Номер лістингу Etsy"><span class="svc-etsy" style="display:inline-grid">${ic('etsy', 'icon-s')}</span>#${l.id}</span>`
            : html`<span class="chip chip-lg chip-amber">без лістингу</span>`}
          ${book.canvaUrl ? html`<button type="button" class="chip chip-lg" data-act="open-canva" data-tip="Відкрити макет у Canva"><span class="svc-canva" style="display:inline-grid">${ic('canva', 'icon-s')}</span>Canva</button>`
            : html`<button type="button" class="chip chip-lg chip-amber" data-act="canva-link" data-tip="Додати посилання на макет у Canva">${ic('canva', 'icon-s')}без Canva</button>`}
          ${l.state && l.state !== 'active' ? html`<span class="chip chip-lg chip-amber">${l.state}</span>` : ''}
          ${l.verifiedAt ? html`<span class="chip chip-lg" data-tip="Лістинг перевірено ${dateTime(l.verifiedAt)}">${ic('shield')}</span>`
            : l.id ? html`<span class="chip chip-lg chip-amber" data-tip="Лістинг ще не перевірено в Etsy">${ic('alert')}</span>` : ''}
          ${book.archived ? html`<span class="chip chip-lg chip-purple" data-tip="Книга в архіві">${ic('archive')}</span>` : ''}
          <span class="spacer"></span>
          ${readiness()}
        </div>
        ${l.title && l.title !== book.title ? html`<div class="faint" style="font-size:12.5px">На Etsy: ${l.title}</div>` : ''}
      </div>
    </div>`);
    autosize($('#bk-title'));
    fadeImages($('#bk-hero'));
  }

  function renderCover() {
    const cover = book.cover;
    setHtml($('#bk-cover-head'), html`<span class="section-title">Обкладинка</span>
      ${cover ? html`<span class="num">${cover.width}×${cover.height}</span><span class="faint" style="font-size:12px">${bytes(cover.bytes)}</span>` : ''}`);
    setHtml($('#bk-cover'), html`<div class="stack">
      <div class="cover-box ${cover?.lqip ? 'lqip' : ''}" data-drop="cover" style="${cover ? `aspect-ratio:${cover.width} / ${cover.height}${cover.lqip ? `;background-image:url(${cover.lqip})` : ''}` : 'min-height:220px'}">
        ${cover ? html`<img data-fade decoding="async" src="${assetUrl(cover, 1400)}" alt="Обкладинка" data-zoom="cover"><div class="gutter"></div>
          <div class="img-actions">
            ${ib('expand', 'Переглянути', 'data-act="zoom" data-key="cover"', { cls: 'sm' })}
            ${ib('upload', 'Замінити обкладинку', 'data-act="pick" data-slot="cover"', { cls: 'sm' })}
            ${ib('trash', 'Видалити обкладинку', 'data-act="remove" data-slot="cover"', { cls: 'sm danger' })}
          </div>
          <i class="crops"></i>`
          : html`<div class="drop-ph" data-act="pick" data-slot="cover" style="min-height:220px"><div class="drop-ico">${ic('upload')}</div><b>Обкладинка</b><span>Перетягніть сюди повний розворот обкладинки</span></div>`}
        ${busy.has('cover') ? html`<div class="busy-overlay"><div class="spinner spinner-l"></div></div>` : ''}
      </div>
      ${textBlock('cover', 'Текст обкладинки')}
    </div>`);
    fadeImages($('#bk-cover'));
  }

  function textBlock(key, label) {
    const t = book.text[key] || '';
    return html`<div class="text-block" data-textblock="${key}">
      <div class="text-block-head"><span class="eyebrow">${label}</span><span class="spacer"></span>
        ${ib('copy', 'Копіювати текст', `data-act="copy-text" data-key="${key}" ${t ? '' : 'disabled'}`, { cls: 'sm' })}
        ${ib('edit', 'Редагувати', `data-act="edit-text" data-key="${key}"`, { cls: 'sm' })}</div>
      <div class="text-body ${t ? '' : 'empty-text'}" data-act="edit-text" data-key="${key}">${t ? highlightTokens(t) : 'Текст ще не додано — натисніть, щоб написати.'}</div>
    </div>`;
  }

  function renderPagesHead() {
    const c = book.completeness;
    setHtml($('#bk-pages-head'), html`
      <span class="section-title">Сторінки</span>
      <span class="num" data-tip="Сторінок з ілюстраціями">${c.illustrations}/16</span>`);
  }

  function rowHtml(key, i) {
    const s = book.slots[key];
    const label = key === 'page1' ? 'Присвята' : key === 'page30' ? 'Післяслово' : `Розворот ${key.slice(6)}`;
    const pages = key === 'page1' ? '1' : key === 'page30' ? '30' : pagesOf(+key.slice(6)).join('–');
    const t = book.text[key] || '';
    const textCol = html`<div class="slot-text" data-textcol="${key}">
      <div class="slot-text-head"><span class="slot-label">${label}</span><span class="slot-pages">${pages}</span><span class="spacer"></span>
        ${ib('copy', 'Копіювати текст', `data-act="copy-text" data-key="${key}" ${t ? '' : 'disabled'}`, { cls: 'sm' })}
        ${ib('edit', 'Редагувати', `data-act="edit-text" data-key="${key}"`, { cls: 'sm' })}</div>
      <div class="slot-text-body ${t ? '' : 'empty-text'}" data-act="edit-text" data-key="${key}">${t ? highlightTokens(t) : 'Текст ще не додано'}</div>
    </div>`;
    const busyOv = (slot) => busy.has(slot) ? html`<div class="busy-overlay"><div class="spinner spinner-l"></div></div>` : '';
    const bg = (asset) => (asset?.lqip ? raw(`style="background-image:url(${asset.lqip})"`) : '');
    const pageSq = (slot, asset, tag, hint) => html`<div class="page-sq ${asset?.lqip ? 'lqip' : ''}" data-drop="${slot}" ${slot.includes(':') ? raw('data-auto="1"') : ''} ${bg(asset)}>
      ${asset ? html`<img data-fade decoding="async" src="${assetUrl(asset, 720)}" alt="" data-zoom="${slot}" loading="lazy">
        <div class="img-actions">
          ${ib('expand', 'Переглянути', `data-act="zoom" data-key="${slot}"`, { cls: 'sm' })}
          ${ib('upload', 'Замінити', `data-act="pick" data-slot="${slot}"`, { cls: 'sm' })}
          ${slot.includes(':') && s.left && s.right ? ib('swap', 'Поміняти сторінки місцями', `data-act="swap" data-key="${key}"`, { cls: 'sm' }) : ''}
          ${ib('trash', 'Видалити', `data-act="remove" data-slot="${slot}"`, { cls: 'sm danger' })}
        </div>
        <span class="page-tag">${tag}</span>`
        : html`<div class="drop-ph" data-act="pick" data-slot="${slot}"><div class="drop-ico">${ic('upload')}</div><b>${hint}</b><span class="num">${tag}</span></div>`}
      ${busyOv(slot)}</div>`;
    const blank = (text) => html`<div class="page-sq blank"><span>${text}</span></div>`;

    let images;
    if (key === 'page1') images = html`<div class="slot-pages-pair">${blank('Форзац')}${pageSq('page1', s.image, '1', 'Присвята')}<i class="crops"></i></div>`;
    else if (key === 'page30') images = html`<div class="slot-pages-pair">${pageSq('page30', s.image, '30', 'Післяслово')}${blank('Нахзац')}<i class="crops"></i></div>`;
    else {
      const [lp, rp] = pagesOf(+key.slice(6));
      if (s.image) {
        images = html`<div class="spread-img ${s.image.lqip ? 'lqip' : ''}" data-drop="${key}" ${bg(s.image)}>
          <img data-fade decoding="async" src="${assetUrl(s.image, 1400)}" alt="" data-zoom="${key}" loading="lazy"><div class="gutter"></div>
          <div class="img-actions">
            ${ib('expand', 'Переглянути', `data-act="zoom" data-key="${key}"`, { cls: 'sm' })}
            ${ib('upload', 'Замінити розворот', `data-act="pick" data-slot="${key}"`, { cls: 'sm' })}
            ${ib('trash', 'Видалити', `data-act="remove" data-slot="${key}"`, { cls: 'sm danger' })}
          </div>
          <span class="page-tag">${lp}–${rp}</span>${busyOv(key)}<i class="crops"></i></div>`;
      } else {
        images = html`<div class="slot-pages-pair">${pageSq(`${key}:left`, s.left, String(lp), 'Ліва')}${pageSq(`${key}:right`, s.right, String(rp), 'Права')}<i class="crops"></i></div>`;
      }
    }
    // Entrance animation only on first paint (i >= 0); re-rendered rows just swap in place.
    return html`<div class="slot-row ${i >= 0 ? 'enter' : ''}" data-row="${key}" ${i >= 0 ? raw(`style="animation-delay:${Math.min(i * 30, 300)}ms"`) : ''}>${textCol}${images}</div>`;
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
    const foot = el(html`<div class="slot-text-foot" ${key === 'cover' ? raw('style="background:none;border:0;padding:8px 0 0"') : ''}>
      <span class="spacer"></span>
      ${ib('x', 'Скасувати', 'data-x="cancel"', { cls: 'sm', kbd: 'Esc' })}${ib('check', 'Зберегти', 'data-x="save"', { cls: 'sm primary', kbd: 'Ctrl+Enter' })}</div>`);
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

  // Several files, a folder or a ZIP: copied into the program, then laid out by the same rules as «Імпорт
  // з папки» (library.scan_folder) — one reading of file names for every way in (22.09.2026 audit: the drop
  // had rules of its own and took another JSON or a picture from an old sub-folder).
  async function importDropped(dropped) {
    toast('Отримую файли…', 'info', 2500);
    try { importFolder(await receiveDrop(dropped, null, { withText: true })); }
    catch (err) { toast(err.message, 'error', 6000); }
  }
  function hasAsset(slot) {
    const [base, part] = slot.split(':');
    if (base === 'cover' || base === 'thumbnail') return !!book[base];
    const s = book.slots[base];
    return part ? !!(s[part] || s.image) : !!(s.image || s.left || s.right);
  }

  // ---------------------------------------------------------------- folder import (native dialog, or a dropped ZIP)
  async function importFolder(path = null) {
    if (!path) {
      try { path = (await api('/api/app/pick-folder', { method: 'POST', body: { title: 'Оберіть папку з файлами книги' } })).path; }
      catch (err) { toast(err.message, 'error'); return; }
    }
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
          ${scan.mapping.cover ? html`<span class="chip chip-green">${ic('check', 'icon-s')}Обкладинка</span>` : html`<span class="chip">без обкладинки</span>`}
          <span class="chip ${slots.length ? 'chip-green' : ''}"><span class="num">${slots.length}</span> ${slots.length === 1 ? 'зображення' : 'зображень'}</span>
          ${scan.text ? html`<span class="chip chip-green">${ic('check', 'icon-s')}Текст ${scan.text.name}</span>` : html`<span class="chip">без тексту</span>`}
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
      // Missing texts are fine: those places simply stay empty.
      toast(res.problems.length ? `Імпортовано ${res.imported} з ${res.imported + res.problems.length} текстів` : 'Текст книги імпортовано повністю', 'success');
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
  function canvaDialog() {
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
      if (v !== (book.canvaUrl || '') && await patch({ canvaUrl: v })) toast(v ? 'Посилання на Canva збережено' : 'Посилання на Canva прибрано', 'success', 1400);
    };
    m.foot.querySelector('[data-c]').onclick = () => m.close();
    m.foot.querySelector('[data-go]').onclick = () => save(input.value.trim());
    m.foot.querySelector('[data-rm]')?.addEventListener('click', () => save(''));
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); save(input.value.trim()); } });
    input.select();
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
      key, src: assetUrl(a, 2600), full: Math.max(a.width, a.height) > 2600 ? assetUrl(a, 4096) : null,
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
      if (act === 'open-canva') { openExternal(book.canvaUrl); return; }
      if (act === 'canva-link') { canvaDialog(); return; }
      if (act === 'import-folder') { importFolder(); return; }
      if (act === 'add-files') { $('#bk-many').click(); return; }
      if (act === 'thumb-etsy') { e.stopPropagation(); thumbFromEtsy(); return; }
      if (act === 'text-menu') {
        menu(t, [
          { label: 'Завантажити файл JSON…', icon: 'upload', onClick: () => $('#bk-json').click() },
          { label: 'Вставити JSON вручну', icon: 'edit', onClick: pasteJsonDialog },
          '-',
          { label: 'Скопіювати весь текст', icon: 'copy', onClick: () => { const a = allText(); a ? copyText(a, 'Увесь текст книги скопійовано') : toast('У книзі ще немає тексту'); } },
          { label: 'Скопіювати як JSON', icon: 'braces', onClick: async () => copyText(JSON.stringify(await api(`/api/library/books/${id}/text.json`), null, 2), 'JSON скопійовано') },
        ]);
        return;
      }
      if (act === 'more') {
        menu(t, [
          ...(book.listing?.id ? [{ label: 'Оновити дані з Etsy', icon: 'sync', onClick: refreshListing },
            { label: 'Фото лістингу як заставка', icon: 'imageDown', onClick: thumbFromEtsy }] : []),
          { label: book.canvaUrl ? 'Змінити посилання на Canva…' : 'Додати посилання на Canva…', icon: 'link', onClick: canvaDialog },
          { label: 'Експорт файлів у папку…', icon: 'download', onClick: exportBook },
          { label: 'Відкрити папку книги', icon: 'folderOpen', onClick: () => api(`/api/library/books/${id}/open-folder`, { method: 'POST', body: {} }).catch((er) => toast(er.message, 'error')) },
          '-',
          book.archived ? { label: 'Відновити з архіву', icon: 'restore', onClick: () => setArchived(false) } : { label: 'Перенести в архів', icon: 'archive', onClick: () => setArchived(true) },
          { label: 'Видалити книгу…', icon: 'trash', danger: true, onClick: deleteBook },
        ]);
      }
    }),
    on(view, 'click', '[data-zoom]', (e, img) => zoom(img.dataset.zoom)),
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
  });
  view.addEventListener('keydown', (e) => {
    if (e.target.id === 'bk-title' && e.key === 'Enter') { e.preventDefault(); e.target.blur(); }
  });
  view.addEventListener('focusout', async (e) => {
    if (e.target.id === 'bk-title') {
      const v = e.target.value.trim();
      if (!v) { e.target.value = book.title; autosize(e.target); return; }
      if (v !== book.title && await patch({ title: v })) { toast('Назву збережено', 'success', 1400); refreshInfo(); }
    }
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
    if (files.length) importDropped({ entries: [], files });
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
    const dropped = dropContents(e); // must be read while the drop event runs
    const files = [...e.dataTransfer.files];
    if (files.length === 1 && /\.json$/i.test(files[0].name)) { importTextJson(await files[0].text()); return; }
    if (target && files.length === 1) { uploadTo(target.dataset.drop, files[0], !!target.dataset.auto); return; }
    if (target && files.length === 2 && /^spread\d+/.test(target.dataset.drop)) {
      const base = target.dataset.drop.split(':')[0];
      const [a, b] = files.sort((x, y) => naturalCompare(x.name, y.name));
      await uploadTo(`${base}:left`, a); await uploadTo(`${base}:right`, b);
      return;
    }
    importDropped(dropped); // a folder, a ZIP or several files: whatever they hold goes to its place
  };
  view.addEventListener('dragover', onDragOver);
  view.addEventListener('dragleave', onDragLeave);
  view.addEventListener('drop', onDrop);

  // Esc steps back to the library when nothing else (a dialog, the viewer, a text field) owns the key.
  const onKey = (e) => {
    if (e.key !== 'Escape' || e.defaultPrevented) return;
    if (document.querySelector('.modal-root, .lightbox, .menu') || /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName || '')) return;
    location.hash = '#/library';
  };
  document.addEventListener('keydown', onKey);

  return {
    unmount() {
      offs.forEach((f) => f());
      document.removeEventListener('keydown', onKey);
    },
  };
}
