// «Інструменти» (2026-09-30): every tool that also works on its own, in the ink of what it serves. Inside an order or
// a book the same tool opens from the object's step with the object loaded; here it opens empty. A tile shows the name and
// the picture only — what the tool does is its tooltip (show, don't tell).
import { html, ic, setHtml } from '../lib.js';
import { TOOLS } from '../places.js';

export async function mount(view) {
  const groups = [...new Set(TOOLS.map((t) => t.for))];
  setHtml(view, html`
    <div class="page-head">
      <div>
        <h1 class="page-title">Інструменти</h1>
      </div>
    </div>
    ${groups.map((g) => {
      const tools = TOOLS.filter((t) => t.for === g);
      return html`<section class="tool-group" data-mode="${tools[0].area === 'books' ? 'listings' : 'orders'}">
        <h2 class="tool-group-title">${g}</h2>
        <div class="tool-grid">${tools.map((t) => html`<a class="tool-tile" href="${t.hash}" data-tip="${t.sub}" aria-label="${t.label} — ${t.sub}">
          <span class="tool-icon">${ic(t.icon)}</span>
          <span class="tool-text"><b>${t.label}</b></span>
          <span class="tool-go">${ic('chevRight')}</span></a>`)}</div>
      </section>`;
    })}`);
  return {};
}
