// «Книги» (2026-09-30, wiki/decisions.md): every book in one place — the ones being made (the Workshop), the
// finished ones of the shop's listings (the library) and the archive — the owner's own words as the tabs — instead of two galleries in two modes. The galleries themselves
// are the Workshop's and the library's own pages, drawn here without their heads (`embedded`); a tab only swaps them.
import { recent, html, ic, setHtml, on, segHtml, setSeg, syncSeg, plural, remembered, remember, toast, BOOKS } from '../lib.js';

const TAB_KEY = 'bs-books-tab';
const TABS = [
  { value: 'work', label: 'Майстерня', icon: 'workshop', tip: 'Майстерня — нові книги в розробці' },
  { value: 'shop', label: 'Бібліотека', icon: 'shelf', tip: 'Бібліотека — готові книги лістингів' },
  { value: 'archive', label: 'Архів', icon: 'archive', tip: 'Архів книг' },
];

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
    // A count that has not arrived is left out, never shown as a false zero.
    const parts = [];
    if (counts.work !== null) parts.push(html`<span class="num">${counts.work}</span> у Майстерні`);
    if (counts.shop !== null) parts.push(html`<span class="num">${counts.shop}</span> ${plural(counts.shop, BOOKS)} у бібліотеці`);
    setHtml(view.querySelector('#bk-sub'), parts.length ? parts.flatMap((p, i) => (i ? [' · ', p] : [p])) : '\u00a0');
  };

  const readCounts = async () => {
    const [ws, lib] = await Promise.all([recent('/api/workshop/books').catch(() => null), recent('/api/library/books').catch(() => null)]);
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
    let ctrl;
    try {
      const mod = tab === 'work' ? await import('./workshop.js') : await import('./library.js');
      ctrl = await mod.mount(box, [], { embedded: true, filter: tab === 'archive' ? 'archived' : 'active' });
    } catch (err) {
      if (my !== seq) return;
      // The old tab's pictures must not stay under the new tab's highlight.
      console.error(err);
      toast(err.message || 'Не вдалося відкрити вкладку', 'error');
      setHtml(body, html`<div class="notice notice-error">${ic('alertCircle')}<div>Не вдалося відкрити цю вкладку: ${err.message || 'помилка'}</div></div>`);
      return;
    }
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
