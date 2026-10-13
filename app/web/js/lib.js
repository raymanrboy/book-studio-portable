// Shared helpers: API client, safe HTML templates, toasts, modals, menus, jobs, formatting.
import { icon } from './icons.js';

export const TOKEN = document.querySelector('meta[name="studio-token"]').content;

// ------------------------------------------------------------------ safe HTML
class Html { constructor(s) { this.s = s; } toString() { return this.s; } }
export const raw = (s) => new Html(String(s ?? ''));
const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
export const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ESC[c]);
function render(v) {
  if (v === null || v === undefined || v === false) return '';
  if (v instanceof Html) return v.s;
  if (Array.isArray(v)) return v.map(render).join('');
  return esc(v);
}
export function html(strings, ...vals) {
  let out = strings[0];
  for (let i = 0; i < vals.length; i++) out += render(vals[i]) + strings[i + 1];
  return new Html(out);
}
export const ic = (name, cls) => raw(icon(name, cls));

/** One attribute for `ib()`'s `attrs` (or any markup string) with its value escaped: `attr('data-name', file.name)` —
 *  for anything that comes from the server or a file name. */
export const attr = (name, value) => `${name}="${esc(value)}"`;

/**
 * Icon-only button. Its meaning travels in the tooltip and the screen-reader label.
 * `attrs` is trusted markup written in this codebase (data-act etc.); a value from the server or a file goes
 * through `attr()`, never in raw.
 */
export function ib(iconName, tip, attrs = '', { cls = '', kbd = '' } = {}) {
  return raw(`<button type="button" class="ib ${cls}" aria-label="${esc(tip)}" data-tip="${esc(tip)}"${kbd ? ` data-kbd="${esc(kbd)}"` : ''} ${attrs}>${icon(iconName)}</button>`);
}

// ------------------------------------------------------------------ tooltips
// One floating element for the whole app. Hover waits a moment (no flicker while the pointer
// travels); once a tip is showing, neighbours in the same toolbar answer instantly. Keyboard
// focus shows it at once, Escape hides it, and it is linked to its button with aria-describedby.
const tipState = { el: null, target: null, timer: 0, hiddenAt: 0 };
function tipNode() {
  if (!tipState.el) {
    tipState.el = document.createElement('div');
    tipState.el.className = 'tip';
    tipState.el.id = 'tip';
    tipState.el.setAttribute('role', 'tooltip');
    document.body.appendChild(tipState.el);
  }
  return tipState.el;
}
function showTip(t) {
  if (!t.isConnected || !t.dataset.tip) return;
  const node = tipNode();
  node.innerHTML = `${esc(t.dataset.tip)}${t.dataset.kbd ? `<kbd>${esc(t.dataset.kbd)}</kbd>` : ''}`;
  node.classList.remove('on');
  const r = t.getBoundingClientRect();
  const w = node.offsetWidth, h = node.offsetHeight;
  const side = t.dataset.tipSide || (r.top > h + 14 ? 'top' : 'bottom');
  let x = r.left + r.width / 2 - w / 2, y = side === 'top' ? r.top - h - 8 : r.bottom + 8;
  if (side === 'right') { x = r.right + 10; y = r.top + r.height / 2 - h / 2; }
  x = Math.max(8, Math.min(innerWidth - w - 8, x));
  y = Math.max(8, Math.min(innerHeight - h - 8, y));
  node.dataset.side = side;
  node.style.transform = `translate3d(${Math.round(x)}px, ${Math.round(y)}px, 0)`;
  t.setAttribute('aria-describedby', 'tip');
  tipState.target = t;
  // Styles were already flushed by the measurement above, so adding the class now still fades in.
  node.classList.add('on');
}
export function hideTip() {
  clearTimeout(tipState.timer);
  if (tipState.target) { tipState.target.removeAttribute('aria-describedby'); tipState.target = null; tipState.hiddenAt = performance.now(); }
  tipState.el?.classList.remove('on');
}
document.addEventListener('pointerover', (e) => {
  const t = e.target.closest?.('[data-tip]');
  if (t === tipState.target) return;
  const warm = !!tipState.target || performance.now() - tipState.hiddenAt < 500;
  hideTip();
  if (!t || e.pointerType === 'touch') return;
  tipState.timer = setTimeout(() => showTip(t), warm ? 0 : 320);
});
document.addEventListener('focusin', (e) => {
  const t = e.target.closest?.('[data-tip]');
  if (t && t.matches(':focus-visible')) { hideTip(); showTip(t); }
});
document.addEventListener('focusout', () => hideTip());
document.addEventListener('pointerdown', () => hideTip(), true);
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && tipState.target) hideTip(); }, true);
document.addEventListener('scroll', () => hideTip(), { capture: true, passive: true });

export function setHtml(el, content) { el.innerHTML = render(content); return el; }
/** setHtml with a short fade of the new content (a region that was visible and is swapped whole). */
export function setHtmlFade(el, content, ms = 140) {
  setHtml(el, content);
  if (!reducedMotion()) el.animate([{ opacity: 0 }, { opacity: 1 }], { duration: ms, easing: 'ease-out' });
  return el;
}
/** Removes `node` once its exit animation (a `-out` keyframe from a `.closing` class) has ended — `animationend` with a
 *  timeout as the fallback, so no CSS duration is copied into the script. `then` runs just before the removal. */
export function removeAfterExit(node, then = null, fallback = 400) {
  let done = false;
  const go = () => { if (done) return; done = true; then?.(); node.remove(); };
  node.addEventListener('animationend', (e) => { if (e.target === node && /out$/.test(e.animationName)) go(); });
  setTimeout(go, fallback);
}
export function el(content) {
  const t = document.createElement('template');
  t.innerHTML = render(content).trim();
  return t.content.firstElementChild;
}
export const $ = (sel, root = document) => root.querySelector(sel);
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
export function on(root, type, selector, handler) {
  const fn = (e) => {
    const target = e.target.closest(selector);
    if (target && root.contains(target)) handler(e, target);
  };
  root.addEventListener(type, fn);
  return () => root.removeEventListener(type, fn);
}
export const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/** A page's own preference kept in the window (a filter, a period, the open cards) — a nicety only: missing or
 *  broken, it is the fallback, never an error that stops the page. */
