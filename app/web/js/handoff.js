// One-shot hand-over between pages: the order card fills the Order Creator with one order's book.
// Kept in memory only, so a reload or a later visit starts empty as always.
let parcel = null;

export function give(to, data) { parcel = { to, data }; }

/** Something waits for this page: it must be built anew, not brought back as it was left. */
export const waiting = (to) => parcel?.to === to;

export function take(to) {
  if (parcel?.to !== to) return null;
  const { data } = parcel;
  parcel = null;
  return data;
}
