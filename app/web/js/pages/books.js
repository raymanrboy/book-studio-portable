// «Книги» (2026-09-30, wiki/decisions.md): every book in one place — the ones being made (the Workshop), the
// finished ones of the shop's listings (the library) and the archive — the owner's own words as the tabs — instead of two galleries in two modes. The galleries themselves
// are the Workshop's and the library's own pages, drawn here without their heads (`embedded`); a tab only swaps them.
import { api, html, setHtml, on, segHtml, setSeg, syncSeg, plural, remembered, remember } from '../lib.js';

const TAB_KEY = 'bs-books-tab';
const TABS = [
  { value: 'work', label: 'Майстерня', icon: 'workshop', tip: 'Майстерня — нові книги в розробці' },
  { value: 'shop', label: 'Бібліотека', icon: 'shelf', tip: 'Бібліотека — готові книги лістингів' },
  { value: 'archive', label: 'Архів', icon: 'archive', tip: 'Архів книг' },
];
const BOOKS = ['книга', 'книги', 'книг'];

export async function mount(view, [tabParam]) {
  let tab = TABS.some((t) => t.value === tabParam) ? tabParam : remembered(TAB_KEY, 'work');
  if (!TABS.some((t) => t.value === tab)) tab = 'work';
  const counts = { work: null, shop: null, archive: null };

  setHtml(view, html`
    <div class="page-head">
      <div>
        <h1 class="page-title">Книги</h1>
        <div class="page-sub" id="bk-sub">&nbsp;</div>
      </div>
    </div>
    <div class="bk-tabs" id="bk-tabs"></div>
    <div id="bk-body"></div>`);
  const body = view.querySelector('#bk-body');

  const paintTabs = () => {
    const box = view.querySelector('#bk-tabs');
    if (!box.firstElementChild) {
      setHtml(box, segHtml(TABS.map((t) => ({ ...t, count: counts[t.value] ?? '' })), tab, { name: 'books-tab', compact: true }));
    } else {
      box.querySelectorAll('button').forEach((b) => {
        const c = b.querySelector('.seg-count');
        if (c) c.textContent = counts[b.dataset.value] ?? '';
      });
      setSeg(box.querySelector('.seg'), tab);
    }
    const sub = view.querySelector('#bk-sub');
    const n = (x) => x ?? 0;
    setHtml(sub, html`<span class="num">${n(counts.work)}</span> у Майстерні · <span class="num">${n(counts.shop)}</span> ${plural(n(counts.shop), BOOKS)} у бібліотеці`);
  };

  const readCounts = async () => {
    const [ws, lib] = await Promise.all([api('/api/workshop/books').catch(() => null), api('/api/library/books').catch(() => null)]);
    if (ws) counts.work = ws.books.filter((b) => !b.library).length;
    if (lib) {
      counts.shop = lib.books.filter((b) => !b.archived).length;
      counts.archive = lib.books.length - counts.shop;
    }
    paintTabs();
  };

  let child = null;
  let seq = 0;
  const show = async () => {
    const my = ++seq;
    try { child?.unmount?.(); } catch (err) { console.error(err); }
    child = null;
    const box = document.createElement('div');
    const mod = tab === 'work' ? await import('./workshop.js') : await import('./library.js');
    const ctrl = await mod.mount(box, [], { embedded: true, filter: tab === 'archive' ? 'archived' : 'active' });
    if (my !== seq) { try { ctrl?.unmount?.(); } catch {} return; }
    body.replaceChildren(box);
    child = ctrl;
    child?.shown?.();
  };

  paintTabs();
  await show();
  readCounts();

  const offs = [
    on(view, 'click', '[data-seg="books-tab"] button', (e, b) => {
      if (b.dataset.value === tab) return;
      tab = b.dataset.value;
      remember(TAB_KEY, tab);
      history.replaceState(null, '', `#/books/${tab}`);
      paintTabs();
      show();
    }),
  ];
  return {
    shown() { syncSeg(view.querySelector('#bk-tabs .seg')); child?.shown?.(); },
    unmount() { seq++; offs.forEach((f) => f()); try { child?.unmount?.(); } catch (err) { console.error(err); } },
  };
}
