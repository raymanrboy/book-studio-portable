// The Workshop's live link to the server (the book console moved in, 26.09.2026). A Workshop page on screen asks every
// 1.5 s what changed — the books' files (an agent has just written one), the generation mode (a picture caught, the
// next prompt in the clipboard) — and redraws itself. While a picture is awaited and the owner is elsewhere in Book
// Studio the link keeps asking every 4 s, so a catch is noticed wherever he is: a notice, and the 'bs:busy' event —
// the rail's dot and the window's title (app.js).
import { api, post, html, ic, ib, toast, tellBusy } from './lib.js';

const FAST = 1500, SLOW = 4000;
let gen = null;              // the generation mode: generate.Session.status() on the server
let page = null;             // the Workshop page on screen: { book, sig, onChange }
let primed = false, seenAt = 0, seenError = '', said = undefined;
let timer = 0, asking = false;

export const genState = () => gen;

/** A page's first data carries what it was drawn from ({sig, gen}); `onChange` is called when that changes. */
export function watch({ book = '', sig, gen: g }, onChange) {
  page = { book, sig, onChange };
  take(g);
  schedule();
  // Leaving the page: one more look, so a wait begun there goes on being followed from anywhere in Book Studio.
  return () => { if (page?.onChange === onChange) { page = null; schedule(0); } };
}

/** After the page did something itself (a picture dropped, a generation started): look at once. */
export const refresh = () => schedule(0);
/** Book Studio's start: one look — a generation may be going on from before a reload. */
export const wake = () => schedule(0);

// The window comes back into view: a look at once — only when there is something to follow.
document.addEventListener('visibilitychange', () => schedule(document.visibilityState === 'visible' && (page || gen?.active) ? 0 : undefined));

function schedule(ms) {
  clearTimeout(timer);
  const wait = ms ?? (page && document.visibilityState === 'visible' ? FAST : gen?.active ? SLOW : null);
  if (wait !== null) timer = setTimeout(ask, wait);
}

async function ask() {
  if (asking) return;
  asking = true;
  const watching = page;
  try {
    // A page on screen: its files and the generation mode. None: the generation mode alone (no book is walked).
    const data = watching ? await api(`/api/workshop/sig${watching.book ? `?book=${encodeURIComponent(watching.book)}` : ''}`)
      : { gen: await api('/api/workshop/gen') };
    take(data.gen);
    if (watching && watching === page && data.sig !== watching.sig) {
      watching.sig = data.sig;
      await watching.onChange();
    }
  } catch { /* the program closed or restarted: the window's own offline notice says so */ }
  asking = false;
  schedule();
}

function take(g) {
  const was = gen?.active;
  gen = g || null;
  const last = gen?.last;
  if (!primed) {
    primed = true;
    seenAt = last?.at || 0;
  } else if (last && last.at > seenAt) {
    seenAt = last.at;
    toast(last.note || `${last.label}: на місці`, 'success');
    if (was?.series && !gen.active && !gen.error) toast('Майстерня: усі картинки черги на місці', 'success', 6000);
  }
  if (gen?.error && gen.error !== seenError && !page) toast(`Майстерня: ${gen.error}`, 'error');
  seenError = gen?.error || '';
  const a = gen?.active;
  const label = a ? `${a.label}${a.of > 1 ? ` · ${a.step} з ${a.of}` : ''}` : null;
  if (label !== said) {
    said = label;
    tellBusy({ workshop: label });
  }
}

// ------------------------------------------------------------------ actions
/** An action from a button: the button waits (no double press), a notice says what happened, the page looks for
 *  changes at once. Resolves to the answer, or null after an error (already told). */
export async function act(btn, fn, ok) {
  if (btn?.classList.contains('busy')) return null;
  btn?.classList.add('busy');
  try {
    const res = await fn();
    const text = typeof ok === 'function' ? ok(res) : ok;
    if (text) toast(text, 'success');
    return res;
  } catch (err) {
    toast(err.message, 'error');
    return null;
  } finally {
    btn?.classList.remove('busy');
    refresh();
  }
}

/** «Генерувати»: the row's first thing goes into the clipboard, the Workshop waits for its picture in Downloads. */
export const startGen = (btn, body) => act(btn, () => post('/api/workshop/gen/start', body),
  (s) => (s.active ? `${s.active.label}: у буфері ${s.active.items[0]} — вставте в Gemini` : null));

/** The bar's buttons: «Далі» (F8), the same thing into the clipboard again, «Стоп». */
export const genAction = (btn, what) => act(btn, () => post(`/api/workshop/gen/${what}`, {}),
  what === 'again' ? 'Знову в буфері' : null);

/** Is this row the one the Workshop waits a picture for? */
export const waitingFor = (book, key, variant) => !!gen?.active && gen.active.book === book && gen.active.key === key
  && (gen.active.variant || '') === (variant || '');

// ------------------------------------------------------------------ the generation bar
/** What is awaited, what's in the clipboard, how far the queue is — sticky on top of the Workshop's pages. On another
 *  book's page (or the gallery) it says which book waits, with a way there. */
export function genBar(book) {
  if (!gen?.active) {
    return gen?.error ? html`<div class="ws-genbar err">${ic('alertCircle')}<div class="ws-gb-main">${gen.error}</div></div>` : '';
  }
  const a = gen.active;
  if (a.book !== book) {
    return html`<div class="ws-genbar other"><span class="ws-pulse"></span>
      <div class="ws-gb-main">Чекаю картинку для книги <b>${a.title}</b> · ${a.label}</div>
      <a class="btn btn-sm" href="#/workshop/${encodeURIComponent(a.book)}">Перейти</a>
      <button class="btn btn-sm btn-ghost" data-gen="stop">Стоп</button></div>`;
  }
  const more = a.item < a.items.length - 1;
  const hint = more ? `вставте в чат, далі — ${a.items[a.item + 1]}: «Далі»${gen.f8 ? ' або F8 у будь-якому вікні' : ''}`
    : `вставте в ${a.items.length > 1 ? 'чат' : 'Gemini'} і завантажте картинку — вона сама стане на місце`;
  return html`<div class="ws-genbar"><span class="ws-pulse"></span>
    <div class="ws-gb-main">
      <div class="ws-gb-title"><b>Чекаю картинку</b> · ${a.label}${a.of > 1 ? html` <span class="ws-gb-count num">${a.step} з ${a.of}</span>` : ''}</div>
      <div class="ws-gb-sub">${a.items.length > 1 ? html`<span class="ws-gb-parts">${a.items.map((label, i) => html`<i class="${i < a.item ? 'done' : i === a.item ? 'now' : ''}" data-tip="${label}"></i>`)}</span>` : ''}У буфері: <b>${a.items[a.item]}</b> — ${hint}</div>
      ${gen.error ? html`<div class="ws-gb-err">${gen.error}</div>` : ''}
    </div>
    ${more ? html`<button class="btn btn-primary btn-sm" data-gen="next" data-kbd="${gen.f8 ? 'F8' : ''}" data-tip="Наступне — у буфер">Далі</button>` : ''}
    ${ib('copy', 'Покласти в буфер ще раз (якщо ви щось скопіювали між тим)', 'data-gen="again"')}
    <button class="btn btn-sm btn-ghost" data-gen="stop" data-tip="Перестати чекати картинку">Стоп</button>
    ${a.of > 1 ? html`<div class="ws-gb-progress"><i style="transform:scaleX(${(a.step - 1) / a.of})"></i></div>` : ''}
  </div>`;
}
