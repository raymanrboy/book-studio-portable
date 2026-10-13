// Mockups, step 4 drawn: the run (its rows, Photoshop's «run this script?»), the result, «Ваша черга» with the
// templates left open, the pictures saved after it — templates of what the page holds (out of mockups.js on
// 27.09.2026).
import { html, ic, ib, media, plural, attr, setHtml, reducedMotion } from '../lib.js';

const SHOT_W = 480;           // a saved picture in the result
export const PICTURES = ['картинка', 'картинки', 'картинок'];

// The percent is unknown while Photoshop is being asked (the job sits at a pinned number) and before the first step
// reports: the bar is then the neutral sweep, never a part-filled one.
export const runIndet = (r) => r.phase === 'ask' || (r.phase === 'prepare' && !(r.percent > 0));

export function runView(r) {
  return html`<div class="mk-run">
    ${r.phase === 'ask' ? askView() : html`<div class="row mk-run-now"><span class="spinner"></span><span class="grow truncate" id="mk-step">${r.step}</span>
      <span class="num faint" id="mk-pct">${Math.round(r.percent)}%</span></div>`}
    <div class="progress live ${runIndet(r) ? 'indet' : ''}"><i id="mk-bar" style="transform:scaleX(${Math.max(0, Math.min(100, r.percent)) / 100})"></i></div>
    <div class="mk-rows" id="mk-rows">${rowsHtml(r.rows || [], r.mode === 'finish')}</div>
  </div>`;
}

// Photoshop's "run this script?" drawn small, its Yes pulsing: the owner knows what to look for.
function askView() {
  return html`<div class="mk-ask">
    <div class="mk-ask-dlg" aria-hidden="true">
      <div class="mk-ask-bar">Adobe Photoshop</div>
      <div class="mk-ask-body"><span class="mk-ask-mark">!</span><span class="mk-ask-lines"><i></i><i></i></span></div>
      <div class="mk-ask-btns"><b>Yes</b><span>No</span></div>
    </div>
    <div class="mk-ask-text"><b>Photoshop питає, чи запустити скрипт</b><span>Натисніть «Yes» у його вікні — далі все саме.</span></div>
  </div>`;
}

// Rows are updated where they stand (class, icon, note), so a row's colour change and the new check play their
// transitions; a list that was rebuilt on every poll never could.
export function morphList(box, content) {
  const tmp = document.createElement('div');
  setHtml(tmp, content);
  const next = [...tmp.children], cur = [...box.children];
  next.forEach((n, i) => {
    const o = cur[i];
    if (!o) { box.appendChild(n); return; }
    if (o.className !== n.className) o.className = n.className;
    const oc = [...o.children], nc = [...n.children];
    if (oc.length !== nc.length) { o.innerHTML = n.innerHTML; return; }
    nc.forEach((c, j) => {
      if (oc[j].className !== c.className) oc[j].className = c.className;
      if (oc[j].innerHTML !== c.innerHTML) oc[j].innerHTML = c.innerHTML;
    });
  });
  cur.slice(next.length).forEach((o) => o.remove());
}

// A block that comes and goes (a hint, a card) opens and closes with real frames instead of jumping: height and
// opacity by the Web Animations API. The first call only sets the state.
export function reveal(box, show) {
  if (!box) return;
  const first = box.dataset.rv === undefined;
  if (!first && box.dataset.rv === (show ? '1' : '0')) return;
  box.dataset.rv = show ? '1' : '0';
  box.getAnimations?.().forEach((a) => a.cancel());
  box.style.overflow = '';
  if (first || reducedMotion() || (box.hidden === !show)) { box.hidden = !show; return; }
  box.style.overflow = 'hidden';
  if (show) {
    box.hidden = false;
    box.animate([{ height: '0px', opacity: 0 }, { height: `${box.scrollHeight}px`, opacity: 1 }], { duration: 260, easing: 'cubic-bezier(.2,.7,.2,1)' })
      .finished.then(() => { box.style.overflow = ''; }, () => {});
  } else {
    const h = box.getBoundingClientRect().height;
    box.animate([{ height: `${h}px`, opacity: 1 }, { height: '0px', opacity: 0 }], { duration: 150, easing: 'ease-in' })
      .finished.then(() => { if (box.dataset.rv === '0') { box.hidden = true; box.style.overflow = ''; } }, () => {});
  }
}

export function rowsHtml(rows, finishing) {
  return rows.map((r) => {
    const icon = r.state === 'done' ? ic('check') : r.state === 'work' ? html`<span class="spinner"></span>` : html`<i class="mk-dot"></i>`;
    let note = '';
    if (finishing) note = r.state === 'done' ? 'збережено й закрито' : '';
    else if (r.keepOpen) note = html`${ic('hand', 'icon-s')}${r.state === 'done' ? 'відкрито для вас' : 'лишиться відкритим'}`;
    else if (r.shots > 1) note = html`<span class="num">${r.saved}/${r.shots}</span>`;
    return html`<div class="mk-row ${r.state}"><span class="mk-row-ico">${icon}</span><span class="grow truncate">${r.title}</span><span class="mk-row-note">${note}</span></div>`;
  });
}

