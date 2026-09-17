// Full-screen image viewer.
// Motion model: every input (wheel, buttons, double-click, keys) only moves a *target* transform;
// a requestAnimationFrame loop eases the visible transform towards it (frame-rate independent
// exponential smoothing), so zoom always has intermediate frames. Dragging is 1:1 and ends with
// inertia. Images are decoded off the main thread before they are shown and cross-fade.
// Items may carry `full` — a sharper version fetched once the user zooms past the preview's pixels
// and swapped in while nothing is moving (same box size, so the picture does not jump).
import { html, ic, el, highlightTokens, reducedMotion } from './lib.js';

const TAU = 85;           // ms — smoothing time constant for zoom/pan
const FRICTION = 260;     // ms — inertia decay after a drag
const MAX_ZOOM = 12;

export function openLightbox(items, start = 0) {
  if (!items.length) return null;
  let index = Math.max(0, Math.min(start, items.length - 1));
  let showText = true;
  const cur = { s: 1, x: 0, y: 0 };
  const tgt = { s: 1, x: 0, y: 0 };
  const vel = { x: 0, y: 0 };
  let fit = 1, natW = 0, natH = 0, active = null, raf = 0, last = 0, dragging = null, seq = 0;
  let hiFor = null, hiReady = null;
  const cache = new Map();

  const root = el(html`<div class="lightbox" role="dialog" aria-modal="true">
    <div class="lb-top">
      <div class="grow"><div class="lb-title"></div><div class="lb-sub"></div></div>
      <button class="lb-btn" data-a="text" aria-label="Текст сторінки" data-tip="Текст сторінки" data-kbd="T">${ic('captions')}</button>
      <button class="lb-btn" data-a="original" aria-label="Відкрити файл-оригінал" data-tip="Відкрити файл-оригінал">${ic('fileOpen')}</button>
      <button class="lb-btn" data-a="close" aria-label="Закрити" data-tip="Закрити" data-kbd="Esc">${ic('x')}</button>
    </div>
    <div class="lb-stage"><div class="spinner spinner-l lb-spinner" hidden></div><img alt="" draggable="false" decoding="async"><img alt="" draggable="false" decoding="async"><div class="lb-text" hidden></div></div>
    <div class="lb-bottom">
      <button class="lb-btn" data-a="prev" aria-label="Попереднє" data-tip="Попереднє" data-kbd="←">${ic('chevLeft')}</button>
      <span class="lb-counter"></span>
      <button class="lb-btn" data-a="next" aria-label="Наступне" data-tip="Наступне" data-kbd="→">${ic('chevRight')}</button>
      <span style="width:18px"></span>
      <button class="lb-btn" data-a="out" aria-label="Зменшити" data-tip="Зменшити" data-kbd="−">${ic('zoomOut')}</button>
      <span class="lb-zoom"></span>
      <button class="lb-btn" data-a="in" aria-label="Збільшити" data-tip="Збільшити" data-kbd="+">${ic('zoomIn')}</button>
      <button class="lb-btn" data-a="fit" aria-label="Вмістити" data-tip="Вмістити" data-kbd="0">${ic('fit')}</button>
    </div></div>`);
  const stage = root.querySelector('.lb-stage');
  const imgs = [...root.querySelectorAll('.lb-stage img')];
  const spinner = root.querySelector('.lb-spinner');
  const textBox = root.querySelector('.lb-text');
  const zoomLabel = root.querySelector('.lb-zoom');
  document.body.appendChild(root);

  // ---------------------------------------------------------------- render loop
  const paint = () => {
    if (active) active.style.transform = `translate3d(${cur.x}px, ${cur.y}px, 0) scale(${cur.s})`;
    zoomLabel.textContent = `${Math.round((tgt.s / fit) * 100)}%`;
  };
  function tick(now) {
    const dt = Math.min(64, now - (last || now));
    last = now;
    if (!dragging && (Math.abs(vel.x) > 0.01 || Math.abs(vel.y) > 0.01)) {
      tgt.x += vel.x * dt; tgt.y += vel.y * dt;
      const k = Math.exp(-dt / FRICTION);
      vel.x *= k; vel.y *= k;
      if (Math.abs(vel.x) <= 0.01 && Math.abs(vel.y) <= 0.01) { vel.x = vel.y = 0; keepInView(); }
    }
    const a = dragging ? 1 : 1 - Math.exp(-dt / TAU);
    cur.s += (tgt.s - cur.s) * a; cur.x += (tgt.x - cur.x) * a; cur.y += (tgt.y - cur.y) * a;
    const settled = Math.abs(tgt.s - cur.s) < 1e-4 * tgt.s && Math.abs(tgt.x - cur.x) < 0.1 && Math.abs(tgt.y - cur.y) < 0.1
      && !vel.x && !vel.y && !dragging;
    if (settled) { cur.s = tgt.s; cur.x = tgt.x; cur.y = tgt.y; }
    paint();
    raf = settled ? 0 : requestAnimationFrame(tick);
    if (settled) swapHi();
  }
  const kick = () => { if (!raf) { last = 0; raf = requestAnimationFrame(tick); } };
  const jump = () => { cur.s = tgt.s; cur.x = tgt.x; cur.y = tgt.y; paint(); };

  const stageSize = () => { const r = stage.getBoundingClientRect(); return [r.width, r.height, r]; };
  function fitTarget() {
    const [w, h] = stageSize();
    fit = Math.min((w - 48) / natW, (h - 32) / natH);
    tgt.s = fit; tgt.x = (w - natW * fit) / 2; tgt.y = (h - natH * fit) / 2;
  }
  function zoomAt(factor, px, py) {
    const ns = Math.max(fit * 0.5, Math.min(fit * MAX_ZOOM, tgt.s * factor));
    tgt.x = px - (px - tgt.x) * (ns / tgt.s);
    tgt.y = py - (py - tgt.y) * (ns / tgt.s);
    tgt.s = ns;
    vel.x = vel.y = 0;
    if (ns <= fit * 1.001) fitTarget();
    kick();
    wantHi();
  }
  // The preview is being enlarged beyond its own pixels: fetch and decode the sharp version in the background.
  function wantHi() {
    const it = items[index];
    if (!it?.full || hiFor === it || tgt.s * (window.devicePixelRatio || 1) <= 1.1) return;
    hiFor = it;
    load(it.full).then((im) => { hiReady = { it, src: im.src }; if (!raf) swapHi(); }).catch(() => { hiFor = null; });
  }
  function swapHi() {
    if (!hiReady || items[index] !== hiReady.it || !active) return;
    active.src = hiReady.src;  // already decoded; the element keeps its size, only the detail changes
    hiReady = null;
  }
  function keepInView() {
    // Never let the picture drift completely off screen.
    const [w, h] = stageSize();
    const iw = natW * tgt.s, ih = natH * tgt.s, m = 80;
    const cx = Math.min(w - m, Math.max(m - iw, tgt.x));
    const cy = Math.min(h - m, Math.max(m - ih, tgt.y));
    if (iw <= w) tgt.x = (w - iw) / 2; else tgt.x = Math.min(0 + m, Math.max(w - iw - m, cx));
    if (ih <= h) tgt.y = (h - ih) / 2; else tgt.y = Math.min(0 + m, Math.max(h - ih - m, cy));
    kick();
  }
  const center = () => { const [w, h] = stageSize(); return [w / 2, h / 2]; };

  // ---------------------------------------------------------------- images
  function load(src) {
    if (!cache.has(src)) {
      const im = new Image();
      im.decoding = 'async';
      im.src = src;
      cache.set(src, (im.decode ? im.decode() : new Promise((r, j) => { im.onload = r; im.onerror = j; })).then(() => im));
    }
    return cache.get(src);
  }
  function preloadAround() {
    [index + 1, index - 1].forEach((i) => { const it = items[(i + items.length) % items.length]; if (it) load(it.src).catch(() => {}); });
  }

  async function show(i, dir = 0) {
    index = (i + items.length) % items.length;
    const it = items[index];
    const my = ++seq;
    hiFor = null; hiReady = null;
    root.querySelector('.lb-title').textContent = it.title || '';
    root.querySelector('.lb-sub').textContent = it.sub || '';
    root.querySelector('.lb-counter').textContent = `${index + 1} / ${items.length}`;
    root.querySelector('[data-a="prev"]').disabled = items.length < 2;
    root.querySelector('[data-a="next"]').disabled = items.length < 2;
    root.querySelector('[data-a="original"]').hidden = !it.onOriginal;
    root.querySelector('[data-a="text"]').hidden = !it.text;
    textBox.hidden = !(it.text && showText);
    root.querySelector('[data-a="text"]').classList.toggle('on', !!(it.text && showText));
    textBox.innerHTML = it.text ? String(highlightTokens(it.text)) : '';
    const slow = setTimeout(() => { if (my === seq) spinner.hidden = false; }, 120);
    let im;
    try { im = await load(it.src); } catch { clearTimeout(slow); spinner.hidden = true; return; }
    clearTimeout(slow);
    if (my !== seq) return;
    spinner.hidden = true;
    const next = imgs.find((x) => x !== active) || imgs[0];
    const prev = active;
    next.src = im.src;
    natW = im.naturalWidth; natH = im.naturalHeight;
    next.style.width = `${natW}px`; next.style.height = `${natH}px`;
    active = next;
    vel.x = vel.y = 0;
    fitTarget();
    // The incoming picture starts slightly offset in the travel direction and glides into place.
    const [w] = stageSize();
    cur.s = tgt.s * (dir ? 0.985 : 0.97); cur.y = tgt.y + (dir ? 0 : 8);
    cur.x = tgt.x + (reducedMotion() ? 0 : dir * Math.min(60, w * 0.04));
    paint();
    next.classList.add('on');
    next.style.zIndex = '1';
    if (prev) { prev.classList.remove('on'); prev.style.zIndex = '0'; }
    kick();
    preloadAround();
  }

  // ---------------------------------------------------------------- input
  function close() {
    root.classList.add('closing');
    cancelAnimationFrame(raf);
    document.removeEventListener('keydown', onKey, true);
    window.removeEventListener('resize', onResize);
    setTimeout(() => root.remove(), 170);
  }
  const onResize = () => { const atFit = Math.abs(tgt.s - fit) < fit * 0.01; if (atFit) { fitTarget(); jump(); } else keepInView(); };
  function onKey(e) {
    const k = e.key;
    if (k === 'Escape') { e.stopPropagation(); close(); }
    else if (k === 'ArrowRight') show(index + 1, 1);
    else if (k === 'ArrowLeft') show(index - 1, -1);
    else if (k === '+' || k === '=') zoomAt(1.4, ...center());
    else if (k === '-') zoomAt(1 / 1.4, ...center());
    else if (k === '0') { fitTarget(); kick(); }
    else if (k.toLowerCase() === 't' || k.toLowerCase() === 'е') { showText = !showText; textBox.hidden = !(items[index].text && showText); root.querySelector('[data-a="text"]').classList.toggle('on', !textBox.hidden); }
    else return;
    e.preventDefault();
  }
  document.addEventListener('keydown', onKey, true);
  window.addEventListener('resize', onResize);

  root.addEventListener('click', (e) => {
    const b = e.target.closest('[data-a]');
    if (!b) return;
    const a = b.dataset.a;
    if (a === 'close') close();
    else if (a === 'prev') show(index - 1, -1);
    else if (a === 'next') show(index + 1, 1);
    else if (a === 'in') zoomAt(1.5, ...center());
    else if (a === 'out') zoomAt(1 / 1.5, ...center());
    else if (a === 'fit') { fitTarget(); kick(); }
    else if (a === 'text') { showText = !showText; textBox.hidden = !(items[index].text && showText); root.querySelector('[data-a="text"]').classList.toggle('on', !textBox.hidden); }
    else if (a === 'original') items[index].onOriginal?.();
  });

  stage.addEventListener('wheel', (e) => {
    e.preventDefault();
    const [, , r] = stageSize();
    const delta = e.deltaMode === 1 ? e.deltaY * 32 : e.deltaY;
    zoomAt(Math.exp(-delta * 0.0018), e.clientX - r.left, e.clientY - r.top);
  }, { passive: false });

  stage.addEventListener('pointerdown', (e) => {
    if (e.target.closest('.lb-text') || e.button !== 0) return;
    // Remember what was pressed before pointer capture retargets the following events to the stage.
    dragging = { px: e.clientX, py: e.clientY, x: tgt.x, y: tgt.y, moved: false, onImage: e.target.tagName === 'IMG',
      hist: [[performance.now(), e.clientX, e.clientY]] };
    vel.x = vel.y = 0;
    stage.setPointerCapture(e.pointerId);
    stage.classList.add('dragging');
    kick();
  });
  stage.addEventListener('pointermove', (e) => {
    if (!dragging) return;
    const dx = e.clientX - dragging.px, dy = e.clientY - dragging.py;
    if (Math.abs(dx) + Math.abs(dy) > 3) dragging.moved = true;
    tgt.x = dragging.x + dx; tgt.y = dragging.y + dy;
    dragging.hist.push([performance.now(), e.clientX, e.clientY]);
    if (dragging.hist.length > 6) dragging.hist.shift();
    kick();
  });
  const endDrag = (e) => {
    if (!dragging) return;
    const d = dragging;
    dragging = null;
    stage.classList.remove('dragging');
    const [t0, x0, y0] = d.hist[0];
    const [t1, x1, y1] = d.hist[d.hist.length - 1];
    const dt = t1 - t0;
    if (d.moved && dt > 0 && performance.now() - t1 < 80 && !reducedMotion()) {
      vel.x = (x1 - x0) / dt; vel.y = (y1 - y0) / dt;   // px per ms → inertia
    } else keepInView();
    kick();
    if (!d.moved && !d.onImage) close(); // a click on the empty backdrop closes the viewer
  };
  stage.addEventListener('pointerup', endDrag);
  stage.addEventListener('pointercancel', endDrag);
  stage.addEventListener('dblclick', (e) => {
    const [, , r] = stageSize();
    if (tgt.s > fit * 1.05) { fitTarget(); kick(); } else zoomAt(2.6, e.clientX - r.left, e.clientY - r.top);
  });

  show(index);
  return { close };
}
