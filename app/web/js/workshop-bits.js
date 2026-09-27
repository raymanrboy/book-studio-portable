// What the Workshop's two pages share: a book's picture address, the book check's word, a step's state in words (the book page imported them from the gallery page until 27.09.2026).
import { media, plural } from './lib.js';

export const ERRORS = ['помилка', 'помилки', 'помилок'];
/** A step's state in words: short on a gallery card's bar, in full in a book's strip. */
export const STATE_WORDS = { done: 'готово', part: 'почато', todo: 'ще ні', skip: 'не потрібно' };
export const STATE_TEXT = { done: 'Готово', part: 'Почато', todo: 'Ще ні', skip: 'Не потрібно — книга без героя (Tier S)' };

/** A book's picture address; with its version the browser keeps it for good — nothing blinks on a redraw. */
export function picture(b, area, name, w, variant = '') {
  const v = b.v?.[`${area}/${variant ? `variants/${variant}/` : ''}${name}`];
  const path = `/media/workshop/${encodeURIComponent(b.id)}/${area}${variant ? `/v/${encodeURIComponent(variant)}` : ''}/${encodeURIComponent(name)}`;
  return media(path, { w, ...(v ? { v } : {}) });
}

/** «Промпти · GO» — the book check's word for a card or a step. */
export function checkWord(c) {
  return c.go ? 'GO' : `${c.fails} ${plural(c.fails, ERRORS)}`;
}
