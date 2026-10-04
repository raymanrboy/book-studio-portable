// «Фотомокапи» (the Listings mode, the owner 30.09.2026): lifestyle photos with a blank white book — a grandmother
// reading, a child holding it, a shelf — by category. A click on a photo puts it into the clipboard, and Ctrl+V in Chrome
// puts the category's prompt in after it (change nothing but the book); the book's cover the owner adds to the chat
// himself. Nothing is caught here: in a Workshop book the same photos go through its «Фото» step, with the book's cover
// and its photo caught into the book. The templates live inside Book Studio (app/data/photo-mockups): a photo dropped
// onto a category joins it, one taken out goes to the Recycle Bin.
import { api, post, html, ic, ib, setHtml, on, toast, confirmBox, upload, fadeImages, patch, media, plural, backToTools, attr } from '../lib.js';
import { store } from '../info.js';
import { openLightbox } from '../lightbox.js';
import { watch, refresh, act, paintGenBar, genAction, genState, startPhoto } from '../workshop-live.js';

const IMG_RE = /\.(png|jpe?g|webp)$/i;
const TEMPLATES = ['заготовка', 'заготовки', 'заготовок'];
// What the owner adds to the chat himself, after the photo and the prompt — the same the book's «Фото» step pastes.
const REF_HINT = {
  cover1: 'Додайте обкладинку книги — мокап Cover 1',
  'cover-open': 'Додайте книгу закриту й розкриту — мокап Cover & Open 1',
  'canva-cover': 'Додайте плаский розгорт обкладинки з Canva',
};

