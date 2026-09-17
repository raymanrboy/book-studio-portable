// One-shot hand-over between pages: the order card fills the Order Creator with one order's book.
// Kept in memory only, so a reload or a later visit starts empty as always.
let parcel = null;

export function give(to, data) { parcel = { to, data }; }

export function take(to) {
  if (parcel?.to !== to) return null;
  const { data } = parcel;
  parcel = null;
  return data;
}
