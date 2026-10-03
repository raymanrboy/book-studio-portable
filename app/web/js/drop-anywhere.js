// Files dropped anywhere in the window (2026-09-30, wiki/decisions.md): a drop on a page's own folder field
// is that page's (`wireFolderDrop()`); a drop anywhere else used to do nothing — or let the browser open the file in place of
// the program. Now: the page in view may take it (`bs:dropped`); otherwise one question — «Куди?» — with the two places a
// Canva ZIP or a book folder goes, and the files are handed to the one chosen. The program never chooses for the owner and
// copies nothing until a place is chosen (the page's own intake does the copy).
import { html, ic, modal, topLayer, el } from './lib.js';
import { dropContents, dropLabel } from './drop.js';
import { give } from './handoff.js';

const PLACES = [
  { to: 'mockups', hash: '#/mockups', icon: 'mockup', label: 'Мокапи', tip: 'Демо-книга з Canva — картинки для лістингу' },
  { to: 'creator', hash: '#/creator', icon: 'printer', label: 'Order Creator', tip: 'Папка книги — чернетка в Gelato' },
];

const carriesFiles = (e) => [...(e.dataTransfer?.types || [])].includes('Files');
const overZone = (e) => !!e.target.closest?.('[data-folder-drop]');

export function installDropAnywhere() {
  const veil = el(html`<div class="drop-veil" aria-hidden="true">${ic('upload')}</div>`);
  document.body.appendChild(veil);
  const hide = () => document.documentElement.classList.remove('drop-any');

  // A window-wide drag: accepted (so the browser never opens the file instead of the program) unless a dialog is on top
  // or the pointer is over a page's own drop field, which has its own highlight.
  const over = (e) => {
    if (!carriesFiles(e)) return;
    if (overZone(e)) { hide(); return; }
    e.preventDefault();
    e.dataTransfer.dropEffect = topLayer() ? 'none' : 'copy';
    document.documentElement.classList.toggle('drop-any', !topLayer());
  };
  document.addEventListener('dragenter', over);
  document.addEventListener('dragover', over);
  document.addEventListener('dragleave', (e) => { if (!e.relatedTarget) hide(); });
  document.addEventListener('dragend', hide);

  document.addEventListener('drop', (e) => {
    hide();
    if (!carriesFiles(e)) return;
    if (e.defaultPrevented) return; // a page's own drop field took it
    e.preventDefault();
    if (topLayer()) return;
    const dropped = dropContents(e); // read now: the entries are good only during this event
    if (!dropped.files.length && !dropped.entries.length) return;
    // The page in view may take it as its own (the Order Creator, the Mockups, when they are open).
    const ask = new CustomEvent('bs:dropped', { detail: { dropped, handled: false }, bubbles: true });
    document.getElementById('view')?.dispatchEvent(ask);
    if (ask.detail.handled) return;
    choose(dropped);
  });
}

function choose(dropped) {
  const body = document.createElement('div');
  body.className = 'where-list';
  body.innerHTML = PLACES.map((p) => `<button type="button" class="tool-tile where-tile" data-to="${p.to}" data-tip="${p.tip}" aria-label="${p.label} — ${p.tip}">
    <span class="tool-icon">${ic(p.icon)}</span><span class="tool-text"><b>${p.label}</b></span><span class="tool-go">${ic('chevRight')}</span></button>`).join('');
  const dlg = modal({ title: 'Куди?', sub: dropLabel(dropped), body, size: 'where' });
  body.addEventListener('click', (e) => {
    const b = e.target.closest('[data-to]');
    if (!b) return;
    const place = PLACES.find((p) => p.to === b.dataset.to);
    dlg.close();
    give(place.to, { drop: dropped });
    location.hash = place.hash;
  });
}
