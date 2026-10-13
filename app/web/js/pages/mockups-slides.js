// Mockups, step 4 — «Слайди для лістингу» (the owner, 29.09.2026: "after the Photoshop script the Mockups page offers
// the next step; I press it and they are made by themselves; then a button offers to go into our editor"). Above it,
// how far the pictures without background are (cut while Photoshop works — studio/slides/cutout.py). The six are
// made from the template (studio/slides/work.py); the editor is its own page, loaded only when opened (#/slides/…).
import { api, post, html, ic, ib, setHtml, media, toast, runJob, fadeImages, plural, confirmBox, menu, attr, setProgress } from '../lib.js';
import { morphList, reveal } from './mockups-run.js';
import { openLightbox } from '../lightbox.js';

const SHOT_W = 480;
const SLIDES = ['слайд', 'слайди', 'слайдів'];
// The slides each template is on (09.10.2026): a part of the mockups made alone offers just those slides.
const SLIDES_OF = { open1: ['slide1', 'slide4'], open2: ['slide5', 'slide6'], cover1: ['slide2'], dedication: ['slide3'] };
const ALL = ['slide1', 'slide2', 'slide3', 'slide4', 'slide5', 'slide6'];
const NEEDS = { slide2: 'Cover 1', slide3: 'Dedication' };   // made in Photoshop by hand first: «Зберегти відкриті»
const TITLES = ['Made just for them', 'Choose your format', 'Dedication & afterword', 'Unique little poems',
  'Personalization made simple', 'Thank you'];
const titleOf = (s) => TITLES[ALL.indexOf(s)] || 'Appearance options';   // slide 7 — the hero's looks

