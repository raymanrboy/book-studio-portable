// Mockups, step 4 — «Слайди для лістингу» (the owner, 29.09.2026: "after the Photoshop script the Mockups page offers
// the next step; I press it and they are made by themselves; then a button offers to go into our editor"). Above it,
// how far the pictures without background are (cut while Photoshop works — studio/slides/cutout.py). The six are
// made from the template (studio/slides/work.py); the editor is its own page, loaded only when opened (#/slides/…).
import { api, post, html, ic, ib, setHtml, media, toast, runJob, fadeImages, plural, confirmBox, menu } from '../lib.js';
import { openLightbox } from '../lightbox.js';

const SHOT_W = 480;
const SLIDES = ['слайд', 'слайди', 'слайдів'];
const TITLES = ['Made just for them', 'Choose your format', 'Dedication & afterword', 'Unique little poems',
  'Personalization made simple', 'Thank you'];

export function slidesStep({ view, st, stepNo, tellDone, busy, blinkFinish }) {
  const sl = {
    numbers: { pages: 24, poems: 11 },
    run: null,        // {step, percent, rows}
    result: null,     // {set, folder, pictures: [{slide, name, v}], missing, seconds}
    error: '',
    cuts: null,       // {files: {name: state}, busy, noBg}
    folder: '',       // the folder the cuts are asked for
    scheme: '',       // the scheme the six start from — chosen here, before they are made; '' = the default for new books
    schemes: null,    // the schemes to choose from [{key, name, default}]
  };
  let gone = false, timer = 0;
  const $ = (sel) => view.querySelector(sel);
  const box = () => $('#mk-s5');
  const ready = () => !!st.result && !st.result.cancelled && st.result.saved.length > 0;
  const folder = () => st.result?.folder || '';
  const book = () => st.result?.workshop || '';   // the Workshop book the run was for
  const target = () => (book() ? `workshop=${encodeURIComponent(book())}` : `folder=${encodeURIComponent(folder())}`);

  // ---------------------------------------------------------------- the cut-outs (polled while any is on its way)
  async function pollCuts() {
    clearTimeout(timer);
    if (gone || !folder()) return;
    try {
      sl.cuts = await api(`/api/slides/cutouts?${target()}`);
      sl.folder = folder();
    } catch { /* the folder went: nothing to say */ }
    if (gone) return;
    paintCuts();
    const running = !!st.run || sl.cuts?.busy;
    if (running && view.isConnected) timer = setTimeout(pollCuts, 1500);
  }

  function cutsLine() {
    // this book's pictures only (a folder may hold an earlier book's too)
    const mine = new Set([...(st.result?.saved || []), ...(st.finished?.saved || [])]);
    const files = Object.entries(sl.cuts?.files || {}).filter(([name]) => !mine.size || mine.has(name));
    if (!files.length) return '';
    const done = files.filter(([, v]) => v === 'done').length;
    const failed = files.filter(([, v]) => v.startsWith('error')).map(([n]) => n);
    const going = files.length - done - failed.length;
    return html`<div class="sl-cuts ${going ? 'going' : 'ok'}">
      ${going ? html`<span class="spinner"></span>` : ic('check', 'icon-s')}
      <span class="grow">Без фону · <span class="num">${done}/${files.length}</span>${going ? ' — вирізаю, поки Photoshop працює' : ''}</span>
      ${done ? ib('folderOpen', 'Відкрити папку «Без фону»', `data-act="open-nobg" data-path="${sl.cuts.noBg}"`, { cls: 'sm' }) : ''}
    </div>${failed.length ? html`<div class="notice notice-warn">${ic('alert')}<div>Не вирізались: ${failed.join(', ')}</div></div>` : ''}`;
  }
  function paintCuts() {
    const line = $('#sl-cuts');
    if (line) setHtml(line, cutsLine());
  }

  // ---------------------------------------------------------------- the scheme (2026-09-30: "a new listing — and I can pick the scheme at once")
  async function loadSchemes() {
    sl.schemes = [];
    try { sl.schemes = (await api('/api/slides/presets?w=template')).presets.filter((x) => x.kind === 'scheme'); } catch { /* the editor still offers it */ }
    if (!gone) paint();
  }
  const schemeNow = () => sl.schemes?.find((x) => x.key === sl.scheme) || sl.schemes?.find((x) => x.default) || null;

  // ---------------------------------------------------------------- the card
  function paint() {
    const b = box();
    if (!b) return;
    const show = ready() || !!sl.result || !!sl.run;
    b.hidden = !show;
    if (!show) return;
    if (sl.schemes === null) loadSchemes();
    if (folder() && folder() !== sl.folder) pollCuts();
    const head = html`<div class="row">${stepNo(4, !!sl.result)}<h3 class="card-title grow">Слайди для лістингу</h3>
      ${sl.result && !sl.run ? ib('regenerate', 'Зробити слайди заново — зі схеми (ваші правки цієї книги пропадуть)', 'data-act="sl-again"', { cls: 'sm' }) : ''}</div>`;
    let body;
    if (sl.run) body = runHtml();
    else if (sl.result) body = resultHtml();
    else body = offerHtml();
    setHtml(b, html`${head}<div id="sl-cuts">${cutsLine()}</div>${body}
      ${sl.error ? html`<div class="notice notice-error">${ic('alertCircle')}<div>${sl.error}</div></div>` : ''}`);
    fadeImages(b);
  }

  function offerHtml() {
    return html`${sl.schemes?.length > 1 ? html`<button type="button" class="btn btn-block" data-act="sl-scheme" data-tip="Шість квадратних картинок для Etsy почнуться з цієї схеми; потім їх можна правити в редакторі">
        ${ic('template', 'icon-s')}<span class="truncate">Схема: ${schemeNow()?.name || '—'}</span>${ic('chevDown', 'icon-s')}</button>` : ''}
      <div class="sl-nums">
        <label class="field"><span class="field-label">Сторінок</span><input class="input num" type="number" min="1" max="999" data-num="pages" value="${sl.numbers.pages}"></label>
        <label class="field"><span class="field-label">Віршів</span><input class="input num" type="number" min="1" max="999" data-num="poems" value="${sl.numbers.poems}"></label>
      </div>
      <div class="sl-ghosts" aria-hidden="true">${TITLES.map((t, i) => html`<div class="sl-ghost"><span class="num">${i + 1}</span><small>${t}</small></div>`)}</div>
      <button type="button" class="btn btn-primary btn-block" data-act="sl-make">${ic('images')}Зробити слайди</button>`;
  }

  function runHtml() {
    const r = sl.run;
    const icon = (s) => (s === 'done' ? ic('check') : s === 'work' ? html`<span class="spinner"></span>` : html`<i class="mk-dot"></i>`);
    return html`<div class="mk-run">
      <div class="row mk-run-now"><span class="spinner"></span><span class="grow truncate" id="sl-step">${r.step}</span>
        <span class="num faint" id="sl-pct">${Math.round(r.percent)}%</span></div>
      <div class="progress"><i id="sl-bar" style="transform:scaleX(${Math.max(3, r.percent) / 100})"></i></div>
      <div class="mk-rows" id="sl-rows">${(r.rows || []).map((row, i) => html`<div class="mk-row ${row.state}"><span class="mk-row-ico">${icon(row.state)}</span>
        <span class="grow truncate"><span class="num faint">${i + 1}</span> · ${row.title}</span></div>`)}</div>
    </div>`;
  }

  function resultHtml() {
    const r = sl.result;
    const count = r.pictures.length;
    return html`<div class="result-card mk-result">
      <h4>${ic('checkCircle')}<span class="grow">Готово · <span class="num">${count}</span> ${plural(count, SLIDES)}</span>
        ${r.seconds ? html`<span class="mk-secs num">${r.seconds} с</span>` : ''}
        ${ib('folderOpen', 'Відкрити папку зі слайдами', `data-act="open-out" data-path="${r.folder}"`, { cls: 'sm' })}</h4>
      <div class="sl-shots">${r.pictures.map((p, i) => html`<div class="sl-shot">
        <button type="button" class="mk-shot" data-act="sl-view" data-i="${i}" aria-label="${p.name}" data-tip="${p.name}">
          <img data-fade alt="" draggable="false" src="${media(`/media/slides/out/${r.set}/${p.slide}`, { w: SHOT_W, v: p.v })}"></button>
        ${ib('edit', `Правити слайд ${i + 1}`, `data-act="sl-edit" data-slide="${p.slide}"`, { cls: 'sm sl-pen' })}
      </div>`)}</div>
      ${r.missing?.length ? html`<div class="notice notice-warn">${ic('alert')}<div>Не було: ${r.missing.join(', ')} — на слайдах замість них порожні місця; в редакторі можна поставити інший мокап.</div></div>` : ''}
      <button type="button" class="btn btn-block" data-act="sl-edit" data-slide="slide1">${ic('edit')}Відкрити в редакторі</button>
    </div>`;
  }

  // ---------------------------------------------------------------- making them
  async function make(fresh = false) {
    if (sl.run || st.run) return;
    if (st.pending) {  // Cover 1 and Dedication are still open in Photoshop: slides 2 and 3 need them
      toast('Спершу «Зберегти відкриті»: Cover 1 і Dedication потрібні для слайдів 2 і 3', 'info');
      blinkFinish();
      return;
    }
    sl.error = '';
    sl.run = { step: 'Починаю…', percent: 0, rows: TITLES.map((title, i) => ({ slide: `slide${i + 1}`, title, state: 'wait' })) };
    paint();
    busy(true);
    const order = [...(st.result?.saved || []), ...(st.finished?.saved || [])];
    try {
      const res = await runJob(post('/api/slides/make', { folder: folder(), workshop: book(), order, book: st.book?.id || '', numbers: sl.numbers, fresh, scheme: sl.scheme || undefined }), (job) => {
        if (gone || !sl.run) return;
        Object.assign(sl.run, { step: job.step, percent: job.percent, rows: job.partial?.rows || sl.run.rows });
        patchRun();
      }, 600, () => !gone);
      if (gone) return;
      sl.result = res;
      tellDone(`Слайди готові · ${res.pictures.length}`);
    } catch (err) {
      if (gone) return;
      sl.error = err.message;
      tellDone('Слайди не вдалися');
    } finally {
      if (!gone) busy(false);
    }
    sl.run = null;
    paint();
  }

  function patchRun() {
    const r = sl.run;
    const step = $('#sl-step'), pct = $('#sl-pct'), bar = $('#sl-bar');
    if (!step) { paint(); return; }
    step.textContent = r.step;
    pct.textContent = `${Math.round(r.percent)}%`;
    bar.style.transform = `scaleX(${Math.max(3, r.percent) / 100})`;
    const rows = $('#sl-rows');
    const icon = (s) => (s === 'done' ? ic('check') : s === 'work' ? html`<span class="spinner"></span>` : html`<i class="mk-dot"></i>`);
    setHtml(rows, (r.rows || []).map((row, i) => html`<div class="mk-row ${row.state}"><span class="mk-row-ico">${icon(row.state)}</span>
      <span class="grow truncate"><span class="num faint">${i + 1}</span> · ${row.title}</span></div>`));
  }

  // The editor may have baked them again: the card shows the pictures as they are now.
  async function refresh() {
    if (!sl.result) return;
    try {
      const v = await api(`/api/slides/state?w=${sl.result.set}`);
      if (gone) return;
      sl.result = { ...sl.result, pictures: v.pictures, seconds: 0 };
      paint();
    } catch { /* the set went: the card stays as it was */ }
  }

  function view_(i) {
    const r = sl.result;
    openLightbox(r.pictures.map((p) => ({
      src: media(`/media/slides/out/${r.set}/${p.slide}`, { w: 1400, v: p.v }), full: media(`/media/slides/out/${r.set}/${p.slide}`, { w: 2600, v: p.v }),
      title: p.name, sub: r.folder,
      actions: [{ icon: 'edit', label: 'Правити', tip: 'Відкрити цей слайд у редакторі', run: (lb) => { lb.close?.(); edit(p.slide); } }],
      onOriginal: () => post('/api/slides/open-picture', { w: r.set, s: p.slide }).catch((err) => toast(err.message, 'error')),
    })), i);
  }

  function edit(slide) {
    if (!sl.result) return;
    location.hash = `#/slides/${sl.result.set}/${slide.replace('slide', '')}`;
  }

  // ---------------------------------------------------------------- events (from mockups.js's one listener)
  async function act(a, t) {
    if (a === 'sl-make') { make(); return true; }
    if (a === 'sl-scheme') {
      menu(t, (sl.schemes || []).map((x) => ({ label: `${x.name}${x.default ? ' · для нових книг' : ''}`, icon: 'template', on: x.key === schemeNow()?.key,
        onClick: () => { sl.scheme = x.default ? '' : x.key; paint(); } })));
      return true;
    }
    if (a === 'sl-edit') { edit(t.dataset.slide); return true; }
    if (a === 'sl-view') { view_(+t.dataset.i); return true; }
    if (a === 'open-nobg') { post('/api/mockups/open-folder', { path: t.dataset.path }).catch((err) => toast(err.message, 'error')); return true; }
    if (a === 'sl-again') {
      const ok = await confirmBox({ title: 'Зробити слайди заново?', text: 'Шість слайдів знову зробляться зі схеми — правки, внесені для цієї книги в редакторі, пропадуть. (Щоб оновити лише мокапи, а правки лишити, досить ще раз «Зробити мокапи».)', confirm: 'Зробити заново' });
      if (ok && !gone) { sl.result = null; make(true); }
      return true;
    }
    return false;
  }
  function input(t) {
    const k = t.dataset.num;
    if (!k) return;
    const n = Math.round(+t.value);
    if (n > 0 && n < 1000) sl.numbers[k] = n;
  }

  return {
    paint, act, input, refresh,
    wake() { refresh(); if (folder()) pollCuts(); },
    runStarted() { sl.folder = ''; },   // a new Photoshop run: its pictures' cut-outs are followed again
    keep: () => !!(sl.run || sl.result),
    running: () => !!sl.run,
    reset() { Object.assign(sl, { run: null, result: null, error: '', cuts: null, folder: '' }); clearTimeout(timer); paint(); },
    stop() { gone = true; clearTimeout(timer); },
  };
}