export function remembered(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key) ?? 'null') ?? fallback; } catch { return fallback; }
}
export function remember(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* not kept this time */ }
}
export function debounce(fn, ms = 300) {
  let t;
  const d = (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
  d.flush = (...a) => { clearTimeout(t); fn(...a); };
  d.cancel = () => clearTimeout(t);
  return d;
}

// ------------------------------------------------------------------ API
class ApiError extends Error {
  constructor(message, status = 0, data = null) { super(message); this.status = status; this.data = data; }
}

let offlineTimer = null;
function markOffline() {
  clearTimeout(offlineTimer);
  offlineTimer = setTimeout(async () => {
    try { await fetch('/api/ping', { cache: 'no-store' }); } catch { document.getElementById('offline').hidden = false; }
  }, 600);
}

export async function api(path, { method = 'GET', body, headers = {}, signal } = {}) {
  const isBinary = body instanceof Blob || body instanceof ArrayBuffer;
  const opts = {
    method,
    headers: { 'X-Studio-Token': TOKEN, ...(body !== undefined && !isBinary ? { 'Content-Type': 'application/json' } : {}), ...headers },
    body: body === undefined ? undefined : isBinary ? body : JSON.stringify(body),
    signal,
    cache: 'no-store',
  };
  let res;
  try {
    res = await fetch(path, opts);
  } catch (err) {
    if (err.name === 'AbortError') throw err;
    markOffline();
    throw new ApiError("Немає зв'язку з програмою.", 0);
  }
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = null; }
  if (!res.ok) {
    // The server's bare «Forbidden» is a stale session (the program was restarted behind an old window); other 403s have their own words.
    const stale = res.status === 403 && data?.error === 'Forbidden';
    throw new ApiError(stale ? 'Це вікно застаріло — натисніть F5, щоб перезавантажити сторінку.' : data?.error || `Помилка ${res.status}`, res.status, data);
  }
  if (method === 'GET' && KEPT.has(path)) kept.set(path, { at: Date.now(), data });
  return data;
}

// The heavy lists' last answers: what only needs a glance right after a page fetched them (the Books tabs' counts) takes
// them from here instead of asking the program again (04.10.2026). A page itself always asks.
const KEPT = new Set(['/api/library/books', '/api/workshop/books']);
const kept = new Map();
export const recent = (path, ms = 5000) => {
  const k = kept.get(path);
  return k && Date.now() - k.at < ms ? Promise.resolve(k.data) : api(path);
};

/** Tells the shell what is going on (the rail's dot, the window's title — app.js): `{ mockups: true }`,
 *  `{ workshop: label }`, `{ done: text }`. */
export const tellBusy = (detail) => window.dispatchEvent(new CustomEvent('bs:busy', { detail }));

/** A POST to the program (`body` as JSON; none — none). */
export function post(path, body) {
  return api(path, { method: 'POST', body });
}

// Pictures carry a key of their own that outlives a restart: the same address, so the window shows them from its cache (04.10.2026).
const MEDIA_TOKEN = document.querySelector('meta[name="media-token"]')?.content || TOKEN;

export const media = (path, params = {}) => {
  const q = new URLSearchParams({ ...params, t: MEDIA_TOKEN });
  return `${path}?${q}`;
};

export function upload(url, file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', url);
    xhr.setRequestHeader('X-Studio-Token', TOKEN);
    xhr.upload.onprogress = (e) => { if (e.lengthComputable && onProgress) onProgress(e.loaded / e.total); };
    xhr.onload = () => {
      let data = null;
      try { data = JSON.parse(xhr.responseText); } catch { data = null; }
      if (xhr.status >= 200 && xhr.status < 300) resolve(data);
      else reject(new ApiError(data?.error || `Помилка ${xhr.status}`, xhr.status, data));
    };
    xhr.onerror = () => { markOffline(); reject(new ApiError("Немає зв'язку з програмою.")); };
    xhr.send(file);
  });
}

// keepGoing() false — the page no longer needs the result: polling stops (the error is for the caller to ignore).
export async function runJob(startPromise, onProgress, interval = 420, keepGoing = () => true) {
  const { jobId } = await startPromise;
  for (;;) {
    await sleep(interval);
    if (!keepGoing()) throw new ApiError('Більше не потрібно', 0);
    const job = await api(`/api/jobs/${jobId}`);
    onProgress?.(job);
    if (job.status === 'done') return job.result;
    if (job.status === 'error') throw new ApiError(job.error || 'Помилка', 0, { ...job, ...job.errorExtra }); // err.data.code as for a request
  }
}

export async function openExternal(url) {
  if (!url) return;
  try { await post('/api/app/open-url', { url }); }
  catch (e) { toast(e.message, 'error'); }
}

export async function copyText(text, label = 'Скопійовано') {
  try {
    await navigator.clipboard.writeText(text);
    toast(label, 'success', 1800);
    return true;
  } catch {
    const ta = document.createElement('textarea');
    ta.value = text; document.body.appendChild(ta); ta.select();
    const ok = document.execCommand('copy');
    ta.remove();
    toast(ok ? label : 'Не вдалося скопіювати', ok ? 'success' : 'error', 1800);
    return ok;
  }
}

/** The way back from a tool that was opened on its own, from «Інструменти» (2026-09-30). */
export const backToTools = () => html`<a class="back-link" href="#/tools" aria-label="До інструментів" data-tip="До інструментів">${ic('arrowLeft')}</a>`;

/** A sticky column taller than the window sticks by its bottom, not its top (2026-09-30): the page scrolls on until the column's
 *  end shows, then it stays — no scroller of its own for the wheel to get stuck in. Returns a function that stops watching. */
export function stickyFit(el, gap = 16) {
  if (!el) return () => {};
  const fit = () => { const box = el.closest('.main') || document.documentElement; el.style.top = `${Math.min(gap, box.clientHeight - el.offsetHeight - gap)}px`; };
  const ro = new ResizeObserver(fit);
  ro.observe(el);
  window.addEventListener('resize', fit);
  fit();
  return () => { ro.disconnect(); window.removeEventListener('resize', fit); };
}