export async function mount(view) {
  let data;
  try {
    data = await api('/api/photos');
  } catch (err) {
    setHtml(view, html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`);
    return null;
  }
  const adding = new Map();   // category → how many photos are still on their way in
  // Opened from a Workshop book (its «Усі заготовки» link) the way back leads to that book; from «Інструменти» — to the tools.
  const fromBook = /^#\/workshop\//.test(store.here) ? store.here : '';

  setHtml(view, html`
    <div class="page-head">
      ${fromBook ? html`<a class="back-link" href="${fromBook}" aria-label="До книги" data-tip="До книги">${ic('arrowLeft')}</a>` : backToTools()}
      <div>
        <h1 class="page-title">Фотомокапи</h1>
        <div class="page-sub" id="ph-sub"></div>
      </div>
      <div class="page-actions"><div class="tools">${ib('folderOpen', 'Папка заготовок', 'data-act="open"')}</div></div>
    </div>
    <div class="ws-genbar-slot" id="ph-gen"></div>
    <div class="ph-sections" id="ph-sections"></div>
    <input type="file" id="ph-file" accept=".png,.jpg,.jpeg,.webp" multiple hidden>`);
  const $ = (s) => view.querySelector(s);
  const thumb = (cat, t, w) => media(`/media/photos/${encodeURIComponent(cat)}/${encodeURIComponent(t.name)}`, { w, v: t.v });
  const ratio = (t) => (t.size ? `${t.size[0]} / ${t.size[1]}` : '1 / 1');
  const now = (cat, name) => {
    const a = genState()?.active;
    return !!a && a.kind === 'photo' && !a.book && a.category === cat && a.template === name;
  };

  function section(c) {
    const n = c.templates.length;
    const busy = adding.get(c.key);
    return html`<section class="ph-sec" data-drop-cat="${c.key}" id="ph-${c.key}">
      <div class="ph-sec-head">
        <h2 class="section-title">${c.label}</h2>
        <span class="num ph-count">${n}</span>
        <span class="ph-sec-ref">${ic(c.omni ? 'video' : 'image', 'icon-s')}${c.omni ? `Відео в Gemini Omni · ${REF_HINT[c.ref].toLowerCase()}` : REF_HINT[c.ref]}</span>
        <span class="spacer"></span>
        ${busy ? html`<span class="chip chip-accent"><span class="ws-pulse"></span>додаю ${busy}</span>` : ''}
        <div class="tools">
          ${ib('prompt', 'Промпт цієї категорії — у буфер', `data-act="prompt" ${attr('data-cat', c.key)}`)}
          ${ib('folderOpen', 'Папка цієї категорії', `data-act="open" ${attr('data-cat', c.key)}`)}
        </div>
      </div>
      <div class="ph-tiles">
        ${c.templates.map((t) => html`<div class="ph-tile ${now(c.key, t.name) ? 'now' : ''}" style="aspect-ratio:${ratio(t)}">
          <button type="button" class="ph-shot" data-act="start" data-cat="${c.key}" data-name="${t.name}"
            data-tip="У буфер: це фото, далі Ctrl+V у Chrome — промпт">
            <img data-fade alt="${t.name}" src="${thumb(c.key, t, 520)}" loading="lazy"></button>
          ${now(c.key, t.name) ? html`<span class="chip chip-accent ph-now"><span class="ws-pulse"></span>у буфері</span>` : ''}
          <div class="img-actions">${ib('expand', 'Переглянути', `data-act="zoom" ${attr('data-cat', c.key)} ${attr('data-name', t.name)}`, { cls: 'sm' })}${ib('trash', 'Прибрати заготовку — у Кошик Windows', `data-act="remove" ${attr('data-cat', c.key)} ${attr('data-name', t.name)}`, { cls: 'sm danger' })}</div>
        </div>`)}
        <button type="button" class="ph-add" data-act="add" data-cat="${c.key}" data-tip="Нова заготовка в «${c.label}» — або перетягніть фото сюди">
          <span class="drop-ico">${ic('plus')}</span><span>Додати фото</span></button>
      </div>
    </section>`;
  }

  function draw() {
    const total = data.categories.reduce((s, c) => s + c.templates.length, 0);
    $('#ph-sub').textContent = `${total} ${plural(total, TEMPLATES)} · клік — у буфер фото, далі Ctrl+V у Chrome — промпт`;
    paintGenBar($('#ph-gen'), null);
    patch($('#ph-sections'), data.categories.map((c) => [c.key, section(c)])).forEach(fadeImages);
  }

  const unwatch = watch({ sig: data.sig, gen: data.gen, sigUrl: '/api/photos/sig' }, async () => {
    try { data = await api('/api/photos'); } catch { return; }
    draw();
  });
  draw();

  // ---------------------------------------------------------------- templates in and out
  async function addFiles(cat, files) {
    const pics = files.filter((f) => IMG_RE.test(f.name));
    if (!pics.length) { toast('Це не картинка (PNG, JPG, WEBP)', 'error'); return; }
    adding.set(cat, (adding.get(cat) || 0) + pics.length);
    draw();
    let done = 0;
    for (const f of pics) {
      try {
        await upload(`/api/photos/add?${new URLSearchParams({ category: cat, name: f.name })}`, f);
        done += 1;
      } catch (err) { toast(`${f.name}: ${err.message}`, 'error'); }
      adding.set(cat, adding.get(cat) - 1);
      if (!adding.get(cat)) adding.delete(cat);
    }
    const c = data.categories.find((x) => x.key === cat);
    if (done) toast(`«${c.label}»: +${done} ${plural(done, TEMPLATES)}`, 'success');
    refresh();
  }

  async function remove(btn, cat, name) {
    const ok = await confirmBox({ title: 'Прибрати заготовку?', text: `${name} піде в Кошик Windows — звідти її можна відновити.`, confirm: 'Прибрати', danger: true });
    if (ok) act(btn, () => post('/api/photos/remove', { category: cat, name }), 'Заготовку прибрано — вона в Кошику');
  }

  function zoom(cat, name) {
    const c = data.categories.find((x) => x.key === cat);
    const items = c.templates.map((t) => ({ key: t.name, src: thumb(cat, t, 1400), full: thumb(cat, t, 2600), title: `${c.label} · ${t.name}`, sub: t.size ? `${t.size[0]}×${t.size[1]}` : '' }));
    openLightbox(items, Math.max(0, items.findIndex((it) => it.key === name)));
  }

  // ---------------------------------------------------------------- events
  let addTo = '';
  const offs = [on(view, 'click', '[data-act]', (e, t) => {
    const { act: a, cat = '', name = '' } = t.dataset;
    if (a === 'start') { startPhoto(t, { category: cat, template: name }); return; }
    if (a === 'prompt') { act(t, () => post('/api/photos/prompt', { category: cat }), 'Промпт у буфері'); return; }
    if (a === 'open') { act(t, () => post('/api/photos/open', { category: cat })); return; }
    if (a === 'add') { addTo = cat; $('#ph-file').click(); return; }
    if (a === 'remove') { remove(t, cat, name); return; }
    if (a === 'zoom') zoom(cat, name);
  }), on(view, 'click', '[data-gen]', (e, t) => genAction(t, t.dataset.gen))];

  $('#ph-file').addEventListener('change', (e) => {
    const files = [...e.target.files];
    e.target.value = '';
    if (files.length && addTo) addFiles(addTo, files);
  });

  // Photos dragged in from Explorer join the category they are dropped on.
  const hasFiles = (e) => [...(e.dataTransfer?.types || [])].includes('Files');
  const mark = (target) => {
    view.querySelectorAll('.ph-sec.drop-on').forEach((x) => x.classList.remove('drop-on'));
    target?.classList.add('drop-on');
  };
  const onOver = (e) => {
    if (!hasFiles(e)) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
    mark(e.target.closest('[data-drop-cat]'));
  };
  const onLeave = (e) => { if (!e.relatedTarget || !view.contains(e.relatedTarget)) mark(null); };
  const onDrop = (e) => {
    if (!hasFiles(e)) return;
    e.preventDefault();
    mark(null);
    const target = e.target.closest('[data-drop-cat]');
    if (!target) { toast('Перетягніть фото на його категорію', 'info'); return; }
    addFiles(target.dataset.dropCat, [...e.dataTransfer.files]);
  };
  view.addEventListener('dragover', onOver);
  view.addEventListener('dragleave', onLeave);
  view.addEventListener('drop', onDrop);

  return {
    unmount() {
      unwatch();
      offs.forEach((off) => off());
    },
  };
}
