// App shell: icon rail, routing between pages (View Transitions), theme, heartbeat.
import { api, html, ic, setHtml, on, TOKEN, toast, syncSeg, reducedMotion, idle, menu, hideTip } from './lib.js';

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

// ------------------------------------------------------------------ rail (built once, then patched)
// «Прибуток» is hidden until bookkeeping starts (the page itself is kept in pages/profit.js).
const NAV = [
  { hash: '#/orders', label: 'Замовлення', icon: 'inbox', kbd: 'Alt+1', match: /^#\/orders/ },
  { hash: '#/library', label: 'Бібліотека книг', icon: 'shelf', kbd: 'Alt+2', match: /^#\/(library|book)/ },
  { hash: '#/creator', label: 'Order Creator', icon: 'printer', kbd: 'Alt+3', match: /^#\/creator/ },
  { hash: '#/settings', label: 'Налаштування', icon: 'sliders', kbd: 'Alt+4', match: /^#\/settings/ },
];
const HOME = '#/orders';
const THEMES = [
  { value: 'dark', label: 'Темна', icon: 'moon' },
  { value: 'light', label: 'Світла', icon: 'sun' },
  { value: 'system', label: 'Як у Windows', icon: 'monitor' },
];
const currentTheme = () => localStorage.getItem('bs-theme') || 'dark';

function buildSidebar() {
  setHtml(document.getElementById('sidebar'), html`
    <div class="brand-mark" data-tip="Book Studio" data-tip-side="right">${ic('spread')}</div>
    <nav class="nav" id="nav">
      <span class="nav-pill" id="nav-pill" style="opacity:0"></span>
      ${NAV.map((n) => html`<a class="nav-item" href="${n.hash}" data-nav="${n.hash}" aria-label="${n.label}" data-tip="${n.label}" data-kbd="${n.kbd}" data-tip-side="right">
        ${ic(n.icon)}${n.hash === '#/settings' ? html`<span class="badge" id="nav-badge" hidden></span>` : ''}</a>`)}
    </nav>
    <div class="sidebar-foot">
      <button class="ib lg" id="theme-btn" aria-label="Вигляд" data-tip="Вигляд" data-tip-side="right"></button>
    </div>`);
}

function placeNavPill() {
  const hash = location.hash || HOME;
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
  const integ = store.info?.integrations || {};
  // One quiet signal instead of a status list: a dot on Settings when a service still needs a key or login.
  const badge = document.getElementById('nav-badge');
  if (badge && store.info) badge.hidden = !!(integ.etsy?.connected && integ.printify?.configured && integ.gelato?.configured);
  const theme = THEMES.find((t) => t.value === currentTheme()) || THEMES[0];
  setHtml(document.getElementById('theme-btn'), ic(theme.icon));
}

function openThemeMenu(anchor) {
  const reduce = document.documentElement.dataset.motion === 'reduce';
  const setTheme = async (value) => {
    applyTheme(value);
    try { await api('/api/settings/ui', { method: 'POST', body: { theme: value } }); } catch {}
  };
  menu(anchor, [
    ...THEMES.map((t) => ({ label: t.label, icon: t.icon, on: currentTheme() === t.value, onClick: () => setTheme(t.value) })),
    '-',
    { label: 'Мінімум анімацій', icon: 'motion', on: reduce, onClick: async () => {
      applyMotion(!reduce);
      try { await api('/api/settings/ui', { method: 'POST', body: { reduceMotion: !reduce } }); } catch {}
    } },
  ], { side: 'right' });
}

function wireSidebar() {
  const side = document.getElementById('sidebar');
  on(side, 'click', '#theme-btn', (e, b) => { hideTip(); openThemeMenu(b); });
  document.addEventListener('keydown', (e) => {
    if (!e.altKey || e.ctrlKey || e.metaKey) return;
    const n = NAV[Number(e.key) - 1];
    if (n) { e.preventDefault(); location.hash = n.hash; }
  });
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
  [/^#\/orders(?:\/(\d{5,20}))?\/?$/, () => import('./pages/orders.js')],
  [/^#\/library\/?$/, () => import('./pages/library.js')],
  [/^#\/book\/([0-9a-f]{32})$/, () => import('./pages/book.js')],
  [/^#\/creator\/?$/, () => import('./pages/creator.js')],
  [/^#\/settings(?:\/(\w+))?$/, () => import('./pages/settings.js')],
];

let current = null;
let navToken = 0;
let firstPage = true;

// The new page is built off-screen while the old one stays visible, then both swap in one
// View Transition (GPU cross-fade) — no blank frames and no half-rendered pages.
async function navigate() {
  const hash = location.hash || HOME;
  const found = ROUTES.find(([re]) => re.test(hash));
  if (!found) { location.hash = HOME; return; }
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
    // Instant, not the smooth scroll-behavior of .main: a new page starts at its top in the same frame.
    document.getElementById('main').scrollTo({ top: 0, behavior: 'instant' });
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
