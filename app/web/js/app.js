// App shell: icon rail, routing between pages (View Transitions), theme, heartbeat.
import {
  post, html, ic, setHtml, on, TOKEN, toast, syncSeg, reducedMotion, idle, menu, closeMenu, hideTip,
} from './lib.js';
import { isKept, stash, unstash, release, startOver } from './keep.js';
import { waiting } from './handoff.js';
import { installDropAnywhere } from './drop-anywhere.js';
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
function applyTheme(theme) {
  try { localStorage.setItem('bs-theme', theme); } catch {}
  const resolved = theme === 'system' ? (matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark') : theme;
  const swap = () => { document.documentElement.dataset.theme = resolved; updateSidebar(); };
  // The whole window cross-fades between themes instead of flashing.
  if (canTransition() && document.documentElement.dataset.theme !== resolved) {
    transition(swap).finished.catch(() => {});
  } else swap();
}
function applyMotion(reduce) {
  try { localStorage.setItem('bs-motion', reduce ? 'reduce' : 'full'); } catch {}
  if (reduce) document.documentElement.dataset.motion = 'reduce'; else delete document.documentElement.dataset.motion;
}
matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => {
  if ((localStorage.getItem('bs-theme') || 'dark') === 'system') applyTheme('system');
});

// ------------------------------------------------------------------ the rail: places and tools
// One labelled rail (2026-09-30, wiki/plans/ui-redesign.md) instead of two modes switched by the brand icon: the
// owner got lost among unlabelled icons in two hidden sets. **Places** hold the objects — an order, a book — each
// with its path; **tools** also work on their own (the Order Creator, the Mockups, the photo mockups, the slides,
// the print archive) and open inside their object from its step. The two inks stay and follow the area: the orders,
// the profit and the order tools orange; the books and the book tools cyan (html[data-mode], still named «listings»
// for the cyan so the styles keep their names). «Прибуток» counts only sales from 1 October 2026.
const PLACES = [
  { hash: '#/orders', label: 'Замовлення', icon: 'inbox', match: /^#\/orders/, key: '1' },
  { hash: '#/books', label: 'Книги', icon: 'shelf', match: /^#\/(books|library|book|workshop)/, key: '2', busy: 'workshop' },
  { hash: '#/profit', label: 'Прибуток', icon: 'chart', match: /^#\/profit/, key: '3' },
  { gap: true },
  { hash: '#/tools', label: 'Інструменти', icon: 'tools', match: /^#\/(tools|creator|archive|mockups|photos|slides)/, key: '4', busy: 'mockups' },
];
const HOME = '#/orders'; // Book Studio always starts in the orders (owner, 24.09.2026)
const TITLE = 'Book Studio';
const THEMES = [
  { value: 'dark', label: 'Темна', icon: 'moon' },
  { value: 'light', label: 'Світла', icon: 'sun' },
  { value: 'system', label: 'Як у Windows', icon: 'monitor' },
];
const currentTheme = () => localStorage.getItem('bs-theme') || 'dark';
let mode = 'orders';     // the ink on screen: 'orders' (orange) or 'listings' (cyan) — the page's area
let navOwner = null;      // a page that serves an object may claim its place (the Order Creator of an order → «Замовлення»)
const lastIn = {};        // where the owner was under each place (until a restart)
const places = () => PLACES.filter((p) => !p.gap);
const placeOf = (hash) => (navOwner && places().find((p) => p.hash === navOwner)) || places().find((p) => p.match.test(hash)) || null;

function buildSidebar() {
  // Icons only (2026-09-30, the owner: "show, don't tell"): the page's own title says where he is, a tooltip names the
  // place and its key. Search is the last of the list, not the first.
  setHtml(document.getElementById('sidebar'), html`
    <button class="skip-link" id="skip" type="button">Перейти до вмісту</button>
    <div class="brand-mark" id="brand" aria-hidden="true">${ic('spread')}<span class="brand-busy" id="brand-busy" hidden></span></div>
    <nav class="nav" id="nav" aria-label="Розділи">
      <span class="nav-pill" id="nav-pill" style="opacity:0"></span>
      ${PLACES.map((n) => n.gap ? html`<span class="nav-gap" aria-hidden="true"></span>`
        : html`<a class="nav-item" href="${n.hash}" data-nav="${n.hash}" aria-label="${n.label}" data-tip="${n.label}" data-kbd="Alt+${n.key}" data-tip-side="right">
        ${ic(n.icon)}${n.busy ? html`<span class="badge busy" data-busy="${n.busy}" hidden></span>` : ''}</a>`)}
      <span class="nav-gap" aria-hidden="true"></span>
      <button class="nav-item nav-search" id="search-btn" type="button" aria-label="Пошук" data-tip="Пошук по всій програмі" data-kbd="Ctrl+K" data-tip-side="right">${ic('search')}</button>
    </nav>
    <div class="sidebar-foot">
      <a class="nav-item nav-small" href="#/settings" data-nav="#/settings" aria-label="Налаштування" data-tip="Налаштування" data-tip-side="right">${ic('sliders')}<span class="badge" id="nav-badge" hidden></span></a>
      <button class="nav-item nav-small" id="theme-btn" type="button" aria-label="Вигляд" data-tip="Вигляд" data-tip-side="right"></button>
    </div>`);
  document.documentElement.dataset.mode = mode;
  paintBusy();
}

/** Where a place is entered: the page the owner left under it — an order's card only while it is kept; a second
 *  click on the place he is in goes to its start (the queue, the gallery, the tools). */
function entryOf(p, here) {
  if (here) return p.hash;
  if (p.hash === '#/orders') return ordersTarget();
  if (p.hash === '#/tools') return p.hash; // the tools are a list to choose from, never the tool last used (2026-09-30)
  return lastIn[p.hash] || p.hash;
}

// Work going on while the owner is elsewhere: a mockups run in Photoshop (pages/mockups.js), a picture the Workshop
// waits for (workshop-live.js — its value says which row: the window's title carries it, so the taskbar shows it while
// the owner is in Gemini). A small cyan dot on «Книги» (a picture awaited) or «Інструменти» (the Mockups), shown when
// he is elsewhere. The pages tell it through the 'bs:busy' event; `done` — how a run ended while the window was not
// in front («Готово · 7 картинок»), in the title until he comes back to it. The window's title is written here only.
const busy = { mockups: false, workshop: null, done: null };
const BUSY_PAGE = { mockups: /^#\/mockups/, workshop: /^#\/workshop/ };
window.addEventListener('bs:busy', (e) => { Object.assign(busy, e.detail || {}); paintBusy(); });
window.addEventListener('focus', () => { if (busy.done) { busy.done = null; paintBusy(); } });
function paintBusy() {
  const hash = location.hash || HOME;
  document.querySelectorAll('[data-busy]').forEach((dot) => {
    dot.hidden = !(busy[dot.dataset.busy] && !BUSY_PAGE[dot.dataset.busy].test(hash));
  });
  const title = busy.workshop ? `● ${busy.workshop} — ${TITLE}` : TITLE;
  document.title = busy.done ? `${busy.done} · ${title}` : title;
}

function placeNavPill() {
  const hash = location.hash || HOME;
  const pill = document.getElementById('nav-pill');
  const owner = placeOf(hash);
  let active = null;
  document.querySelectorAll('[data-nav]').forEach((a) => {
    const on = a.dataset.nav === '#/settings' ? /^#\/settings/.test(hash) : owner?.hash === a.dataset.nav;
    a.classList.toggle('active', on);
    if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
    if (on && a.closest('#nav')) active = a;
  });
  places().forEach((p) => {
    const a = document.querySelector(`#nav [data-nav="${p.hash}"]`);
    if (a) a.setAttribute('href', entryOf(p, owner === p));
  });
  if (!pill) return;
  if (!active) { pill.style.opacity = '0'; return; }
  pill.style.transform = `translateY(${active.offsetTop}px)`;
  pill.style.height = `${active.offsetHeight}px`;
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
    try { await post('/api/settings/ui', { theme: value }); }
    catch (err) { toast(`Тему не збережено: ${err.message}`, 'error'); }
  };
  menu(anchor, [
    ...THEMES.map((t) => ({ label: t.label, icon: t.icon, on: currentTheme() === t.value, onClick: () => setTheme(t.value) })),
    '-',
    { label: 'Мінімум анімацій', icon: 'motion', on: reduce, onClick: async () => {
      applyMotion(!reduce);
      try { await post('/api/settings/ui', { reduceMotion: !reduce }); }
      catch (err) { toast(`Налаштування не збережено: ${err.message}`, 'error'); }
    } },
  ], { side: 'right' });
}

function wireSidebar() {
  const side = document.getElementById('sidebar');
  on(side, 'click', '#theme-btn', (e, b) => { hideTip(); openThemeMenu(b); });
  on(side, 'click', '#search-btn', () => { hideTip(); openSearch(); });
  // The first Tab stop: past the rail, straight to the page (15 presses to the first order before, 2026-09-30).
  on(side, 'click', '#skip', () => {
    const view = document.getElementById('view');
    const first = view?.querySelector('input:not([type=hidden]), button, a[href], [tabindex]:not([tabindex="-1"])');
    (first || view)?.focus();
  });
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && !e.altKey && !e.shiftKey && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      if (!document.querySelector('.modal-root, .lightbox')) openSearch();
      return;
    }
    if (!e.altKey || e.ctrlKey || e.metaKey) return;
    if (document.querySelector('.modal-root, .lightbox')) return; // a dialog or the viewer first; the page stays under it
    const p = places().find((x) => x.key === e.key);
    if (p) { e.preventDefault(); location.hash = entryOf(p, placeOf(location.hash || HOME) === p); }
  });
}
const openSearch = () => import('./palette.js').then((m) => m.openPalette()).catch((err) => { console.error(err); toast('Пошук не відкрився', 'error'); });

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
// Every page belongs to one area (its ink): the address alone says which (back/forward just work).
const ROUTES = [
  [/^#\/orders(?:\/(\d{5,20}))?\/?$/, () => import('./pages/orders.js'), 'orders'],
  [/^#\/books(?:\/(work|shop|archive))?\/?$/, () => import('./pages/books.js'), 'listings'],
  [/^#\/book\/([0-9a-f]{32})$/, () => import('./pages/book.js'), 'listings'],
  [/^#\/tools\/?$/, () => import('./pages/tools.js'), 'orders'],
  [/^#\/creator\/?$/, () => import('./pages/creator.js'), 'orders'],
  [/^#\/archive(?:\/(\d{8}-\d{6}-[0-9a-f]{6}))?\/?$/, () => import('./pages/archive.js'), 'orders'],
  [/^#\/profit\/?$/, () => import('./pages/profit.js'), 'orders'],
  [/^#\/settings(?:\/(\w+))?$/, () => import('./pages/settings.js'), 'orders'],
  [/^#\/workshop\/([^/]+)$/, () => import('./pages/workshop-book.js'), 'listings'],
  [/^#\/mockups\/?$/, () => import('./pages/mockups.js'), 'listings'],
  [/^#\/photos\/?$/, () => import('./pages/photos.js'), 'listings'],
  // the slides' editor: its own module, loaded only when opened (the owner, 29.09.2026) — not warmed up below
  [/^#\/slides\/(template|scheme:[a-z0-9-]+|\d{8}-\d{6}-[0-9a-f]{6}|\d{1,5}\.[^/]+)\/([1-6])$/, () => import('./pages/slides-editor.js'), 'listings', 'lazy'],
];
// The two galleries became one «Книги» (2026-09-30): their old addresses still lead there.
const ALIASES = [[/^#\/library\/?$/, '#/books/shop'], [/^#\/workshop\/?$/, '#/books/work']];

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
  const alias = ALIASES.find(([re]) => re.test(location.hash));
  if (alias) { history.replaceState(null, '', alias[1]); }
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
  // From the list of tools a tool opens clean, never as it was left (an order's kept Order Creator stays for its order).
  const aside = !waiting(hash.slice(2).split('/')[0]) && store.here === '#/tools' && startOver(hash);
  const saved = aside ? null : unstash(hash);
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
    if (currentHash !== hash) store.from = currentHash;
    currentHash = hash;
    store.here = hash;
    if (/^#\/orders/.test(hash)) lastOrders = hash;
    try { navOwner = ctrl?.navFor?.() || null; } catch { navOwner = null; }
    const owner = placeOf(hash);
    if (owner) lastIn[owner.hash] = hash;
    if (pageMode !== mode) { mode = pageMode; document.documentElement.dataset.mode = mode; }
    placeNavPill();
    paintBusy();
  };
  const shown = () => {
    document.querySelectorAll('.seg').forEach(syncSeg);
    // The page that was pressed on is gone and the focus with it (a keyboard user opened a row): it lands on the new page's
    // title, so the next Tab starts inside the page, not back at the rail (2026-09-30, the Tab walk). Focus that is somewhere
    // real — a rail link, a field — is left alone.
    if (!document.activeElement || document.activeElement === document.body || !document.contains(document.activeElement)) {
      const h = view.querySelector('h1');
      if (h) { h.tabIndex = -1; h.focus({ preventScroll: true }); }
    }
    try { ctrl?.shown?.(); } catch (err) { console.error(err); }
    topbarDone();
  };
  if (!firstPage && canTransition()) {
    const root = document.documentElement;
    root.classList.add('vt-running');
    const vt = transition(swap);
    pageTransition = vt;
    // A quicker second click skips this transition; only the latest one clears the class.
    const done = () => { if (pageTransition === vt) { pageTransition = null; root.classList.remove('vt-running'); } };
    vt.updateCallbackDone.then(shown, shown);
    vt.finished.then(done, done);
  } else {
    swap();
    shown();
  }
  firstPage = false;
}

// ------------------------------------------------------------------ heartbeat / lifecycle
function heartbeat() { post('/api/app/heartbeat', {}).catch(() => {}); }
setInterval(heartbeat, 20000);
document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') heartbeat(); });
window.addEventListener('pagehide', () => {
  try { navigator.sendBeacon('/api/app/bye', new Blob([JSON.stringify({ t: TOKEN })], { type: 'text/plain' })); } catch {}
});

// Prevent the window from navigating away when a file is dropped outside a drop zone.
window.addEventListener('dragover', (e) => e.preventDefault());
window.addEventListener('drop', (e) => e.preventDefault());

// A picture dragged from the window itself is never a file dropped in: the browser hands it over as a file (its
// shown preview), so a spread dragged a little and let go replaced itself with a square of its own (the owner,
// 26.09.2026). Every page's file drop is shut for a drag that started here — before any page sees it; the mockups'
// own drags (spreads, slots) carry no files and go on as before.
let dragFromPage = false;
document.addEventListener('dragstart', () => { dragFromPage = true; }, true);
document.addEventListener('dragend', () => { dragFromPage = false; }, true);
const ownPicture = (e) => dragFromPage && [...(e.dataTransfer?.types || [])].includes('Files');
for (const type of ['dragenter', 'dragover', 'drop']) {
  window.addEventListener(type, (e) => {
    if (!ownPicture(e)) return;
    e.stopImmediatePropagation(); // no drop zone lights up; dragover not allowed → no drop at all
    if (type === 'drop') { e.preventDefault(); dragFromPage = false; }
  }, true);
}

async function boot() {
  topbar.el = document.getElementById('topbar');
  heartbeat();
  buildSidebar();
  wireSidebar();
  updateSidebar();
  installDropAnywhere();
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
  // Warm up the other pages' code while the user looks at the first one; a picture the Workshop may be waiting for
  // since before a reload is noticed (the rail's dot, the title).
  idle(() => {
    ROUTES.forEach(([, load, , lazy]) => { if (!lazy) load().catch(() => {}); });
    import('./workshop-live.js').then((live) => live.wake()).catch(() => {});
  });
}

boot();
