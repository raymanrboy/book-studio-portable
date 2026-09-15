// App shell: sidebar, routing between pages (View Transitions), theme, heartbeat.
import { api, html, ic, setHtml, on, TOKEN, toast, syncSeg, reducedMotion, idle } from './lib.js';

export const store = { info: null };
const listeners = new Set();
export const onInfo = (fn) => { listeners.add(fn); return () => listeners.delete(fn); };

export async function refreshInfo() {
  try {
    store.info = await api('/api/app');
    updateSidebar();
    listeners.forEach((fn) => fn(store.info));
  } catch { /* offline overlay handles it */ }
  return store.info;
}

// A minimised window or a newer navigation skips the animation; the DOM update still runs.
const canTransition = () => !!document.startViewTransition && !reducedMotion() && !document.hidden;
function transition(update) {
  const vt = document.startViewTransition(update);
  vt.ready.catch(() => {}); // a skipped transition rejects `ready` — expected, not an error
  return vt;
}

// ------------------------------------------------------------------ theme
export function applyTheme(theme) {
  try { localStorage.setItem('bs-theme', theme); } catch {}
  const resolved = theme === 'system' ? (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark') : theme;
  const swap = () => { document.documentElement.dataset.theme = resolved; updateSidebar(); };
  // The whole window cross-fades between themes instead of flashing.
  if (canTransition() && document.documentElement.dataset.theme !== resolved) {
    transition(swap).finished.catch(() => {});
  } else swap();
}
export function applyMotion(reduce) {
  try { localStorage.setItem('bs-motion', reduce ? 'reduce' : 'full'); } catch {}
  if (reduce) document.documentElement.dataset.motion = 'reduce'; else delete document.documentElement.dataset.motion;
}
matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => {
  if ((localStorage.getItem('bs-theme') || 'dark') === 'system') applyTheme('system');
});

