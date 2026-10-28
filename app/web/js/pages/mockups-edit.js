// Mockups: the crop window (13.10.2026, the owner: "a mini editor just for cropping the cover"). Book Studio draws
// the mockups itself; where the front cover shows (Cover 1, Cover & Open 1, All & Open 1) it puts the right half of
// the wide cover in by itself, and here the owner may move it and bring it closer when it looks so-so. In the two
// softcover scenes the background colour (one for the book's both scenes) and the open book's edge colours (taken from
// the cover's edges, an eyedropper on the cover takes another). Left — the cover with the front's frame (and the
// back's, where the back shows — All & Open 1, 27.10.2026), right — the mockup as it will be (drawn by the server,
// a second or three); «Зберегти» draws it over the picture of this run.
import { api, post, html, ic, ib, setHtml, modal, toast, media } from '../lib.js';

const PREVIEW_W = 1400;
const WAIT = 320;           // ms of quiet before the mockup is drawn again
const COVER_W = 1400;

export async function openEditor({ job, key, onSaved }) {
  let s;
  try { s = await api(`/api/mockups/edit?${new URLSearchParams({ job, key })}`); }
  catch (err) { toast(err.message, 'error'); return; }
  const [W, H] = s.cover;
  const [BW, BH] = s.board, aspect = BW / BH;
  const base = Math.max(BW / (W / 2), BH / H);    // the scale filling a half (zoom 1), as the server's
  // Each side the mockup shows has its own window: the front always, the back where it shows too (All & Open 1;
  // 27.10.2026 — since the two squares the back is a scene of its own). Kept apart, each moved by itself.
  const sides = { front: { x: s.crop.x, y: s.crop.y, zoom: s.crop.zoom, centre: 0.75 } };
  if (s.back) sides.back = { x: s.back.x, y: s.back.y, zoom: s.back.zoom, centre: 0.25 };
  const names = Object.keys(sides);
  const st = { colours: { ...(s.colours || {}) }, pick: null, active: 'front' };
  // The back is sent only when moved from the program's place: left there, it is drawn as before (the left half)
  const moved = (c) => c && (Math.abs(c.x - c.centre) > 1e-4 || Math.abs(c.y - 0.5) > 1e-4 || Math.abs(c.zoom - 1) > 1e-4);
  const shot = () => JSON.stringify([names.map((n) => [sides[n].x, sides[n].y, sides[n].zoom]), st.colours]);
  let first = '';

  const handles = ['nw', 'ne', 'sw', 'se'].map((h) => html`<i class="mk-ed-h ${h}" data-h="${h}"></i>`);
  const tags = { front: 'Лицьова', back: 'Задня' };
  const frames = names.map((n) => html`<span class="mk-ed-frame" data-side="${n}">${names.length > 1 ? html`<b class="mk-ed-tag">${tags[n]}</b>` : ''}${handles}</span>`);
  const m = modal({
    title: html`Поправити · ${s.title}`, sub: s.name, size: 'xl',
    body: html`<div class="mk-ed">
      <div class="mk-ed-side stack">
        <div class="mk-ed-cover" id="ed-cover" style="aspect-ratio:${W} / ${H}">
          <img id="ed-img" alt="" draggable="false" src="${media(`/media/mockups/${s.book}/cover`, { w: COVER_W })}">
          <svg class="mk-ed-shade" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true">
            <mask id="ed-holes" maskUnits="userSpaceOnUse"><rect width="${W}" height="${H}" fill="#fff"></rect><path id="ed-shade" fill="#000"></path></mask>
            <rect width="${W}" height="${H}" mask="url(#ed-holes)"></rect></svg>
          <i class="mk-ed-spine"></i>
          ${frames}
        </div>
        <div class="row mk-ed-tools"><span class="spacer"></span>${ib('undo', 'Як поставила програма', 'data-ed="reset"', { cls: 'sm' })}</div>
        ${s.scene ? html`<div class="mk-ed-colours stack-s" id="ed-colours"></div>` : ''}
      </div>
      <div class="mk-ed-view" id="ed-view"><img id="ed-out" alt="Мокап"><span class="mk-ed-busy" id="ed-busy"><span class="spinner"></span></span></div>
    </div>`,
    foot: html`<button type="button" class="btn btn-primary" data-ed="save">${ic('check')}Зберегти</button>`,
  });
  const $ = (sel) => m.root.querySelector(sel);
  const cover = $('#ed-cover');
  const frameOf = (n) => m.root.querySelector(`.mk-ed-frame[data-side="${n}"]`);

  // ---------------------------------------------------------------- the frames over the whole cover
  // The window a side takes, in the cover's pixels — the same sums as the server's _window(): its size from the zoom
  // (the board's proportions, never stretched), kept inside the picture (13.10.2026, the owner: "the whole picture's
  // spare, and drag the edges as with Ctrl+T in Photoshop").
  const tallest = Math.min(H, W / aspect);                       // the biggest window the cover takes
  const zoomOf = (ch) => BH / (base * ch);
  function windowOf(c) {
    const scale = base * c.zoom;
    const cw = BW / scale, ch = BH / scale;
    const x0 = Math.min(Math.max(c.x * W - cw / 2, 0), Math.max(W - cw, 0));
    const y0 = Math.min(Math.max(c.y * H - ch / 2, 0), Math.max(H - ch, 0));
    return { x0, y0, cw, ch };
  }
  function clampCentre(c) {     // what is sent is what is seen: the centre the frame really has
    if (!Number.isFinite(c.x) || !Number.isFinite(c.y)) Object.assign(c, { x: c.centre, y: 0.5 });
    c.zoom = Math.min(s.maxZoom, Math.max(s.minZoom, Number.isFinite(c.zoom) ? c.zoom : 1));
    const w = windowOf(c);
    c.x = (w.x0 + w.cw / 2) / W;
    c.y = (w.y0 + w.ch / 2) / H;
  }
  function paintFrames() {      // every frame, and the dark outside them all (a mask: frames that overlap stay clear)
    let d = '';
    for (const n of names) {
      const w = windowOf(sides[n]), f = frameOf(n);
      Object.assign(f.style, { left: `${(100 * w.x0) / W}%`, top: `${(100 * w.y0) / H}%`,
        width: `${(100 * w.cw) / W}%`, height: `${(100 * w.ch) / H}%` });
      f.classList.toggle('on', names.length > 1 && n === st.active);
      d += `M${w.x0} ${w.y0}h${w.cw}v${w.ch}h${-w.cw}Z`;
    }
    $('#ed-shade').setAttribute('d', d);
  }
  // The side a press belongs to: the frame under it, else the half it is on (the back left of the spine).
  const sideAt = (e, p) => e.target.closest('[data-side]')?.dataset.side || (sides.back && p.x < W / 2 ? 'back' : 'front');

  // Inside a frame — move it; a corner — resize it, the opposite corner staying put (Ctrl+T with the
  // proportions locked); outside — that half's frame jumps there and follows.
  let drag = null;
  const at = (e, r) => ({ x: ((e.clientX - r.left) / r.width) * W, y: ((e.clientY - r.top) / r.height) * H });
  cover.addEventListener('pointerdown', (e) => {
    if (st.pick) { takeColour(e); return; }
    const r = cover.getBoundingClientRect();
    if (!r.width || !r.height) return;
    e.preventDefault();
    const p = at(e, r), n = sideAt(e, p), c = sides[n], h = e.target.closest('[data-h]')?.dataset.h;
    st.active = n;
    const w = windowOf(c);
    if (h) {
      drag = { c, h, r, ox: h.includes('w') ? w.x0 + w.cw : w.x0, oy: h.includes('n') ? w.y0 + w.ch : w.y0 };
    } else {
      if (!e.target.closest('[data-side]')) {    // a press beside the frames: that half's comes under the pointer
        c.x = p.x / W; c.y = p.y / H; clampCentre(c);
      }
      drag = { c, r, p, x: c.x, y: c.y };
    }
    paintFrames();
    try { cover.setPointerCapture(e.pointerId); } catch { /* the drag still follows inside */ }
    cover.classList.add(drag.h ? 'resizing' : 'dragging');
  });
  cover.addEventListener('pointermove', (e) => {
    if (!drag) return;
    const p = at(e, drag.r), c = drag.c;
    if (drag.h) {
      const left = drag.h.includes('w'), up = drag.h.includes('n');
      // as big as the pointer asks, the proportions kept; at the cover's edge the frame grows on and slides back
      // inside (clampCentre) rather than stopping
      let ch = Math.max(Math.abs(p.y - drag.oy), Math.abs(p.x - drag.ox) / aspect);
      ch = Math.max(Math.min(ch, tallest), BH / (base * s.maxZoom));
      const cw = ch * aspect;
      const x0 = left ? drag.ox - cw : drag.ox, y0 = up ? drag.oy - ch : drag.oy;
      c.zoom = zoomOf(ch);
      c.x = (x0 + cw / 2) / W; c.y = (y0 + ch / 2) / H;
    } else {
      c.x = drag.x + (p.x - drag.p.x) / W;
      c.y = drag.y + (p.y - drag.p.y) / H;
    }
    clampCentre(c); paintFrames();
  });
  const endDrag = () => {
    if (!drag) return;
    drag = null;
    cover.classList.remove('dragging', 'resizing');
    redraw();
  };
  cover.addEventListener('pointerup', endDrag);
  cover.addEventListener('pointercancel', endDrag);
  cover.addEventListener('wheel', (e) => {       // the wheel: closer or farther, around the middle of that side's frame
    e.preventDefault();
    const r = cover.getBoundingClientRect();
    if (!r.width || !r.height) return;
    const n = sideAt(e, at(e, r)), c = sides[n];
    st.active = n;
    c.zoom *= e.deltaY < 0 ? 1.06 : 1 / 1.06;
    clampCentre(c); paintFrames(); redraw();
  }, { passive: false });

  // ---------------------------------------------------------------- the colours of the softcover scenes
  const sw = (what, hex, tip) => html`<button type="button" class="mk-sw ${st.colours[what] === hex ? 'on' : ''}" style="--c:${hex}"
    data-ed="colour" data-what="${what}" data-hex="${hex}" aria-label="${tip}" data-tip="${tip}"></button>`;
  const pickSw = (what, tip) => html`<label class="mk-sw mk-pick" style="--c:${st.colours[what] || '#ffffff'}" data-tip="${tip}">
    <input type="color" data-what="${what}" value="${st.colours[what] || '#ffffff'}" aria-label="${tip}"></label>`;
  const edge = (what, label) => html`<button type="button" class="mk-edge ${st.pick === what ? 'on' : ''}" data-ed="pick" data-what="${what}"
    data-tip="Клацніть, потім — по обкладинці: колір ${label.toLowerCase()} візьметься звідти"><i style="--c:${st.colours[what]}"></i>${label}${ic('eyedropper', 'icon-s')}</button>`;
  function paintColours() {
    const box = $('#ed-colours');
    if (!box) return;
    const sg = s.suggest || {};
    const autoEdges = sg.edges && (st.colours.front !== sg.edges.front || st.colours.back !== sg.edges.back);
    setHtml(box, html`
      <div class="row mk-ed-label"><span class="eyebrow" data-tip="${s.others?.length ? `Один фон на книгу — «${s.others.join(', ')}» перемалюється теж` : 'Фон сцени'}">Фон</span></div>
      <div class="mk-sws">${(sg.background || []).map((hex, i) => sw('background', hex, i ? 'Пастельний відтінок з обкладинки' : 'Найкращий пастельний — з обкладинки'))}${pickSw('background', 'Інший колір')}</div>
      <div class="row mk-ed-label"><span class="eyebrow grow">Краї розкритої книги</span>
        ${autoEdges ? ib('undo', 'Як узяла програма — з країв обкладинки', 'data-ed="edges-auto"', { cls: 'sm' }) : ''}</div>
      <div class="row mk-edges">${edge('front', 'Ліва половина')}${edge('back', 'Права половина')}</div>`);
    cover.classList.toggle('picking', !!st.pick);
  }

  // The eyedropper: the cover as the window shows it, read from a canvas of the same picture.
  let canvas = null;
  function takeColour(e) {
    const img = $('#ed-img');
    if (!img.complete || !img.naturalWidth) return;
    if (!canvas) {
      canvas = document.createElement('canvas');
      canvas.width = img.naturalWidth; canvas.height = img.naturalHeight;
      canvas.getContext('2d', { willReadFrequently: true }).drawImage(img, 0, 0);
    }
    const r = cover.getBoundingClientRect();
    if (!r.width || !r.height) return;
    const x = Math.round(((e.clientX - r.left) / r.width) * (canvas.width - 1));
    const y = Math.round(((e.clientY - r.top) / r.height) * (canvas.height - 1));
    const d = canvas.getContext('2d').getImageData(Math.max(0, x - 1), Math.max(0, y - 1), 3, 3).data;
    const avg = [0, 1, 2].map((c) => Math.round((d[c] + d[c + 4] + d[c + 8] + d[c + 12] + d[c + 16] + d[c + 20] + d[c + 24] + d[c + 28] + d[c + 32]) / 9));
    st.colours[st.pick] = `#${avg.map((v) => v.toString(16).padStart(2, '0')).join('')}`;
    st.pick = null;
    paintColours(); redraw();
  }

  // ---------------------------------------------------------------- the mockup, drawn again after a pause
  // One drawing at a time (each is seconds of the server's work): changes made meanwhile wait, and only the newest
  // state is asked for when it is back.
  let timer = 0, busy = false, again = false;
  function redraw(now = false) {
    clearTimeout(timer);
    timer = setTimeout(ask, now ? 0 : WAIT);
  }
  function ask() {
    if (busy) { again = true; return; }
    busy = true; again = false;
    $('#ed-busy').classList.add('on');
    const img = new Image();
    const done = (ok) => {
      busy = false;
      if (ok) $('#ed-out').src = img.src;
      if (again) { ask(); return; }
      $('#ed-busy').classList.remove('on');
      if (!ok) toast('Мокап не намалювався — спробуйте ще раз', 'error');
    };
    img.onload = () => done(true);
    img.onerror = () => done(false);
    const f = sides.front, b = sides.back;
    img.src = media('/media/mockups/edit', { job, key, x: f.x.toFixed(4), y: f.y.toFixed(4), zoom: f.zoom.toFixed(3),
      ...(moved(b) ? { bx: b.x.toFixed(4), by: b.y.toFixed(4), bzoom: b.zoom.toFixed(3) } : {}), ...st.colours, w: PREVIEW_W });
  }

  m.root.addEventListener('input', (e) => {
    const t = e.target;
    if (t.type !== 'color') return;
    st.colours[t.dataset.what] = t.value;
    t.closest('.mk-pick')?.style.setProperty('--c', t.value);
    m.root.querySelectorAll(`.mk-sw[data-what="${t.dataset.what}"]`).forEach((b) => b.classList.remove('on'));
    redraw();
  });
  m.root.addEventListener('click', async (e) => {
    const t = e.target.closest('[data-ed]');
    if (!t) return;
    const act = t.dataset.ed;
    if (act === 'reset') {       // both sides as the program put them
      for (const c of Object.values(sides)) { Object.assign(c, { x: c.centre, y: 0.5, zoom: 1 }); clampCentre(c); }
      paintFrames(); redraw(); return;
    }
    if (act === 'colour') { st.colours[t.dataset.what] = t.dataset.hex; paintColours(); redraw(); return; }
    if (act === 'pick') { st.pick = st.pick === t.dataset.what ? null : t.dataset.what; paintColours(); return; }
    if (act === 'edges-auto') { Object.assign(st.colours, s.suggest.edges); paintColours(); redraw(); return; }
    if (act === 'save') save(t);
  });

  async function save(btn) {
    if (shot() === first) { m.close(); return; }
    btn.disabled = true;
    setHtml(btn, html`<span class="spinner"></span>Зберігаю…`);
    try {
      const part = (c) => ({ x: c.x, y: c.y, zoom: c.zoom });
      const crop = { ...part(sides.front), ...(moved(sides.back) ? { back: part(sides.back) } : {}) };
      const res = await post('/api/mockups/edit', { job, key, crop, ...st.colours });
      m.close();
      onSaved?.(res);
      toast(res.saved.length > 1 ? 'Збережено — обидві сцени з новим фоном' : 'Збережено', 'success');
    } catch (err) {
      btn.disabled = false;
      setHtml(btn, html`${ic('check')}Зберегти`);
      toast(err.message, 'error');
    }
  }

  Object.values(sides).forEach(clampCentre); first = shot();
  paintFrames(); paintColours(); redraw(true);
}
