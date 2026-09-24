// What the program says about itself (/api/app: connections, counts, settings), shared by the shell and the
// pages. Its own module, so pages need not import the shell that loads them (app.js ↔ pages).
import { api } from './lib.js';

export const store = { info: null };
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
