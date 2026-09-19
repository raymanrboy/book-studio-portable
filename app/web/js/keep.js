// Work on an order survives stepping to another tab (owner, 18.09.2026): an order card and the Order
// Creator working on that order are hidden — not rebuilt — when the owner leaves them, and come back
// exactly as left (files, proof, the creator's form or its result) until the order leaves «Нові».
// Memory only: a restart of the program forgets everything, like the temporary copies of the files.
const pages = new Map(); // hash → { view, ctrl, scroll }
const sent = new Map();  // receipt id → { provider, what } once the Order Creator has made its draft

export const isKept = (hash) => pages.has(hash);
/** Which order the page kept under this hash is working on ('' when none is kept). */
export const keptOrder = (hash) => String(pages.get(hash)?.ctrl?.receiptId || '');
// Cards with nothing but a position to remember (no files, no draft) are cheap but add up over a day of
// opening orders: only the latest few of them are kept (code review 19.09.2026).
const IDLE_KEPT = 3;
export function stash(hash, page) {
  pages.set(hash, page);
  const idle = [...pages].filter(([, p]) => { try { return !!p.ctrl?.idle?.(); } catch { return false; } });
  for (const [old] of idle.slice(0, Math.max(0, idle.length - IDLE_KEPT))) release(old);
}
export function unstash(hash) {
  const page = pages.get(hash) || null;
  pages.delete(hash);
  return page;
}
export function release(hash) {
  const page = unstash(hash);
  try { page?.ctrl?.unmount?.(); } catch (err) { console.error(err); }
}

/** Forgets the work on orders that are no longer new (ordered at a printer, shipped, cancelled). */
export function settle(orders) {
  const open = new Set(orders.filter((o) => o.stage === 'new').map((o) => String(o.receiptId)));
  for (const [hash, page] of [...pages]) {
    const rid = page.ctrl?.receiptId;
    if (rid && !open.has(String(rid))) release(hash);
  }
  for (const rid of [...sent.keys()]) if (!open.has(rid)) sent.delete(rid);
}

/** The Order Creator made the draft for this order; its card shows it instead of «До друку». */
export const markSent = (rid, info) => { sent.set(String(rid), info); };
export const sentOf = (rid) => sent.get(String(rid)) || null;