// ------------------------------------------------------------------ toasts
/** `undo: {label, run}` (2026-09-30): a «Скасувати» on the toast — only for an action the program can really take back
 *  (a book moved to the library's trash), never a promise it cannot keep. It stays longer than a plain message. */
export function toast(message, type = 'info', ms = 3800, { undo = null } = {}) {
  const box = document.getElementById('toasts');
  const name = type === 'success' ? 'checkCircle' : type === 'error' ? 'alertCircle' : 'info';
  const t = el(html`<div class="toast toast-${type}">${ic(name)}<div>${message}</div>${undo ? html`<button type="button" class="toast-undo">${undo.label || 'Скасувати'}</button>` : ''}</div>`);
  stackFlip(box, () => box.appendChild(t));
  // The others in the stack glide into their new places (as the toast leaves, too) instead of jumping.
  const close = () => {
    if (t.classList.contains('out')) return;
    t.classList.add('out');
    let gone = false;
    const leave = () => { if (gone) return; gone = true; stackFlip(box, () => t.remove()); };
    t.addEventListener('animationend', (e) => { if (e.target === t && e.animationName === 'toast-out') leave(); });
    setTimeout(leave, 320);
  };
  t.addEventListener('click', close);
  if (undo) t.querySelector('.toast-undo').addEventListener('click', async (e) => {
    e.stopPropagation();
    e.currentTarget.disabled = true;
    try { await undo.run(); } catch (err) { toast(err.message, 'error'); }
    close();
  });
  setTimeout(close, type === 'error' ? Math.max(ms, 6500) : undo ? Math.max(ms, 9000) : ms);
}

/** The children of a vertical stack glide to their new places after `mutate()` added or removed one (FLIP, transform only). */
function stackFlip(box, mutate) {
  const before = [...box.children].map((n) => [n, n.getBoundingClientRect().top]);
  mutate();
  if (reducedMotion()) return;
  const moves = before.filter(([n]) => n.isConnected).map(([n, top]) => [n, top - n.getBoundingClientRect().top]);
  for (const [n, d] of moves) {
    if (Math.abs(d) > 0.5) n.animate([{ transform: `translateY(${d}px)` }, { transform: 'none' }], { duration: 260, easing: EASE });
  }
}

/** A press that cannot go on yet lights up what is missing (the owner, 23.09.2026: "a button never ignores a press in
 *  silence"): each field gets an amber edge until it is typed in, the first one takes the focus (2026-09-30). */
export function markMissing(fields) {
  const list = fields.filter(Boolean);
  list.forEach((f) => {
    f.classList.add('is-missing');
    f.addEventListener('input', () => f.classList.remove('is-missing'), { once: true });
    f.addEventListener('change', () => f.classList.remove('is-missing'), { once: true });
  });
  list[0]?.focus();
}

// ------------------------------------------------------------------ modal
/** The dialog or page viewer on top (the one opened last) — only it answers the keyboard. */
export function topLayer() {
  const open = document.querySelectorAll('.modal-root:not(.closing), .lightbox:not(.closing)');
  return open[open.length - 1] || null;
}

const modalStack = [];
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && modalStack.length) {
    const top = modalStack[modalStack.length - 1];
    if (top.root === topLayer() && top.dismissible) { e.preventDefault(); top.close(); }
  }
});

// Tab stays inside the dialog on top: it wraps from the last control to the first and back.
document.addEventListener('keydown', (e) => {
  if (e.key !== 'Tab' || !modalStack.length) return;
  const top = modalStack[modalStack.length - 1];
  if (top.root !== topLayer()) return;
  const stops = [...top.el.querySelectorAll('a[href], button:not(:disabled), input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])')]
    .filter((x) => x.offsetParent);
  if (!stops.length) return;
  const first = stops[0], last = stops[stops.length - 1];
  if (!top.el.contains(document.activeElement)) { e.preventDefault(); first.focus(); }
  else if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
  else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
});

let modalSeq = 0;
export function modal({ title, sub = '', body = '', foot = null, size = '', dismissible = true, onClose } = {}) {
  const titleId = `modal-title-${++modalSeq}`;
  const root = el(html`<div class="modal-root">
    <div class="modal ${size ? 'modal-' + size : ''}" role="dialog" aria-modal="true" aria-labelledby="${titleId}">
      <div class="modal-head">
        <div class="grow"><h3 id="${titleId}">${title}</h3>${sub ? html`<div class="modal-sub">${sub}</div>` : ''}</div>
        ${dismissible ? ib('x', 'Закрити', 'data-close', { kbd: 'Esc' }) : ''}
      </div>
      <div class="modal-body"></div>
      ${foot !== null ? html`<div class="modal-foot"></div>` : ''}
    </div></div>`);
  const bodyEl = root.querySelector('.modal-body');
  const footEl = root.querySelector('.modal-foot');
  if (body instanceof Node) bodyEl.appendChild(body); else setHtml(bodyEl, body);
  if (footEl && foot !== null) { if (foot instanceof Node) footEl.appendChild(foot); else setHtml(footEl, foot); }
  let closed = false;
  const opener = document.activeElement; // the control that opened it gets the focus back (2026-09-30, the Tab walk)
  const api_ = {
    root, el: root.querySelector('.modal'), body: bodyEl, foot: footEl, dismissible,
    close(result) {
      if (closed) return; closed = true;
      const i = modalStack.indexOf(api_); if (i >= 0) modalStack.splice(i, 1);
      root.classList.add('closing');
      removeAfterExit(root);
      onClose?.(result);
      if (opener && opener !== document.body && document.contains(opener) && root.contains(document.activeElement)) opener.focus({ preventScroll: true });
    },
  };
  root.addEventListener('mousedown', (e) => { if (e.target === root && dismissible) api_.close(); });
  root.querySelector('[data-close]')?.addEventListener('click', () => api_.close());
  document.body.appendChild(root);
  modalStack.push(api_);
  setTimeout(() => root.querySelector('[autofocus]')?.focus(), 60);
  return api_;
}