// ------------------------------------------------------------------ sidebar (built once, then patched)
const NAV = [
  { hash: '#/library', label: 'Бібліотека книг', icon: 'book', match: /^#\/(library|book)/ },
  { hash: '#/profit', label: 'Прибуток', icon: 'chart', match: /^#\/profit/ },
  { hash: '#/creator', label: 'Order Creator', icon: 'package', match: /^#\/creator/ },
  { hash: '#/settings', label: 'Налаштування', icon: 'sliders', match: /^#\/settings/ },
];

function buildSidebar() {
  setHtml(document.getElementById('sidebar'), html`
    <div class="brand">
      <div class="brand-mark">${ic('logo')}</div>
      <div><div class="brand-name">Book Studio</div><div class="brand-sub">майстерня книг Etsy</div></div>
    </div>
    <nav class="nav" id="nav">
      <div class="nav-label">Робота</div>
      <span class="nav-pill" id="nav-pill" style="opacity:0"></span>
      ${NAV.map((n) => html`<a class="nav-item" href="${n.hash}" data-nav="${n.hash}">
        ${ic(n.icon)}<span>${n.label}</span>${n.hash === '#/library' ? html`<span class="nav-count" id="nav-count" hidden></span>` : ''}
      </a>`)}
    </nav>
    <div class="sidebar-foot">
      <div class="conn-list">
        ${[['etsy', 'Etsy', '#/settings/etsy'], ['printify', 'Printify', '#/settings/printify'], ['gelato', 'Gelato', '#/settings/gelato']]
          .map(([k, label, go]) => html`<div class="conn" data-conn="${k}" data-go="${go}" title="${label}"><span class="dot"></span><b>${label}</b><span class="conn-val truncate"></span></div>`)}
      </div>
      <div class="theme-toggle" role="group" aria-label="Тема">
        <button data-theme="dark" title="Темна">${ic('moon', 'icon-s')}</button>
        <button data-theme="light" title="Світла">${ic('sun', 'icon-s')}</button>
        <button data-theme="system" title="Як у Windows">${ic('monitor', 'icon-s')}</button>
      </div>
    </div>`);
}

function placeNavPill() {
  const hash = location.hash || '#/library';
  const pill = document.getElementById('nav-pill');
  let active = null;
  document.querySelectorAll('[data-nav]').forEach((a) => {
    const on = NAV.find((n) => n.hash === a.dataset.nav).match.test(hash);
    a.classList.toggle('active', on);
    if (on) active = a;
  });
  if (!pill) return;
  if (!active) { pill.style.opacity = '0'; return; }
  pill.style.transform = `translateY(${active.offsetTop}px)`;
  pill.style.opacity = '1';
}

function updateSidebar() {
  if (!document.getElementById('nav')) return;
  placeNavPill();
  const info = store.info || {};
  const integ = info.integrations || {};
  const count = document.getElementById('nav-count');
  if (count && info.library) { count.hidden = false; count.textContent = info.library.active; }
  const set = (k, state, text) => {
    const row = document.querySelector(`[data-conn="${k}"]`);
    if (!row) return;
    row.classList.toggle('on', state === 'on');
    row.classList.toggle('warn', state === 'warn');
    row.querySelector('.conn-val').textContent = text;
  };
  const etsy = integ.etsy || {};
  set('etsy', etsy.connected ? 'on' : etsy.keysConfigured ? 'warn' : '', etsy.connected ? (etsy.shopName || 'підключено') : 'не підключено');
  set('printify', integ.printify?.configured ? 'on' : '', integ.printify?.configured ? (integ.printify.shopTitle || 'підключено') : 'немає токена');
  set('gelato', integ.gelato?.configured ? 'on' : '', integ.gelato?.configured ? 'підключено' : 'немає ключа');
  const theme = localStorage.getItem('bs-theme') || 'dark';
  document.querySelectorAll('.theme-toggle [data-theme]').forEach((b) => b.classList.toggle('active', b.dataset.theme === theme));
}

function wireSidebar() {
  const side = document.getElementById('sidebar');
  on(side, 'click', '[data-theme]', async (e, b) => {
    applyTheme(b.dataset.theme);
    try { await api('/api/settings/ui', { method: 'POST', body: { theme: b.dataset.theme } }); } catch {}
  });
  on(side, 'click', '[data-go]', (e, b) => { location.hash = b.dataset.go; });
}

// ------------------------------------------------------------------ top progress bar (only for slow page loads)
const topbar = { el: null, timer: null };
function topbarStart() {
  clearTimeout(topbar.timer);
  topbar.el.className = 'topbar';
  topbar.timer = setTimeout(() => topbar.el.classList.add('run'), 140);
}
function topbarDone() {
  clearTimeout(topbar.timer);
  if (!topbar.el.classList.contains('run')) { topbar.el.className = 'topbar'; return; }
  topbar.el.classList.add('done');
  setTimeout(() => { topbar.el.className = 'topbar'; }, 320);
}

// ------------------------------------------------------------------ router
const ROUTES = [
  [/^#\/library\/?$/, () => import('./pages/library.js')],
  [/^#\/book\/([0-9a-f]{32})$/, () => import('./pages/book.js')],
  [/^#\/profit\/?$/, () => import('./pages/profit.js')],
  [/^#\/creator\/?$/, () => import('./pages/creator.js')],
  [/^#\/settings(?:\/(\w+))?$/, () => import('./pages/settings.js')],
];

let current = null;
let navToken = 0;
let firstPage = true;

// The new page is built off-screen while the old one stays visible, then both swap in one
// View Transition (GPU cross-fade) — no blank frames and no half-rendered pages.
async function navigate() {
  const hash = location.hash || '#/library';
  const found = ROUTES.find(([re]) => re.test(hash));
  if (!found) { location.hash = '#/library'; return; }
  const my = ++navToken;
  const [re, loader] = found;
  const params = hash.match(re).slice(1);
  topbarStart();
  let mod;
  try { mod = await loader(); } catch (err) { console.error(err); topbarDone(); toast('Не вдалося відкрити сторінку', 'error'); return; }
  if (my !== navToken) return;

  const view = document.createElement('div');
  view.className = 'view';
  view.id = 'view';
  let ctrl = null;
  try {
    ctrl = (await mod.mount(view, params)) || null;
  } catch (err) {
    console.error(err);
    setHtml(view, html`<div class="empty"><div class="empty-icon">${ic('alertCircle')}</div><h3>Сторінку не вдалося завантажити</h3><p>${err.message || err}</p></div>`);
  }
  if (my !== navToken) { try { ctrl?.unmount?.(); } catch {} return; }

  const swap = () => {
    try { current?.unmount?.(); } catch (err) { console.error(err); }
    document.getElementById('view').replaceWith(view);
    document.getElementById('main').scrollTop = 0;
    current = ctrl;
    placeNavPill();
  };
  const shown = () => {
    document.querySelectorAll('.seg').forEach(syncSeg);
    try { ctrl?.shown?.(); } catch (err) { console.error(err); }
    topbarDone();
  };
  if (!firstPage && canTransition()) {
    document.documentElement.classList.add('vt-running');
    const vt = transition(swap);
    const done = () => document.documentElement.classList.remove('vt-running');
    vt.updateCallbackDone.then(shown, shown);
    vt.finished.then(done, done);
  } else {
    swap();
    shown();
  }
  firstPage = false;
}

// ------------------------------------------------------------------ heartbeat / lifecycle
function heartbeat() { api('/api/app/heartbeat', { method: 'POST', body: {} }).catch(() => {}); }
setInterval(heartbeat, 20000);
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') heartbeat(); });
window.addEventListener('pagehide', () => {
  try { navigator.sendBeacon('/api/app/bye', new Blob([JSON.stringify({ t: TOKEN })], { type: 'text/plain' })); } catch {}
});

// Prevent the window from navigating away when a file is dropped outside a drop zone.
window.addEventListener('dragover', (e) => e.preventDefault());
window.addEventListener('drop', (e) => e.preventDefault());

async function boot() {
  topbar.el = document.getElementById('topbar');
  heartbeat();
  buildSidebar();
  wireSidebar();
  updateSidebar();
  window.addEventListener('hashchange', navigate);
  const info = refreshInfo();
  await navigate();
  await info;
  const ui = store.info?.ui;
  if (ui) {
    if (!localStorage.getItem('bs-theme') && ui.theme) applyTheme(ui.theme);
    applyMotion(!!ui.reduceMotion);
    updateSidebar();
  }
  // Warm up the other pages' code while the user looks at the first one.
  idle(() => ROUTES.forEach(([, load]) => load().catch(() => {})));
}

boot();
