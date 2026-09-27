// A Workshop book's rows drawn: a spread or a page with its prompt, its frame (the picture, or the place to drop
// one) and its text — and the small parts the cover's card shares (out of workshop-book.js on 27.09.2026).
import { html, ic, ib, highlightTokens } from '../lib.js';
import { picture } from '../workshop-bits.js';
import { waitingFor } from '../workshop-live.js';

const CUT = { sides: 'обрізано з боків', 'top-bottom': 'обрізано зверху й знизу' };
export const waitChip = (text) => html`<span class="chip chip-accent"><span class="ws-pulse"></span>${text}</span>`;

/** The rows of one open book: `book()` — the book as it is now, `mem` — what the page remembers of it (the
 *  prompts shown whole), `uploading` — a drop's key → the share uploaded. */
export function rowTemplates({ id, book, mem, uploading }) {
  const pic = (area, name, w, variant) => picture(book(), area, name, w, variant);

  const saveBtn = (area, name, variant, tip) => html`<button type="button" class="ws-save" data-act="save" data-area="${area}" data-name="${name}" data-variant="${variant || ''}" aria-label="${tip}" data-tip="${tip}">${ic('download')}</button>`;
  const waitCover = (text) => html`<div class="ws-wait"><span class="ws-pulse"></span>${text}</div>`;
  const busyCover = (key) => (uploading.has(key) ? html`<div class="busy-overlay"><div class="ws-up"><i data-up="${key}"></i></div></div>` : '');

  function marks(r) {
    const m = r.marks || {};
    const chips = [];
    if (m.mirrored) chips.push(html`<span class="chip ws-mark">${ic('mirror', 'icon-s')}віддзеркалено</span>`);
    if (m.cut) chips.push(html`<span class="chip chip-amber ws-mark" data-tip="${m.source ? `Картинка ${m.source[0]}×${m.source[1]}` : ''}">${ic('alert', 'icon-s')}${CUT[m.cut] || m.cut}</span>`);
    return chips.length ? html`<div class="ws-marks">${chips}</div>` : '';
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
      <img data-fade alt="${r.label}" src="${pic('pictures', name, 900, variant)}" data-act="zoom" data-key="${r.key}" data-part="${i}">
      ${saveBtn('pictures', name, variant, `Зберегти сторінку ${name.replace(/\.\w+$/, '')} як…`)}</div>`;
    const tools = html`<div class="img-actions">
      ${variant ? '' : ib('expand', 'Переглянути', `data-act="zoom" data-key="${r.key}"`, { cls: 'sm' })}
      ${r.kind === 'spread' ? ib('mirror', r.marks?.mirrored ? 'Віддзеркалено — клацніть, щоб повернути' : 'Віддзеркалити розворот', `data-act="flip" data-key="${r.key}" data-variant="${variant}"`, { cls: `sm ${r.marks?.mirrored ? 'on' : ''}` }) : ''}
      ${variant ? '' : ib('copy', r.kind === 'spread' ? 'Копіювати розворот як картинку (як його зробив Gemini) — наприклад, агенту 6 як найкращий кадр' : 'Копіювати сторінку як картинку', `data-act="copy-picture" data-key="${r.key}"`, { cls: 'sm' })}
      ${r.original && !variant ? ib('imageDown', 'Зберегти оригінал як…', `data-act="save" data-area="originals" data-name="${r.original}" data-variant=""`, { cls: 'sm' }) : ''}
      ${ib('upload', 'Замінити файлом', `data-act="pick" data-key="${r.key}" data-variant="${variant}"`, { cls: 'sm' })}
      ${ib('trash', 'Прибрати картинку', `data-act="remove" data-key="${r.key}" data-variant="${variant}"`, { cls: 'sm danger' })}</div>`;
    if (r.kind === 'spread') {
      return html`<div class="ws-frame">${drop(html`<div class="ws-art ws-pairart">${r.pictures.map(page)}<div class="gutter"></div>${marks(r)}${tools}</div>`)}</div>`;
    }
    const art = drop(html`<div class="ws-art">${page(r.pictures[0], 0)}${marks(r)}${tools}</div>`);
    const endpaper = html`<div class="ws-endpaper"><span>форзац</span></div>`;
    return html`<div class="ws-frame ws-single">${r.key === 'page1' ? html`${endpaper}${art}` : html`${art}${endpaper}`}</div>`;
  }

  function genButton(r, variant = '', label = '') {
    if (!r.prompt) return '';
    if (waitingFor(id, r.key, variant)) return waitChip('чекаю картинку');
    const again = r.pictures.length > 0;
    // A spread of a book with a hero: the hero goes first, then the prompt (the owner, 27.09.2026).
    const hero = r.kind === 'spread' && !variant && book().steps.find((s) => s.key === 'hero')?.thumb;
    const what = hero ? 'У буфер герой, потім промпт — Ctrl+V у Chrome сам перемикає' : 'Промпт — у буфер';
    return html`<button class="btn btn-sm ${again ? '' : 'btn-primary'}" data-act="gen" data-key="${r.key}" data-variant="${variant}"
      data-tip="${again ? `Згенерувати ще раз — нова картинка замінить цю (стара піде в .replaced). ${what}` : `${what}; Майстерня чекає картинку з «Завантажень»`}">${ic(again ? 'regenerate' : 'generate')}${label || (again ? 'Ще раз' : 'Генерувати')}</button>`;
  }

  function promptBlock(r, variant = '', title = 'Промпт') {
    const key = `${variant}/${r.key}`;
    const long = r.prompt.split('\n').length > 7;
    const open = mem.open.has(key);
    return html`<div class="ws-block ws-prompt">
      <div class="ws-block-head"><span class="eyebrow">${title}</span><span class="spacer"></span>
        ${r.prompt ? ib('copy', 'Скопіювати промпт', `data-act="copy" data-what="prompt" data-key="${r.key}" data-variant="${variant}"`, { cls: 'sm' }) : ''}</div>
      ${r.prompt ? html`<pre class="ws-body ws-mono ${long && !open ? 'clamp' : ''}">${r.prompt}</pre>
        ${long ? html`<button class="ws-more" data-act="whole-prompt" data-key="${key}">${open ? 'Згорнути' : 'Показати весь промпт'}</button>` : ''}`
        : html`<div class="ws-body empty-text">${r.key === 'cover' ? 'Промпту ще немає — його напише агент 6, коли розвороти будуть готові.' : 'Промпту ще немає — його напише агент.'}</div>`}
    </div>`;
  }

  function textBlock(r) {
    return html`<div class="ws-block ws-text">
      <div class="ws-block-head"><span class="eyebrow">${r.key === 'cover' ? 'Назва на обкладинці' : 'Текст'}</span><span class="spacer"></span>
        ${r.text ? ib('copy', 'Скопіювати текст', `data-act="copy" data-what="text" data-key="${r.key}" data-variant=""`, { cls: 'sm' }) : ''}</div>
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

  return { saveBtn, waitCover, busyCover, genButton, promptBlock, textBlock, rowCard };
}
