// Mockups, step 4 drawn: the run (its rows, Photoshop's «run this script?»), the result, «Ваша черга» with the
// templates left open, the pictures saved after it — templates of what the page holds (out of mockups.js on
// 27.09.2026).
import { html, ic, ib, media, plural } from '../lib.js';

const SHOT_W = 480;           // a saved picture in the result
export const PICTURES = ['картинка', 'картинки', 'картинок'];

export function runView(r) {
  return html`<div class="mk-run">
    ${r.phase === 'ask' ? askView() : html`<div class="row mk-run-now"><span class="spinner"></span><span class="grow truncate" id="mk-step">${r.step}</span>
      <span class="num faint" id="mk-pct">${Math.round(r.percent)}%</span></div>`}
    <div class="progress"><i id="mk-bar" style="transform:scaleX(${Math.max(3, r.percent) / 100})"></i></div>
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

export function rowsHtml(rows, finishing) {
  return rows.map((r) => {
    const icon = r.state === 'done' ? ic('check') : r.state === 'work' ? html`<span class="spinner"></span>` : html`<i class="mk-dot"></i>`;
    let note = '';
    if (finishing) note = r.state === 'done' ? 'збережено й закрито' : '';
    else if (r.keepOpen) note = html`${ic('hand', 'icon-s')}${r.state === 'done' ? 'відкрито для вас' : 'лишиться відкритим'}`;
    else note = html`<span class="num">${r.saved}/${r.shots}</span>`;
    return html`<div class="mk-row ${r.state}"><span class="mk-row-ico">${icon}</span><span class="grow truncate">${r.title}</span><span class="mk-row-note">${note}</span></div>`;
  });
}

function shotsGrid(r, which) {
  if (!r.saved.length) return '';
  return html`<div class="mk-shots">${r.saved.map((name, i) => html`<button type="button" class="mk-shot" data-act="shot" data-which="${which}" data-i="${i}"
    aria-label="${name}" data-tip="${name}"><img data-fade alt="" draggable="false" src="${media(`/media/mockups/out/${r.job}/${i}`, { w: SHOT_W })}"></button>`)}</div>`;
}

const problemsHtml = (list) => (list?.length ? html`<div class="notice notice-warn">${ic('alert')}<div><ul>${list.map((p) => html`<li>${p}</li>`)}</ul></div></div>` : '');

export function resultCard(r) {
  const count = r.saved.length;
  return html`<div class="result-card mk-result">
    <h4>${ic(r.cancelled ? 'alert' : 'checkCircle')}<span class="grow">${r.cancelled ? 'Зупинено' : 'Готово'} · <span class="num">${count}</span> ${plural(count, PICTURES)}</span>
      <span class="mk-secs num">${r.seconds} с</span>
      ${ib('folderOpen', 'Відкрити папку з картинками', `data-act="open-out" data-path="${r.folder}"`, { cls: 'sm' })}</h4>
    ${shotsGrid(r, 'result')}
    ${problemsHtml(r.problems)}
  </div>`;
}

export function turnCard(p) {
  return html`<div class="mk-turn">
    <div class="mk-turn-head">${ic('hand')}<span>Ваша черга — у Photoshop</span></div>
    <p>Відкриті: <b>${p.open.join(', ')}</b>${p.cover ? html` і обкладинка книги <b>Cover</b> — з неї й беріть лицьову` : ''}. Підженіть лицьову обкладинку${p.open.includes('Dedication') ? ' й кольори фону та столу в Dedication' : ''} — і збережіть усі разом:</p>
    <button type="button" class="btn btn-block mk-finish" data-act="finish">${ic('download')}Зберегти відкриті й закрити</button>
    <div class="mk-turn-note">Картинки ляжуть у ту саму папку й будуть названі, як решта. Можна зберегти їх і самому, як звикли, — тимчасові копії програма прибере сама.</div>
  </div>`;
}

export function finishedCard(f) {
  const count = f.saved.length;
  return html`<div class="result-card mk-result">
    <h4>${ic('checkCircle')}<span class="grow">Збережено ще <span class="num">${count}</span> ${plural(count, PICTURES)}</span>
      ${ib('folderOpen', 'Відкрити папку з картинками', `data-act="open-out" data-path="${f.folder}"`, { cls: 'sm' })}</h4>
    ${shotsGrid(f, 'finished')}
    ${f.cleaned ? html`<div class="mk-clean">${ic('check', 'icon-s')}Тимчасові копії шаблонів прибрано</div>` : ''}
    ${problemsHtml(f.problems)}
  </div>`;
}
