// A Workshop book's rows drawn: a spread or a page with its prompt, its frame (the picture, or the place to drop
// one) and its text — and the small parts the cover's card shares (out of workshop-book.js on 27.09.2026); a row's
// upscaling shows as a chip over its picture.
import { html, ic, ib, highlightTokens, attr } from '../lib.js';
import { picture } from '../workshop-bits.js';
import { waitingFor } from '../workshop-live.js';

const CUT = { sides: 'обрізано з боків', 'top-bottom': 'обрізано зверху й знизу' };
/** A row's slot, as the server names it: the key, or «variant/key». */
export const slot = (key, variant) => (variant ? `${variant}/${key}` : key);
/** A 2 px fill along a chip's foot: drawn only for a real fraction (0…1), never for a guess. */
export const chipFill = (f) => (f > 0 ? html`<i class="ws-chipfill" style="--f:${Math.min(1, f)}"></i>` : '');
export const waitChip = (text) => html`<span class="chip chip-accent"><span class="ws-pulse"></span>${text}</span>`;

/** The rows of one open book: `book()` — the book as it is now, `mem` — what the page remembers of it (the
 *  prompts shown whole), `uploading` — a drop's key → the share uploaded. */
export function rowTemplates({ id, book, mem, uploading }) {
  const pic = (area, name, w, variant) => picture(book(), area, name, w, variant);

  const saveBtn = (area, name, variant, tip) => html`<button type="button" class="ws-save" data-act="save" data-area="${area}" data-name="${name}" data-variant="${variant || ''}" aria-label="${tip}" data-tip="${tip}">${ic('download')}</button>`;
  const waitCover = (text) => html`<div class="ws-wait"><span class="ws-pulse"></span>${text}</div>`;
  const busyCover = (key) => (uploading.has(key) ? html`<div class="busy-overlay"><div class="ws-up"><i data-up="${key}"></i></div></div>` : '');

  /** A row's upscaling (27.09.2026): in work, waiting, failed, or done ×2 — as a chip over its picture. `key` is the
   *  row's slot: «spread3», or «G2_brunette/spread3» in a hero variant. */
  function upChip(key, m = {}) {
    const u = book().upscale;
    if (!u) return '';
    if (u.current?.key === key) return html`<span class="chip chip-accent ws-mark chip-prog"><span class="ws-pulse"></span>апскейл ${u.current.pct}%${chipFill(u.current.pct / 100)}</span>`;
    if (u.queue.includes(key)) return html`<span class="chip ws-mark">${ic('hourglass', 'icon-s')}чекає апскейлу</span>`;
    if (u.errors[key]) return html`<span class="chip chip-amber ws-mark" data-tip="${u.errors[key]}">${ic('alert', 'icon-s')}не апскейлено</span>`;
    // Every picture says how big its page is, so it's clear what is upscaled and what isn't (27.09.2026).
    const s = u.sides?.[key];
    if (!s) return '';
    const px = html`<span class="ws-px">${s.side} px</span>`;
    if (s.upscaled) {
      return html`<span class="chip ws-mark ws-up-chip" data-tip="Апскейлено ×${m.upscaled?.scale || u.scale} (${m.upscaled?.model || u.model}) — сторінка ${s.side}×${s.side} px">${ic('sparkle', 'icon-s')}<span>×${m.upscaled?.scale || u.scale}</span><i class="ws-sep"></i>${px}</span>`;
    }
    if (s.big) return html`<span class="chip ws-mark ws-up-chip" data-tip="Картинка вже велика — сторінка ${s.side} px (від ${u.big} px вистачає для друку), апскейл не потрібен">${ic('check', 'icon-s')}${px}</span>`;
    if (s.recut) return html`<span class="chip ws-mark ws-up-chip dim" data-tip="Сторінка ${s.side} px, а оригінал у папці вже ${s.original} px — «Перерізати з великих оригіналів»">${px}<i class="ws-sep"></i><span>оригінал ${s.original}</span></span>`;
    return html`<span class="chip ws-mark ws-up-chip dim" data-tip="Ще не апскейлено — сторінка ${s.side} px">${px}</span>`;
  }

  /** «Апскейлити ще раз» among a picture's tools — while upscaling is on and Upscayl is there. */
  function upBtn(key, m = {}) {
    const u = book().upscale;
    if (!u?.on || !u.available || u.current?.key === key || u.queue.includes(key) || u.sides?.[key]?.big) return '';
    const tip = u.sides?.[key]?.recut ? 'Перерізати з великого оригіналу' : m.upscaled ? 'Апскейлити ще раз (з оригіналу)' : 'Апскейлити ×2';
    return ib('sparkle', tip, `data-act="upscale-row" ${attr('data-key', key)}`, { cls: 'sm' });
  }

  function marks(r, variant = '') {
    const m = r.marks || {};
    const chips = [];
    chips.push(upChip(slot(r.key, variant), m));
    if (m.mirrored) chips.push(html`<span class="chip ws-mark">${ic('mirror', 'icon-s')}віддзеркалено</span>`);
    if (m.cut) chips.push(html`<span class="chip chip-amber ws-mark" data-tip="${m.source ? `Картинка ${m.source[0]}×${m.source[1]}` : ''}">${ic('alert', 'icon-s')}${CUT[m.cut] || m.cut}</span>`);
    return chips.some(Boolean) ? html`<div class="ws-marks">${chips}</div>` : '';
  }

  function placeholder(r, variant, half = null) {
    const what = r.kind === 'spread' ? 'розворот 2:1' : 'сторінку';
    return html`<button type="button" class="ws-ph" data-act="pick" data-key="${r.key}" data-variant="${variant}">
      ${half === null ? html`<span class="ws-half num">${r.pages[0]}</span><span class="ws-half num">${r.pages[1]}</span>` : html`<span class="ws-half ws-one num">${half}</span>`}
      <span class="ws-ph-text"><span class="drop-ico">${ic('upload')}</span><b>Перетягніть ${what}</b><span>або клацніть, щоб обрати файл</span>
        ${r.kind === 'spread' && r.mirrored ? html`<span class="ws-will-flip">${ic('mirror', 'icon-s')}віддзеркалиться</span>` : ''}</span></button>`;
  }

  function frame(r, variant = '') {
    const waiting = waitingFor(id, r.key, variant) ? waitCover('Чекаю картинку з «Завантажень»…') : '';
    const drop = (inside) => html`<div class="ws-drop" data-drop="${r.key}" data-variant="${variant}">${inside}${busyCover(r.key)}${waiting}</div>`;
    if (!r.pictures.length) {
      if (r.kind === 'spread') return html`<div class="ws-frame">${drop(placeholder(r, variant))}</div>`;
      const page = drop(placeholder(r, variant, r.pages[0]));
      const endpaper = html`<div class="ws-endpaper"><span>форзац</span></div>`;
      return html`<div class="ws-frame ws-single">${r.key === 'page1' ? html`${endpaper}${page}` : html`${page}${endpaper}`}</div>`;
    }
    const page = (name, i) => html`<div class="ws-page">
      <img data-fade loading="lazy" decoding="async" alt="${r.label}" src="${pic('pictures', name, 900, variant)}" data-act="zoom" data-key="${r.key}" data-part="${i}">
      ${saveBtn('pictures', name, variant, `Зберегти сторінку ${name.replace(/\.\w+$/, '')} як…`)}</div>`;
    const tools = html`<div class="img-actions">
      ${ib('expand', 'Переглянути', `data-act="zoom" ${attr('data-key', r.key)}`, { cls: 'sm' })}
      ${r.kind === 'spread' ? ib('mirror', r.marks?.mirrored ? 'Віддзеркалено — клацніть, щоб повернути' : 'Віддзеркалити розворот', `data-act="flip" ${attr('data-key', r.key)} ${attr('data-variant', variant)}`, { cls: `sm ${r.marks?.mirrored ? 'on' : ''}` }) : ''}
      ${variant ? '' : ib('copy', r.kind === 'spread' ? 'Копіювати розворот як картинку (як його зробив Gemini) — наприклад, агенту 6 як найкращий кадр' : 'Копіювати сторінку як картинку', `data-act="copy-picture" ${attr('data-key', r.key)}`, { cls: 'sm' })}
      ${upBtn(slot(r.key, variant), r.marks)}
      ${r.original && !variant ? ib('imageDown', 'Зберегти оригінал як…', `data-act="save" data-area="originals" ${attr('data-name', r.original)} data-variant=""`, { cls: 'sm' }) : ''}
      ${ib('upload', 'Замінити файлом', `data-act="pick" ${attr('data-key', r.key)} ${attr('data-variant', variant)}`, { cls: 'sm' })}
      ${ib('trash', 'Прибрати картинку', `data-act="remove" ${attr('data-key', r.key)} ${attr('data-variant', variant)}`, { cls: 'sm danger' })}</div>`;
    if (r.kind === 'spread') {
      return html`<div class="ws-frame">${drop(html`<div class="ws-art ws-pairart">${r.pictures.map(page)}<div class="gutter"></div>${marks(r, variant)}${tools}</div>`)}</div>`;
    }
    const art = drop(html`<div class="ws-art">${page(r.pictures[0], 0)}${marks(r, variant)}${tools}</div>`);
    const endpaper = html`<div class="ws-endpaper"><span>форзац</span></div>`;
    return html`<div class="ws-frame ws-single">${r.key === 'page1' ? html`${endpaper}${art}` : html`${art}${endpaper}`}</div>`;
  }

  function genButton(r, variant = '', label = '') {
    if (!r.prompt) return '';
    if (waitingFor(id, r.key, variant)) return waitChip('чекаю картинку');
    const again = r.pictures.length > 0;
    // A spread of a book with a hero: the hero goes first, then the prompt (the owner, 27.09.2026).
    const hero = r.kind === 'spread' && !variant && book().steps.find((s) => s.key === 'hero')?.thumb;
    const what = hero ? 'У буфер герой, потім промпт — Ctrl+V у Chrome сам перемикає'
      : r.key === 'cover' && !variant ? 'У буфер референс, схема, потім промпт — Ctrl+V у Chrome сам перемикає' : 'Промпт — у буфер';
    // Quiet: up to sixteen empty rows each shouting «Генерувати» read as sixteen next steps; the loud one is «Генерувати всю книгу».
    return html`<button class="btn btn-sm" data-act="gen" data-key="${r.key}" data-variant="${variant}"
      data-tip="${again ? `Згенерувати ще раз — нова картинка замінить цю (стара піде в .replaced). ${what}` : `${what}; Майстерня чекає картинку з «Завантажень»`}">${ic(again ? 'regenerate' : 'generate')}${label || (again ? 'Ще раз' : 'Генерувати')}</button>`;
  }

  function promptBlock(r, variant = '', title = 'Промпт') {
    const key = `${variant}/${r.key}`;
    const long = r.prompt.split('\n').length > 3;
    const open = mem.open.has(key);
    return html`<div class="ws-block ws-prompt">
      <div class="ws-block-head"><span class="eyebrow">${title}</span><span class="spacer"></span>
        ${r.prompt ? ib('copy', 'Скопіювати промпт', `data-act="copy" data-what="prompt" ${attr('data-key', r.key)} ${attr('data-variant', variant)}`, { cls: 'sm' }) : ''}</div>
      ${r.prompt ? html`<pre class="ws-body ws-mono ${long && !open ? 'clamp' : ''}">${r.prompt}</pre>
        ${long ? html`<button class="ws-more" data-act="whole-prompt" data-key="${key}">${open ? 'Згорнути' : 'Весь промпт'}</button>` : ''}`
        : html`<div class="ws-body empty-text">${r.key === 'cover' ? 'Промпту ще немає — його напише агент 6, коли розвороти будуть готові.' : 'Промпту ще немає — його напише агент.'}</div>`}
    </div>`;
  }

  function textBlock(r) {
    return html`<div class="ws-block ws-text">
      <div class="ws-block-head"><span class="eyebrow">${r.key === 'cover' ? 'Назва на обкладинці' : 'Текст'}</span><span class="spacer"></span>
        ${r.text ? ib('copy', 'Скопіювати текст', `data-act="copy" data-what="text" ${attr('data-key', r.key)} data-variant=""`, { cls: 'sm' }) : ''}</div>
      ${r.text ? html`<div class="ws-body">${highlightTokens(r.text)}</div>` : html`<div class="ws-body empty-text">Тексту ще немає.</div>`}
    </div>`;
  }

  function rowCard(r, variant = '') {
    return html`<section class="ws-row ${waitingFor(id, r.key, variant) ? 'waiting' : ''}" id="row-${r.key}">
      <div class="ws-row-head"><span class="ws-row-label">${r.label}</span><span class="ws-row-act">${genButton(r, variant)}</span></div>
      ${promptBlock(r, variant, variant ? 'Промпт заміни героя' : 'Промпт')}
      ${frame(r, variant)}
      ${variant ? '' : textBlock(r)}
    </section>`;
  }

  return { saveBtn, waitCover, busyCover, genButton, promptBlock, textBlock, rowCard, upChip, upBtn };
}
