// App shell: icon rail, routing between pages (View Transitions), theme, heartbeat.
import { api, html, ic, setHtml, on, TOKEN, toast, syncSeg, reducedMotion, idle, menu, closeMenu, hideTip } from './lib.js';
import { isKept, stash, unstash, release } from './keep.js';
import { waiting } from './handoff.js';
import { store, refreshInfo, whenInfoChanges } from './info.js';

whenInfoChanges(() => updateSidebar());

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

// ------------------------------------------------------------------ the two modes and their rails
// Book Studio has two modes (owner, 24.09.2026): «Замовлення» — the orders, and «Лістинги» — making new books
// and their listing pictures, "like another program, separated from everything". A click on the brand icon
// (Alt+0) switches; each mode has its own rail items and its own ink (cyan / magenta, html[data-mode]).
// «Прибуток» is hidden until bookkeeping starts (the page itself is kept in pages/profit.js).
const MODES = {
  orders: {
    title: 'Book Studio', icon: 'spread', other: 'listings', tip: 'Перейти до лістингів',
    nav: [
      { hash: '#/orders', label: 'Замовлення', icon: 'inbox', match: /^#\/orders/ },
      { hash: '#/library', label: 'Бібліотека книг', icon: 'shelf', match: /^#\/(library|book)/ },
      { hash: '#/creator', label: 'Order Creator', icon: 'printer', match: /^#\/creator/ },
      { hash: '#/archive', label: 'Архів замовлень', icon: 'orderArchive', match: /^#\/archive/ },
      { hash: '#/settings', label: 'Налаштування', icon: 'sliders', match: /^#\/settings/ },
    ],
  },
  listings: {
    title: 'Book Studio · Лістинги', icon: 'listing', other: 'orders', tip: 'Перейти до замовлень',
    nav: [
      { hash: '#/workshop', label: 'Майстерня', icon: 'workshop', match: /^#\/workshop/ },
      { hash: '#/mockups', label: 'Мокапи', icon: 'mockup', match: /^#\/mockups/ },
    ],
  },
};
const HOME = '#/orders'; // Book Studio always starts in the orders (owner, 24.09.2026)
const THEMES = [
  { value: 'dark', label: 'Темна', icon: 'moon' },
  { value: 'light', label: 'Світла', icon: 'sun' },
  { value: 'system', label: 'Як у Windows', icon: 'monitor' },
];
const currentTheme = () => localStorage.getItem('bs-theme') || 'dark';
let mode = 'orders';                                   // the mode on screen
const last = { orders: HOME, listings: '#/workshop' };  // where the owner was in each mode (until a restart)
const nav = () => MODES[mode].nav;

function buildSidebar() {
  setHtml(document.getElementById('sidebar'), html`
    <button class="brand-mark" id="brand" type="button"></button>
    <nav class="nav" id="nav"></nav>
    <div class="sidebar-foot">
      <button class="ib lg" id="theme-btn" aria-label="Вигляд" data-tip="Вигляд" data-tip-side="right"></button>
    </div>`);
  buildNav();
}

/** The rail of the mode on screen: its items (Alt+1…) and the brand icon that leads to the other mode. */
function buildNav() {
  const m = MODES[mode];
  const brand = document.getElementById('brand');
  setHtml(brand, html`${ic(m.icon)}<span class="brand-busy" id="brand-busy" hidden></span>`);
  brand.setAttribute('aria-label', m.tip);
  Object.assign(brand.dataset, { tip: m.tip, kbd: 'Alt+0', tipSide: 'right' });
  setHtml(document.getElementById('nav'), html`
    <span class="nav-pill" id="nav-pill" style="opacity:0"></span>
    ${m.nav.map((n, i) => html`<a class="nav-item" href="${n.hash}" data-nav="${n.hash}" aria-label="${n.label}" data-tip="${n.label}" data-kbd="Alt+${i + 1}" data-tip-side="right">
      ${ic(n.icon)}${n.hash === '#/settings' ? html`<span class="badge" id="nav-badge" hidden></span>` : ''}${n.hash === '#/mockups' ? html`<span class="badge busy" id="nav-busy" hidden></span>` : ''}</a>`)}`);
  document.documentElement.dataset.mode = mode;
  document.title = m.title;
  paintBusy();
}

/** Where a mode is entered: the page the owner left there — an order's card only while it is kept. */
function entryOf(m) {
  if (m === 'orders' && /^#\/orders\/\d/.test(last.orders) && !isKept(last.orders)) return HOME;
  return last[m];
}
function switchMode() {
  hideTip();
  location.hash = entryOf(MODES[mode].other);
}

// A mockups run going on while the owner is elsewhere: a small magenta dot on the brand icon (in the orders) or
// on «Мокапи» (in the listings). pages/mockups.js tells it through the 'bs:busy' event.
const busy = { mockups: false };
window.addEventListener('bs:busy', (e) => { Object.assign(busy, e.detail || {}); paintBusy(); });
function paintBusy() {
  const brandDot = document.getElementById('brand-busy');
  const navDot = document.getElementById('nav-busy');
  if (brandDot) brandDot.hidden = !(busy.mockups && mode === 'orders');
  if (navDot) navDot.hidden = !(busy.mockups && !/^#\/mockups/.test(location.hash));
}

function placeNavPill() {
  const hash = location.hash || HOME;
  const pill = document.getElementById('nav-pill');
  let active = null;
  document.querySelectorAll('[data-nav]').forEach((a) => {
    const on = !!nav().find((n) => n.hash === a.dataset.nav)?.match.test(hash);
    a.classList.toggle('active', on);
    if (on) active = a;
  });
  document.querySelector('[data-nav="#/orders"]')?.setAttribute('href', ordersTarget());
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
    try { await api('/api/settings/ui', { method: 'POST', body: { theme: value } }); }
    catch (err) { toast(`Тему не збережено: ${err.message}`, 'error'); }
  };
  menu(anchor, [
    ...THEMES.map((t) => ({ label: t.label, icon: t.icon, on: currentTheme() === t.value, onClick: () => setTheme(t.value) })),
    '-',
    { label: 'Мінімум анімацій', icon: 'motion', on: reduce, onClick: async () => {
      applyMotion(!reduce);
      try { await api('/api/settings/ui', { method: 'POST', body: { reduceMotion: !reduce } }); }
      catch (err) { toast(`Налаштування не збережено: ${err.message}`, 'error'); }
    } },
  ], { side: 'right' });
}

function wireSidebar() {
  const side = document.getElementById('sidebar');
  on(side, 'click', '#theme-btn', (e, b) => { hideTip(); openThemeMenu(b); });
  on(side, 'click', '#brand', switchMode);
  document.addEventListener('keydown', (e) => {
    if (!e.altKey || e.ctrlKey || e.metaKey) return;
    if (document.querySelector('.modal-root, .lightbox')) return; // a dialog or the viewer first; the page stays under it
    if (e.key === '0') { e.preventDefault(); switchMode(); return; }
    const n = nav()[Number(e.key) - 1];
    if (n) { e.preventDefault(); location.hash = n.hash === '#/orders' ? ordersTarget() : n.hash; }
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
// Every page belongs to one mode: the address alone says which mode is on screen (back/forward just work).
const ROUTES = [
  [/^#\/orders(?:\/(\d{5,20}))?\/?$/, () => import('./pages/orders.js'), 'orders'],
  [/^#\/library\/?$/, () => import('./pages/library.js'), 'orders'],
  [/^#\/book\/([0-9a-f]{32})$/, () => import('./pages/book.js'), 'orders'],
  [/^#\/creator\/?$/, () => import('./pages/creator.js'), 'orders'],
  [/^#\/archive(?:\/(\d{8}-\d{6}-[0-9a-f]{6}))?\/?$/, () => import('./pages/archive.js'), 'orders'],
  [/^#\/settings(?:\/(\w+))?$/, () => import('./pages/settings.js'), 'orders'],
  [/^#\/workshop\/?$/, () => import('./pages/workshop.js'), 'listings'],
  [/^#\/workshop\/([0-9a-f]{32})$/, () => import('./pages/workshop-book.js'), 'listings'],
  [/^#\/mockups\/?$/, () => import('./pages/mockups.js'), 'listings'],
];

let current = null;
let currentHash = '';
let lastOrders = HOME; // where the owner was inside «Замовлення»: the queue or one order's card
let navToken = 0;
let firstPage = true;
let pageTransition = null;

const unmountSafely = (ctrl) => { try { ctrl?.unmount?.(); } catch (err) { console.error(err); } };

/** The Orders icon brings back the order card the owner stepped away from (kept while the order is new). */
function ordersTarget() {
  return !/^#\/orders/.test(location.hash || HOME) && isKept(lastOrders) ? lastOrders : HOME;
}

// The new page is built off-screen while the old one stays visible, then both swap in one
// View Transition (GPU cross-fade) — no blank frames and no half-rendered pages.
// A page with work on a new order is not taken down when left: it is kept hidden (keep.js) and comes
// back as it was — unless its order has moved on (revive() says no) or new data waits for the page.
async function navigate() {
  const hash = location.hash || HOME;
  const found = ROUTES.find(([re]) => re.test(hash));
  if (!found) { location.hash = HOME; return; }
  const my = ++navToken;
  hideTip();
  closeMenu(); // a menu or a tip of the page being left never stays over the next one
  const [re, loader, pageMode] = found;
  const params = hash.match(re).slice(1);
  topbarStart();

  let view = null, ctrl = null, scroll = 0, inner = [];
  if (waiting(hash.slice(2).split('/')[0])) release(hash);
  const saved = unstash(hash);
  if (saved) {
    let alive = false;
    try { alive = (await saved.ctrl?.revive?.()) !== false; } catch (err) { console.error(err); }
    if (my !== navToken) {
      if (alive) { try { saved.ctrl?.hidden?.(); } catch {} stash(hash, saved); } else unmountSafely(saved.ctrl);
      return;
    }
    if (alive) ({ view, ctrl, scroll, inner = [] } = saved);
    else unmountSafely(saved.ctrl);
  }
  if (!view) {
    let mod;
    try { mod = await loader(); } catch (err) { console.error(err); topbarDone(); toast('Не вдалося відкрити сторінку', 'error'); return; }
    if (my !== navToken) return;
    view = document.createElement('div');
    view.className = 'view';
    view.id = 'view';
    try {
      ctrl = (await mod.mount(view, params)) || null;
    } catch (err) {
      console.error(err);
      setHtml(view, html`<div class="empty"><div class="empty-icon">${ic('alertCircle')}</div><h3>Сторінку не вдалося завантажити</h3><p>${err.message || err}</p></div>`);
    }
    if (my !== navToken) { unmountSafely(ctrl); return; }
  }

  const swap = () => {
    const old = document.getElementById('view');
    const main = document.getElementById('main');
    let keepOld = false;
    try { keepOld = !!current?.keep?.(); } catch (err) { console.error(err); }
    if (keepOld) {
      try { current.hidden?.(); } catch (err) { console.error(err); }
      // A detached element forgets how far it was scrolled (the proof strip, the sticky data column).
      const scrolled = [...old.querySelectorAll('*')].filter((el) => el.scrollLeft || el.scrollTop)
        .map((el) => [el, el.scrollLeft, el.scrollTop]);
      stash(currentHash, { view: old, ctrl: current, scroll: main.scrollTop, inner: scrolled });
    } else unmountSafely(current);
    old.replaceWith(view);
    // Instant, not the smooth scroll-behavior of .main: a page starts at its top (or where it was left) in the same frame.
    main.scrollTo({ top: scroll, behavior: 'instant' });
    for (const [el, left, top] of inner) { el.scrollLeft = left; el.scrollTop = top; }
    current = ctrl;
    currentHash = hash;
    if (/^#\/orders/.test(hash)) lastOrders = hash;
    last[pageMode] = hash;
    if (pageMode !== mode) { mode = pageMode; buildNav(); updateSidebar(); } else placeNavPill();
    paintBusy();
  };
  const shown = () => {
    document.querySelectorAll('.seg').forEach(syncSeg);
    try { ctrl?.shown?.(); } catch (err) { console.error(err); }
    topbarDone();
  };
  if (!firstPage && canTransition()) {
    const root = document.documentElement;
    root.classList.add('vt-running');
    root.classList.toggle('vt-mode', pageMode !== mode); // the rails swap: their own animation (app.css)
    const vt = transition(swap);
    pageTransition = vt;
    // A quicker second click skips this transition; only the latest one clears the classes.
    const done = () => { if (pageTransition === vt) { pageTransition = null; root.classList.remove('vt-running', 'vt-mode'); } };
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
    // The saved settings decide both, the same way; the browser's copy only paints the first frame before they come.
    if (ui.theme && ui.theme !== currentTheme()) applyTheme(ui.theme);
    applyMotion(!!ui.reduceMotion);
    updateSidebar();
  }
  // Warm up the other pages' code while the user looks at the first one.
  idle(() => ROUTES.forEach(([, load]) => load().catch(() => {})));
}

boot();
