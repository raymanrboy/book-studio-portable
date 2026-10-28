// «Обкладинка» (the owner, 2026-10-25): the book's cover as a step of its own, like the Mockups and the photo mockups — a
// tool in «Інструменти» that works on one Workshop book (`#/cover/<book>`; without one it asks which). One way since
// 2026-10-27 («Два квадрати» taken out): the 2:1 picture — «Генерувати» pastes the reference, the layout guide picked
// under the picture (where the title and the name's room go), then Agent 6's prompt with the guide's words put in —
// then its margins outpainted on the printer's template (the cover card the Workshop had, 2026-09-26).
import { api, post, html, ic, ib, raw, setHtml, on, toast, menu, upload, copyText, fadeImages, patch, backToTools } from '../lib.js';
import { store } from '../info.js';
import { openLightbox } from '../lightbox.js';
import { picture } from '../workshop-bits.js';
import { bookTile } from '../book-tile.js';
import { watch, refresh, act, startGen, genAction, paintGenBar, waitingFor } from '../workshop-live.js';
import { rowTemplates, waitChip } from './workshop-rows.js';

const IMG_RE = /\.(png|jpe?g|webp)$/i;
// What the page remembers about each book until a restart: the 2:1 stage picked by hand, the lines, the prompts shown whole.
const memory = new Map();

export async function mount(view, [rawId]) {
  return rawId ? bookPage(view, decodeURIComponent(rawId)) : pickBook(view);
}