// A picture Book Studio drew where the front cover shows carries the crop button (r.edits: name -> template key);
// r.v — its version once redrawn, so the new one is shown.
function shotsGrid(r, which) {
  if (!r.saved.length) return '';
  return html`<div class="mk-shots">${r.saved.map((name, i) => {
    const shot = html`<button type="button" class="mk-shot" data-act="shot" data-which="${which}" data-i="${i}"
      aria-label="${name}" data-tip="${name}"><img data-fade alt="" draggable="false" src="${media(`/media/mockups/out/${r.job}/${i}`, { w: SHOT_W, ...(r.v?.[name] && { v: r.v[name] }) })}"></button>`;
    const key = r.edits?.[name];
    return key ? html`<div class="mk-shot-wrap">${shot}${ib('crop', 'Поправити обкладинку', `data-act="edit-shot" ${attr('data-key', key)}`, { cls: 'sm mk-shot-edit' })}</div>` : shot;
  })}</div>`;
}

const problemsHtml = (list) => (list?.length ? html`<div class="notice notice-warn">${ic('alert')}<div><ul>${list.map((p) => html`<li>${p}</li>`)}</ul></div></div>` : '');

export function resultCard(r) {
  const count = r.saved.length;
  return html`<div class="result-card mk-result">
    <h4>${ic(r.cancelled ? 'alert' : 'checkCircle')}<span class="grow">${r.cancelled ? 'Зупинено' : 'Готово'} · <span class="num">${count}</span> ${plural(count, PICTURES)}</span>
      <span class="mk-secs num">${r.seconds} с</span>
      ${ib('folderOpen', 'Відкрити папку з картинками', `data-act="open-out" ${attr('data-path', r.folder)}`, { cls: 'sm' })}</h4>
    ${shotsGrid(r, 'result')}
    ${problemsHtml(r.problems)}
  </div>`;
}

// Everything already in the Workshop book's mockups/ — made another day or by an earlier run (11.10.2026): shown
// whatever this session ran, and step 4 makes the slides from them.
export function existingCard(x) {
  const count = x.files.length;
  return html`<div class="result-card mk-result mk-existing">
    <h4>${ic('images')}<span class="grow">У папці книги · <span class="num">${count}</span> ${plural(count, PICTURES)}</span>
      ${ib('folderOpen', 'Відкрити папку мокапів цієї книги', `data-act="open-out" ${attr('data-path', x.folder)}`, { cls: 'sm' })}</h4>
    <div class="mk-shots">${x.files.map((f, i) => html`<button type="button" class="mk-shot" data-act="shot" data-which="existing" data-i="${i}"
      aria-label="${f.name}" data-tip="${f.name}"><img data-fade alt="" draggable="false" src="${media('/media/mockups/existing', { workshop: x.id, name: f.name, w: SHOT_W, v: f.v })}"></button>`)}</div>
  </div>`;
}

export function turnCard(p) {
  return html`<div class="mk-turn">
    <div class="mk-turn-head">${ic('hand')}<span>Ваша черга — у Photoshop</span></div>
    <p>Відкриті: <b>${p.open.join(', ')}</b>${p.cover ? html` і обкладинка книги <b>Cover</b> — з неї й беріть передню` : ''}. Підженіть передню обкладинку${p.open.includes('Dedication') ? ' й кольори фону та столу в Dedication' : ''} — і збережіть усі разом:</p>
    <button type="button" class="btn btn-block mk-finish" data-act="finish">${ic('download')}Зберегти відкриті й закрити</button>
    <div class="mk-turn-note">Картинки ляжуть у ту саму папку й будуть названі, як решта. Можна зберегти їх і самому, як звикли, — тимчасові копії програма прибере сама.</div>
  </div>`;
}

export function finishedCard(f) {
  const count = f.saved.length;
  return html`<div class="result-card mk-result">
    <h4>${ic('checkCircle')}<span class="grow">Збережено ще <span class="num">${count}</span> ${plural(count, PICTURES)}</span>
      ${ib('folderOpen', 'Відкрити папку з картинками', `data-act="open-out" ${attr('data-path', f.folder)}`, { cls: 'sm' })}</h4>
    ${shotsGrid(f, 'finished')}
    ${f.cleaned ? html`<div class="mk-clean">${ic('check', 'icon-s')}Тимчасові копії шаблонів прибрано</div>` : ''}
    ${problemsHtml(f.problems)}
  </div>`;
}
