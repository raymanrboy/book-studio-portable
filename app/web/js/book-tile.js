// One book on a shelf (2026-09-30, late — wiki/plans/ui-redesign.md, «one book, one language»): the library's tile and
// the Workshop's card were two components for the same object. Now both are this: a square cover (the book's face), its
// title, one quiet line under it, a bar of segments and — only where it has something to say — a line for what is next.
import { html, ic } from './lib.js';

/** A bar of segments — the one way a book's progress is drawn (library: 4 parts, Workshop: 11 steps).
 *  `parts`: [{v: 0…1, skip?, nogo?, tip?}] */
export function segBar(parts, tip = '') {
  return html`<span class="segbar" ${tip ? html`data-tip="${tip}"` : ''}>${parts.map((p) => html`<i class="${p.skip ? 'skip' : ''} ${p.nogo ? 'nogo' : ''}" ${p.tip ? html`data-tip="${p.tip}"` : ''}><b style="transform:scaleX(${p.v})"></b></i>`)}</span>`;
}

/** A tile. `cover`: {src, lqip, front, cls, letter}; `sub`: the quiet line (html); `bar`: html from segBar();
 *  `meta`: html for the last line (or ''); `over`: html laid over the cover (a badge, a waiting mark). */
export function bookTile({ key, title, number, sub = '', cover, over = '', bar = '', meta = '', i = 0, enter = false }) {
  const bg = cover.lqip ? html`style="background-image:url(${cover.lqip});background-position:${cover.front ? '100% 50%' : 'center'}"` : '';
  return html`<button class="book-card ${enter ? 'enter' : ''}" type="button" data-key="${key}" data-open="${key}" aria-label="${title}" style="animation-delay:${Math.min(i * 22, 400)}ms">
    <div class="book-frame">
      <div class="book-cover ${cover.lqip ? 'lqip' : ''}" ${bg}>
        ${cover.src ? html`<img data-fade loading="lazy" decoding="async" alt="" class="${cover.cls || ''}" src="${cover.src}">`
          : html`<div class="book-cover-ph"><span class="serif">${cover.letter}</span></div>`}
        ${over}
      </div>
      <i class="crops"></i>
    </div>
    <div class="book-meta">
      <div class="book-title">${number != null ? html`<span class="ws-no num">№${number}</span>` : ''}${title}</div>
      ${sub ? html`<div class="book-sub">${sub}</div>` : ''}
      ${bar}
      ${meta ? html`<div class="book-next">${meta}</div>` : ''}
    </div>
  </button>`;
}

export const tickBadge = (tip) => html`<span class="book-badge" data-tip="${tip}">${ic('check')}</span>`;