// ---------------------------------------------------------------- no book yet: which one
async function pickBook(view) {
  let data;
  try { data = await api('/api/workshop/books'); } catch (err) {
    setHtml(view, html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`);
    return null;
  }
  const list = data.books.filter((b) => !b.abc);
  setHtml(view, html`
    <div class="page-head">${backToTools()}<div><h1 class="page-title">Обкладинка</h1><div class="page-sub">Для якої книги?</div></div></div>
    ${list.length ? html`<div class="lib-grid">${list.map((b, i) => bookTile({
      key: b.id, title: b.title, number: b.number, i,
      cover: { src: b.thumb ? picture(b, b.thumb.area, b.thumb.name, 720) : '', cls: b.thumb?.face ? 'face' : b.thumb?.kind === 'cover' ? 'front' : '', letter: (b.title || '?').charAt(0).toUpperCase() },
      sub: html`<span class="serif">${b.coverTitle || ''}</span>`,
    }))}</div>` : html`<div class="empty">${ic('workshop')}<div>У Майстерні ще немає книг.</div></div>`}`);
  view.querySelectorAll('img[data-fade]').length && fadeImages(view);
  const off = on(view, 'click', '[data-open]', (e, t) => { location.hash = `#/cover/${encodeURIComponent(t.dataset.open)}`; });
  return { unmount: off };
}

// ---------------------------------------------------------------- one book
async function bookPage(view, id) {
  const url = (tail = '') => `/api/workshop/books/${encodeURIComponent(id)}${tail}`;
  let first;
  try { first = await api(url()); } catch (err) {
    setHtml(view, html`<div class="page-head">${backToTools()}<div><h1 class="page-title">Обкладинка</h1></div></div>
      <div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`);
    return null;
  }
  let b = first.book;
  if (!memory.has(id)) memory.set(id, { cover: 0, guides: true, open: new Set() });
  const mem = memory.get(id);
  const uploading = new Map();
  // Opened from the book's «Обкладинка» step the way back leads to that book; from «Інструменти» — to the list of books.
  const fromBook = store.here === `#/workshop/${encodeURIComponent(id)}` || store.here === `#/workshop/${id}` ? store.here : '';
  const pic = (area, name, w) => picture(b, area, name, w);
  const { saveBtn, waitCover, busyCover, genButton, promptBlock, textBlock, upChip, upBtn } = rowTemplates({ id, book: () => b, mem, uploading });

  setHtml(view, html`
    <div class="page-head">
      ${fromBook ? html`<a class="back-link" href="${fromBook}" aria-label="До книги" data-tip="До книги">${ic('arrowLeft')}</a>`
        : html`<a class="back-link" href="#/cover" aria-label="До списку книг" data-tip="До списку книг">${ic('arrowLeft')}</a>`}
      <div><h1 class="page-title">Обкладинка</h1><div class="page-sub" id="cv-sub"></div></div>
      <div class="page-actions" id="cv-actions"></div>
    </div>
    <div class="ws-genbar-slot" id="cv-gen"></div>
    <div class="cv-body" id="cv-body"></div>
    <input type="file" id="cv-file" accept=".png,.jpg,.jpeg,.webp" hidden>`);
  const $ = (s) => view.querySelector(s);

  // ---------------------------------------------------------------- the head
  function head() {
    return [
      ['sub', html`<span>${b.number != null ? `№${b.number} ` : ''}${b.title}</span>`],
    ];
  }
  function actions() {
    return [['t', html`<div class="tools">${ib('folderOpen', 'Папка сторінок книги — там Cover.png', 'data-act="open" data-what="pictures"')}
        ${ib('workshop', 'Книга в Майстерні', 'data-act="to-book"')}</div>`]];
  }

  const box = (g) => `left:${(g[0] * 100).toFixed(3)}%;top:${(g[1] * 100).toFixed(3)}%;width:${(g[2] * 100).toFixed(3)}%;height:${(g[3] * 100).toFixed(3)}%`;
  const pct = (v, of) => `${((v / of) * 100).toFixed(3)}%`;

  // A cover made of the two squares (2026-10-25…27) stays the book's until a new one: shown with Gelato's lines.
  function gelatoLines(G) {
    return html`<div class="ws-tpl" aria-hidden="true">
      <span class="ws-tpl-trim" style="${box(G.trim)}"></span><span class="ws-tpl-spine" style="${box(G.spine)}"></span>
      ${G.hinges.map((h) => html`<span class="ws-tpl-hinge" style="${box(h)}"></span>`)}
      <span class="ws-tpl-safe" style="${box(G.back)}"><em>задня</em></span><span class="ws-tpl-safe" style="${box(G.front)}"><em>лицьова</em></span></div>`;
  }

  // ---------------------------------------------------------------- what goes into the clipboard with the prompt
  function refChip() {
    const c = b.cover, t = c.tool, set = t.settings.ref;
    const spread = set.startsWith('spread') ? t.refs.find((r) => r.key === set) : null;
    const agent = set !== 'none' && !spread ? c.refs?.cover : '';
    const label = spread ? spread.label : agent ? 'з промпту агента' : 'без референсу';
    const thumb = spread ? html`<img alt="" src="${pic('pictures', spread.page, 120)}">` : agent ? html`<img alt="" src="${pic('agent', agent, 120)}">` : ic('image', 'icon-s');
    return html`<button type="button" class="cv-ref ${spread || agent ? '' : 'none'}" data-act="ref-menu" data-tip="Референс: персонажі й стиль — у буфер першою картинкою">
      <span class="cv-ref-thumb">${thumb}</span><span>${label}</span>${ic('chevDown', 'icon-s')}</button>`;
  }

  function guidePicker() {
    const t = b.cover.tool, now = t.settings.guide;
    const one = (name, label, inner) => html`<button type="button" role="radio" aria-checked="${name === now}" class="cv-guide cv-guide-wide ${name === now ? 'on' : ''}"
      data-act="guide" data-guide="${name}" data-tip="${label}" aria-label="${label}">${inner}</button>`;
    return html`<div class="cv-guides" role="radiogroup" aria-label="Схема">
      ${t.guides.map((g) => one(g.name, `Схема: ${g.label}`, html`<img alt="" src="${g.src}">`))}
      ${one('none', 'Без схеми — тільки референс і промпт', ic('x', 'icon-s'))}
    </div>`;
  }

  const ratio = (s) => (s && s[0] && s[1] ? raw(` style="aspect-ratio:${s[0]} / ${s[1]}"`) : '');
  let artSeen = null;   // the 2:1 picture at the last draw: a new one turns the card to its margins
  function wideBody() {
    const r = b.rows.find((x) => x.key === 'cover');
    const c = b.cover;
    const artV = c.art ? b.v?.[`originals/${c.art}`] || c.art : '';
    if (artSeen !== null && artV && artSeen !== artV) mem.cover = 0;
    artSeen = artV;
    const stage = mem.cover || (c.final || c.art ? 2 : 1);
    const w1 = waitingFor(id, 'cover', ''), w2 = waitingFor(id, 'cover-wrap', '');
    const stepBtn = (n, label, done, now) => html`<button type="button" class="ws-cv-step ${stage === n ? 'on' : ''} ${done ? 'done' : ''}" data-act="cover-stage" data-stage="${n}">
      <span class="ws-cv-no">${done ? ic('check') : n}</span>${label}${now ? html`<span class="ws-pulse"></span>` : ''}</button>`;
    let pane;
    if (stage === 1) {
      const artFrame = c.art
        ? html`<div class="ws-drop" data-drop="cover" data-variant=""><div class="ws-art ws-wide"${ratio(c.artMarks.source)}>
            <img data-fade alt="Обкладинка" src="${pic('originals', c.art, 1400)}" data-act="zoom" data-key="cover-art">
            ${saveBtn('originals', c.art, '', 'Зберегти обкладинку як…')}
            ${c.artMarks.source ? html`<div class="ws-marks"><span class="chip ws-mark num">${c.artMarks.source[0]}×${c.artMarks.source[1]}</span></div>` : ''}
            <div class="img-actions">${ib('upload', 'Замінити файлом', 'data-act="pick" data-key="cover"', { cls: 'sm' })}${ib('trash', 'Прибрати обкладинку (і її поля)', 'data-act="remove" data-key="cover"', { cls: 'sm danger' })}</div>
          </div>${busyCover('cover')}${w1 ? waitCover('Чекаю обкладинку…') : ''}</div>`
        : html`<div class="ws-frame"><div class="ws-drop" data-drop="cover" data-variant=""><button type="button" class="ws-ph" data-act="pick" data-key="cover">
            <span class="ws-half">задня</span><span class="ws-half">передня</span>
            <span class="ws-ph-text"><span class="drop-ico">${ic('upload')}</span><b>Перетягніть обкладинку</b><span>або клацніть, щоб обрати файл</span></span></button>
            ${busyCover('cover')}${w1 ? waitCover('Чекаю обкладинку з «Завантажень»…') : ''}</div></div>`;
      // the prompt as «Генерувати» pastes it: with the guide's words, without a reference it has no picture for
      pane = html`${promptBlock({ ...r, prompt: c.tool.prompt || r.prompt }, '', 'Промпт обкладинки (агент 6 + схема)')}${artFrame}
        <div class="cv-guides-row"><span class="eyebrow" data-tip="Іде в буфер після референсу: де назва й порожнє місце під ім'я">Схема</span>${guidePicker()}</div>${textBlock(r)}
        ${c.art ? html`<div class="ws-cv-next"><button class="btn btn-primary" data-act="cover-stage" data-stage="2">Далі: поля${ic('chevRight')}</button></div>` : ''}`;
    } else {
      // The picture laid on the printer's template, white all round → the generator fills the margins → Cover.png at the
      // template's exact size. The template's lines can be shown over it.
      const lay = c.layout || {};
      const [cw, ch] = lay.size || [1, 1];
      const [ax, ay, aw, ah] = lay.art || [0, 0, cw, ch];
      const G = c.guides;
      const gsq = !!c.finalSquares && !!c.final;     // a cover made of squares is still the book's: its own lines
      const lines = !mem.guides || c.skipped ? '' : gsq ? gelatoLines(G) : html`<div class="ws-tpl" aria-hidden="true">
          <span class="ws-tpl-trim" style="${box(G.trim)}"></span><span class="ws-tpl-spine" style="${box(G.spine)}"></span>
          <span class="ws-tpl-safe" style="${box(G.back)}"><em>задня</em></span><span class="ws-tpl-safe" style="${box(G.front)}"><em>передня</em></span></div>`;
      const tpx = c.template.px;
      const shown = c.final
        ? html`<img data-fade alt="Обкладинка з полями" src="${pic('pictures', c.final, 2600)}" data-act="zoom" data-key="cover">${saveBtn('pictures', c.final, '', 'Зберегти готову обкладинку як…')}`
        : c.expanded ? html`<img data-fade alt="Обкладинка з білими полями" src="${pic('originals', c.expanded, 2600)}"><span class="ws-cv-inner" style="left:${pct(ax, cw)};top:${pct(ay, ch)};width:${pct(aw, cw)};height:${pct(ah, ch)}"></span>` : '';
      const where = gsq ? 'Gelato' : 'друкарні';
      pane = html`<div class="ws-cv-bar">
          <div class="tools">${ib('guides', mem.guides ? `Сховати лінії шаблону ${where}` : `Показати лінії шаблону ${where}`, 'data-act="guides"', { cls: mem.guides ? 'on' : '' })}</div>
          <span class="ws-cv-info num">${c.final ? (c.skipped ? 'без полів' : `${tpx[0]}×${tpx[1]} px · ${c.template.dpi} dpi`) : c.expanded ? `поля за шаблоном · ${cw}×${ch} px` : 'спершу картинка'}</span>
          ${c.final ? upChip('cover-wrap', c.wrapMarks) : ''}
          <span class="spacer"></span>
          ${c.final ? '' : html`<button class="btn btn-sm btn-ghost" data-act="no-margins" data-tip="Взяти обкладинку як є, без полів — вона стане Cover.png">Без полів</button>`}
          ${w2 ? waitChip('чекаю обкладинку з полями')
            : html`<button class="btn btn-sm ${c.final ? '' : 'btn-primary'}" data-act="gen" data-key="cover-wrap" data-tip="У буфер: обкладинка з полями, потім промпт аутпейнту — Ctrl+V у Chrome сам перемикає">${ic(c.final ? 'regenerate' : 'generate')}${c.final ? 'Ще раз' : 'Генерувати поля'}</button>`}
        </div>
        <div class="ws-drop" data-drop="cover-wrap" data-variant="">
          <div class="ws-art ws-wide ${c.final ? '' : 'margins'}"${ratio(c.final && !c.skipped ? tpx : c.final ? c.artMarks.source : [cw, ch])}>${shown}${lines}
            ${c.final ? html`<div class="img-actions">${upBtn('cover-wrap', c.wrapMarks)}${ib('copy', 'Копіювати готову обкладинку як картинку', 'data-act="copy-picture" data-key="cover"', { cls: 'sm' })}
              ${ib('upload', 'Замінити файлом', 'data-act="pick" data-key="cover-wrap"', { cls: 'sm' })}
              ${ib('trash', 'Прибрати поля (сама обкладинка лишиться)', 'data-act="remove" data-key="cover-wrap"', { cls: 'sm danger' })}</div>` : ''}
          </div>${busyCover('cover-wrap')}${w2 ? waitCover('Чекаю обкладинку з полями…') : ''}</div>
        ${c.outpaint ? promptBlock({ key: 'cover-wrap', prompt: c.outpaint }, '', 'Промпт аутпейнту — заповнити тільки білі поля') : ''}`;
    }
    return [['wide', html`<section class="ws-row ws-cover ${w1 || w2 ? 'waiting' : ''}" id="row-cover">
      <div class="ws-row-head">
        <span class="ws-cv-steps">${stepBtn(1, 'Картинка', !!c.art, w1)}<i class="ws-cv-line ${c.art ? 'on' : ''}"></i>${stepBtn(2, 'Поля', !!c.final, w2)}</span>
        <span class="ws-row-act">${stage === 1 ? html`${refChip()}${genButton({ ...r, pictures: c.art ? [c.art] : [] })}` : ''}</span></div>
      <div class="ws-cv-body"><div class="ws-cv-pane">${pane}</div></div>
    </section>`]];
  }

  // ---------------------------------------------------------------- drawing
  function draw() {
    const drawn = [...patch($('#cv-sub'), head()), ...patch($('#cv-actions'), actions()),
      ...patch($('#cv-body'), wideBody())];
    drawn.forEach(fadeImages);
    paintGenBar($('#cv-gen'), id);
    uploading.forEach((_, key) => paintProgress(key));
  }
  function paintProgress(key) {
    const bar = view.querySelector(`[data-up="${CSS.escape(key)}"]`);
    if (!bar) return;
    const p = uploading.get(key) || 0;
    bar.parentElement.classList.toggle('proc', p >= 1);
    bar.style.transform = p >= 1 ? '' : `scaleX(${p})`;
  }

  const reload = async () => {
    try { b = (await api(url())).book; } catch (err) {
      if (err.status === 404) { toast('Книги більше немає в Майстерні', 'info'); location.hash = '#/cover'; }
      return;
    }
    draw();
  };
  const unwatch = watch({ book: id, sig: first.sig, gen: first.gen }, reload);
  draw();

  // ---------------------------------------------------------------- pictures in, out
  async function uploadTo(key, file) {
    if (!IMG_RE.test(file.name)) { toast(`«${file.name}» — не картинка (PNG, JPG, WEBP)`, 'error'); return; }
    if (uploading.has(key)) { toast('Попередня картинка ще вантажиться', 'info'); return; }
    uploading.set(key, 0);
    draw();
    try {
      const q = new URLSearchParams({ key, name: file.name });
      const res = await upload(url(`/place?${q}`), file, (p) => { uploading.set(key, p); paintProgress(key); });
      toast(res.note || 'Готово', res.cut ? 'info' : 'success', res.cut ? 4000 : 2600);
    } catch (err) { toast(err.message, 'error'); }
    uploading.delete(key);
    await reload();
    refresh();
  }
  async function removePicture(btn, key) {
    const done = await act(btn, () => post(url('/remove'), { key }));
    if (!done?.undo) return;
    const what = { cover: 'Обкладинку прибрано', 'cover-wrap': 'Поля обкладинки прибрано' }[key];
    toast(what || 'Картинку прибрано', 'success', 9000, {
      undo: { label: 'Скасувати', run: async () => { await post(url('/restore'), { undo: done.undo }); toast('Повернуто', 'success', 2000); reload(); } },
    });
    reload();
  }
  const settings = (btn, body) => act(btn, () => post(url('/cover-tool'), body)).then((res) => res && reload());

  function zoom(key) {
    const c = b.cover, items = [];
    const push = (k, area, name, title, sub) => items.push({ key: k, src: pic(area, name, 1400), full: pic(area, name, 2600), title, sub,
      onOriginal: () => post('/api/workshop/open', { book: id, what: area, name }).catch((err) => toast(err.message, 'error')) });
    if (c.final) push('cover', 'pictures', c.final, 'Обкладинка', c.skipped ? 'без полів' : c.finalSquares ? 'з двох квадратів, Gelato 458×246 мм' : 'з полями, за шаблоном друкарні');
    if (c.art) push('cover-art', 'originals', c.art, 'Обкладинка 2:1 · картинка', 'як її зробив генератор');
    openLightbox(items, Math.max(0, items.findIndex((it) => it.key === key)));
  }

  function refMenu(btn) {
    const c = b.cover, t = c.tool;
    const choose = (ref) => () => settings(btn, { ref });
    menu(btn, [
      ...(c.refs?.cover ? [{ label: `З промпту агента — ${c.refs.cover}`, icon: 'agent', onClick: choose('') }] : []),
      ...t.refs.map((r) => ({ label: r.label, icon: 'spread', onClick: choose(r.key) })),
      { label: 'Без референсу', icon: 'x', onClick: choose('none') },
    ]);
  }

  // ---------------------------------------------------------------- events
  const offs = [on(view, 'click', '[data-act]', (e, t) => {
    const a = t.dataset.act, key = t.dataset.key || '';
    if (a === 'open') { act(t, () => post('/api/workshop/open', { book: id, what: t.dataset.what })); return; }
    if (a === 'to-book') { location.hash = `#/workshop/${encodeURIComponent(id)}`; return; }
    if (a === 'guides') { mem.guides = !mem.guides; draw(); return; }
    if (a === 'cover-stage') { mem.cover = Number(t.dataset.stage); draw(); return; }
    if (a === 'guide') { if (!t.classList.contains('on')) settings(t, { guide: t.dataset.guide }); return; }
    if (a === 'ref-menu') { refMenu(t); return; }
    if (a === 'gen') { startGen(t, { book: id, key, variant: '' }); return; }
    if (a === 'pick') { pickFor = key; $('#cv-file').click(); return; }
    if (a === 'remove') { removePicture(t, key); return; }
    if (a === 'zoom') { zoom(key); return; }
    if (a === 'save') { act(t, () => post(url('/save-as'), { area: t.dataset.area, name: t.dataset.name, variant: '' }), (r) => (r.saved ? `Збережено: ${r.name}` : null)); return; }
    if (a === 'copy-picture') { act(t, () => post(url('/copy-picture'), { key }), 'Обкладинка в буфері — вставте куди треба'); return; }
    if (a === 'no-margins') { act(t, () => post(url('/no-margins'), {}), (r) => r.note).then(() => reload()); return; }
    if (a === 'upscale-row') { act(t, () => post(url('/upscale/start'), { key }), 'У черзі на апскейл'); return; }
    if (a === 'copy' && t.dataset.what === 'text') {
      const r = b.rows.find((x) => x.key === key);
      if (r?.text) copyText(r.text, 'Текст скопійовано');
      return;
    }
    if (a === 'copy') {
      const prompt = key === 'cover-wrap' ? b.cover.outpaint : b.cover.tool.prompt || b.rows.find((r) => r.key === 'cover')?.prompt;
      if (prompt) copyText(prompt, 'Промпт скопійовано');
      return;
    }
    if (a === 'whole-prompt') { if (mem.open.has(key)) mem.open.delete(key); else mem.open.add(key); draw(); }
  }), on(view, 'click', '[data-gen]', (e, t) => genAction(t, t.dataset.gen))];

  let pickFor = '';
  $('#cv-file').addEventListener('change', (e) => {
    const f = e.target.files[0];
    e.target.value = '';
    if (f && pickFor) uploadTo(pickFor, f);
  });

  // A picture dragged in from Explorer lands in the frame it is dropped on (a drag out of Book Studio itself is shut out by app.js).
  const files = (e) => [...(e.dataTransfer?.types || [])].includes('Files');
  let hot = null;
  const mark = (target) => {
    if (target === hot) return;
    hot = target;
    view.querySelectorAll('.drop-hot').forEach((x) => x.classList.remove('drop-hot'));
    target?.classList.add('drop-hot');
  };
  const onOver = (e) => { if (!files(e)) return; e.preventDefault(); e.dataTransfer.dropEffect = 'copy'; mark(e.target.closest('[data-drop]')); };
  const onLeave = (e) => { if (!e.relatedTarget || !view.contains(e.relatedTarget)) mark(null); };
  const onDrop = (e) => {
    if (!files(e)) return;
    e.preventDefault();
    mark(null);
    const target = e.target.closest('[data-drop]');
    if (!target) { toast('Перетягніть картинку на її рамку', 'info'); return; }
    const dropped = [...e.dataTransfer.files].filter((f) => IMG_RE.test(f.name));
    if (dropped.length !== 1) { toast(dropped.length ? 'Одна картинка — в одну рамку' : 'Це не картинка (PNG, JPG, WEBP)', 'error'); return; }
    uploadTo(target.dataset.drop, dropped[0]);
  };
  view.addEventListener('dragover', onOver);
  view.addEventListener('dragleave', onLeave);
  view.addEventListener('drop', onDrop);

  return {
    navFor: () => (fromBook ? '#/books' : null),
    unmount() { unwatch(); offs.forEach((off) => off()); },
  };
}