export function slidesStep({ view, st, existing, stepNo, tellDone, busy, blinkFinish, paintBook }) {
  const sl = {
    numbers: { pages: 24, poems: 11 },
    run: null,        // {step, percent, rows}
    result: null,     // {set, folder, pictures: [{slide, name, v}], missing, seconds}
    error: '',
    cuts: null,       // {files: {name: state}, busy, noBg}
    folder: '',       // the folder the cuts are asked for
    pick: null,       // the ticked slides (a Set); null — the ones the run's ticked templates are on, else all six
    scheme: '',       // the scheme the six start from — chosen here, before they are made; '' = the default for new books
    schemes: null,    // the schemes to choose from [{key, name, default}]
  };
  let gone = false, timer = 0, polling = false;
  const $ = (sel) => view.querySelector(sel);
  const box = () => $('#mk-s5');
  // The Workshop book's folder as it is (11.10.2026): its mockups made another day or by an earlier run, its slides — the
  // step is there whenever the book has something to make slides from, not only after a run on this page.
  const ex = existing;
  const onDisk = () => !!(ex()?.files.some((f) => SLIDES_OF[f.template]) || ex()?.slides);
  // The page's Photoshop run — only while it is for where the pictures go now: another book chosen after it, the step is that book's.
  const run = () => {
    const r = st.result;
    if (!r) return null;
    if (st.out) return !r.workshop && r.folder === st.out ? r : null;
    return !st.workshop || r.workshop === st.workshop.id ? r : null;
  };
  const finished = () => (run() ? st.finished : null);
  // saved by the run, or later by «Зберегти відкриті» (a run of Dedication alone saves nothing by itself)
  const ready = () => (!!run() && !run().cancelled && (run().saved.length + (finished()?.saved.length || 0)) > 0) || onDisk();
  const picked = () => sl.pick || new Set(run() && st.only ? st.only.flatMap((k) => SLIDES_OF[k] || []) : ALL);
  const folder = () => run()?.folder || ex()?.folder || '';
  const book = () => (run() ? run().workshop || '' : ex()?.id || '');   // the Workshop book the run was for
  const target = () => (book() ? `workshop=${encodeURIComponent(book())}` : `folder=${encodeURIComponent(folder())}`);

  // ---------------------------------------------------------------- the cut-outs (polled while any is on its way)
  async function pollCuts() {
    clearTimeout(timer);
    if (gone || !folder() || polling) return; // one chain only: a call while a request is out joins it
    polling = true;
    try {
      sl.cuts = await api(`/api/slides/cutouts?${target()}`);
      sl.folder = folder();
    } catch { /* the folder went: nothing to say */ }
    polling = false;
    if (gone) return;
    paintCuts();
    const running = !!st.run || sl.cuts?.busy;
    if (running && view.isConnected) timer = setTimeout(pollCuts, 1500);
  }

  function cutsLine() {
    // this book's pictures only (a folder may hold an earlier book's too); a Workshop book's folder is all its own
    const mine = new Set(book() ? [] : [...(run()?.saved || []), ...(finished()?.saved || [])]);
    const files = Object.entries(sl.cuts?.files || {}).filter(([name]) => !mine.size || mine.has(name));
    if (!files.length) return '';
    const done = files.filter(([, v]) => v === 'done').length;
    const failed = files.filter(([, v]) => v.startsWith('error')).map(([n]) => n);
    const going = files.length - done - failed.length;
    return html`<div class="sl-cuts ${going ? 'going' : 'ok'}">
      ${going ? html`<span class="progress progress-thin live sl-cuts-bar"><i style="transform:scaleX(${done / files.length})"></i></span>` : ic('check', 'icon-s')}
      <span class="grow">Без фону · <span class="num sl-cuts-num">${done}/${files.length}</span>${going ? ' — вирізаю, поки Photoshop працює' : ''}</span>
      ${done ? ib('folderOpen', 'Відкрити папку «Без фону»', `data-act="open-nobg" ${attr('data-path', sl.cuts.noBg)}`, { cls: 'sm' }) : ''}
    </div>${failed.length ? html`<div class="notice notice-warn">${ic('alert')}<div>Не вирізались: ${failed.join(', ')}</div></div>` : ''}`;
  }
  function paintCuts() {
    const line = $('#sl-cuts');
    if (!line) return;
    // still going and the line is already drawn: its bar and count move on (a rebuild would restart the glide)
    const bar = line.querySelector('.sl-cuts-bar > i');
    if (bar) {
      const next = document.createElement('div');
      setHtml(next, cutsLine());
      const nb = next.querySelector('.sl-cuts-bar > i');
      if (nb && next.children.length === line.children.length) {
        setProgress(bar, Number(nb.style.transform.replace(/[^0-9.]/g, '')) * 100 || 0);
        line.querySelector('.sl-cuts-num').textContent = next.querySelector('.sl-cuts-num').textContent;
        return;
      }
    }
    setHtml(line, cutsLine());
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
    reveal(b, show);
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
      <div class="sl-ghosts">${TITLES.map((t, i) => html`<label class="sl-ghost check ${picked().has(ALL[i]) ? 'on' : ''}" data-tip="Робити цей слайд">
        <input type="checkbox" data-act="sl-pick" data-slide="${ALL[i]}" ${picked().has(ALL[i]) ? 'checked' : ''} aria-label="Робити слайд ${i + 1}">
        <span class="num">${i + 1}</span><small>${t}</small></label>`)}</div>
      <button type="button" class="btn btn-primary btn-block" data-act="sl-make">${ic('images')}${picked().size === ALL.length ? 'Зробити слайди' : picked().size ? `Зробити слайди: ${picked().size} з ${ALL.length}` : 'Оберіть слайди'}</button>`;
  }

  function runHtml() {
    const r = sl.run;
    const icon = (s) => (s === 'done' ? ic('check') : s === 'work' ? html`<span class="spinner"></span>` : html`<i class="mk-dot"></i>`);
    return html`<div class="mk-run">
      <div class="row mk-run-now"><span class="spinner"></span><span class="grow truncate" id="sl-step">${r.step}</span>
        <span class="num faint" id="sl-pct">${Math.round(r.percent)}%</span></div>
      <div class="progress live ${r.percent > 0 ? '' : 'indet'}"><i id="sl-bar" style="transform:scaleX(${Math.max(0, Math.min(100, r.percent)) / 100})"></i></div>
      <div class="mk-rows" id="sl-rows">${(r.rows || []).map((row, i) => html`<div class="mk-row ${row.state}"><span class="mk-row-ico">${icon(row.state)}</span>
        <span class="grow truncate"><span class="num faint">${i + 1}</span> · ${row.title}</span></div>`)}</div>
    </div>`;
  }

  function resultHtml() {
    const r = sl.result;
    const count = r.pictures.length, todo = r.todo || [];
    return html`<div class="result-card mk-result">
      <h4>${ic('checkCircle')}<span class="grow">${todo.length ? html`Зроблено <span class="num">${count}</span> з <span class="num">${count + todo.length}</span> ${plural(count + todo.length, SLIDES)}` : html`Готово · <span class="num">${count}</span> ${plural(count, SLIDES)}`}</span>
        ${r.seconds ? html`<span class="mk-secs num">${r.seconds} с</span>` : ''}
        ${ib('folderOpen', 'Відкрити папку зі слайдами', `data-act="open-out" data-path="${r.folder}"`, { cls: 'sm' })}</h4>
      <div class="sl-shots">${r.pictures.map((p, i) => html`<div class="sl-shot">
        <button type="button" class="mk-shot" data-act="sl-view" data-i="${i}" aria-label="${p.name}" data-tip="${p.name}">
          <img data-fade alt="" draggable="false" src="${media(`/media/slides/out/${r.set}/${p.slide}`, { w: SHOT_W, v: p.v })}"></button>
        ${ib('edit', `Правити слайд ${i + 1}`, `data-act="sl-edit" data-slide="${p.slide}"`, { cls: 'sm sl-pen' })}
      </div>`)}</div>
      ${r.missing?.length ? html`<div class="notice notice-warn">${ic('alert')}<div>Не було: ${r.missing.join(', ')} — на слайдах замість них порожні місця; в редакторі можна поставити інший мокап.</div></div>` : ''}
      ${todo.length ? html`<button type="button" class="btn btn-primary btn-block" data-act="sl-rest" data-tip="Зробити з мокапів книги слайди, яких ще немає; зроблені лишаться, як є">${ic('images')}Доробити ${todo.length > 1 ? 'слайди' : 'слайд'} ${todo.map((s) => s.slice(5)).join(', ')}</button>` : ''}
      <button type="button" class="btn btn-block" data-act="sl-edit" data-slide="${r.pictures[0]?.slide || 'slide1'}">${ic('edit')}Відкрити в редакторі</button>
    </div>`;
  }

  // ---------------------------------------------------------------- making them
  // `list` — these slides exactly («Доробити»: the ones not made yet, slide 7 among them)
  async function make(fresh = false, list = null) {
    if (sl.run || st.run) return;
    const slides = list || ALL.filter((s) => picked().has(s));
    if (!slides.length) { toast('Позначте хоча б один слайд', 'info'); return; }
    const waiting = slides.filter((s) => NEEDS[s] && st.pending?.open?.includes(NEEDS[s]));
    if (waiting.length) {  // Cover 1 / Dedication are still open in Photoshop: the slides with them have to wait
      toast(`Спершу «Зберегти відкриті»: ${waiting.map((s) => NEEDS[s]).join(' і ')} потрібн${waiting.length > 1 ? 'і' : 'ий'} для слайд${waiting.length > 1 ? 'ів' : 'а'} ${waiting.map((s) => s.slice(5)).join(' і ')}`, 'info');
      blinkFinish();
      return;
    }
    const whole = !list && slides.length === ALL.length;
    // «Доробити» / «Зробити заново» act on the book whose card it is
    const workshop = (list || fresh) && /^\d{1,5}\./.test(sl.result?.set || '') ? sl.result.set : book();
    sl.error = '';
    sl.run = { step: 'Починаю…', percent: 0, rows: slides.map((s) => ({ slide: s, title: titleOf(s), state: 'wait' })) };
    paint();
    busy(true);
    paintBook();   // the book can't be changed while its slides are made
    const order = [...(run()?.saved || []), ...(finished()?.saved || [])];
    try {
      const res = await runJob(post('/api/slides/make', { folder: folder(), workshop, order, book: st.book?.id || '', numbers: sl.numbers, fresh: fresh && whole, scheme: sl.scheme || undefined, ...(whole ? {} : { slides }) }), (job) => {
        if (gone || !sl.run) return;
        Object.assign(sl.run, { step: job.step, percent: job.percent, rows: job.partial?.rows || sl.run.rows });
        patchRun();
      }, 600, () => !gone);
      if (gone) return;
      sl.result = res;
      const x = ex();   // the folder as the page knows it is now this result (a later seed() must not bring back the old)
      if (x && x.id === res.set) x.slides = { set: res.set, folder: res.folder, pictures: res.pictures, numbers: { ...sl.numbers }, todo: res.todo || [] };
      tellDone(`Слайди готові · ${res.pictures.length}`);
    } catch (err) {
      if (gone) return;
      sl.error = err.message;
      tellDone('Слайди не вдалися');
    } finally {
      if (!gone) busy(false);
    }
    sl.run = null;
    if (!gone) paintBook();
    paint();
  }

  function patchRun() {
    const r = sl.run;
    const step = $('#sl-step'), pct = $('#sl-pct'), bar = $('#sl-bar');
    if (!step) { paint(); return; }
    step.textContent = r.step;
    pct.textContent = `${Math.round(r.percent)}%`;
    bar.parentElement.classList.toggle('indet', !(r.percent > 0));
    setProgress(bar, r.percent);
    const rows = $('#sl-rows');
    const icon = (s) => (s === 'done' ? ic('check') : s === 'work' ? html`<span class="spinner"></span>` : html`<i class="mk-dot"></i>`);
    morphList(rows, (r.rows || []).map((row, i) => html`<div class="mk-row ${row.state}"><span class="mk-row-ico">${icon(row.state)}</span>
      <span class="grow truncate"><span class="num faint">${i + 1}</span> · ${row.title}</span></div>`));
  }

  // The editor may have baked them again: the card shows the pictures as they are now.
  async function refresh() {
    if (!sl.result) return;
    const set = sl.result.set;
    try {
      const v = await api(`/api/slides/state?w=${set}`);
      if (gone || sl.result?.set !== set) return;   // another book was chosen meanwhile
      const done = new Set(v.pictures.map((p) => p.slide));
      sl.result = { ...sl.result, pictures: v.pictures, todo: v.slides.map((s) => s.id).filter((s) => !done.has(s)), seconds: 0 };
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
    if (a === 'sl-rest') { if (sl.result?.todo?.length) make(false, sl.result.todo); return true; }
    if (a === 'sl-pick') {
      const next = new Set(picked());
      next[t.checked ? 'add' : 'delete'](t.dataset.slide);
      sl.pick = next;
      paint();
      return true;
    }
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
    // The Workshop book's folder was read (another book chosen, a run ended, the page opened): with no run on this page,
    // its own slides show as they are on disk — a part made, «Доробити» the rest; none yet — the six to make.
    seed() {
      if (sl.run || st.run || run()) { paint(); return; }
      const s = ex()?.slides;
      Object.assign(sl, { result: s?.pictures.length ? { set: s.set, folder: s.folder, pictures: s.pictures, todo: s.todo, missing: [], seconds: 0 } : null,
        numbers: { pages: 24, poems: 11, ...(s?.numbers || {}) }, error: '', pick: null, cuts: null, folder: '' });
      paint();
    },
    wake() { refresh(); if (folder()) pollCuts(); },
    runStarted() { sl.folder = ''; sl.pick = null; },   // a new Photoshop run: its pictures' cut-outs are followed again
    keep: () => !!(sl.run || sl.result),
    running: () => !!sl.run,
    reset() { Object.assign(sl, { run: null, result: null, error: '', cuts: null, folder: '', pick: null }); clearTimeout(timer); paint(); },
    stop() { gone = true; clearTimeout(timer); },
  };
}
