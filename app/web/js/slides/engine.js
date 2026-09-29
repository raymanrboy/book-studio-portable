// Listing slides: a scene (a list of elements) drawn into a 1000×1000 stage. The same code draws the editor, the
// Mockups' previews and the baked picture (web/slides/render.html in headless Edge — studio/slides/bake.py).
// Moved in from the owner's external Slide Editor on 29.09.2026 (wiki/features/slides.md): the drawing is the same;
// a book or a flat picture now names its slot (which mockup — open1:1…4, open2:1…2, cover, dedication, page30), and a
// book's set says what fills the slots (setAssets()). Texts may carry {pages} and {poems} — the book's numbers.
const SVGNS = 'http://www.w3.org/2000/svg';
const mk = (tag, attrs, parent) => {
  const e = document.createElementNS(SVGNS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
};
export const STRETCH = 1.32;                          // the Canva look: Comica ~1.3× wider
export const caps = (t) => t.toUpperCase().replace(/I/g, 'i');
export const TSHADOW = 0.7;                           // the shadow under letters (the owner's pick, 29.09.2026)
export const FONT = '/fonts/ComicaRegular.otf';

// ---------------------------------------------------------------- what fills the slots
let ASSETS = { books: {}, pictures: {}, numbers: {} };
export function setAssets(a) { ASSETS = { books: {}, pictures: {}, numbers: {}, ...(a || {}) }; }
// a book whose mockup is missing is drawn as a placeholder of its usual shape
const ASPECT = { open1: 0.518, open2: 0.62, cover: 1.008 };
export const bookInfo = (e) => ASSETS.books[e.slot] || null;
export const bookAspect = (e) => bookInfo(e)?.aspect || ASPECT[String(e.slot || '').split(':')[0]] || 0.6;
// {pages}, {poems} — the book's numbers
export const fill = (t) => String(t ?? '').replace(/\{(pages|poems)\}/g, (_, k) => String(ASSETS.numbers?.[k] ?? ''));

let fontReady = null;
/** Comica loaded once (the drawing measures its letters). */
export function ready() {
  if (!fontReady) {
    const face = new FontFace('Comica', `url(${FONT})`);
    fontReady = face.load().then((f) => { document.fonts.add(f); }).catch(() => {});
  }
  return fontReady;
}

// Every element's box (w, h) in stage units; x, y is its centre.
export function boxOf(e) {
  switch (e.type) {
    case 'book': return [e.w, e.w * bookAspect(e)];
    case 'sticker': return [2 * e.r + 16, 2 * e.r + 16];
    case 'sparkle': return [2 * e.size, 2 * e.size];
    case 'grain': return [1000, 1000];
    case 'text': return [e.w, e.size * (e.lh || 1.18) * String(e.text).split('\n').length];
    default: return [e.w, e.h];
  }
}

// a smooth organic blob from a seed
function rnd(seed) { let s = seed * 9301 + 49297; return () => ((s = (s * 9301 + 49297) % 233280) / 233280); }
function blobPath(w, h, seed, n = 9, wob = 0.22) {
  const r = rnd(seed), pts = [];
  for (let i = 0; i < n; i++) {
    const a = i / n * Math.PI * 2, k = 1 - wob + r() * wob * 2;
    pts.push([w / 2 + Math.cos(a) * w / 2 * k, h / 2 + Math.sin(a) * h / 2 * k]);
  }
  let d = `M${pts[0][0]},${pts[0][1]}`;
  for (let i = 0; i < n; i++) {
    const p0 = pts[(i - 1 + n) % n], p1 = pts[i], p2 = pts[(i + 1) % n], p3 = pts[(i + 2) % n];
    d += ` C${p1[0] + (p2[0] - p0[0]) / 6},${p1[1] + (p2[1] - p0[1]) / 6} ${p2[0] - (p3[0] - p1[0]) / 6},${p2[1] - (p3[1] - p1[1]) / 6} ${p2[0]},${p2[1]}`;
  }
  return d + 'Z';
}
function scallop(cx, cy, r, bumps, depth) {
  let d = '';
  const n = bumps * 16;
  for (let i = 0; i <= n; i++) {
    const a = i / n * Math.PI * 2 - Math.PI / 2, rr = r + depth * Math.cos(a * bumps);
    d += (i ? 'L' : 'M') + (cx + rr * Math.cos(a)).toFixed(2) + ',' + (cy + rr * Math.sin(a)).toFixed(2);
  }
  return d + 'Z';
}
const sparkPath = (x, y, s) => `M${x},${y - s} Q${x + s * 0.18},${y - s * 0.18} ${x + s},${y} Q${x + s * 0.18},${y + s * 0.18} ${x},${y + s} Q${x - s * 0.18},${y + s * 0.18} ${x - s},${y} Q${x - s * 0.18},${y - s * 0.18} ${x},${y - s}Z`;

// An SVG that may paint outside its box by `pad` (for torn edges and shadows).
function padSvg(el, w, h, pad) {
  const svg = mk('svg', { width: w + 2 * pad, height: h + 2 * pad, viewBox: `${-pad} ${-pad} ${w + 2 * pad} ${h + 2 * pad}` }, el);
  Object.assign(svg.style, { position: 'absolute', left: -pad + 'px', top: -pad + 'px', overflow: 'visible' });
  return svg;
}

// Lay out a badge's lines by their real ink (not line boxes), centred on 0,0: a big number (k) on top,
// the label rows sharing one cap height; the largest size at which `fits` still holds.
function fitLines(lines, fits) {
  const ctx = document.createElement('canvas').getContext('2d');
  const measure = (t, size) => {
    ctx.font = `${size}px Comica`;
    const m = ctx.measureText(t);
    return { w: (m.width + size * 0.05 * (t.length - 1)) * STRETCH, asc: m.actualBoundingBoxAscent, desc: m.actualBoundingBoxDescent };
  };
  const layout = (s) => {
    const L = lines.map((l) => ({ ...l, text: caps(fill(l.t)), size: s * (l.k || 1) }));
    L.forEach((l) => Object.assign(l, measure(l.text, l.size)));
    const lab = L.filter((l) => !l.k);
    if (lab.length) { const asc = Math.max(...lab.map((l) => l.asc)); lab.forEach((l) => { l.asc = asc; l.desc = 0; }); }
    const gapBig = s * 0.62, gap = s * 0.36;
    const gapBefore = (i) => (!i ? 0 : (L[i - 1].k ? gapBig : gap));
    let H = 0;
    L.forEach((l, i) => { H += l.asc + l.desc + gapBefore(i); });
    let y = -H / 2;
    L.forEach((l, i) => { y += gapBefore(i); l.top = y; l.base = y + l.asc; y += l.asc + l.desc; });
    return L;
  };
  let lo = 4, hi = 160;
  for (let i = 0; i < 30; i++) { const m = (lo + hi) / 2; if (fits(layout(m))) lo = m; else hi = m; }
  return layout(lo);
}
// …inside a circle of radius `face`, with an even margin
const fitText = (lines, face, pad = 0.22) => fitLines(lines, (L) => L.every((l) => {
  const hw = l.w / 2 + l.size * 0.04, lim = face * (1 - pad);
  return [l.top, l.top + l.asc + l.desc].every((y) => Math.hypot(hw, y) <= lim);
}));
// …inside a w × h rectangle
const fitRect = (lines, w, h, pad = 0.16) => fitLines(lines, (L) => {
  const H = L[L.length - 1].top + L[L.length - 1].asc + L[L.length - 1].desc - L[0].top;
  return H <= h * (1 - pad) && L.every((l) => l.w / 2 + l.size * 0.04 <= w / 2 * (1 - pad));
});

// badge lines (from fitLines) as white stretched Comica, centred at cx, cy
function drawLines(parent, L, cx, cy, filterId, color = '#fff') {
  const tg = mk('g', filterId ? { filter: `url(#${filterId})` } : {}, parent);
  for (const l of L) {
    const ls = l.size * 0.05;
    const t = mk('text', {
      x: (cx + ls / 2).toFixed(2), y: (cy + l.base).toFixed(2), 'text-anchor': 'middle',
      'font-family': 'Comica', 'font-size': l.size.toFixed(2), 'letter-spacing': ls.toFixed(2),
      fill: color, stroke: color, 'stroke-width': (l.size * 0.06).toFixed(2), 'stroke-linejoin': 'round', 'paint-order': 'stroke',
      transform: `translate(${cx} 0) scale(${STRETCH} 1) translate(${-cx} 0)`,
    }, tg);
    t.textContent = l.text;
  }
}
// the shadow a die-cut piece casts, and the soft shadow under white letters (one, offset down: the owner wanted flat
// letters with a shadow, not "embossed" ones — 29.09.2026)
const letterShadow = (id, ts) => `<filter id="${id}ts" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="1" dy="4" stdDeviation="3.5" flood-color="#4a2e18" flood-opacity="${ts}"/></filter>`;
const SHADOW_DEFS = (id, ts = TSHADOW) => `<filter id="${id}s" x="-30%" y="-30%" width="160%" height="160%">
    <feGaussianBlur in="SourceAlpha" stdDeviation="9"/><feOffset dx="6" dy="11" result="b"/>
    <feComponentTransfer in="b" result="s"><feFuncA type="linear" slope=".34"/></feComponentTransfer>
    <feFlood flood-color="#4a3020"/><feComposite in2="s" operator="in"/>
    <feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <linearGradient id="${id}gl" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".30"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/></linearGradient>
  ${letterShadow(id, ts)}`;

// Text bent into an arc: `arc` — how many degrees the line spans (+ an arch ∩, − a smile ∪).
// Every letter is placed on the circle by itself and turned with it, keeping the stretched Comica look.
function arcText(el, e, id, color) {
  const ctx = document.createElement('canvas').getContext('2d');
  const size = e.size, lh = e.lh || 1.18, ls = size * 0.05, ts = e.shadow === false ? 0 : (e.tshadow ?? TSHADOW);
  const lines = fill(e.text).split('\n'), w = e.w, h = size * lh * lines.length;
  const svg = padSvg(el, w, h, size * 3);
  mk('defs', {}, svg).innerHTML = letterShadow(id, ts);
  const g = mk('g', ts ? { filter: `url(#${id}ts)` } : {}, svg);
  ctx.font = `${size}px Comica`;
  const ang = e.arc * Math.PI / 180;
  lines.forEach((line, i) => {
    const chars = [...caps(line)], adv = chars.map((c) => (ctx.measureText(c).width + ls) * STRETCH);
    const total = adv.reduce((a, b) => a + b, 0) - ls * STRETCH;
    const R = total / Math.abs(ang), up = ang > 0 ? 1 : -1;
    const base = size * lh * (i + 0.5) + size * 0.33;          // this line's baseline in the box
    const cx = w / 2, cy = base + up * R;                        // the circle's centre (below for ∩, above for ∪)
    let s = -total / 2;
    chars.forEach((c, j) => {
      const mid = s + (adv[j] - ls * STRETCH) / 2, phi = mid / R;  // the letter's middle, as an angle
      const x = cx + R * Math.sin(phi), y = cy - up * R * Math.cos(phi);
      const t = mk('text', {
        x: 0, y: 0, 'text-anchor': 'middle', 'font-family': 'Comica', 'font-size': size,
        fill: color, stroke: color, 'stroke-width': size * 0.05, 'stroke-linejoin': 'round', 'paint-order': 'stroke',
        transform: `translate(${x.toFixed(2)} ${y.toFixed(2)}) rotate(${(up * phi * 180 / Math.PI).toFixed(2)}) scale(${STRETCH} 1)`,
      }, g);
      t.textContent = c;
      s += adv[j];
    });
  });
}
const polyPath = (p) => 'M' + p.map(([x, y]) => x.toFixed(2) + ',' + y.toFixed(2)).join(' L');

// An arrow's line: from the first point to the last, bowed into an arc, with an optional round loop.
// Arrows drawn before (through many hand-placed points) keep their ends; their arc and loop are read
// off the old points: which side the middle points were on, and a loop if there were many of them.
function arrowCurve(P, e) {
  const A = P[0], B = P[P.length - 1], dx = B[0] - A[0], dy = B[1] - A[1], L = Math.hypot(dx, dy) || 1;
  const T = [dx / L, dy / L], N = [-T[1], T[0]];
  const mids = P.slice(1, -1), side = mids.length ? mids.reduce((s, q) => s + (q[0] - A[0]) * N[0] + (q[1] - A[1]) * N[1], 0) / mids.length : 0;
  const hasLoop = e.loop != null ? e.loop > 0 : P.length >= 6;
  const bow = e.bow ?? (hasLoop ? Math.sign(side || 1) * 0.18 : Math.max(-0.4, Math.min(0.4, side / L * 1.3)));
  const loop = e.loop ?? (hasLoop ? 0.15 : 0);
  const dir = e.loopDir ?? Math.sign(side || bow || 1), at = e.loopAt ?? 0.45, win = 0.38;
  const out = [];
  for (let i = 0; i <= 160; i++) {
    const s = i / 160, b = bow * L * 4 * s * (1 - s);
    let x = A[0] + dx * s + N[0] * b, y = A[1] + dy * s + N[1] * b;
    if (loop > 0) {
      let u = Math.max(0, Math.min(1, (s - (at - win / 2)) / win));
      u = u * u * (3 - 2 * u);
      const ang = 2 * Math.PI * u, r = loop * L, ot = r * Math.sin(ang), on = dir * r * (1 - Math.cos(ang));
      x += T[0] * ot + N[0] * on; y += T[1] * ot + N[1] * on;
    }
    out.push([x, y]);
  }
  return out;
}
const HEART = 'M.5,.96 C.2,.74 0,.54 0,.31 C0,.13 .14,0 .3,0 C.4,0 .47,.06 .5,.15 C.53,.06 .6,0 .7,0 C.86,0 1,.13 1,.31 C1,.54 .8,.74 .5,.96Z';
const ICONS = {
  thumb: 'M7 10v12 M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88Z',
  heart: 'M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z',
};

// A slot nothing fills (a mockup the book didn't get): its outline, dashed, and what should be there.
function placeholder(el, w, h, label) {
  const svg = padSvg(el, w, h, 0);
  mk('rect', { x: 2, y: 2, width: Math.max(0, w - 4), height: Math.max(0, h - 4), rx: 10, fill: 'rgba(255,255,255,.35)',
    stroke: 'rgba(90,70,50,.55)', 'stroke-width': 3, 'stroke-dasharray': '14 10' }, svg);
  const t = mk('text', { x: w / 2, y: h / 2, 'text-anchor': 'middle', 'dominant-baseline': 'middle', 'font-family': 'Segoe UI, sans-serif',
    'font-size': Math.max(14, Math.min(34, w / 14)), fill: 'rgba(90,70,50,.8)' }, svg);
  t.textContent = label;
}
const SLOT_NAME = { cover: 'Cover 1', dedication: 'Dedication', page30: 'Сторінка 30' };
const slotName = (slot) => SLOT_NAME[slot] || String(slot || '?').replace('open1:', 'Open 1 · ').replace('open2:', 'Open 2 · ');

export const DRAW = {
  grain(el, e, id) {
    const svg = padSvg(el, 1000, 1000, 0);
    const f = mk('filter', { id: id + 'g', x: 0, y: 0, width: '100%', height: '100%' }, svg);
    mk('feTurbulence', { type: 'fractalNoise', baseFrequency: 0.9, numOctaves: 2, seed: 7 }, f);
    mk('feColorMatrix', { type: 'matrix', values: '0 0 0 0 .35  0 0 0 0 .25  0 0 0 0 .15  0 0 0 .06 0' }, f);
    mk('rect', { width: 1000, height: 1000, filter: `url(#${id}g)` }, svg);
  },
  blob(el, e) {
    const svg = padSvg(el, e.w, e.h, 0);
    mk('path', { d: blobPath(e.w, e.h, e.seed || 1), fill: e.color }, svg);
  },
  band(el, e, id) {
    const pad = 40, svg = padSvg(el, e.w, e.h, pad), seed = e.seed || 4;
    const defs = mk('defs', {}, svg);
    const torn = (fid, s, scale, freq) => {
      const f = mk('filter', { id: fid, x: '-10%', y: '-10%', width: '120%', height: '120%' }, defs);
      mk('feTurbulence', { type: 'fractalNoise', baseFrequency: freq, numOctaves: 4, seed: s, result: 'n' }, f);
      mk('feDisplacementMap', { in: 'SourceGraphic', in2: 'n', scale }, f);
    };
    torn(id + 't', seed, 16, 0.045); torn(id + 'c', seed + 5, 12, 0.05);
    const lift = mk('filter', { id: id + 'l', x: '-20%', y: '-20%', width: '140%', height: '140%' }, defs);
    lift.innerHTML = `<feGaussianBlur in="SourceAlpha" stdDeviation="7"/><feOffset dx="5" dy="8" result="b"/>
      <feComponentTransfer in="b" result="s"><feFuncA type="linear" slope=".28"/></feComponentTransfer>
      <feFlood flood-color="#4a3020"/><feComposite in2="s" operator="in"/>
      <feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>`;
    const tex = mk('filter', { id: id + 'x', x: 0, y: 0, width: '100%', height: '100%' }, defs);
    tex.innerHTML = `<feTurbulence type="fractalNoise" baseFrequency=".6" numOctaves="3" seed="5" result="n"/>
      <feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .09 0" result="w"/>
      <feComposite in="w" in2="SourceGraphic" operator="in"/>`;
    const g = mk('g', { filter: `url(#${id}l)` }, svg);
    const rim = e.rim ?? 8;
    mk('rect', { x: -rim, y: -rim, width: e.w + 2 * rim, height: e.h + 2 * rim, fill: '#fbf6ee', filter: `url(#${id}c)` }, g);
    mk('rect', { x: 0, y: 0, width: e.w, height: e.h, fill: e.color, filter: `url(#${id}t)` }, g);
    mk('rect', { x: 0, y: 0, width: e.w, height: e.h, fill: e.color, filter: `url(#${id}x)` }, g);
  },
  // the book: its shadow from Photoshop (strength `bake`), then the book with a soft extra lift (`shadow`)
  book(el, e) {
    const f = bookInfo(e), h = e.w * bookAspect(e);
    if (!f) { placeholder(el, e.w, h, `${slotName(e.slot)} — немає мокапа`); return; }
    const W = e.w / f.w;
    const layer = (src, style) => {
      const img = document.createElement('img');
      img.src = src; img.draggable = false;
      img.onload = () => {
        const H = W * img.naturalHeight / img.naturalWidth;
        Object.assign(img.style, { position: 'absolute', width: W + 'px', left: (e.w / 2 - f.cx * W) + 'px', top: (h / 2 - f.cy * H) + 'px',
          maxWidth: 'none', pointerEvents: 'none', ...style });
      };
      el.appendChild(img);
    };
    layer(f.shadow, { opacity: e.bake ?? 0.6 });
    layer(f.src, { filter: `drop-shadow(8px 14px 18px rgba(55,40,25,${e.shadow ?? 0.18}))` });
  },
  dashes(el, e) {
    const svg = padSvg(el, e.w, e.h, 0), n = e.count || 11, dw = e.dash || 62;
    const step = (e.w - dw) / (n - 1);
    for (let i = 0; i < n; i++) mk('rect', { x: i * step, y: 0, width: dw, height: e.h, fill: e.color || '#fff' }, svg);
  },
  leaves(el, e, id) {
    const svg = padSvg(el, e.w, e.h, 0), sx = e.w / 600;
    const defs = mk('defs', {}, svg);
    defs.innerHTML = `<filter id="${id}b"><feGaussianBlur stdDeviation="3.5"/></filter>
      <radialGradient id="${id}f" cx="100%" cy="0%" r="100%"><stop offset="0" stop-color="#fff"/><stop offset=".55" stop-color="#fff" stop-opacity=".6"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
      <mask id="${id}m"><rect width="${e.w}" height="${e.h}" fill="url(#${id}f)"/></mask>`;
    const g = mk('g', { fill: '#6b4a33', filter: `url(#${id}b)`, mask: `url(#${id}m)` }, svg);
    const inner = mk('g', { transform: `scale(${sx})` }, g);
    const branch = (x, y, len, ang, n) => {
      mk('path', { d: `M${x},${y} Q${x + Math.cos(ang) * len * 0.5 + 30},${y + Math.sin(ang) * len * 0.5 - 20} ${x + Math.cos(ang) * len},${y + Math.sin(ang) * len}`, stroke: '#6b4a33', 'stroke-width': 5, fill: 'none' }, inner);
      for (let i = 0; i < n; i++) {
        const t = i / n, px = x + Math.cos(ang) * len * t, py = y + Math.sin(ang) * len * t, side = i % 2 ? 1 : -1;
        const cx = px + Math.cos(ang + side * 0.9) * 30, cy = py + Math.sin(ang + side * 0.9) * 30;
        mk('ellipse', { cx, cy, rx: 40, ry: 15, transform: `rotate(${ang * 180 / Math.PI + side * 52} ${cx} ${cy})` }, inner);
      }
    };
    branch(510, 90, 620, 2.25, 13); branch(460, 210, 360, 2.75, 8); branch(530, 410, 300, 2.9, 6);
    el.style.mixBlendMode = 'multiply';
  },
  sticker(el, e, id) {
    const S = 2 * e.r + 16, c = S / 2, face = e.r * 0.9, depth = e.r * 0.05;
    const svg = padSvg(el, S, S, 60), defs = mk('defs', {}, svg);
    defs.innerHTML = `<filter id="${id}s" x="-30%" y="-30%" width="160%" height="160%">
        <feGaussianBlur in="SourceAlpha" stdDeviation="9"/><feOffset dx="6" dy="11" result="b"/>
        <feComponentTransfer in="b" result="s"><feFuncA type="linear" slope=".34"/></feComponentTransfer>
        <feFlood flood-color="#4a3020"/><feComposite in2="s" operator="in"/>
        <feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      <linearGradient id="${id}gl" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".32"/><stop offset=".5" stop-color="#fff" stop-opacity="0"/></linearGradient>
      <filter id="${id}te"><feTurbulence type="fractalNoise" baseFrequency=".25" numOctaves="2" seed="3" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="5"/></filter>
      ${letterShadow(id, e.tshadow ?? TSHADOW)}`;
    const body = mk('g', { filter: `url(#${id}s)` }, svg);
    mk('path', { d: scallop(c, c, e.r, e.bumps || 14, depth), fill: '#fffaf2' }, body);
    mk('path', { d: scallop(c, c, face, e.bumps || 14, depth * 0.85), fill: e.color || '#e8c59d' }, svg);
    mk('path', { d: scallop(c, c, face, e.bumps || 14, depth * 0.85), fill: `url(#${id}gl)` }, svg);
    drawLines(svg, fitText(e.lines, face, e.pad ?? 0.22), c, c, id + 'ts', e.textColor);
    if (e.tape) {
      const [dx, ang] = e.tape, px = c + dx * e.r / 142, py = c - e.r + 6;
      const tape = mk('g', { transform: `rotate(${ang} ${px} ${py})`, opacity: 0.86 }, svg);
      const tw = 116 * e.r / 142, th = 34 * e.r / 142, tx = px - tw / 2, ty = py - th / 2;
      mk('rect', { x: tx, y: ty, width: tw, height: th, fill: '#c9cba0', filter: `url(#${id}te)` }, tape);
      for (let x = tx + 8; x < tx + tw - 6; x += 13) {
        mk('line', { x1: x, y1: ty + 3, x2: x + 6, y2: ty + th - 3, stroke: '#fff', 'stroke-width': 3, opacity: 0.45 }, tape);
      }
    }
  },
  sparkle(el, e, id) {
    const s = e.size, svg = padSvg(el, 2 * s, 2 * s, 10);
    mk('defs', {}, svg).innerHTML = `<filter id="${id}g" x="-50%" y="-50%" width="200%" height="200%"><feDropShadow dx="0" dy="1.5" stdDeviation="2.5" flood-color="#7a5a3a" flood-opacity=".25"/></filter>`;
    mk('path', { d: sparkPath(s, s, s), fill: e.color || '#fff', filter: `url(#${id}g)` }, svg);
  },
  // lines of text: Comica stretched like his Canva (capitals, a small dotted "i"), or a plain sans
  text(el, e, id) {
    const sans = e.font === 'sans', color = e.color || '#fff', align = e.align || 'left';
    if (e.arc && !sans) { arcText(el, e, id, color); return; }
    const box = document.createElement('div');
    Object.assign(box.style, { position: 'absolute', left: 0, top: 0, width: '100%', textAlign: align, whiteSpace: 'nowrap',
      fontFamily: sans ? '"Segoe UI",sans-serif' : 'Comica', fontSize: e.size + 'px', lineHeight: e.lh || 1.18, color,
      fontWeight: sans ? 400 : 'normal' });
    for (const line of fill(e.text).split('\n')) {
      const row = document.createElement('div'), span = document.createElement('span');
      span.textContent = sans ? line : caps(line);
      const ts = e.tshadow ?? TSHADOW;
      Object.assign(span.style, { display: 'inline-block', textShadow: e.shadow === false || !ts ? 'none'
        : `.02em .09em .12em rgba(60,36,18,${ts})` });
      if (!sans) {
        Object.assign(span.style, { transform: `scaleX(${STRETCH})`, letterSpacing: '.05em',
          transformOrigin: { left: '0 50%', center: '50% 50%', right: '100% 50%' }[align],
          webkitTextStroke: `.05em ${color}`, paintOrder: 'stroke fill' });
      }
      row.appendChild(span);
      box.appendChild(row);
    }
    el.appendChild(box);
  },
  // an arrow from its first to its last point (drawn in a w0 × h0 box, stretched to w × h):
  // a smooth arc (`bow`, a share of its length, ± = which side) with an optional round loop (`loop`)
  arrow(el, e, id) {
    const sx = e.w / e.w0, sy = e.h / e.h0, p = arrowCurve(e.pts.map(([x, y]) => [x * sx, y * sy]), e);
    const svg = padSvg(el, e.w, e.h, 80), sw = e.sw || 7, color = e.color || '#6b3a3a';
    const ts = e.tshadow ?? 0.45;
    mk('defs', {}, svg).innerHTML = `<filter id="${id}as" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="1" dy="3" stdDeviation="2.5" flood-color="#4a2e18" flood-opacity="${ts}"/></filter>`;
    const g = mk('g', ts ? { filter: `url(#${id}as)` } : {}, svg);
    const line = { fill: 'none', stroke: color, 'stroke-width': sw, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' };
    const [x, y] = p[p.length - 1], [px, py] = p[Math.max(0, p.length - 4)];
    const a = Math.atan2(y - py, x - px);
    if (e.solid) {   // a sharp filled head; the line stops inside it so the tip stays pointed
      const L = e.head || sw * 3.4, half = sw * 1.55;
      const bx = x - L * Math.cos(a), by = y - L * Math.sin(a);
      const keep = p.filter(([qx, qy]) => Math.hypot(qx - x, qy - y) > L - sw * 0.5);
      mk('path', { d: polyPath(keep.concat([[bx + Math.cos(a) * sw * 0.5, by + Math.sin(a) * sw * 0.5]])), ...line, 'stroke-linecap': 'butt' }, g);
      const nx = -Math.sin(a) * half, ny = Math.cos(a) * half;
      mk('path', { d: `M${x},${y} L${bx + nx},${by + ny} L${bx - nx},${by - ny}Z`, fill: color }, g);
    } else {
      mk('path', { d: polyPath(p), ...line }, g);
      const L = e.head || sw * 3.3, spread = 0.55;
      const wing = (s) => [x - L * Math.cos(a + s), y - L * Math.sin(a + s)];
      mk('path', { d: `M${wing(spread)} L${x},${y} L${wing(-spread)}`, ...line }, g);
    }
  },
  // a flat picture (a page, a whole mockup), optionally in a scalloped die-cut frame
  image(el, e, id) {
    const pic = ASSETS.pictures[e.slot];
    if (!pic) { placeholder(el, e.w, e.h, `${slotName(e.slot)} — немає картинки`); return; }
    if (pic.cut && e.shape !== 'scallop') {
      // cut out (Dedication: the book and the desk, the floor see-through, the shadows in the picture itself):
      // no white card under it and no frame — the slide shows through (29.09.2026)
      const svg = padSvg(el, e.w, e.h, 0);
      mk('image', { href: pic.src, x: 0, y: 0, width: e.w, height: e.h, preserveAspectRatio: 'xMidYMid slice' }, svg);
      return;
    }
    const svg = padSvg(el, e.w, e.h, 60), defs = mk('defs', {}, svg);
    defs.innerHTML = SHADOW_DEFS(id);
    const shape = e.shape === 'scallop'
      ? scallop(e.w / 2, e.h / 2, Math.min(e.w, e.h) / 2 * (1 - (e.depth ?? 0.07)), e.bumps || 10, Math.min(e.w, e.h) / 2 * (e.depth ?? 0.07))
      : `M0,0 H${e.w} V${e.h} H0Z`;
    const clip = mk('clipPath', { id: id + 'c' }, defs);
    mk('path', { d: shape }, clip);
    const g = mk('g', e.shadow === false ? {} : { filter: `url(#${id}s)` }, svg);
    if (e.rim) mk('path', { d: shape, fill: 'none', stroke: '#fffaf2', 'stroke-width': e.rim * 2, 'stroke-linejoin': 'round' }, g);
    mk('path', { d: shape, fill: '#fff' }, g);
    mk('image', { href: pic.src, x: 0, y: 0, width: e.w, height: e.h, preserveAspectRatio: 'xMidYMid slice', 'clip-path': `url(#${id}c)` }, svg);
  },
  // a bookmark ribbon (a V-notch at the bottom) with fitted text
  ribbon(el, e, id) {
    const { w, h } = e, notch = h * (e.notch ?? 0.13), svg = padSvg(el, w, h, 60);
    mk('defs', {}, svg).innerHTML = SHADOW_DEFS(id, e.tshadow ?? TSHADOW);
    const shape = `M0,0 H${w} V${h} L${w / 2},${h - notch} L0,${h}Z`;
    const g = mk('g', { filter: `url(#${id}s)` }, svg);
    if (e.rim ?? 7) mk('path', { d: shape, fill: '#fffaf2', stroke: '#fffaf2', 'stroke-width': (e.rim ?? 7) * 2, 'stroke-linejoin': 'round' }, g);
    mk('path', { d: shape, fill: e.color || '#a2a066' }, g);
    mk('path', { d: shape, fill: `url(#${id}gl)` }, svg);
    const hAvail = h - notch;
    drawLines(svg, fitRect(e.lines, w, hAvail, e.pad ?? 0.16), w / 2, hAvail / 2, id + 'ts', e.textColor);
  },
  // a die-cut heart with an icon
  heart(el, e, id) {
    const { w, h } = e, svg = padSvg(el, w, h, 60);
    mk('defs', {}, svg).innerHTML = SHADOW_DEFS(id);
    const tr = `scale(${w} ${h})`;
    const g = mk('g', { filter: `url(#${id}s)` }, svg);
    mk('path', { d: HEART, transform: tr, fill: '#fffaf2', stroke: '#fffaf2', 'stroke-width': 14 / w, 'stroke-linejoin': 'round' }, g);
    mk('path', { d: HEART, transform: tr, fill: e.color || '#e8c59d' }, g);
    mk('path', { d: HEART, transform: tr, fill: `url(#${id}gl)` }, svg);
    if (e.icon) {
      const s = Math.min(w, h) * (e.iconSize ?? 0.4) / 24;
      // the shadow on a group in the slide's scale (on the scaled path it smeared into a dark square)
      const ig = mk('g', { filter: `url(#${id}ts)` }, svg);
      mk('path', { d: ICONS[e.icon], fill: 'none', stroke: '#fff', 'stroke-width': 1.7, 'stroke-linecap': 'round', 'stroke-linejoin': 'round',
        transform: `translate(${w / 2 - 12 * s} ${h * 0.44 - 12 * s}) scale(${s})` }, ig);
    }
  },
};

// centre on x, y; turn; mirror (flipX ↔, flipY ↕)
export const elTransform = (e) => `translate(-50%,-50%) rotate(${e.rot || 0}deg) scale(${e.flipX ? -1 : 1},${e.flipY ? -1 : 1})`;

/** One element into a positioned div; `prefix` keeps its SVG ids apart from another scene's on the same page. */
export function drawElement(e, idx, prefix = 's') {
  const el = document.createElement('div');
  el.className = 'el';
  el.dataset.idx = idx;
  const [w, h] = boxOf(e);
  Object.assign(el.style, { position: 'absolute', left: e.x + 'px', top: e.y + 'px', width: w + 'px', height: h + 'px',
    transform: elTransform(e), opacity: e.opacity ?? 1, display: e.hidden ? 'none' : 'block' });
  (DRAW[e.type] || (() => {}))(el, e, `${prefix}${idx}_${e.uid || idx}_`);
  return el;
}

export function drawScene(scene, stage, prefix = 's') {
  stage.replaceChildren();
  stage.style.background = scene.bg;
  scene.items.forEach((e, i) => stage.appendChild(drawElement(e, i, prefix)));
}
