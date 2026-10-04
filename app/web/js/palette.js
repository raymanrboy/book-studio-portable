// Search everywhere — Ctrl+K or «Пошук» in the rail (2026-09-30): an order by the buyer, the child or the receipt, a
// book by its title or number, a place, a tool, a Settings block. Enter opens; ↑ ↓ move; Esc closes. The lists are
// read when it opens (the orders from the last sync — opening it never starts one).
import { api, html, ic, setHtml, modal, on, relTime, remember } from './lib.js';
import { PLACES, TOOLS, SETTINGS } from './places.js';

const STAGE_WORD = { new: 'нове', work: 'друкується', sent: 'позначити в Etsy', shipped: 'відправлене' };
const norm = (s) => String(s ?? '').toLowerCase().replace(/[’'`]/g, '').replace(/ё/g, 'е');

let open = null;

export async function openPalette() {
  if (open) { open.input.focus(); return; }
  const body = document.createElement('div');
  setHtml(body, html`
    <div class="pal-field">${ic('search')}<input class="pal-input" id="pal-q" type="text" autocomplete="off" spellcheck="false"
      placeholder="Замовлення, книга, інструмент…" aria-label="Пошук по всій програмі" aria-controls="pal-list" autofocus>
      <span class="kbd">Esc</span></div>
    <div class="pal-list" id="pal-list" role="listbox" aria-label="Знайдене"></div>`);
  const dlg = modal({ title: 'Пошук', body, size: 'palette', onClose: () => { open = null; } });
  const input = body.querySelector('#pal-q');
  const list = body.querySelector('#pal-list');
  open = { dlg, input };

  const fixed = [
    ...PLACES.map((p) => ({ ...p, group: 'Перейти' })),
    ...TOOLS.map((t) => ({ ...t, group: 'Інструменти' })),
    ...SETTINGS.map((s) => ({ ...s, group: 'Налаштування', words: '' })),
  ];
  let orders = [];
  let books = [];
  let doers = []; // verbs with an object: «Мокапи · №41» goes straight to that book's mockups
  let failed = false; // none of the three lists came: «nothing found» would be a lie
  let pick = 0;
  let shown = [];

  const load = async () => {
    const [o, lib, ws] = await Promise.all([
      api('/api/orders').catch(() => null), api('/api/library/books').catch(() => null), api('/api/workshop/books').catch(() => null)]);
    failed = !o && !lib && !ws;
    orders = (o?.orders || []).map((x) => ({
      group: 'Замовлення', icon: 'inbox', hash: `#/orders/${x.receiptId}`,
      label: x.name, sub: [`#${x.receiptId}`, x.childName, STAGE_WORD[x.stage], relTime(x.createdAt)].filter(Boolean).join(' · '),
      words: `${x.receiptId} ${x.childName || ''} ${x.book?.title || ''}`, rank: x.stage === 'new' ? 0 : 1,
    }));
    books = [
      ...(ws?.books || []).filter((b) => !b.library).map((b) => ({
        group: 'Книги', icon: 'workshop', hash: `#/workshop/${encodeURIComponent(b.id)}`,
        label: `${b.number != null ? `№${b.number} ` : ''}${b.title}`, sub: 'Майстерня', words: b.coverTitle || '',
      })),
      ...(lib?.books || []).map((b) => ({
        group: 'Книги', icon: 'shelf', hash: `#/book/${b.id}`, label: b.title,
        sub: [b.archived ? 'Архів' : 'Бібліотека', b.listingId && `#${b.listingId}`].filter(Boolean).join(' · '), words: b.listingId || '',
      })),
    ];
    // Ctrl+K as a doer (2026-09-30): "mockups 41" opens the Mockups with that book already chosen. Only ways in — nothing is
    // sent, changed or written from here.
    doers = (ws?.books || []).filter((b) => !b.library).flatMap((b) => {
      const name = `${b.number != null ? `№${b.number} ` : ''}${b.title}`;
      return [
        { group: 'Зробити', icon: 'mockup', label: `Мокапи · ${name}`, sub: 'Картинки для лістингу з Photoshop', words: `мокапи mockups ${b.number ?? ''}`,
          run: () => { remember('mk-for-book', { id: b.id }); location.hash = '#/mockups'; } },
        { group: 'Зробити', icon: 'template', label: `Слайди · ${name}`, sub: 'Шість слайдів лістингу', words: `слайди slides ${b.number ?? ''}`,
          run: () => { location.hash = `#/slides/${encodeURIComponent(b.id)}/1`; } },
      ];
    });
    paint();
  };

  function results() {
    const q = norm(input.value.trim());
    if (!q) {
      const fresh = orders.filter((o) => o.rank === 0).slice(0, 5);
      return [...fresh, ...fixed.filter((x) => x.group === 'Перейти' || x.group === 'Інструменти')];
    }
    const terms = q.split(/\s+/);
    const score = (x) => {
      const hay = norm(`${x.label} ${x.sub || ''} ${x.words || ''}`);
      if (!terms.every((t) => hay.includes(t))) return -1;
      const label = norm(x.label);
      return (label.startsWith(terms[0]) ? 3 : label.includes(terms[0]) ? 2 : 1) - (x.rank || 0) * 0.1;
    };
    return [...orders, ...doers, ...books, ...fixed].map((x) => [x, score(x)]).filter(([, s]) => s >= 0)
      .sort((a, b) => b[1] - a[1]).slice(0, 40).map(([x]) => x);
  }

  function paint() {
    shown = results();
    pick = Math.min(pick, Math.max(0, shown.length - 1));
    if (!shown.length) {
      setHtml(list, html`<div class="pal-empty">${ic(failed ? 'alertCircle' : 'search')}<span>${failed
        ? 'Не вдалося завантажити замовлення й книги для пошуку — перевірте зв’язок із програмою'
        : 'Нічого не знайдено — спробуйте ім’я покупця, номер чека чи назву книги'}</span></div>`);
      return;
    }
    let group = '';
    setHtml(list, shown.map((x, i) => {
      const head = x.group !== group ? html`<div class="pal-group">${(group = x.group)}</div>` : '';
      return html`${head}<button type="button" class="pal-item ${i === pick ? 'on' : ''}" role="option" aria-selected="${i === pick}" data-i="${i}" tabindex="-1">
        <span class="pal-icon">${ic(x.icon)}</span><span class="pal-text"><b>${x.label}</b>${x.sub ? html`<small>${x.sub}</small>` : ''}</span>
        <span class="pal-enter">${ic('chevRight')}</span></button>`;
    }));
  }

  const go = (i) => {
    const x = shown[i];
    if (!x) return;
    dlg.close();
    if (x.run) x.run();
    else if (location.hash !== x.hash) location.hash = x.hash;
  };
  const move = (d) => {
    if (!shown.length) return;
    pick = (pick + d + shown.length) % shown.length;
    paint();
    list.querySelector('.pal-item.on')?.scrollIntoView({ block: 'nearest' });
  };

  input.addEventListener('input', () => { pick = 0; paint(); });
  input.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
    else if (e.key === 'Enter') { e.preventDefault(); go(pick); }
  });
  on(list, 'click', '.pal-item', (e, b) => go(Number(b.dataset.i)));
  on(list, 'mousemove', '.pal-item', (e, b) => {
    const i = Number(b.dataset.i);
    if (i !== pick) { pick = i; list.querySelectorAll('.pal-item').forEach((n) => n.classList.toggle('on', Number(n.dataset.i) === i)); }
  });
  paint();
  input.focus();
  load();
}
