/* Book Studio → Canva: the panel in the Canva editor. It shows the book the way it is printed — the cover, then the
   spreads [endpaper | 1], [2 | 3] … [30 | endpaper] — each page lit by its state; the chosen page's text below.
   Lives in a shadow root so Canva's styles and ours never meet. Book Studio's light look (app/web/css/app.css). */
(function () {
  'use strict';
  if (window.__bsCanvaPanel) return;
  window.__bsCanvaPanel = true;
  const Book = window.BSBook;
  const Bot = window.BSCanva;

  const store = {
    get(k, d) { try { const v = localStorage.getItem('bs-canva:' + k); return v === null ? d : v; } catch (_) { return d; } },
    set(k, v) { try { localStorage.setItem('bs-canva:' + k, v); } catch (_) { /* a private window — fine */ } },
  };

  // Book Studio's icon (app/web/img/icon.png) drawn; each copy has its own gradient — a hidden copy's would paint nothing.
  const logo = id => `<svg class="logo" viewBox="0 0 48 48" aria-hidden="true"><defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#f68d4e"/><stop offset="1" stop-color="#df5418"/></linearGradient></defs>
    <rect width="48" height="48" rx="12" fill="url(#${id})"/>
    <path d="M9.5 14.2c4.3-1.7 8.8-1.5 13.3.6v20.4c-4.5-2.1-9-2.3-13.3-.6zM38.5 14.2c-4.3-1.7-8.8-1.5-13.3.6v20.4c4.5-2.1 9-2.3 13.3-.6z" fill="#fff"/>
    <path d="M13.2 19.6h6.2M13.2 23.2h6.2M13.2 26.8h4.2M28.6 19.6h6.2M28.6 23.2h6.2M28.6 26.8h4.2" stroke="#ec7432" stroke-width="1.7" stroke-linecap="round"/></svg>`;
  const ICON = {
    folder: '<svg viewBox="0 0 24 24"><path d="M3.5 7A1.5 1.5 0 0 1 5 5.5h4l2 2h8A1.5 1.5 0 0 1 20.5 9v8.5A1.5 1.5 0 0 1 19 19H5a1.5 1.5 0 0 1-1.5-1.5z"/></svg>',
    minus: '<svg viewBox="0 0 24 24"><path d="M7 12h10"/></svg>',
    text: '<svg viewBox="0 0 24 24"><path d="M6 7h12M12 7v11"/></svg>',
    book: '<svg viewBox="0 0 24 24"><path d="M12 6.5c-2-1.3-4.6-1.6-7.5-.9v12c2.9-.7 5.5-.4 7.5.9 2-1.3 4.6-1.6 7.5-.9v-12c-2.9-.7-5.5-.4-7.5.9zM12 6.5v12"/></svg>',
    check: '<svg viewBox="0 0 24 24"><path d="m6.5 12.5 3.5 3.5 7.5-8"/></svg>',
    bang: '<svg viewBox="0 0 24 24"><path d="M12 6.5v7M12 17.5v.01"/></svg>',
    play: '<svg viewBox="0 0 24 24"><path d="M8 6.5v11l9-5.5z" fill="currentColor"/></svg>',
    stop: '<svg viewBox="0 0 24 24"><rect x="7.5" y="7.5" width="9" height="9" rx="1.5" fill="currentColor"/></svg>',
  };

  const CSS = `
    :host { all: initial; }
    :host {
      --surface: #fafaf8; --surface-2: #f1f1ee; --surface-3: #e5e5e1; --hover: #f3f3f0;
      --border: #d8d8d3; --border-strong: #c3c3bd; --text: #141517; --text-2: #45484d; --text-3: #63666c; --text-4: #9b9ea3;
      --accent: #bf4f1a; --accent-hover: #a8440f; --accent-soft: rgba(191,79,26,.1); --accent-line: rgba(191,79,26,.32);
      --green: #1d7a4c; --green-soft: rgba(29,122,76,.1); --red: #bf3a2c; --red-soft: rgba(191,58,44,.08);
      --shadow-l: 0 2px 6px rgba(20,21,23,.08), 0 28px 64px -16px rgba(20,21,23,.32);
      --art: 0 1px 1px rgba(20,21,23,.08), 0 6px 14px -8px rgba(20,21,23,.45);
      --ease: cubic-bezier(.2,.9,.25,1);
      --font: "Segoe UI", system-ui, sans-serif; --display: "Bahnschrift", "Segoe UI", system-ui, sans-serif;
      --book: "Sitka Text", Georgia, serif;
    }
    * { box-sizing: border-box; margin: 0; }
    svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; flex: none; }
    button { font: inherit; color: inherit; }
    button:focus-visible, input:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

    .fab { position: fixed; z-index: 2147483000; width: 48px; height: 48px; padding: 0; border: 0; touch-action: none;
      border-radius: 13px; background: none; cursor: pointer; box-shadow: 0 6px 18px -4px rgba(191,79,26,.55), 0 1px 2px rgba(0,0,0,.12);
      transition: transform .2s var(--ease), box-shadow .2s var(--ease); }
    .fab.dragging { cursor: grabbing; transform: scale(1.06); box-shadow: 0 14px 30px -8px rgba(191,79,26,.6), 0 2px 4px rgba(0,0,0,.14); transition: none; }
    .box.dragging { box-shadow: 0 4px 10px rgba(20,21,23,.1), 0 36px 80px -16px rgba(20,21,23,.4); }
    .fab:hover { transform: translateY(-2px) scale(1.04); box-shadow: 0 10px 24px -6px rgba(191,79,26,.6), 0 1px 2px rgba(0,0,0,.12); }
    .fab:active { transform: scale(.96); }
    .fab .logo { width: 48px; height: 48px; display: block; }
    .fab.run::after { content: ""; position: absolute; inset: -4px; border-radius: 16px; border: 2px solid var(--accent);
      animation: halo 1.4s ease-in-out infinite; }
    @keyframes halo { 0%,100% { opacity: .15; transform: scale(.98); } 50% { opacity: .8; transform: scale(1.02); } }

    .box { position: fixed; z-index: 2147483000; width: 352px; max-height: calc(100vh - 32px); display: flex; flex-direction: column;
      background: var(--surface); color: var(--text); font: 13px/1.4 var(--font); border: 1px solid var(--border);
      border-radius: 14px; box-shadow: var(--shadow-l); overflow: hidden;
      transform-origin: bottom right; animation: rise .22s var(--ease); }
    .box[hidden] { display: none; }
    @keyframes rise { from { opacity: 0; transform: translateY(8px) scale(.97); } }

    .head { display: flex; align-items: center; gap: 10px; padding: 12px 10px 12px 14px; cursor: grab; user-select: none; touch-action: none; }
    .head:active { cursor: grabbing; }
    .head .logo { width: 26px; height: 26px; border-radius: 7px; }
    .head h1 { flex: 1; font: 600 15px/1.2 var(--display); letter-spacing: .01em; }
    .head h1 span { color: var(--text-4); font-weight: 400; margin: 0 2px; }
    .icon { width: 30px; height: 30px; border: 0; border-radius: 8px; background: none; color: var(--text-3); cursor: pointer;
      display: grid; place-items: center; transition: background .12s; }
    .icon:hover { background: var(--surface-3); color: var(--text); }

    .controls { display: flex; gap: 8px; padding: 0 14px 12px; }
    .book { flex: 1; min-width: 0; display: flex; align-items: center; gap: 8px; height: 36px; padding: 0 12px; cursor: pointer;
      border: 1px solid var(--border); border-radius: 9px; background: #fff; color: var(--text-2); text-align: left;
      transition: border-color .15s, background .15s, box-shadow .15s; }
    .book:hover { border-color: var(--border-strong); background: var(--hover); }
    .book span { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .book.chosen { color: var(--text); font-weight: 600; }
    .book.chosen svg { color: var(--accent); }
    .pages { width: 84px; height: 36px; padding: 0 8px; border: 1px solid var(--border); border-radius: 9px; background: #fff;
      color: var(--text); font: 600 13px var(--font); text-align: center; font-variant-numeric: tabular-nums; transition: border-color .15s, box-shadow .15s; }
    .pages:hover { border-color: var(--border-strong); }
    .missing { border-color: var(--red) !important; box-shadow: 0 0 0 3px var(--red-soft) !important; animation: nudge .3s; }
    @keyframes nudge { 25% { transform: translateX(-3px); } 75% { transform: translateX(3px); } }

    .shelf { flex: 1; min-height: 0; overflow-y: auto; padding: 14px; background: var(--surface-2);
      border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); scrollbar-width: thin; }
    .welcome { display: grid; place-items: center; gap: 12px; padding: 26px 12px 30px; color: var(--text-3); text-align: center; }
    .welcome .open-book { width: 120px; height: 72px; display: flex; gap: 3px; perspective: 400px; }
    .welcome .open-book i { flex: 1; border-radius: 3px 3px 6px 6px; background: #fff; box-shadow: var(--art);
      background-image: repeating-linear-gradient(transparent 0 11px, var(--surface-3) 11px 13px); background-size: 70% 100%;
      background-repeat: no-repeat; background-position: center 14px; }
    .welcome .open-book i:first-child { transform: rotateY(14deg); transform-origin: right; }
    .welcome .open-book i:last-child { transform: rotateY(-14deg); transform-origin: left; }

    .cover { display: block; width: 64%; aspect-ratio: 5370 / 2850; margin: 0 auto 16px; }
    .spreads { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px 12px; }
    .spread { display: flex; gap: 1px; border-radius: 3px; box-shadow: var(--art); background: var(--border); }
    .spread.single { box-shadow: none; background: none; }

    .pg { position: relative; flex: 1; aspect-ratio: 1; padding: 0; border: 0; background: #fff center / cover no-repeat;
      cursor: pointer; transition: opacity .2s, transform .15s var(--ease), filter .2s; }
    .spread .pg:first-child { border-radius: 3px 0 0 3px; }
    .spread .pg:last-child { border-radius: 0 3px 3px 0; }
    .cover.pg { border-radius: 3px; box-shadow: var(--art); }
    .pg.endpaper { background: #fff; cursor: default; box-shadow: var(--art); border-radius: 3px; }
    .pg.endpaper.l { visibility: hidden; }
    .pg.endpaper.r { visibility: hidden; }
    .pg:not(.endpaper):hover { transform: translateY(-1px); z-index: 1; }
    .pg.nopic { background: repeating-linear-gradient(-45deg, #fff 0 6px, var(--red-soft) 6px 12px); outline: 1.5px dashed var(--red); outline-offset: -1.5px; }
    .pg.off { opacity: .28; filter: grayscale(1); }
    .pg.focus { outline: 2px solid var(--text); outline-offset: 2px; z-index: 2; }
    .pg .num { position: absolute; left: 3px; bottom: 3px; min-width: 15px; height: 15px; padding: 0 3px; border-radius: 4px;
      background: rgba(20,21,23,.55); color: #fff; font: 600 10px/15px var(--font); text-align: center; font-variant-numeric: tabular-nums; }
    .pg .tx { position: absolute; right: 3px; top: 3px; width: 16px; height: 16px; border-radius: 5px; background: #fff;
      color: var(--text-2); display: grid; place-items: center; box-shadow: 0 1px 2px rgba(0,0,0,.25); }
    .pg .tx svg { width: 11px; height: 11px; stroke-width: 2.4; }
    .pg .tx.bad { background: var(--red); color: #fff; }
    .pg .st { position: absolute; inset: 0; border-radius: inherit; pointer-events: none; transition: box-shadow .25s, background .25s; }
    .pg.work .st { box-shadow: inset 0 0 0 2.5px var(--accent); background: rgba(255,255,255,.35); animation: breathe 1.1s ease-in-out infinite; }
    @keyframes breathe { 50% { background: rgba(255,255,255,.05); } }
    .pg.done .st { box-shadow: inset 0 0 0 2px var(--green); }
    .pg.error .st { box-shadow: inset 0 0 0 2.5px var(--red); background: rgba(191,58,44,.12); }
    .pg .badge { position: absolute; right: -5px; bottom: -5px; width: 18px; height: 18px; border-radius: 50%; display: none;
      place-items: center; color: #fff; border: 2px solid var(--surface-2); animation: pop .25s var(--ease); }
    .pg .badge svg { width: 12px; height: 12px; stroke-width: 2.6; }
    .pg.done .badge { display: grid; background: var(--green); }
    .pg.error .badge { display: grid; background: var(--red); }
    @keyframes pop { from { transform: scale(.4); opacity: 0; } }

    .reader { padding: 12px 16px; min-height: 64px; max-height: 150px; overflow-y: auto; background: #fff; border-bottom: 1px solid var(--border); scrollbar-width: thin; }
    .reader .cap { display: flex; gap: 6px; align-items: baseline; margin-bottom: 4px; color: var(--text-4); font: 600 11px var(--font);
      text-transform: uppercase; letter-spacing: .06em; }
    .reader .cap b { color: var(--text-2); }
    .reader .cap .look { margin-left: auto; color: var(--text-3); font-weight: 500; text-transform: none; letter-spacing: 0;
      font-variant-numeric: tabular-nums; }
    .reader p { font: 13px/1.55 var(--book); color: var(--text); white-space: pre-line; }
    .reader p.none { font-family: var(--font); color: var(--text-4); }
    .reader .var { color: var(--accent-hover); background: var(--accent-soft); border-radius: 3px; padding: 0 2px; }
    .reader .err { margin-top: 6px; padding: 6px 8px; border-radius: 6px; background: var(--red-soft); color: var(--red); font: 12px/1.4 var(--font); }
    .reader .ok { margin-top: 6px; color: var(--green); font: 12px var(--font); }

    .foot { padding: 12px 14px 14px; display: grid; gap: 10px; }
    .bar { height: 4px; border-radius: 2px; background: var(--surface-3); overflow: hidden; }
    .bar i { display: block; height: 100%; width: 0; border-radius: inherit; background: var(--accent); transition: width .5s var(--ease); }
    .bar.ok i { background: var(--green); }
    .row { display: flex; align-items: center; gap: 12px; }
    .msg { flex: 1; min-width: 0; color: var(--text-3); font-size: 12px; line-height: 1.35; }
    .msg.err { color: var(--red); }
    .msg b { color: var(--text); font-variant-numeric: tabular-nums; }
    .go { display: inline-flex; align-items: center; gap: 6px; height: 38px; padding: 0 18px 0 14px; border: 0; border-radius: 10px;
      background: var(--accent); color: #fff; font: 600 14px var(--display); letter-spacing: .01em; cursor: pointer;
      box-shadow: 0 1px 1px rgba(0,0,0,.08), 0 6px 14px -6px rgba(191,79,26,.7);
      transition: background .15s, transform .12s var(--ease), box-shadow .15s; }
    .go:hover { background: var(--accent-hover); }
    .go:active { transform: scale(.96); }
    .go.stop { background: #fff; color: var(--red); box-shadow: inset 0 0 0 1.5px var(--red); }
    .go.stop:hover { background: var(--red-soft); }
    .go svg { width: 16px; height: 16px; }

    /* The lock: while a run goes, a clear layer over Canva takes the real mouse (a hand on the mouse made Canva drag
       a frame); the panel and the button stay above it. */
    .lock { position: fixed; inset: 0; z-index: 2147482990; background: rgba(20,21,23,.05); cursor: progress;
      animation: fade .2s var(--ease); }
    .lock[hidden] { display: none; }
    @keyframes fade { from { opacity: 0; } }
    .lock .pill { position: absolute; left: 50%; top: 18px; transform: translateX(-50%); display: flex; align-items: center; gap: 10px;
      padding: 8px 16px 8px 10px; border-radius: 999px; background: #141517; color: #f2f2f0; font: 500 13px var(--font);
      box-shadow: 0 10px 30px -10px rgba(0,0,0,.5); white-space: nowrap; }
    .lock .pill b { display: grid; place-items: center; width: 26px; height: 26px; border-radius: 50%; background: var(--accent);
      color: #fff; font: 700 14px var(--display); font-variant-numeric: tabular-nums; }
    .lock .pill b.tick { animation: tick .9s var(--ease); }
    @keyframes tick { from { transform: scale(1.5); opacity: .4; } }
    .lock .pill b svg { width: 14px; height: 14px; }
  `;

  const host = document.createElement('div');
  host.id = 'bs-canva-panel';
  const root = host.attachShadow({ mode: 'open' });
  root.innerHTML = `<style>${CSS}</style>
    <div class="lock" hidden><div class="pill"><b></b><span></span></div></div>
    <button class="fab" title="Книга → Canva">${logo('bs-fab')}</button>
    <section class="box" hidden>
      <div class="head">${logo('bs-head')}<h1>Книга <span>→</span> Canva</h1><button class="icon min" title="Згорнути">${ICON.minus}</button></div>
      <div class="controls">
        <button class="book" title="Папка книги з Майстерні: pipeline/books/…">${ICON.folder}<span>Папка книги</span></button>
        <input class="pages" value="1-31" spellcheck="false" title="Сторінки: 1-31, 5-10 або 3,7,12">
      </div>
      <div class="shelf"><div class="welcome"><div class="open-book"><i></i><i></i></div><div>Виберіть папку книги</div></div></div>
      <div class="reader" hidden></div>
      <div class="foot">
        <div class="bar" hidden><i></i></div>
        <div class="row"><span class="msg"></span><button class="go">${ICON.play}<span>Розкласти</span></button></div>
      </div>
    </section>`;
  const $ = s => root.querySelector(s);
  const fab = $('.fab'), box = $('.box'), bookBtn = $('.book'), pagesIn = $('.pages'), shelf = $('.shelf'),
    reader = $('.reader'), bar = $('.bar'), msg = $('.msg'), go = $('.go');

  let book = null;        // {name, plan}
  let running = false;
  let focused = null;     // the page whose text the reader shows
  const results = {};     // page → {state, note}

  // ---- Open, close, move. The button and the panel share one place (their top-left corner): the panel opens where the
  // button stood, the button comes back where the panel's corner was; either is dragged, the place is remembered.
  const W = 352, FAB = 48;
  let anchor = (() => {
    const p = String(store.get('anchor', '')).split(',').map(Number);
    return p.length === 2 && p.every(Number.isFinite) ? { x: p[0], y: p[1] } : null;
  })();
  function layout() {
    const open = !box.hidden;
    const el = open ? box : fab;
    const w = open ? W : FAB;
    const h = open ? Math.min(box.offsetHeight || 640, innerHeight - 32) : FAB;
    const a = anchor || { x: innerWidth - (open ? W : FAB) - 20, y: open ? 80 : innerHeight - FAB - 92 };
    el.style.left = Math.min(Math.max(8, a.x), innerWidth - w - 8) + 'px';
    el.style.top = Math.min(Math.max(8, a.y), Math.max(8, innerHeight - h - 8)) + 'px';
  }
  const setOpen = open => {
    box.hidden = !open;
    fab.hidden = open;
    store.set('open', open ? '1' : '');
    layout();
  };
  let dragged = false;   // a drag of the button ends in a click — that click must not open the panel
  fab.onclick = () => { if (dragged) { dragged = false; return; } setOpen(true); };
  $('.min').onclick = () => setOpen(false);
  addEventListener('resize', layout);

  function draggable(handle, el) {
    handle.addEventListener('pointerdown', e => {
      if (e.button !== 0 || (handle !== fab && e.target.closest('button'))) return;
      const r = el.getBoundingClientRect();
      const dx = e.clientX - r.left, dy = e.clientY - r.top, sx = e.clientX, sy = e.clientY;
      try { handle.setPointerCapture(e.pointerId); } catch (_) { /* the drag still works without it */ }
      let moved = false;
      const move = ev => {
        if (!moved && Math.hypot(ev.clientX - sx, ev.clientY - sy) < 4) return;  // a click, not a drag
        moved = true;
        el.classList.add('dragging');
        el.style.left = (ev.clientX - dx) + 'px';
        el.style.top = (ev.clientY - dy) + 'px';
      };
      const up = () => {
        removeEventListener('pointermove', move, true);
        removeEventListener('pointerup', up, true);
        el.classList.remove('dragging');
        if (!moved) return;
        dragged = handle === fab;
        anchor = { x: parseInt(el.style.left, 10), y: parseInt(el.style.top, 10) };
        store.set('anchor', anchor.x + ',' + anchor.y);
        layout();
      };
      addEventListener('pointermove', move, true);
      addEventListener('pointerup', up, true);
    });
  }
  draggable(fab, fab);
  draggable($('.head'), box);

  pagesIn.value = store.get('pages', '1-31');
  pagesIn.oninput = () => { pagesIn.classList.remove('missing'); store.set('pages', pagesIn.value); lightPages(); };

  const say = (html, bad) => { msg.innerHTML = html || ''; msg.classList.toggle('err', Boolean(bad)); };
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const missing = el => { el.classList.remove('missing'); void el.offsetWidth; el.classList.add('missing'); };

  // ---- The book folder
  async function readFolder(dir) {
    let pics;
    try { pics = await dir.getDirectoryHandle('pictures'); } catch (_) {
      throw new Error(`У «${dir.name}» немає папки pictures — виберіть папку книги з pipeline/books`);
    }
    const pictures = {};
    for await (const [name, h] of pics.entries()) {
      const key = h.kind === 'file' && Book.pictureKey(name);
      if (key) pictures[key] = await h.getFile();
    }
    let text = '';
    try { text = await (await (await (await dir.getDirectoryHandle('agent')).getFileHandle('book-text.md')).getFile()).text(); } catch (_) { /* pictures only */ }
    let rows = {};
    try { rows = JSON.parse(await (await (await dir.getFileHandle('book.json')).getFile()).text()).rows || {}; } catch (_) { /* the default sides */ }
    return { name: dir.name, pictures, text, rows };
  }

  // Without the folder picker (an older Chrome): a folder input — the same files, by their paths.
  function readFolderInput() {
    return new Promise((resolve, reject) => {
      const input = document.createElement('input');
      input.type = 'file';
      input.webkitdirectory = true;
      input.onchange = async () => {
        const files = [...input.files];
        if (!files.length) return reject(new DOMException('', 'AbortError'));
        const name = files[0].webkitRelativePath.split('/')[0];
        const pictures = {};
        let text = '', rows = {};
        for (const f of files) {
          const rel = f.webkitRelativePath.split('/').slice(1).join('/');
          const m = /^pictures\/([^/]+)$/.exec(rel);
          if (m && Book.pictureKey(m[1])) pictures[Book.pictureKey(m[1])] = f;
          if (rel === 'agent/book-text.md') text = await f.text();
          if (rel === 'book.json') { try { rows = JSON.parse(await f.text()).rows || {}; } catch (_) { /* default sides */ } }
        }
        if (!Object.keys(pictures).length) return reject(new Error(`У «${name}» немає картинок у pictures — виберіть папку книги`));
        resolve({ name, pictures, text, rows });
      };
      input.click();
    });
  }

  // {name, pictures, text, rows} → the shelf. Also Bot.loadBook — how a book is given without the folder dialog (tests).
  function useBook(raw) {
    book = { name: raw.name, plan: Book.buildPlan(raw.pictures, Book.textSections(raw.text), raw.rows) };
    Object.keys(results).forEach(k => delete results[k]);
    bookBtn.querySelector('span').textContent = raw.name;
    bookBtn.title = raw.name;
    bookBtn.classList.add('chosen');
    drawShelf();
    const noPic = book.plan.filter(p => !p.picture).length;
    const noText = book.plan.filter(p => p.textMissing).length;
    if (!raw.text) say('Немає agent/book-text.md — розкладу лише картинки', true);
    else if (noPic || noText) say([noPic && `без картинки: ${noPic}`, noText && `без тексту: ${noText}`].filter(Boolean).join(' · '), true);
    else say(`<b>${book.plan.length}</b> сторінок · <b>${book.plan.filter(p => p.text).length}</b> з текстом`);
    bar.hidden = true;
  }
  Bot.loadBook = useBook;

  bookBtn.onclick = async () => {
    if (running) return say('Спершу зупиніть розкладку', true);
    bookBtn.classList.remove('missing');
    try {
      useBook(window.showDirectoryPicker
        ? await readFolder(await window.showDirectoryPicker({ id: 'bs-book', mode: 'read' }))
        : await readFolderInput());
    } catch (e) {
      if (e && e.name === 'AbortError') return;
      say(esc(e.message || String(e)), true);
    }
  };

  // ---- The book on the shelf: the cover, then the spreads as they are printed
  const byPage = n => book && book.plan.find(p => p.page === n);

  function pageHtml(p, cls = '') {
    if (!p) return `<span class="pg endpaper ${cls}"></span>`;
    const tx = p.text ? `<span class="tx">${ICON.text}</span>` : p.textMissing ? `<span class="tx bad">${ICON.text}</span>` : '';
    const num = p.page === Book.COVER_PAGE ? '' : `<span class="num">${p.page}</span>`;
    const title = p.page === Book.COVER_PAGE ? 'Обкладинка (сторінка 31)' : `Сторінка ${p.page}`;
    return `<button class="pg ${cls} ${p.picture ? '' : 'nopic'}" data-page="${p.page}" title="${title}">${num}${tx}<span class="st"></span><span class="badge"></span></button>`;
  }

  function drawShelf() {
    const spreads = [[null, 1]];
    for (let n = 2; n <= 28; n += 2) spreads.push([n, n + 1]);
    spreads.push([30, null]);
    shelf.innerHTML = pageHtml(byPage(Book.COVER_PAGE), 'cover') + '<div class="spreads">' + spreads.map(([l, r]) =>
      `<div class="spread${!l || !r ? ' single' : ''}">${pageHtml(l && byPage(l), l ? '' : 'endpaper l')}${pageHtml(r && byPage(r), r ? '' : 'endpaper r')}</div>`
    ).join('') + '</div>';
    for (const b of shelf.querySelectorAll('.pg[data-page]')) b.onclick = () => focus(Number(b.dataset.page));
    lightPages();
    for (const [page, r] of Object.entries(results)) paintPage(Number(page), r.state);
    focus(focused && byPage(focused) ? focused : 1);
    previews();
  }

  function lightPages() {
    if (!book) return;
    const on = new Set(Book.parsePages(pagesIn.value) || []);
    for (const b of shelf.querySelectorAll('.pg[data-page]')) b.classList.toggle('off', !on.has(Number(b.dataset.page)));
  }

  // Small previews, one at a time — the pictures are big.
  async function previews() {
    const plan = book.plan;
    for (const p of plan) {
      if (!p.picture || book.plan !== plan) continue;
      const el = shelf.querySelector(`.pg[data-page="${p.page}"]`);
      if (!el) continue;
      try {
        const cover = p.page === Book.COVER_PAGE;
        const bmp = await createImageBitmap(p.picture, cover ? { resizeHeight: 160, resizeQuality: 'high' } : { resizeWidth: 120, resizeQuality: 'high' });
        const c = document.createElement('canvas');
        c.width = bmp.width; c.height = bmp.height;
        c.getContext('2d').drawImage(bmp, 0, 0);
        bmp.close();
        el.style.backgroundImage = `url(${c.toDataURL('image/jpeg', 0.85)})`;
      } catch (_) { /* no preview — the page still shows its number */ }
    }
  }

  // ---- The reader: the chosen page's text, its {Name} lit, its result
  function focus(n) {
    focused = n;
    for (const b of shelf.querySelectorAll('.pg.focus')) b.classList.remove('focus');
    const el = shelf.querySelector(`.pg[data-page="${n}"]`);
    if (el) el.classList.add('focus');
    const p = byPage(n);
    if (!p) { reader.hidden = true; return; }
    const what = n === Book.COVER_PAGE ? 'Обкладинка' : `Сторінка ${n}`;
    const body = p.text
      ? `<p>${esc(p.text).replace(/\{(Name|Gifter)\}/g, '<span class="var">{$1}</span>')}</p>`
      : p.textMissing ? '<p class="none">У book-text.md немає тексту для цього розвороту</p>'
      : `<p class="none">${n === Book.COVER_PAGE ? 'Лише картинка — назву ви ставите самі' : 'Лише картинка'}</p>`;
    const r = results[n];
    const result = !r ? '' : r.state === 'error' ? `<div class="err">${esc(r.note)}</div>` : r.state === 'done' ? `<div class="ok">✓ ${esc(r.note)}</div>` : '';
    const look = p.text ? `<span class="look">${Bot.STYLE.font} · ${Bot.sizeOf(n)} · трекінг ${Bot.STYLE.tracking}${Bot.spacingOf(n) ? ` · рядки ${Bot.spacingOf(n)}` : ''}</span>` : '';
    reader.innerHTML = `<div class="cap"><b>${what}</b>${p.picture ? '' : ' · немає картинки'}${look}</div>${body}${result}`;
    reader.hidden = false;
  }

  function paintPage(n, state) {
    const el = shelf.querySelector(`.pg[data-page="${n}"]`);
    if (!el) return;
    el.classList.remove('work', 'done', 'error');
    if (state === 'work' || state === 'done' || state === 'error') el.classList.add(state);
    el.querySelector('.badge').innerHTML = state === 'done' ? ICON.check : state === 'error' ? ICON.bang : '';
  }

  // ---- The lock over Canva: the real mouse goes nowhere while the extension works
  const lock = $('.lock');
  const lockSay = (badge, text) => {
    const b = lock.querySelector('b');
    b.innerHTML = badge;
    b.classList.remove('tick'); void b.offsetWidth; b.classList.add('tick');
    lock.querySelector('span').textContent = text;
  };
  for (const type of ['pointerdown', 'pointermove', 'pointerup', 'mousedown', 'mousemove', 'mouseup', 'click', 'dblclick',
    'contextmenu', 'wheel', 'dragstart']) {
    lock.addEventListener(type, e => { e.stopPropagation(); e.preventDefault(); }, { passive: false });
  }

  // 3-2-1 before the start, so the hand is off the mouse; Stop during it cancels. True when it ran to the end.
  let countdownCancel = null;
  async function countdown() {
    lock.hidden = false;
    for (let s = 3; s > 0; s--) {
      lockSay(String(s), 'Відпустіть мишку — далі Canva під замком');
      const cancelled = await new Promise(res => { const t = setTimeout(() => res(false), 1000); countdownCancel = () => { clearTimeout(t); res(true); }; });
      if (cancelled) { countdownCancel = null; lock.hidden = true; return false; }
    }
    countdownCancel = null;
    return true;
  }

  // ---- Розкласти / Зупинити
  function setRunning(on) {
    running = on;
    go.classList.toggle('stop', on);
    go.innerHTML = on ? `${ICON.stop}<span>Зупинити</span>` : `${ICON.play}<span>Розкласти</span>`;
    fab.classList.toggle('run', on);
  }

  go.onclick = async () => {
    if (countdownCancel) { countdownCancel(); return; }
    if (running) { Bot.stop(); go.querySelector('span').textContent = 'Зупиняю…'; return; }
    if (!book) { missing(bookBtn); return say('Спершу виберіть папку книги', true); }
    const pages = Book.parsePages(pagesIn.value);
    if (!pages) { missing(pagesIn); return say('Сторінки: 1-31, 5-10 або 3,7,12', true); }
    // the run's mark in the upload names (month-day-hour-minute-second): no older upload of the same page is ever taken
    const now = new Date();
    const stamp = [now.getMonth() + 1, now.getDate(), now.getHours(), now.getMinutes(), now.getSeconds()].map(v => String(v).padStart(2, '0'))
      .reduce((a, v, i) => a + (i === 2 ? '-' : '') + v, '');
    const plan = book.plan.map(p => ({
      ...p,
      picture: p.picture && new File([p.picture], Book.uploadName(book.name, p.page, p.picture.name, stamp), { type: p.picture.type || 'image/png' }),
    }));
    const todo = plan.filter(p => pages.includes(p.page)).length;
    for (const page of pages) { delete results[page]; paintPage(page, null); }
    const count = state => pages.filter(p => results[p] && results[p].state === state).length;
    const progress = share => { bar.querySelector('i').style.width = (100 * share) + '%'; };
    bar.hidden = false;
    bar.classList.remove('ok');
    progress(0);
    setRunning(true);
    say('Відпустіть мишку…');
    if (!(await countdown())) { setRunning(false); bar.hidden = true; return say('Скасовано'); }
    lockSay(ICON.book, 'Розкладаю книгу — мишка Canva не чіпає; зупинити можна в панелі');
    const t0 = Date.now();
    const report = (page, state, note) => {
      if (page === null) {  // the run as a whole: its share done, or stopped
        if (state === 'progress') progress(note);
        return;
      }
      results[page] = { state, note };
      paintPage(page, state);
      if (state === 'work') {
        const el = shelf.querySelector(`.pg[data-page="${page}"]`);
        if (el) el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        if (focused !== page) focus(page);
        say(`<b>${count('done')}</b> з <b>${todo}</b> готово · ${page === Book.COVER_PAGE ? 'обкладинка' : 'сторінка ' + page}: ${esc(note)}`);
      } else if (focused === page) focus(page);
    };
    let runError = null;
    try {
      await Bot.run(plan, pages, report);
    } catch (e) {
      runError = e.message || String(e);
    }
    lock.hidden = true;
    setRunning(false);
    for (const page of pages) {  // a stop or an error between the steps: those pages are not «in work» any more
      if (results[page] && results[page].state === 'work') { delete results[page]; paintPage(page, null); }
    }
    const done = count('done'), failed = count('error');
    if (runError) return say(`Розкладку перервано: ${esc(runError)}`, true);
    const min = Math.max(1, Math.round((Date.now() - t0) / 60000));
    if (failed) {
      const red = pages.filter(p => results[p] && results[p].state === 'error');
      pagesIn.value = red.join(', ');  // a rerun of just these: their pictures only are uploaded again
      store.set('pages', pagesIn.value);
      lightPages();
      say(`Готово <b>${done}</b>, не вийшло <b>${failed}</b> — у полі вже лише червоні сторінки, «Розкласти» ще раз`, true);
      if (red.length) focus(red[0]);
    } else if (done < todo) say(`Зупинено: готово <b>${done}</b> з <b>${todo}</b>`);
    else { bar.classList.add('ok'); progress(1); say(`Готово: <b>${done}</b> сторінок за ${min} хв`); }
  };

  // Canva is one page app: the panel lives only in the editor.
  function place() {
    const inEditor = /^\/design\//.test(location.pathname);
    if (inEditor && !host.isConnected) { document.documentElement.appendChild(host); setOpen(store.get('open', '1') === '1'); }
    if (!inEditor && host.isConnected && !running) host.remove();
  }
  place();
  setInterval(place, 1000);
})();