// `extra` — markup under the text (built with html``), e.g. what exactly is about to be saved.
/** Esc steps back to `hash` (a detail page to its list) when nothing else owns the key: a dialog, the viewer, a menu
 *  — and, with `fields`, a text field being edited. Returns `listen(yes)`: a page kept out of sight lets go of the
 *  key and takes it again when it is back. */
export function escBack(hash, { fields = false } = {}) {
  const onKey = (e) => {
    if (e.key !== 'Escape' || e.defaultPrevented) return;
    if (document.querySelector('.modal-root:not(.closing), .lightbox:not(.closing), .menu:not(.closing)')) return;
    if (fields && /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName || '')) return;
    location.hash = hash;
  };
  const listen = (yes = true) => document[yes ? 'addEventListener' : 'removeEventListener']('keydown', onKey);
  listen(true);
  return listen;
}

/** A detail page that could not open: the way back to its list and what went wrong. */
export function notFound(view, { back, backLabel, icon, title, text }) {
  setHtml(view, html`<a class="back-link" href="${back}" aria-label="${backLabel}" data-tip="${backLabel}">${ic('arrowLeft', 'icon-s')}</a>
    <div class="empty"><div class="empty-icon">${ic(icon)}</div><h3>${title}</h3><p>${text}</p></div>`);
}

export function confirmBox({ title, text = '', extra = '', confirm = 'Підтвердити', cancel = 'Скасувати', danger = false } = {}) {
  return new Promise((resolve) => {
    let result = false;
    const m = modal({
      title,
      body: html`<p class="muted" style="white-space:pre-line">${text}</p>${extra}`,
      // A destructive question starts on «Скасувати»: a stray Enter must not be the destructive press.
      foot: html`<button class="btn btn-ghost" data-no ${danger ? 'autofocus' : ''}>${cancel}</button>
        <button class="btn ${danger ? 'btn-danger' : 'btn-primary'}" data-yes ${danger ? '' : 'autofocus'}>${confirm}</button>`,
      onClose: () => resolve(result),
    });
    m.foot.querySelector('[data-no]').onclick = () => m.close();
    m.foot.querySelector('[data-yes]').onclick = () => { result = true; m.close(); };
  });
}

/** A step that needs the owner's word first: «Продовжити» stays off until the box (`check` — what he confirms) is
 *  ticked. `act()`, if given, runs before the dialog closes; when it fails, its error shows and the dialog stays.
 *  Resolves true when the step may go on (the Etsy sign-in, the Printify store's manual approval). */
export function confirmChecked({ title, sub = '', warning, extra = '', check, confirm = 'Продовжити', cancel = 'Скасувати', icon = '', act = null }) {
  return new Promise((resolve) => {
    let ok = false;
    const m = modal({
      title,
      sub,
      body: html`<div class="stack">
          <div class="notice notice-warn">${ic('alert')}<div>${warning}</div></div>
          ${extra}
          <label class="check card-soft" style="padding:12px"><input type="checkbox" data-agree><span style="font-weight:600">${check}</span></label>
        </div>`,
      foot: html`<button class="btn btn-ghost" data-c>${cancel}</button><button class="btn btn-primary" data-go disabled>${icon ? ic(icon, 'icon-s') : ''}${confirm}</button>`,
      onClose: () => resolve(ok),
    });
    const go = m.foot.querySelector('[data-go]');
    m.el.querySelector('[data-agree]').addEventListener('change', (e) => { go.disabled = !e.target.checked; });
    m.foot.querySelector('[data-c]').onclick = () => m.close();
    go.onclick = async () => {
      go.disabled = true;
      try {
        await act?.();
        ok = true;
        m.close();
      } catch (err) { toast(err.message, 'error'); go.disabled = false; }
    };
  });
}

// ------------------------------------------------------------------ dropdown menu
let closeOpenMenu = null;
/** Closes the dropdown menu on screen, if any: a page change must not leave one floating over another page
 *  (Alt+1…5 moved on while «Ще» of a book's passport, with «Видалити книгу…», stayed open — 19.09.2026). */
export function closeMenu() { closeOpenMenu?.(); }

