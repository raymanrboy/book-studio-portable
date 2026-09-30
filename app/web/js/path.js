// An object's path (2026-09-30, wiki/plans/ui-redesign.md): where an order or a book is and what comes next, drawn
// the one way — a strip of squares, ✓ done, half-filled started, dashed skipped, the next one breathing, red where
// something is wrong. A step is `{key, label, state: 'done'|'part'|'todo'|'skip', icon?, thumb?, count?, tip?, nogo?}`;
// the first step not done is the next. With `icon` the square shows the step's picture instead of its number and the
// word goes to the tooltip — a path is shown, not told (the owner, 2026-09-30: "minimum captions, maximum icons").
// The Workshop's book page draws the same steps one by one (`pathStep`) so its keyed patching keeps the strip smooth.
import { html, ic } from './lib.js';

const WORDS = { done: 'готово', part: 'почато', todo: 'ще ні', skip: 'не потрібно' };

/** One step of the path. `steps` is the whole list (for the step before and the next one). */
export function pathStep(s, i, steps, { act = 'path', active = '', tabs = false } = {}) {
  const next = steps.findIndex((x) => x.state !== 'done' && x.state !== 'skip');
  const pictured = steps.every((x) => x.icon);
  const prev = steps[i - 1];
  const cls = [s.state, i === next && 'next', prev && ['done', 'skip'].includes(prev.state) && 'after-done',
    active === s.key && 'sel', s.nogo && 'nogo'].filter(Boolean).join(' ');
  const tip = [s.tip || `${s.label}: ${WORDS[s.state]}`, s.tip ? '' : s.count].filter(Boolean).join(' · ');
  const face = s.thumb ? html`<img alt="" src="${s.thumb}">`
    : s.icon ? ic(s.nogo ? 'alert' : s.icon) : s.state === 'done' ? ic(s.nogo ? 'alert' : 'check') : s.state === 'skip' ? ic('minus') : i + 1;
  const role = tabs ? html`role="tab" aria-selected="${active === s.key}"` : html`role="listitem"`;
  return html`<button type="button" class="ws-step ${cls}" ${role} data-act="${act}" data-step="${s.key}" data-tip="${tip}"
    aria-label="${tip}" ${i === next ? html`aria-current="step"` : ''}>
    <span class="ws-dot ${s.thumb ? 'photo' : ''}">${face}</span>
    ${pictured ? '' : html`<span class="ws-step-label">${s.label}</span>${s.count ? html`<span class="ws-step-count ${s.nogo ? 'nogo' : ''}">${s.count}</span>` : ''}`}</button>`;
}

export function pathHtml(steps, { label = 'Шлях', active = '', act = 'path' } = {}) {
  const pictured = steps.every((s) => s.icon);
  return html`<div class="ws-strip path-strip ${pictured ? 'path-icons' : ''}" style="--steps:${steps.length}" role="list" aria-label="${label}">${steps.map((s, i) => pathStep(s, i, steps, { act, active }))}</div>`;
}
