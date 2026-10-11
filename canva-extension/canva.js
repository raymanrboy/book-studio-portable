/* Book Studio → Canva: drives the Canva editor the way a person would — the Ukrainian interface, found by its
   accessibility labels. Runs in the page's own world (manifest "world": "MAIN"): Canva's file chooser has to be
   answered from there. Everything here was tried by hand on the owner's template first (wiki: features/canva-extension.md). */
(function () {
  'use strict';
  const NS = (window.BSCanva = window.BSCanva || {});

  // What we look for on the screen. If Canva renames something, this is the one place to change.
  const UI = {
    pageThumb: 'Сторінка: ',          // the page strip: «Сторінка: 3», «Сторінка: 31 – Cover»
    pageGroup: 'Сторінка ',           // the accessibility layer's page: «Сторінка 3»
    frameRole: 'Елемент рамки',
    emptyFrame: 'Заповнювач',
    textRole: 'Елемент тексту',
    replace: 'Замінити',
    uploadFiles: 'Передати файли',
    closePanel: /^Закрити/,
    navElements: 'Елементи',
    navText: 'Текст',
    navUploads: 'Передані',
    addTextBox: 'Додати текстове поле',
    fontButton: 'Перемкніть шрифт',     // «Перемкніть шрифт, поточний шрифт: Schoolbell»
    fontSize: 'Розмір шрифту',
    sphereTile: 'Додати на полотно Yellow gradient sphere',
    sphereName: 'Yellow gradient sphere',
    colorButton: 'поточний колір',          // the selected element's colour: «поточний колір: …»
    spacingButton: 'Розширені параметри',  // the text toolbar's spacing popover
    lineSpacing: 'Відстань між рядками',
    tracking: 'Трекінг',
    position: 'Розташування',              // the toolbar's position panel: its «По центру» is vertical, «У центрі» horizontal
    alignMiddle: 'По центру',
    alignCentre: 'У центрі',
  };
  // The owner's text look: Schoolbell; 110 on the dedication and the afterword (pages 1 and 30), 100 on the spreads;
  // the line spacing 2.04.
  // The afterword (page 30) keeps Canva's own line spacing (the owner, 2026-10-08).
  const STYLE = { font: 'Schoolbell', size: '100', endSize: '110', endPages: [1, 30], lineSpacing: '2.04', ownSpacingPages: [30], tracking: '50',
    sphereColor: '#ffffff' };
  const sizeOf = n => (STYLE.endPages.includes(n) ? STYLE.endSize : STYLE.size);
  const spacingOf = n => (STYLE.ownSpacingPages.includes(n) ? null : STYLE.lineSpacing);  // null — left as it is
  const lookOf = n => `${STYLE.font} ${sizeOf(n)}, трекінг ${STYLE.tracking}${spacingOf(n) ? `, рядки ${spacingOf(n)}` : ''}`;
  NS.sizeOf = sizeOf;
  NS.spacingOf = spacingOf;
  const PLACEHOLDER_IMG = 'static.canva.com/web/images/';
  NS.UI = UI;
  NS.STYLE = STYLE;

  class Stopped extends Error {}
  let stopping = false;
  let runDesign = null;   // the design a run started on — another one opened in the tab stops it
  NS.stop = () => { stopping = true; };

  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const shown = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const norm = s => String(s || '').replace(/\s+/g, ' ').trim().toLowerCase();

  async function waitFor(fn, what, timeout = 15000) {
    const t0 = Date.now();
    for (;;) {
      if (stopping) throw new Stopped();
      if (runDesign && location.pathname.split('/')[2] !== runDesign) throw new Error('Відкрито інший дизайн — розкладку зупинено');
      const v = fn();
      if (v) return v;
      if (Date.now() - t0 > timeout) throw new Error('Не дочекався: ' + what);
      await sleep(150);
    }
  }

  const buttonByText = text => $$('button').find(b => shown(b) && b.innerText.trim() === text);
  const buttonByLabel = test => $$('button[aria-label]').find(b => shown(b) && test(b.getAttribute('aria-label')));
  const railButton = label => $$('button, [role=tab], [role=button]')
    .find(b => shown(b) && b.getBoundingClientRect().x < 60 && b.innerText.trim() === label);

  async function press(target, x, y) {
    const base = { bubbles: true, cancelable: true, composed: true, clientX: x, clientY: y, button: 0,
      pointerId: 1, pointerType: 'mouse', isPrimary: true, view: window, detail: 1 };
    // down and up at once: with any gap, a real mouse moving at that moment made Canva drag the frame (the owner, 2026-10-08)
    target.dispatchEvent(new PointerEvent('pointerdown', { ...base, buttons: 1 }));
    target.dispatchEvent(new MouseEvent('mousedown', { ...base, buttons: 1 }));
    target.dispatchEvent(new PointerEvent('pointerup', { ...base, buttons: 0 }));
    target.dispatchEvent(new MouseEvent('mouseup', { ...base, buttons: 0 }));
    target.dispatchEvent(new MouseEvent('click', { ...base, buttons: 0 }));
  }

  function pressKey(target, key, code, keyCode) {
    for (const type of ['keydown', 'keyup']) {
      target.dispatchEvent(new KeyboardEvent(type, { key, code, keyCode, which: keyCode, bubbles: true, cancelable: true, composed: true }));
    }
  }

  // Types into a focused field the way the keyboard does (React ignores a plain `value =`) — never anywhere else.
  function typeInto(input, text) {
    input.focus();
    input.select();
    if (document.activeElement !== input) throw new Error('Поле не взяло фокус — нічого не вписано');
    document.execCommand('insertText', false, text);
  }

  // ---- Canva's file chooser: the next one Canva opens gets these files instead of a dialog.
  let pendingFiles = null;
  let pendingTimer = 0;
  const nativeClick = HTMLInputElement.prototype.click;
  HTMLInputElement.prototype.click = function () {
    if (this.type === 'file' && pendingFiles) {
      const files = pendingFiles;
      const input = this;
      pendingFiles = null;
      setTimeout(() => {
        const dt = new DataTransfer();
        files.forEach(f => dt.items.add(f));
        input.files = dt.files;
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }, 0);
      return;
    }
    return nativeClick.call(this);
  };

  // ---- Pages
  const thumbs = () => $$(`[role="button"][aria-label^="${UI.pageThumb}"]`);
  const thumbNumber = t => parseInt(t.getAttribute('aria-label').slice(UI.pageThumb.length), 10);

  async function findThumb(n) {
    for (let i = 0; i < 40; i++) {
      const all = thumbs();
      const hit = all.find(t => thumbNumber(t) === n);
      if (hit) return hit;
      if (!all.length) throw new Error('Не бачу стрічки сторінок унизу — відкрийте «Сторінки»');
      const nums = all.map(thumbNumber).filter(Number.isFinite);
      if (!nums.length) throw new Error('Не впізнаю мініатюр сторінок');
      const edge = all.find(t => thumbNumber(t) === (n > Math.max(...nums) ? Math.max(...nums) : Math.min(...nums)));
      edge.scrollIntoView({ block: 'nearest', inline: 'center' });  // the strip draws only what is in view
      await sleep(250);
    }
    throw new Error(`У дизайні немає сторінки ${n}`);
  }

  // Page n is found through Canva's accessibility layer («Сторінка 3»), which sits inside the drawn page; the page's
  // `data-page-id` is Canva's own id, not its number (0 for page 1 in the owner's Chrome, 2026-10-08).
  function pageGroup(n) {
    const re = new RegExp('^' + UI.pageGroup + n + '(?!\\d)');
    return $$('[id^="accessibility_dom"][role="group"]').find(g => re.test(g.getAttribute('aria-label') || '')) || null;
  }
  const pageEl = n => { const g = pageGroup(n); return g ? g.closest('[data-page-id]') : null; };

  // The page Canva has open, from the counter in the bottom bar («7 з 32»); null when it isn't seen.
  function currentPage() {
    const c = $$('span, div, p').find(el => el.childElementCount === 0 && /^\d+\s+з\s+\d+$/.test(el.textContent.trim()) && shown(el)
      && el.getBoundingClientRect().y > innerHeight - 120);
    return c ? parseInt(c.textContent, 10) : null;
  }

  // Opens page n with nothing on it selected (the page itself is). Also how a selection is dropped. A click lost while
  // Canva is busy is tried once more.
  // No frame or text selected (a page, nothing, or something harmless like a group): what adding the sphere or a text needs.
  const nothingAtRisk = () => !['frame', 'text'].includes(selection());

  async function openPage(n) {
    for (let attempt = 0; ; attempt++) {
      const t = await findThumb(n);
      t.scrollIntoView({ block: 'nearest', inline: 'center' });
      t.click();
      try {
        await waitFor(() => pageEl(n) && pageModel(n).length && [n, null].includes(currentPage()) && nothingAtRisk(), `сторінку ${n}`, 8000);
        break;
      } catch (e) {
        if (e instanceof Stopped) throw e;
        if (attempt) throw new Error(`Не дочекався сторінки ${n}: ${pageReport(n)}`);
      }
    }
    await sleep(150);
  }

  // What was seen while waiting for a page — the failing sign is in the message, so a screenshot of it is enough.
  function pageReport(n) {
    const groups = $$('[id^="accessibility_dom"][role="group"]').map(g => g.getAttribute('aria-label')).slice(0, 3);
    const bar = $$('button').filter(b => { const r = b.getBoundingClientRect(); return r.width > 0 && r.x > 60 && r.y > 30 && r.y < 170; })
      .map(b => (b.innerText.trim() || b.getAttribute('aria-label') || '?').slice(0, 14)).slice(0, 5);
    const ids = $$('[data-page-id]').map(p => p.getAttribute('data-page-id')).slice(0, 4);
    return [
      `сторінки на екрані [${ids.join(', ') || '—'}]`,
      `шари [${groups.join(', ') || '—'}], на цій ${pageModel(n).length}`,
      `лічильник ${currentPage() === null ? '—' : currentPage()}`,
      `виділення ${selection()} [${bar.join(' | ')}]`,
      `вікно ${innerWidth}×${innerHeight}`,
    ].join('; ');
  }

  // What is selected, read from the toolbar above the page: a page has its duration («5.0с»), a frame «Замінити»,
  // a text the font button.
  function selection() {
    const bar = $$('button').filter(b => { const r = b.getBoundingClientRect(); return r.width > 0 && r.x > 60 && r.y > 30 && r.y < 170; });
    if (bar.some(b => /^\d+([.,]\d+)?\s*с$/.test(b.innerText.trim()))) return 'page';
    if (bar.some(b => b.innerText.trim() === UI.replace)) return 'frame';
    if (bar.some(b => (b.getAttribute('aria-label') || '').startsWith(UI.fontButton))) return 'text';
    return bar.length ? 'other' : 'none';
  }

  // The page's elements: the accessibility layer (role + label) matched in order to the drawn elements.
  function pageModel(n) {
    const group = pageGroup(n);
    const pg = group && group.closest('[data-page-id]');
    if (!pg) return [];
    const nodes = $$('[role]', group);
    const els = $$('div[id]', pg).filter(d => /^[A-Za-z0-9_-]{16}$/.test(d.id));
    return nodes.map((a, i) => ({
      role: a.getAttribute('aria-roledescription') || '',
      label: a.getAttribute('aria-label') || '',
      el: els.length === nodes.length ? els[i] : null,
    }));
  }

  const area = el => { const r = el.getBoundingClientRect(); return r.width * r.height; };

  // The biggest empty frame on the page, or null when every frame already has a picture.
  function emptyFrame(n) {
    const model = pageModel(n);
    let frames;
    if (model.length && model.every(m => m.el)) {
      frames = model.filter(m => m.role === UI.frameRole && m.label === UI.emptyFrame).map(m => m.el);
    } else {  // the layers didn't line up — fall back to Canva's placeholder picture
      const els = $$('div[id]', pageEl(n)).filter(d => /^[A-Za-z0-9_-]{16}$/.test(d.id));
      frames = els.filter(d => $$('img', d).some(i => i.src.includes(PLACEHOLDER_IMG)))
        .filter(d => !els.some(o => o !== d && d.contains(o) && $$('img', o).some(i => i.src.includes(PLACEHOLDER_IMG))));
    }
    return frames.sort((a, b) => area(b) - area(a))[0] || null;
  }

  // Still Canva's placeholder? Read from the layers, or — when they didn't line up — from the frame's own picture.
  function isEmpty(n, el) {
    const model = pageModel(n);
    if (model.length && model.every(m => m.el)) return model.some(m => m.el.id === el.id && m.label === UI.emptyFrame);
    const now = document.getElementById(el.id) || el;
    return $$('img', now).some(i => i.src.includes(PLACEHOLDER_IMG));
  }

  // The page's text box that starts like `text` (the newest one if several), or null.
  function textBox(n, text) {
    const first = norm(text.split('\n').find(l => l.trim())).slice(0, 40);
    const model = pageModel(n);
    const hits = model.length && model.every(m => m.el)
      ? model.filter(m => m.role === UI.textRole && norm(m.label).startsWith(first)).map(m => m.el)
      : $$('div[id]', pageEl(n)).filter(d => /^[A-Za-z0-9_-]{16}$/.test(d.id) && d.querySelector('p') && norm(d.innerText).startsWith(first));
    return hits[hits.length - 1] || null;
  }

  const count = (n, test) => pageModel(n).filter(test).length;

  // A sphere this extension put: on the page itself, not inside a group (the old templates' own sphere sits in one —
  // an element in a group has the group's 16-letter id above it).
  const ELEMENT_ID = /^[A-Za-z0-9_-]{16}$/;
  const inGroup = el => { const up = el.parentElement && el.parentElement.closest('div[id]'); return Boolean(up && ELEMENT_ID.test(up.id)); };
  const looseSphere = m => m.label === UI.sphereName && !(m.el && inGroup(m.el));

  // ---- Side panels
  async function sidePanel(rail, ready, what) {
    if (ready()) return ready();
    for (let i = 0; i < 4; i++) {  // a click Canva swallows while busy (right after the sphere's colour) is made again soon
      const b = railButton(rail);
      if (!b) throw new Error(`Не бачу кнопки «${rail}» зліва`);
      b.click();
      try { return await waitFor(ready, what, 2000); } catch (e) { if (e instanceof Stopped) throw e; }
    }
    throw new Error('Не дочекався: ' + what);
  }

  async function closeSidePanel() {
    const b = $$('button[aria-label]').find(x => shown(x) && x.getBoundingClientRect().x < 450 && UI.closePanel.test(x.getAttribute('aria-label')));
    if (b) { b.click(); await sleep(200); }
  }

  // ---- The three things done to a page
  async function selectFrame(frame) {
    const img = frame.querySelector('img');
    const target = (img && img.parentElement && img.parentElement.parentElement) || frame.firstElementChild || frame;
    const r = frame.getBoundingClientRect();
    const x = Math.min(Math.max(r.x + r.width / 2, 1), innerWidth - 1);
    const y = Math.min(Math.max(r.y + r.height / 2, 1), innerHeight - 1);
    await press(target, x, y);  // straight at the frame: whatever lies on top of it (the cover's guides) is skipped
    await waitFor(() => selection() === 'frame', 'виділення рамки');
  }

  // Step 1 of a run: every picture into «Передані» at once — Canva uploads them side by side while the texts are made.
  async function uploadAll(files) {
    const upload = await sidePanel(UI.navUploads, () => buttonByText(UI.uploadFiles), 'кнопку «' + UI.uploadFiles + '»');
    clearTimeout(pendingTimer);
    pendingFiles = files;
    upload.click();
    pendingTimer = setTimeout(() => { pendingFiles = null; }, 5000);  // never answer a chooser the owner opens later
    await waitFor(() => files.some(f => tileNamed(f.name)), 'початку завантаження', 30000);
    uploadStarted = Date.now();
  }

  let uploadStarted = 0;
  const UPLOAD_LIMIT = 20 * 60000;  // one deadline for the whole batch, not ten minutes per page

  // An uploaded picture's tile (the names carry the run's mark, so no older upload is ever taken).
  const tileNamed = name => $$('[role="button"][aria-label]').find(t => t.getAttribute('aria-label') === name) || null;

  // The tile once Canva has the file: its local preview (data:/blob:) turns into Canva's own picture. The list draws only
  // what is in view: it is walked from the top down, and from the top again. A tile that was there and is gone — the
  // upload failed.
  async function readyTile(name) {
    const tiles = () => $$('[role="button"][aria-label]').filter(x => shown(x) && x.getBoundingClientRect().x < 450 && x.querySelector('img'));
    const first = tiles()[0];
    if (first) first.scrollIntoView({ block: 'start' });
    let polls = 0, seen = false, lastName = '';
    const left = Math.max(60000, UPLOAD_LIMIT - (Date.now() - uploadStarted));
    return waitFor(() => {
      const t = tileNamed(name);
      if (t) {
        seen = true;
        return /^https:/.test((t.querySelector('img') || {}).src || '') ? t : null;
      }
      if (seen) throw new Error(`Canva не прийняла файл ${name} (завантаження зникло)`);
      if (++polls % 4 === 0) {
        const all = tiles();
        const last = all[all.length - 1];
        const at = last ? last.getAttribute('aria-label') : '';
        if (last && at !== lastName) last.scrollIntoView({ block: 'end' });  // further down
        else if (all[0]) all[0].closest('[role="button"]').scrollIntoView({ block: 'start' });  // the end — from the top again
        lastName = at === lastName ? '' : at;
      }
      return null;
    }, 'завантаження ' + name, left);
  }

  // Step 3: the frame selected → «Замінити» → the uploaded tile → the picture fills the frame.
  async function putPicture(n, frame, file, say) {
    await selectFrame(frame);
    buttonByText(UI.replace).click();
    await waitFor(() => buttonByText(UI.uploadFiles), 'панель «Заміна»');
    say('чекаю завантаження');
    const tile = await readyTile(file.name);
    // a long wait: the frame must still be the one selected, or the picture would land loose on the page
    if (selection() !== 'frame' || !isEmpty(n, frame)) throw new Error('Рамка втратила виділення — картинку не вставлено, запустіть ще раз');
    say('вставляю');
    tile.click();
    await waitFor(() => !isEmpty(n, frame), 'картинку в рамці', 30000);
    await closeSidePanel();
  }

  async function addSphere(n) {
    const isSphere = m => m.label === UI.sphereName;
    const before = count(n, isSphere);
    const tile = await sidePanel(UI.navElements, () => $$(`[role="button"][aria-label^="${UI.sphereTile}"]`)[0],
      `«${UI.sphereName}» серед нещодавно використаних (додайте її один раз вручну)`);
    tile.click();
    await waitFor(() => count(n, isSphere) > before, 'сферу на сторінці');
  }

  // The sphere's picture by its middle pixel: 'white', 'other', 'none' (no picture drawn yet — Canva redraws it while
  // recolouring) or 'unknown' (its pixels can't be read).
  async function sphereColor(el) {
    const img = el && el.querySelector('img');
    if (!img || !img.src) return 'none';
    try {
      const im = new Image();
      im.crossOrigin = 'anonymous';
      im.src = img.src;
      await im.decode();
      const c = document.createElement('canvas');
      c.width = im.naturalWidth;
      c.height = im.naturalHeight;
      const ctx = c.getContext('2d');
      ctx.drawImage(im, 0, 0);
      const [r, g, b] = ctx.getImageData(c.width >> 1, c.height >> 1, 1, 1).data;
      return r > 235 && g > 235 && b > 235 ? 'white' : 'other';  // Canva's white sphere reads 248
    } catch (_) { return 'unknown'; }
  }

  // The owner's sphere is white: the sphere put by the extension gets «поточний колір» → #ffffff (2026-10-08).
  // `fresh`: the sphere was just put — it is yellow and already selected (a press on a selected picture unselects it,
  // tried live). `wait`: wait for Canva's recoloured picture — ~5 s (measured); a run doesn't — it goes on to the text and
  // looks at the sphere again in step 3 (one sphere stayed yellow in the owner's run).
  async function whiten(n, fresh, wait) {
    const sphere = () => { const s = pageModel(n).filter(looseSphere); return s.length ? s[s.length - 1].el : null; };
    const el = await waitFor(sphere, 'сферу на сторінці', 6000);
    if (!fresh && await sphereColor(el) === 'white') return false;  // 'unknown' is recoloured too: #ffffff on white does no harm
    if (selection() !== 'frame') {
      const img = el.querySelector('img');
      const target = (img && img.parentElement && img.parentElement.parentElement) || el;
      const r = el.getBoundingClientRect();
      await press(target, Math.min(Math.max(r.x + r.width / 2, 1), innerWidth - 1), Math.min(Math.max(r.y + r.height / 2, 1), innerHeight - 1));
    }
    await waitFor(() => selection() === 'frame', 'виділення сфери');  // a picture is selected (never the text above it)
    (await waitFor(() => buttonByLabel(l => l.startsWith(UI.colorButton)), 'кнопку кольору сфери')).click();
    await sleep(350);  // the panel «Колір» may still be the previous page's — let it turn to this sphere
    (await waitFor(() => $$(`button[aria-label="${STYLE.sphereColor}"]`).find(b => shown(b) && b.getBoundingClientRect().x < 450),
      'білий колір у панелі «Колір»')).click();
    if (!wait) return true;
    for (let i = 0; i < 30; i++) {
      if (stopping) throw new Stopped();
      await sleep(500);
      if (['white', 'unknown'].includes(await sphereColor(sphere()))) return true;
    }
    throw new Error('Сфера не стала білою');
  }

  // Step 3's look at a text page's sphere (the page is open for its picture anyway): one reading of it; one that stayed
  // yellow (page 24 in the owner's run) is recoloured, this time waiting for Canva.
  async function checkWhite(n) {
    const s = pageModel(n).filter(looseSphere);
    if (!s.length || await sphereColor(s[s.length - 1].el) !== 'other') return false;
    await whiten(n, false, true);
    await openPage(n);
    return true;
  }

  const editing = () => Boolean(document.activeElement && document.activeElement.classList.contains('ql-editor'));
  const fontButton = () => buttonByLabel(l => l.startsWith(UI.fontButton));
  const fontNow = () => { const b = fontButton(); return b ? (b.getAttribute('aria-label') || '').split(': ').pop() : ''; };
  const sizeField = () => $$(`input[aria-label="${UI.fontSize}"]`).find(shown);

  // The whole text box selected (not typed in): what font and size then apply to.
  async function selectText(box) {
    const span = box.querySelector('span') || box;
    const r = span.getBoundingClientRect();
    await press(span, r.x + Math.min(r.width / 2, 40), r.y + r.height / 2);
    await waitFor(() => selection() === 'text' && !editing(), 'виділення тексту');
    await sleep(150);  // the toolbar catches up with the box's font and size
  }

  // The font button opens the panel «Шрифт»: the font's own button is there when it was used lately; else its search.
  async function setFont(name) {
    if (fontNow() === name) return;
    fontButton().click();
    const inPanel = el => el.getBoundingClientRect().x < 450;
    const fontHit = () => $$('button[aria-label]').find(b => shown(b) && inPanel(b) && b.getAttribute('aria-label') === name);
    const search = () => $$('input[type="search"]').find(i => shown(i) && inPanel(i));
    await waitFor(() => fontHit() || search(), 'панель «Шрифт»');
    if (!fontHit()) typeInto(search(), name);
    (await waitFor(fontHit, `шрифт ${name}`)).click();
    await waitFor(() => fontNow() === name, `шрифт ${name}`);
  }

  const sameNumber = (a, b) => Math.abs(parseFloat(String(a).replace(',', '.')) - parseFloat(b)) < 0.001;

  // The size field (a number field): a script can't select it, Canva selects it on a click
  // into it — so click, wait, type, and press Enter only when the field reads exactly the number (else Escape, again).
  // A box of mixed sizes shows an empty size field.
  async function typeNumber(field, value, what) {
    for (let attempt = 0; attempt < 4; attempt++) {
      const input = await waitFor(field, what);
      if (sameNumber(input.value, value)) return;
      const r = input.getBoundingClientRect();
      input.focus();
      await press(input, r.x + r.width / 2, r.y + r.height / 2);
      await sleep(300 + attempt * 300);
      if (document.activeElement !== input) continue;  // never type into whatever else has the focus
      document.execCommand('insertText', false, value);
      if (sameNumber(input.value, value)) { pressKey(input, 'Enter', 'Enter', 13); await sleep(300); return; }
      pressKey(input, 'Escape', 'Escape', 27);
      await sleep(300);
    }
    throw new Error(`Не вдалося вписати ${what} ${value}`);
  }

  // The tracking and the line spacing live in the spacing popover («Розширені параметри»): each is a number field next to
  // its words, with a slider beside it.
  // The field is the number box nearest under its words (walking up the boxes found the neighbour's field — tried live).
  function popoverField(label) {
    const words = $$('div, span, label, p').find(el => shown(el) && el.childElementCount === 0 && el.textContent.trim() === label);
    if (!words) return null;
    const top = words.getBoundingClientRect().top;
    const below = $$('input').filter(i => shown(i) && i.type !== 'range' && i.getBoundingClientRect().top >= top - 4
      && Math.abs(i.getBoundingClientRect().left - words.getBoundingClientRect().left) < 400);
    below.sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top);
    return below[0] || null;
  }
  const lineField = () => popoverField(UI.lineSpacing);
  async function openSpacing() {
    if (lineField()) return;
    buttonByLabel(l => l.startsWith(UI.spacingButton)).click();
    await waitFor(lineField, 'поле «' + UI.lineSpacing + '»', 6000);
  }

  // Set by the slider (the number beside it shows a typed value, but Canva ignores what a script types into it): the
  // slider's value and its input event, the way React hears a drag.
  async function setSlider(label, value) {
    await openSpacing();
    const field = () => popoverField(label);
    if (!field()) throw new Error(`Не бачу поля «${label}»`);
    if (sameNumber(field().value, value)) return;
    // its slider is the one in the same row (walking up the boxes found the tracking slider for both — tried live)
    const middle = el => { const r = el.getBoundingClientRect(); return r.top + r.height / 2; };
    const slider = $$('input[type="range"]').filter(shown)
      .sort((a, b) => Math.abs(middle(a) - middle(field())) - Math.abs(middle(b) - middle(field())))[0];
    if (!slider || Math.abs(middle(slider) - middle(field())) > 30) throw new Error(`Не бачу повзунка «${label}»`);
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(slider, value);
    slider.dispatchEvent(new Event('input', { bubbles: true }));
    slider.dispatchEvent(new Event('change', { bubbles: true }));
    await waitFor(() => field() && sameNumber(field().value, value), `«${label}» ${value}`, 4000);
  }

  // Is the selected box already in the owner's look?
  async function looksRight(size, spacing) {
    if (fontNow() !== STYLE.font || !sameNumber((sizeField() || {}).value, size)) return false;
    await openSpacing();
    const tracking = popoverField(UI.tracking);
    if (!tracking || !sameNumber(tracking.value, STYLE.tracking)) return false;
    return !spacing || sameNumber(lineField().value, spacing);
  }

  // Font, size, tracking and line spacing on the whole box, then checked the way they were saved: the box selected again from
  // scratch. True when something had to change.
  async function styleText(n, text) {
    const size = sizeOf(n);
    const spacing = spacingOf(n);
    for (let attempt = 0; attempt < 3; attempt++) {
      await selectText(await waitFor(() => textBox(n, text), 'текст на сторінці'));
      if (await looksRight(size, spacing)) { await openPage(n); return attempt > 0; }
      await setFont(STYLE.font);
      await typeNumber(sizeField, size, 'розмір шрифту');
      await setSlider(UI.tracking, STYLE.tracking);
      if (spacing) await setSlider(UI.lineSpacing, spacing);
      await openPage(n);
    }
    throw new Error(`Не вдалося поставити ${lookOf(n)}`);
  }

  // A new text box is made one line high in the page's centre and grows downwards as the text and its size go in — so it
  // is put back in the middle of the page (the owner: «текст падає вниз»).
  async function centreText(n, text) {
    await selectText(await waitFor(() => textBox(n, text), 'текст на сторінці'));
    const toolbar = $$('button').find(b => shown(b) && b.innerText.trim() === UI.position && b.getBoundingClientRect().y < 170);
    if (!toolbar) throw new Error(`Не бачу кнопки «${UI.position}»`);
    toolbar.click();
    for (const label of [UI.alignMiddle, UI.alignCentre]) {
      const b = await waitFor(() => $$('button, [role=button]').find(x => shown(x) && x.getBoundingClientRect().x < 450
        && (x.getAttribute('aria-label') || x.innerText.trim()) === label), `кнопку «${label}»`);
      b.click();
      await sleep(250);
    }
    await closeSidePanel();
    await openPage(n);
  }

  async function addText(n, text) {
    const add = await sidePanel(UI.navText, () => buttonByText(UI.addTextBox), 'кнопку «' + UI.addTextBox + '»');
    add.click();
    await waitFor(editing, 'нове текстове поле');
    document.execCommand('selectAll');
    document.execCommand('insertText', false, text);  // a line break becomes a new line in Canva
    await sleep(200);
    await openPage(n);  // leaves the text box
    await styleText(n, text);
    await centreText(n, text);
  }

  // ---- One run, in three steps: 1) every picture into «Передані» at once, 2) the text pages — sphere and text — while
  // Canva uploads, 3) the pictures into the frames. report(page, state, note); report(null, 'progress', share).
  NS.run = async function (plan, pages, report) {
    stopping = false;
    runDesign = location.pathname.split('/')[2];
    const todo = plan.filter(p => pages.includes(p.page));
    const notes = {};
    const errors = {};
    const note = (n, text) => (notes[n] = notes[n] || []).push(text);
    const texts = todo.filter(p => p.text);
    const units = texts.length + todo.length + 1;
    let unit = 0;
    const step = () => report(null, 'progress', ++unit / units);
    // what an error or a stop interrupted is tidied up: the side panel closed, the page left unselected
    const tidy = async n => { try { await closeSidePanel(); if (n) await openPage(n); } catch (_) { /* as it is */ } };

    try {
      // 1 — the pictures to Canva, all at once
      const pics = todo.filter(p => p.picture);
      if (pics.length) {
        report(pics[0].page, 'work', `передаю в Canva ${pics.length} картинок`);
        await uploadAll(pics.map(p => p.picture));
        await closeSidePanel();
      }
      step();

      // 2 — the text pages, while the pictures upload
      for (const item of texts) {
        const n = item.page;
        const say = text => report(n, 'work', text);
        try {
          say('відкриваю');
          await openPage(n);
          // each part's seconds go into the page's note, so a slow part shows itself
          let t0 = Date.now();
          const took = [];
          const lap = label => { took.push(`${label} ${((Date.now() - t0) / 1000).toFixed(1)} с`); t0 = Date.now(); };
          if (textBox(n, item.text)) {  // there already — only its look made right, the sphere too
            say('текст уже є, перевіряю');
            if (count(n, looseSphere) && await whiten(n, false, false)) { note(n, 'сфера → біла'); await openPage(n); }
            lap('сфера');
            note(n, await styleText(n, item.text) ? `текст уже був → ${lookOf(n)}` : 'текст уже є');
            lap('текст');
          } else {
            // a sphere already there (a run stopped between the sphere and the text) is not added twice
            const fresh = !count(n, looseSphere);
            if (fresh) { say('сфера'); await addSphere(n); }
            lap('сфера');
            say('сфера біла');
            await whiten(n, fresh, false);  // no waiting for Canva's redraw — step 3 looks at the sphere again
            await openPage(n);  // nothing selected: with the sphere selected Canva put the new text under it (page 23)
            lap('білий');
            say('текст');
            await addText(n, item.text);
            lap('текст');
            note(n, 'сфера + текст');
          }
          note(n, took.join(', '));
          say(notes[n].join(' · '));
        } catch (e) {
          if (e instanceof Stopped) throw e;
          errors[n] = e.message || String(e);
          report(n, 'error', errors[n]);
          await tidy(n);
        }
        step();
      }

      // 3 — the pictures into the frames
      for (const item of todo) {
        const n = item.page;
        const say = text => report(n, 'work', text);
        try {
          if (item.picture) {
            say('відкриваю');
            await openPage(n);
            const frame = emptyFrame(n);
            const frames = count(n, m => m.role === UI.frameRole);
            if (frame) { await putPicture(n, frame, item.picture, say); await openPage(n); note(n, 'картинка'); }
            else if (frames || !pageModel(n).length) note(n, 'рамка вже з картинкою');
            else throw new Error('На сторінці немає рамки для картинки');
          } else note(n, 'немає картинки в pictures');
          if (item.text && !errors[n]) {
            if (!pageModel(n).length) await openPage(n);
            if (await checkWhite(n)) note(n, 'сфера перефарбована ще раз');
          }
          if (!item.text && item.textMissing) note(n, 'немає тексту в book-text.md');
          if (errors[n]) report(n, 'error', errors[n]);
          else report(n, 'done', (notes[n] || []).join(' · '));
        } catch (e) {
          if (e instanceof Stopped) throw e;
          errors[n] = [errors[n], e.message || String(e)].filter(Boolean).join(' · ');
          report(n, 'error', errors[n]);
          await tidy(n);
        }
        step();
      }
    } catch (e) {
      pendingFiles = null;
      runDesign = null;
      if (!(e instanceof Stopped)) { stopping = false; await tidy(currentPage()); throw e; }
      stopping = false;
      await tidy(currentPage());
      report(null, 'stopped', 'зупинено');
    }
    pendingFiles = null;
    stopping = false;
    runDesign = null;
    return { failed: Object.keys(errors).length };
  };
})();