export function menu(anchor, items, { side = 'below' } = {}) {
  closeMenu();
  document.querySelectorAll('.menu').forEach((m) => m.remove());
  const m = el(html`<div class="menu" role="menu">${items.map((it, i) => it === '-' ? raw('<hr>') :
    html`<button type="button" role="menuitem" tabindex="-1" data-i="${i}" class="${it.danger ? 'danger' : ''} ${it.on ? 'on' : ''}" ${it.disabled ? 'disabled' : ''}>${ic(it.icon || 'chevRight')}<span class="grow">${it.label}</span>${it.on ? ic('check', 'icon-s') : ''}</button>`)}</div>`);
  document.body.appendChild(m);
  const r = anchor.getBoundingClientRect();
  const w = m.offsetWidth, h = m.offsetHeight;
  let left = Math.min(r.right - w, window.innerWidth - w - 10);
  let top = r.bottom + 6;
  if (side === 'right') { left = r.right + 8; top = Math.min(r.top, window.innerHeight - h - 10); m.style.transformOrigin = 'bottom left'; }
  else if (top + h > window.innerHeight - 10) top = Math.max(10, r.top - h - 6);
  m.style.left = `${Math.max(10, left)}px`;
  m.style.top = `${top}px`;
  const stops = () => [...m.querySelectorAll('button[role="menuitem"]:not(:disabled)')];
  let closed = false;
  // `restore`: the focus goes back to the control that opened the menu (Esc, a pick, Tab) — not when the page changes
  // under it or the pointer went elsewhere.
  const close = (restore = false) => {
    if (closed) return; closed = true; // the listeners below may not even have been added yet (the timeout)
    const hadFocus = m.contains(document.activeElement);
    m.classList.add('closing'); m.inert = true; removeAfterExit(m, null, 300);
    document.removeEventListener('mousedown', outside, true); document.removeEventListener('keydown', key, true);
    if (closeOpenMenu === closeThis) closeOpenMenu = null;
    if (restore && (hadFocus || document.activeElement === document.body) && anchor.isConnected) anchor.focus({ preventScroll: true });
  };
  const closeThis = () => close(false);
  closeOpenMenu = closeThis;
  const outside = (e) => { if (!m.contains(e.target)) close(false); };
  const key = (e) => {
    if (e.key === 'Escape') { e.stopPropagation(); close(true); return; }
    if (e.key === 'Tab') { close(true); return; } // the Tab goes on from the opener
    if (!['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(e.key)) return;
    const list = stops();
    if (!list.length) return;
    e.preventDefault(); e.stopPropagation();
    const i = list.indexOf(document.activeElement);
    const next = e.key === 'Home' ? 0 : e.key === 'End' ? list.length - 1
      : e.key === 'ArrowDown' ? (i + 1) % list.length : (i <= 0 ? list.length - 1 : i - 1);
    list[next].focus();
  };
  setTimeout(() => {
    if (closed) return; // closed before the timeout fired: no listener may be left behind
    document.addEventListener('mousedown', outside, true); document.addEventListener('keydown', key, true);
  });
  m.addEventListener('click', (e) => {
    const b = e.target.closest('button[data-i]');
    if (!b) return;
    close(true);
    items[+b.dataset.i].onClick?.();
  });
  // The first item takes the focus: Up/Down walk the list, Enter picks, Esc closes (a mouse opens it the same way).
  stops()[0]?.focus({ preventScroll: true });
}

// ------------------------------------------------------------------ segmented control
// `compact` — icons with their counts; only the active one shows its word (2026-09-30: show, don't tell).
export function segHtml(options, active, { accent = false, name = '', compact = false } = {}) {
  // The accessible name starts with the visible word (a tip alone would replace it); an icon-only tab is named by its tip.
  const label = (o) => {
    if (!o.tip) return '';
    const base = o.label ? (String(o.tip).startsWith(String(o.label)) ? o.tip : `${o.label} — ${o.tip}`) : o.tip;
    return raw(`data-tip="${esc(o.tip)}" aria-label="${esc(o.count !== undefined && o.count !== '' ? `${base}, ${o.count}` : base)}"`);
  };
  return html`<div class="seg ${accent ? 'seg-accent' : ''} ${compact ? 'seg-compact' : ''}" data-seg="${name}" role="tablist">
    <span class="seg-pill"></span>
    ${options.map((o) => html`<button type="button" role="tab" aria-selected="${String(o.value === active)}" data-value="${o.value}" class="${o.value === active ? 'active' : ''} ${o.label ? '' : 'seg-ico'}"
      ${label(o)}>${o.icon ? ic(o.icon, o.label ? 'icon-s' : '') : ''}${o.label ? html`<span class="seg-label">${o.label}</span>` : ''}${o.count !== undefined ? html`<span class="seg-count">${o.count}</span>` : ''}</button>`)}
  </div>`;
}
export function syncSeg(seg) {
  if (!seg) return;
  const active = seg.querySelector('button.active');
  // One Tab stop for the group, arrows inside it (the tabs pattern): the chosen tab is the stop.
  seg.querySelectorAll('button').forEach((b) => { b.tabIndex = !active || b === active ? 0 : -1; b.setAttribute('aria-selected', String(b === active)); });
  placePill(seg);
}
function placePill(seg) {
  const active = seg.querySelector('button.active');
  const pill = seg.querySelector('.seg-pill');
  if (!active || !pill) return;
  pill.style.width = `${active.offsetWidth}px`;
  pill.style.transform = `translateX(${active.offsetLeft - 3}px)`;
}
export function setSeg(seg, value) {
  seg.querySelectorAll('button').forEach((b) => b.classList.toggle('active', b.dataset.value === value));
  syncSeg(seg);
}
// On a window resize: every measurement first, then every write (no layout between the segments).
new ResizeObserver(() => {
  const m = [];
  document.querySelectorAll('.seg').forEach((seg) => {
    const a = seg.querySelector('button.active'), p = seg.querySelector('.seg-pill');
    if (a && p) m.push([p, a.offsetWidth, a.offsetLeft]);
  });
  for (const [p, w, l] of m) { p.style.width = `${w}px`; p.style.transform = `translateX(${l - 3}px)`; }
}).observe(document.documentElement);
document.addEventListener('keydown', (e) => {
  const tab = e.target.closest?.('.seg [role="tab"]');
  if (!tab || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
  const tabs = [...tab.closest('.seg').querySelectorAll('[role="tab"]')].filter((b) => !b.disabled);
  const i = tabs.indexOf(tab);
  const next = e.key === 'Home' ? tabs[0] : e.key === 'End' ? tabs[tabs.length - 1] : tabs[(i + (e.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length];
  e.preventDefault();
  next.focus();
  if (next !== tab) next.click(); // the tab it lands on is chosen at once, as a click would
});

// A clickable non-button (a row, a chip, a picture) is marked `role="button" tabindex="0" data-press`: Enter or Space on
// its own focus presses it, as on a real button. (A page that handles the keys itself leaves `data-press` off.)
document.addEventListener('keydown', (e) => {
  if ((e.key !== 'Enter' && e.key !== ' ') || e.defaultPrevented || e.target !== document.activeElement) return;
  if (!e.target.matches?.('[data-press]')) return;
  e.preventDefault();
  e.target.click();
});

/** True while the keyboard belongs to a field or a dialog: a page's single-key shortcuts stay quiet then. */
export const typing = () => /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName || '')
  || !!document.activeElement?.isContentEditable || !!document.querySelector('.modal-root:not(.closing), .lightbox:not(.closing)');

/** The gallery pages' keys (the Workshop, the library): Ctrl+F or «/» goes to the search `q`; a lone «N» runs `onNew`.
 *  Keys are told by their place on the keyboard (`code`), so the Ukrainian layout works as well as the Latin one;
 *  with Ctrl/Alt/Meta/Shift held, in a field or under a dialog, «N» does nothing. Returns the keydown handler. */
export function galleryKeys(q, onNew) {
  return (e) => {
    if (e.defaultPrevented) return;
    if (e.ctrlKey && !e.altKey && !e.metaKey && e.code === 'KeyF') { e.preventDefault(); q.focus(); q.select(); return; }
    if (e.ctrlKey || e.altKey || e.metaKey || typing()) return;
    if (e.key === '/' || (e.code === 'Slash' && !e.shiftKey)) { e.preventDefault(); q.focus(); q.select(); }
    else if (e.code === 'KeyN' && !e.shiftKey && !e.repeat) { e.preventDefault(); onNew(); }
  };
}

// ------------------------------------------------------------------ formatting
/** Dollars: «$12.50», «-$5.00» (a minus before the sign — the Profit page's own `usd()` until 27.09.2026; this one
 *  printed «$-5.00»), «—» for nothing. */
export const money = (n) => (n === null || n === undefined || Number.isNaN(Number(n)) ? '—'
  : `${n < 0 ? '-' : ''}$${Math.abs(Number(n)).toFixed(2)}`);
export const signedMoney = (n) => `${n >= 0 ? '+' : '-'}$${Math.abs(n).toFixed(2)}`;
export function dateTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString('uk-UA', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
function dateOnly(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString('uk-UA', { day: '2-digit', month: '2-digit', year: 'numeric' });
}
export function relTime(iso) {
  if (!iso) return 'ніколи';
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 45) return 'щойно';
  if (diff < 3600) return `${Math.round(diff / 60)} хв тому`;
  if (diff < 86400) return `${Math.round(diff / 3600)} год тому`;
  if (diff < 86400 * 7) return `${Math.round(diff / 86400)} дн тому`;
  return dateOnly(iso);
}
// An Etsy listing's state in plain Ukrainian; a state not listed here shows as Etsy wrote it.
const LISTING_STATES = { active: 'активний', inactive: 'неактивний', draft: 'чернетка', sold_out: 'розпродано', expired: 'термін минув',
  edit: 'редагується', create: 'створюється', private: 'приватний', unavailable: 'недоступний' };
export const listingState = (s) => LISTING_STATES[String(s ?? '').toLowerCase()] || s;
export function bytes(n) {
  if (!n && n !== 0) return '';
  if (n < 1024) return `${n} Б`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(0)} КБ`;
  if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} МБ`;
  return `${(n / 1024 ** 3).toFixed(2)} ГБ`;
}
/** The plural forms of «книга», for `plural(n, BOOKS)`. */
export const BOOKS = ['книга', 'книги', 'книг'];
export function plural(n, [one, few, many]) {
  const m10 = n % 10, m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
  return many;
}
export function naturalCompare(a, b) {
  return a.localeCompare(b, undefined, { numeric: true, sensitivity: 'base' });
}
export function highlightTokens(text) {
  // {Name}, {Gifter}, {ім'я} … get a soft accent to be easy to spot before Ctrl+F in Canva.
  return raw(esc(text).replace(/\{[^{}\n]{1,30}\}/g, (m) => `<span class="token">${m}</span>`));
}

// ------------------------------------------------------------------ smooth motion helpers
export const reducedMotion = () => document.documentElement.dataset.motion === 'reduce'
  || matchMedia('(prefers-reduced-motion: reduce)').matches;
const EASE = 'cubic-bezier(.2, .9, .25, 1)'; // the same as the CSS --ease-out

// Images fade in only after they are decoded off the main thread (no decode stall on first paint).
export function fadeImages(root) {
  root.querySelectorAll('img[data-fade=""]').forEach((img) => {
    img.dataset.fade = 'wait';
    img.decoding = 'async';
    // Even a cached picture is decoded off-thread before it becomes visible, so no frame waits for it.
    const reveal = () => (img.decode ? img.decode().catch(() => {}) : Promise.resolve()).then(() => { img.dataset.fade = 'in'; });
    if (img.complete && img.naturalWidth) reveal();
    else img.addEventListener('load', reveal, { once: true });
  });
}

// Height open/close with real intermediate frames: measured pixel heights animated by the Web Animations API.
export function slide(el, open, duration = 320) {
  el.getAnimations?.().forEach((a) => a.cancel());
  const from = el.getBoundingClientRect().height;
  el.classList.toggle('open', open);
  const to = open ? el.scrollHeight : 0;
  if (reducedMotion() || Math.abs(to - from) < 1) return;
  el.animate([{ height: `${from}px` }, { height: `${to}px` }], { duration, easing: EASE });
}

/** A block whose content `mutate()` changes glides from its old height to the new one (measured, Web Animations). */
export function glide(el, mutate, duration = 260) {
  const from = el.getBoundingClientRect().height;
  mutate();
  const to = el.scrollHeight;
  if (!reducedMotion() && Math.abs(to - from) > 1) el.animate([{ height: `${from}px` }, { height: `${to}px` }], { duration, easing: EASE });
}

// FLIP: children with data-key glide from their old to their new position after a DOM change.
export function flip(container, mutate, duration = 380) {
  const before = new Map();
  const nodes = new Map();
  if (!reducedMotion()) {
    container.querySelectorAll(':scope > [data-key]').forEach((node) => {
      if (!node.hidden) { before.set(node.dataset.key, node.getBoundingClientRect()); nodes.set(node.dataset.key, node); }
    });
  }
  mutate();
  if (reducedMotion()) return;
  // Every position read first, then every animation started: reading one card after another's animation began made
  // the browser lay the page out again for each card.
  const moves = [...container.querySelectorAll(':scope > [data-key]')].filter((node) => !node.hidden)
    .map((node) => [node, before.get(node.dataset.key), node.getBoundingClientRect()]);
  // A child that left fades out where it stood (a ghost clone, out of the layout) while the others glide into its place.
  const still = new Set(moves.map(([node]) => node.dataset.key));
  for (const [key, node] of nodes) {
    if (still.has(key) || node.isConnected) continue;
    try {
      const r = before.get(key);
      const ghost = node.cloneNode(true);
      ghost.removeAttribute('data-key'); ghost.removeAttribute('id');
      ghost.setAttribute('aria-hidden', 'true'); ghost.inert = true;
      Object.assign(ghost.style, { position: 'fixed', left: `${r.left}px`, top: `${r.top}px`, width: `${r.width}px`, height: `${r.height}px`,
        margin: '0', pointerEvents: 'none', zIndex: '5' });
      container.appendChild(ghost);
      const rm = () => ghost.remove();
      ghost.animate([{ opacity: 1, transform: 'scale(1)' }, { opacity: 0, transform: 'scale(.96)' }], { duration: 160, easing: EASE, fill: 'forwards' }).finished.then(rm, rm);
      setTimeout(rm, 600);
    } catch { /* no ghost: the card simply goes */ }
  }
  for (const [node, old, now] of moves) {
    if (!old) {
      node.animate([{ opacity: 0, transform: 'scale(.96)' }, { opacity: 1, transform: 'none' }], { duration: 260, easing: EASE });
      continue;
    }
    const dx = old.left - now.left, dy = old.top - now.top;
    if (Math.abs(dx) < 0.5 && Math.abs(dy) < 0.5) continue;
    node.animate([{ transform: `translate(${dx}px, ${dy}px)` }, { transform: 'none' }], { duration, easing: EASE });
  }
}

// A live page redrawn in place (the Workshop looks for changes every 1.5 s): each child of `container` is keyed
// (`data-key`); one whose markup hasn't changed stays as it is — its pictures, hover and focus with it —, a changed one
// is replaced, new ones come in, gone ones go, and the order follows `items` ([key, markup] pairs). A picture the old
// child already showed is carried into the new one as it is, decoded: nothing reloads or blinks. Returns the children
// (re)drawn this time, for the caller to fade their new pictures in.
const drawnFrom = new WeakMap(); // element → the markup it was drawn from
export function patch(container, items, redraw = null) {
  const old = new Map([...container.children].map((n) => [n.dataset.key, n]));
  const drawn = [];
  // The gone ones go first: a child that disappeared used to leave every one after it to be moved — and a moved
  // element loses focus and hover, which patch() is here to keep.
  const keep = new Set(items.map(([key]) => key));
  old.forEach((n, key) => { if (!keep.has(key)) { n.remove(); old.delete(key); } });
  let cursor = container.firstElementChild;
  for (const [key, markup] of items) {
    const text = render(markup);
    let node = old.get(key);
    old.delete(key);
    if (!node || drawnFrom.get(node) !== text || redraw?.has(key)) { // `redraw`: keys changed by hand meanwhile
      const next = el(raw(text));
      noteStyles(next);
      // A changed child is updated in place (same element, new attributes and content), so a class that flips plays its CSS
      // transition instead of being drawn already in its end state. Any failure falls back to the old replace below.
      if (node && !redraw?.has(key) && canMorph(node, next) && tryMorph(node, next)) {
        drawnFrom.set(node, text);
        drawn.push(node);
        if (node.querySelector('img[data-fade=""]')) fadeImages(node);
        if (node === cursor) cursor = node.nextElementSibling;
        else if (container.moveBefore && node.isConnected) container.moveBefore(node, cursor);
        else container.insertBefore(node, cursor);
        continue;
      }
      next.dataset.key = key;
      drawnFrom.set(next, text);
      if (node) {
        carryPictures(node, next);
        if (node === cursor) cursor = node.nextElementSibling;
        node.remove();
      }
      node = next;
      drawn.push(next);
    }
    if (node === cursor) cursor = node.nextElementSibling;
    else if (container.moveBefore && node.isConnected) container.moveBefore(node, cursor); // keeps focus and state
    else container.insertBefore(node, cursor);
  }
  // A class was taken off somewhere: the style is settled once here, so a caller that puts it back (a one-shot animation
  // class) really restarts the animation instead of finding the class never left.
  if (morphDirty) { morphDirty = false; void container.offsetWidth; }
  return drawn;
}

// ---- the in-place update behind patch(): the old element becomes the new one without being replaced.
let morphDirty = false;
const FORM_TAG = /^(INPUT|TEXTAREA|SELECT)$/;
const KEEP_ATTRS = new Set(['style', 'data-key', 'aria-describedby', 'tabindex']); // set from script, not by the markup
const noMorph = (n) => n.nodeType === 1 && n.hasAttribute('data-nomorph');
// The style an element's markup gave it: when the new markup has none, that one goes — a script's own style stays (11.10.2026:
// the cover's «Поля» picture left its aspect-ratio on the element that became the cover title's head, stretching it tall).
const markupStyle = new WeakMap();
function noteStyles(root) {
  if (root?.nodeType !== 1) return;
  if (root.hasAttribute('style')) markupStyle.set(root, root.getAttribute('style'));
  root.querySelectorAll('[style]').forEach((x) => markupStyle.set(x, x.getAttribute('style')));
}
const canMorph = (o, n) => !!n && o.tagName === n.tagName && !FORM_TAG.test(o.tagName) && !noMorph(o) && !noMorph(n);
function tryMorph(o, n) {
  try { morphAttrs(o, n); morphChildren(o, n); return true; }
  catch (err) { console.error('patch: in-place update failed, replacing', err); return false; }
}
function morphAttrs(o, n, skip = null) {
  for (const { name, value } of [...n.attributes]) {
    if (skip?.has(name)) continue;
    if (name === 'class') {
      const next = new Set(value.split(/\s+/).filter(Boolean));
      if (o.classList.contains('enter')) next.add('enter');    // an entrance still playing is not cut short
      for (const c of o.classList) if (!next.has(c)) morphDirty = true;
      const v = [...next].join(' ');
      if (o.getAttribute('class') !== v) o.setAttribute('class', v);
    } else {
      if (o.getAttribute(name) !== value) o.setAttribute(name, value);
      if (name === 'style') markupStyle.set(o, value);
    }
  }
  for (const { name } of [...o.attributes]) {
    if (name === 'style' && !n.hasAttribute(name) && !skip?.has(name) && markupStyle.get(o) === o.getAttribute('style')) {
      o.removeAttribute(name);
      markupStyle.delete(o);
      continue;
    }
    if (n.hasAttribute(name) || KEEP_ATTRS.has(name) || skip?.has(name)) continue;
    if (name === 'class') { morphDirty = true; if (o.classList.contains('enter')) { o.setAttribute('class', 'enter'); continue; } }
    o.removeAttribute(name);
  }
}
function swapNode(o, n) {
  if (o.nodeType === 1 && n.nodeType === 1) carryPictures(o, n);
  o.replaceWith(n);
}
function morphChildren(o, n) {
  const oc = [...o.childNodes], nc = [...n.childNodes];
  const k = Math.min(oc.length, nc.length);
  for (let i = 0; i < k; i++) morphNode(oc[i], nc[i]);
  for (let i = k; i < oc.length; i++) oc[i].remove();
  for (let i = k; i < nc.length; i++) o.appendChild(nc[i]);
}
function morphNode(o, n) {
  if (o.nodeType !== n.nodeType || (o.nodeType === 1 && (o.tagName !== n.tagName || noMorph(o) || noMorph(n)))) return swapNode(o, n);
  if (o.nodeType !== 1) { if (o.nodeValue !== n.nodeValue) o.nodeValue = n.nodeValue; return undefined; }
  const active = document.activeElement;
  if (FORM_TAG.test(o.tagName)) {
    // A field being typed in is never touched (value, selection, focus stay); an idle one with the same value keeps what was typed;
    // an idle one with another value is drawn anew.
    const skip = new Set(['value', 'checked', 'selected']);
    if (o === active) return morphAttrs(o, n, skip);
    if (o.tagName === 'INPUT' && (o.getAttribute('value') ?? '') === (n.getAttribute('value') ?? '') && o.hasAttribute('checked') === n.hasAttribute('checked')) return morphAttrs(o, n, skip);
    if (o.outerHTML === n.outerHTML) return undefined;
    return swapNode(o, n);
  }
  if (o.isContentEditable && (o === active || o.contains(active))) return morphAttrs(o, n); // text being edited stays
  if (o.tagName === 'IMG') return morphImg(o, n);
  morphAttrs(o, n);
  morphChildren(o, n);
  return undefined;
}
// A picture whose address changed keeps showing the old one until the new one is decoded — no blank frame between.
function morphImg(o, n) {
  const was = o.getAttribute('src'), now = n.getAttribute('src');
  morphAttrs(o, n, new Set(['src', 'srcset', 'data-fade']));
  if (!o.hasAttribute('data-fade') && n.hasAttribute('data-fade')) o.setAttribute('data-fade', n.getAttribute('data-fade'));
  if (was === now) return;
  if (!now || !was) { if (now) o.setAttribute('src', now); else o.removeAttribute('src'); return; }
  o._morphSrc = now;
  const pre = new Image();
  pre.decoding = 'async';
  pre.src = now;
  const go = () => { if (o._morphSrc === now) { o._morphSrc = null; o.setAttribute('src', now); } };
  (pre.decode ? pre.decode() : Promise.reject()).then(go, go);
}
/** One keyed child redrawn by hand (not through patch()) keeps its `data-key` and what it was drawn from, so the next patch()
 *  finds it unchanged instead of making a new one. Returns the new node. */
export function replaceKeyed(node, markup) {
  const text = render(markup);
  const next = el(raw(text));
  noteStyles(next);
  if (node.dataset.key !== undefined) next.dataset.key = node.dataset.key;
  drawnFrom.set(next, text);
  node.replaceWith(next);
  return next;
}
function carryPictures(from, to) {
  const shown = new Map([...from.querySelectorAll('img[data-fade="in"]')].map((img) => [img.getAttribute('src'), img]));
  to.querySelectorAll('img[src]').forEach((img) => {
    const same = shown.get(img.getAttribute('src'));
    if (!same) return;
    for (const { name } of [...same.attributes]) if (!img.hasAttribute(name) && name !== 'class') same.removeAttribute(name);
    for (const { name, value } of img.attributes) if (name !== 'data-fade') same.setAttribute(name, value);  // shown stays shown
    img.replaceWith(same);
  });
}

/** A progress bar (`.progress > i`) at `percent`: drawn by a transform, not its width — no layout on every step. */
export function setProgress(bar, percent, { reset = false } = {}) {
  if (!bar) return;
  const p = Math.max(0, Math.min(100, Number(percent) || 0));
  const track = bar.closest('.progress');
  track?.classList.remove('indet');
  if (reset) {              // a new run starts at the value at once — the bar never slides backwards
    bar.style.transition = 'none';
    bar.style.transform = `scaleX(${p / 100})`;
    void bar.offsetWidth;
    bar.style.transition = '';
  } else bar.style.transform = `scaleX(${p / 100})`;
  track?.classList.toggle('full', p >= 100);       // a finished bar stops its glint
}

// A copy button answers with a small pop and a green icon for a moment (`.copied`): any [data-copy] / [data-copy-text] button.
document.addEventListener('click', (e) => {
  const b = e.target.closest?.('[data-copy], [data-copy-text]');
  if (!b) return;
  b.classList.remove('copied');
  void b.offsetWidth;
  b.classList.add('copied');
  clearTimeout(b._copiedTimer);
  b._copiedTimer = setTimeout(() => b.classList.remove('copied'), 1300);
});

/** A row new to a list comes in with the page's entrance (`.enter`, `delay` ms late) — once: the class goes when it
 *  has played, so a later move of the row (patch()) never replays it. */
export function enterOnce(node, delay = 0) {
  if (delay) node.style.animationDelay = `${delay}ms`;
  node.classList.add('enter');
  node.addEventListener('animationend', () => { node.classList.remove('enter'); node.style.animationDelay = ''; }, { once: true });
}

// Re-render a region without stealing the caret from the field the user is typing in.
export function keepFocus(fn) {
  const a = document.activeElement;
  const id = a && a.id;
  const sel = id && typeof a.selectionStart === 'number' ? [a.selectionStart, a.selectionEnd] : null;
  fn();
  if (!id) return;
  const again = document.getElementById(id);
  if (again && again !== document.activeElement) {
    again.focus({ preventScroll: true });
    if (sel) { try { again.setSelectionRange(...sel); } catch { /* not a text field */ } }
  }
}

// Idle-time work that must not compete with animations.
export const idle = (fn) => (window.requestIdleCallback ? requestIdleCallback(fn, { timeout: 1500 }) : setTimeout(fn, 200));
