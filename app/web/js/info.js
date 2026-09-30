// What the program says about itself (/api/app: connections, counts, settings), shared by the shell and the
// pages. Its own module, so pages need not import the shell that loads them (app.js ↔ pages).
import { api } from './lib.js';

// `here` — the page on screen (while the next one is built, still the one being left); `from` — the page shown before
// it. The shell keeps both: «back» leads where the owner came from (2026-09-30).
export const store = { info: null, here: '', from: '' };
let onChange = () => {};

/** The shell redraws its rail when the info changes (app.js sets this once). */
export function whenInfoChanges(fn) { onChange = fn; }

export async function refreshInfo() {
  try {
    store.info = await api('/api/app');
    onChange();
  } catch { /* offline overlay handles it */ }
  return store.info;
}
