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

/**
 * Icon-only button. Its meaning travels in the tooltip and the screen-reader label.
 * `attrs` is trusted markup written in this codebase (data-act etc.), never user text.
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
document.addEventListener('scroll', () => hideTip(), true);

export function setHtml(el, content) { el.innerHTML = render(content); return el; }
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
export function debounce(fn, ms = 300) {
  let t;
  const d = (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
  d.flush = (...a) => { clearTimeout(t); fn(...a); };
  d.cancel = () => clearTimeout(t);
  return d;
}

// ------------------------------------------------------------------ API
export class ApiError extends Error {
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
  if (!res.ok) throw new ApiError(data?.error || `Помилка ${res.status}`, res.status, data);
  return data;
}

export const media = (path, params = {}) => {
  const q = new URLSearchParams({ ...params, t: TOKEN });
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
  try { await api('/api/app/open-url', { method: 'POST', body: { url } }); }
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

// ------------------------------------------------------------------ toasts
export function toast(message, type = 'info', ms = 3800) {
  const box = document.getElementById('toasts');
  const name = type === 'success' ? 'checkCircle' : type === 'error' ? 'alertCircle' : 'info';
  const t = el(html`<div class="toast toast-${type}">${ic(name)}<div>${message}</div></div>`);
  box.appendChild(t);
  const close = () => { t.classList.add('out'); setTimeout(() => t.remove(), 220); };
  t.addEventListener('click', close);
  setTimeout(close, type === 'error' ? Math.max(ms, 6500) : ms);
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

export function modal({ title, sub = '', body = '', foot = null, size = '', dismissible = true, onClose } = {}) {
  const root = el(html`<div class="modal-root">
    <div class="modal ${size ? 'modal-' + size : ''}" role="dialog" aria-modal="true">
      <div class="modal-head">
        <div class="grow"><h3>${title}</h3>${sub ? html`<div class="modal-sub">${sub}</div>` : ''}</div>
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
  const api_ = {
    root, el: root.querySelector('.modal'), body: bodyEl, foot: footEl, dismissible,
    close(result) {
      if (closed) return; closed = true;
      const i = modalStack.indexOf(api_); if (i >= 0) modalStack.splice(i, 1);
      root.classList.add('closing');
      setTimeout(() => root.remove(), 190);
      onClose?.(result);
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
export function confirmBox({ title, text = '', extra = '', confirm = 'Підтвердити', cancel = 'Скасувати', danger = false } = {}) {
  return new Promise((resolve) => {
    let result = false;
    const m = modal({
      title,
      body: html`<p class="muted" style="white-space:pre-line">${text}</p>${extra}`,
      foot: html`<button class="btn btn-ghost" data-no>${cancel}</button>
        <button class="btn ${danger ? 'btn-danger' : 'btn-primary'}" data-yes autofocus>${confirm}</button>`,
      onClose: () => resolve(result),
    });
    m.foot.querySelector('[data-no]').onclick = () => m.close();
    m.foot.querySelector('[data-yes]').onclick = () => { result = true; m.close(); };
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
    html`<button role="menuitem" data-i="${i}" class="${it.danger ? 'danger' : ''} ${it.on ? 'on' : ''}" ${it.disabled ? 'disabled' : ''}>${ic(it.icon || 'chevRight')}<span class="grow">${it.label}</span>${it.on ? ic('check', 'icon-s') : ''}</button>`)}</div>`);
  document.body.appendChild(m);
  const r = anchor.getBoundingClientRect();
  const w = m.offsetWidth, h = m.offsetHeight;
  let left = Math.min(r.right - w, window.innerWidth - w - 10);
  let top = r.bottom + 6;
  if (side === 'right') { left = r.right + 8; top = Math.min(r.top, window.innerHeight - h - 10); m.style.transformOrigin = 'bottom left'; }
  else if (top + h > window.innerHeight - 10) top = Math.max(10, r.top - h - 6);
  m.style.left = `${Math.max(10, left)}px`;
  m.style.top = `${top}px`;
  const close = () => {
    m.remove(); document.removeEventListener('mousedown', outside, true); document.removeEventListener('keydown', key, true);
    if (closeOpenMenu === close) closeOpenMenu = null;
  };
  closeOpenMenu = close;
  const outside = (e) => { if (!m.contains(e.target)) close(); };
  const key = (e) => { if (e.key === 'Escape') { e.stopPropagation(); close(); } };
  setTimeout(() => { document.addEventListener('mousedown', outside, true); document.addEventListener('keydown', key, true); });
  m.addEventListener('click', (e) => {
    const b = e.target.closest('button[data-i]');
    if (!b) return;
    close();
    items[+b.dataset.i].onClick?.();
  });
}

// ------------------------------------------------------------------ segmented control
export function segHtml(options, active, { accent = false, name = '' } = {}) {
  return html`<div class="seg ${accent ? 'seg-accent' : ''}" data-seg="${name}" role="tablist">
    <span class="seg-pill"></span>
    ${options.map((o) => html`<button type="button" role="tab" data-value="${o.value}" class="${o.value === active ? 'active' : ''} ${o.label ? '' : 'seg-ico'}"
      ${o.tip ? raw(`data-tip="${esc(o.tip)}" aria-label="${esc(o.tip)}"`) : ''}>${o.icon ? ic(o.icon, o.label ? 'icon-s' : '') : ''}${o.label || ''}${o.count !== undefined ? html`<span class="seg-count">${o.count}</span>` : ''}</button>`)}
  </div>`;
}
export function syncSeg(seg) {
  if (!seg) return;
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
new ResizeObserver(() => document.querySelectorAll('.seg').forEach(syncSeg)).observe(document.documentElement);

// ------------------------------------------------------------------ formatting
export const money = (n) => (n === null || n === undefined || Number.isNaN(n)) ? '—' : `$${Number(n).toFixed(2)}`;
export const signedMoney = (n) => `${n >= 0 ? '+' : '-'}$${Math.abs(n).toFixed(2)}`;
export function dateTime(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString('uk-UA', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
export function dateOnly(iso) {
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
export function bytes(n) {
  if (!n && n !== 0) return '';
  if (n < 1024) return `${n} Б`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(0)} КБ`;
  if (n < 1024 ** 3) return `${(n / 1024 ** 2).toFixed(1)} МБ`;
  return `${(n / 1024 ** 3).toFixed(2)} ГБ`;
}
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
const EASE = 'cubic-bezier(.22, 1, .36, 1)';

// Images fade in only after they are decoded off the main thread (no decode stall on first paint).
export function fadeImages(root) {
  root.querySelectorAll('img[data-fade]').forEach((img) => {
    img.removeAttribute('data-fade');
    img.decoding = 'async';
    // Even a cached picture is decoded off-thread before it becomes visible, so no frame waits for it.
    const reveal = () => (img.decode ? img.decode().catch(() => {}) : Promise.resolve()).then(() => img.classList.add('loaded'));
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

// FLIP: children with data-key glide from their old to their new position after a DOM change.
export function flip(container, mutate, duration = 380) {
  const before = new Map();
  if (!reducedMotion()) {
    container.querySelectorAll(':scope > [data-key]').forEach((node) => {
      if (!node.hidden) before.set(node.dataset.key, node.getBoundingClientRect());
    });
  }
  mutate();
  if (reducedMotion()) return;
  container.querySelectorAll(':scope > [data-key]').forEach((node) => {
    if (node.hidden) return;
    const old = before.get(node.dataset.key);
    const now = node.getBoundingClientRect();
    if (!old) {
      node.animate([{ opacity: 0, transform: 'scale(.96)' }, { opacity: 1, transform: 'none' }], { duration: 260, easing: EASE });
      return;
    }
    const dx = old.left - now.left, dy = old.top - now.top;
    if (Math.abs(dx) < 0.5 && Math.abs(dy) < 0.5) return;
    node.animate([{ transform: `translate(${dx}px, ${dy}px)` }, { transform: 'none' }], { duration, easing: EASE });
  });
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
