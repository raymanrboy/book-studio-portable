// Settings' two dialogs of their own: the Etsy sign-in (from the Kyiv PC only) and the choice of the Printify Master
// — out of the page's mount() since 27.09.2026; the page passes what they need.
import {
  api, post, html, ic, setHtml, modal, toast, confirmBox, copyText, openExternal, sleep, confirmChecked,
} from '../lib.js';

// ---------------------------------------------------------------- Etsy OAuth flow
/** The Etsy sign-in: first the owner confirms he is on the Kyiv PC, then the Etsy page (here, or on the Kyiv PC with
 *  the address pasted back). `done()` — the page reloads what it shows. */
export async function oauthFlow(done) {
  const confirmed = await confirmChecked({
    title: 'Перевірка безпеки Etsy',
    sub: 'Захист від блокування через сторонній IP',
    warning: html`Ви збираєтеся перейти на офіційну сторінку авторизації Etsy.<br><b>Переконайтеся, що ви зараз працюєте через віддалений київський комп'ютер</b>, де зареєстрований магазин. Якщо ви на польському ноутбуці чи телефоні — закрийте це вікно.`,
    check: 'Я підтверджую, що відкриватиму вхід в Etsy на віддаленому київському комп\'ютері',
    cancel: 'Скасувати (я на звичайному ПК)',
    icon: 'login',
  });
  if (!confirmed) return;

  let start;
  try { start = await post('/api/etsy/oauth/start', {}); }
  catch (err) { toast(err.message, 'error'); return; }
  let polling = true;
  const m = modal({
    title: 'Авторизація Etsy',
    sub: 'Оберіть, де ви зараз працюєте',
    size: 'l',
    body: html`<div class="stack">
      <div class="card-soft stack-s" style="padding:14px">
        <b>Варіант 1 — програма запущена на київському комп'ютері</b>
        <div class="faint" style="font-size: var(--fs)">Сторінка входу відкриється у вашому браузері. Після підтвердження Etsy поверне вас у програму автоматично.</div>
        <div><button class="btn btn-primary btn-sm" data-x="open">${ic('external', 'icon-s')}Відкрити сторінку входу Etsy</button></div>
      </div>
      <div class="card-soft stack-s" style="padding:14px">
        <b>Варіант 2 — програма на цьому ПК, а вхід робите на київському</b>
        <div class="faint" style="font-size: var(--fs)">1) Скопіюйте посилання і відкрийте його в браузері на київському ПК. 2) Підтвердіть доступ. 3) Браузер перейде на адресу <span class="mono">localhost</span>, яка не відкриється — це нормально: скопіюйте повну адресу з рядка браузера й вставте нижче.</div>
        <div><button class="btn btn-sm" data-x="copy">${ic('copy', 'icon-s')}Скопіювати посилання для Києва</button></div>
        <div class="row" style="margin-top:4px"><input class="input mono" id="oauth-back" placeholder="${start.redirectUri}?code=…&state=…" autocomplete="off" spellcheck="false">
          <button class="btn btn-primary" data-x="finish">Завершити</button></div>
      </div>
      <div class="row faint" style="font-size: var(--fs-s)"><span class="spinner" style="width:14px;height:14px"></span>Очікування підтвердження від Etsy… Посилання дійсне 60 хвилин.</div>
    </div>`,
    foot: html`<button class="btn btn-ghost" data-x="close">Закрити</button>`,
    onClose: () => { polling = false; },
  });
  m.el.addEventListener('click', async (e) => {
    const b = e.target.closest('[data-x]');
    if (!b) return;
    const x = b.dataset.x;
    if (x === 'close') m.close();
    if (x === 'open') openExternal(start.authUrl);
    if (x === 'copy') copyText(start.authUrl, 'Посилання скопійовано — відкрийте його на київському ПК');
    if (x === 'finish') {
      const url = m.el.querySelector('#oauth-back').value.trim();
      if (!url) { toast('Вставте адресу, на яку перейшов браузер після входу', 'error'); return; }
      b.disabled = true;
      try {
        const res = await post('/api/etsy/oauth/complete', { url });
        polling = false; m.close();
        toast(`Etsy підключено${res.shopName ? `: ${res.shopName}` : ''}`, 'success');
        done();
      } catch (err) { toast(err.message, 'error', 8000); b.disabled = false; }
    }
  });
  // Auto-detect success when the callback lands on this machine.
  (async () => {
    while (polling) {
      await sleep(2000);
      if (!polling) break;
      try {
        const st = await api('/api/etsy/status');
        if (st.connected) { polling = false; m.close(); toast(`Etsy підключено${st.shopName ? `: ${st.shopName}` : ''}`, 'success'); done(); }
      } catch { /* ignore */ }
    }
  })();
}

// ---------------------------------------------------------------- Printify master
/** The Printify Master: a shop, one of its products (or an ID pasted), read and checked, then saved as the model for
 *  every new book. `printify` — the settings' own section (the current shop and Master); `done()` — the page
 *  reloads. */
export async function pickMaster(printify, done) {
  let shops;
  try { shops = (await api('/api/printify/shops')).shops; } catch (err) { toast(err.message, 'error'); return; }
  let shopId = printify.shopId && shops.some((x) => x.id === printify.shopId) ? printify.shopId : shops[0]?.id;
  let selected = printify.master?.productId || null;
  let analysis = null;
  const m = modal({
    title: 'Оберіть Master-продукт',
    sub: 'Правильно налаштована книга, з якої копіюється конфігурація нових чернеток',
    size: 'xl',
    body: html`<div class="stack">
      <div class="row"><span class="field-label" style="margin:0">Магазин</span>
        <select class="select" id="mp-shop" style="width:auto">${shops.map((x) => html`<option value="${x.id}" ${x.id === shopId ? 'selected' : ''}>${x.title} (#${x.id}${x.channel ? ` · ${x.channel}` : ''})</option>`)}</select>
        <span class="spacer"></span><input class="input" id="mp-id" placeholder="…або вставте ID / посилання на продукт" style="width:330px"></div>
      <div id="mp-list" class="prod-grid" style="max-height:420px;overflow:auto"></div>
      <div id="mp-more"></div>
      <div id="mp-analysis"></div>
    </div>`,
    foot: html`<button class="btn btn-ghost" data-x="close">Скасувати</button><button class="btn" data-x="analyze">${ic('search', 'icon-s')}Проаналізувати</button><button class="btn btn-primary" data-x="save" disabled>${ic('check', 'icon-s')}Зробити Master</button>`,
  });
  const list = m.el.querySelector('#mp-list');
  let page = 1, last = 1;
  async function loadProducts(reset = true) {
    if (reset) { page = 1; setHtml(list, html`<div class="faint" style="padding:20px">Завантаження продуктів…</div>`); }
    try {
      const res = await api(`/api/printify/products?shop=${shopId}&page=${page}`);
      last = res.lastPage || 1;
      const cards = res.products.map((p) => html`<button class="prod ${p.id === selected ? 'sel' : ''}" data-pid="${p.id}">
        ${p.image ? html`<img src="${p.image}" alt="" loading="lazy">` : html`<div class="prod-ph"></div>`}
        <div><b style="display:block" class="truncate">${p.title}</b><span class="faint mono" style="font-size: var(--fs-s)">bp ${p.blueprintId} · ${p.id.slice(-6)}</span></div></button>`);
      if (reset) setHtml(list, cards); else list.insertAdjacentHTML('beforeend', String(html`${cards}`));
      setHtml(m.el.querySelector('#mp-more'), page < last ? html`<button class="btn btn-sm" data-x="more">Завантажити ще</button>` : '');
    } catch (err) { setHtml(list, html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`); }
  }
  async function analyze() {
    const idInput = m.el.querySelector('#mp-id').value.trim();
    const productId = idInput || selected;
    if (!productId) { toast('Оберіть продукт', 'info'); return; }
    setHtml(m.el.querySelector('#mp-analysis'), html`<div class="row faint"><span class="spinner"></span>Аналіз продукту…</div>`);
    try {
      analysis = await post('/api/printify/master/analyze', { shopId, productId });
      const bad = analysis.pageCount !== 24;
      setHtml(m.el.querySelector('#mp-analysis'), html`<div class="card-soft" style="padding:14px">
        <div style="font-weight:650;margin-bottom:8px">${analysis.title}</div>
        <dl class="master-card">
          <dt>Blueprint / постачальник</dt><dd>${analysis.blueprintId} / ${analysis.printProviderId}</dd>
          <dt>Позиції</dt><dd>cover + ${analysis.pageCount} сторінок</dd>
          <dt>Увімкнені варіанти</dt><dd>${analysis.enabledVariants.join(', ') || '—'}</dd>
          <dt>Розміри artwork</dt><dd>обкладинка ${(analysis.coverSize || []).join('×') || '—'} · сторінки ${(analysis.pageSize || []).join('×') || '—'}</dd>
          <dt>Обкладинка x / y / scale</dt><dd class="mono" style="font-size: var(--fs-s)">${analysis.placements.cover.x} / ${analysis.placements.cover.y} / ${analysis.placements.cover.scale}</dd>
        </dl>
        ${bad ? html`<div class="notice notice-warn" style="margin-top:10px">${ic('alert')}<div>У цьому продукті ${analysis.pageCount} сторінок (очікується 24). Переконайтеся, що це правильний еталон.</div></div>` : ''}
      </div>`);
      m.foot.querySelector('[data-x="save"]').disabled = false;
    } catch (err) {
      setHtml(m.el.querySelector('#mp-analysis'), html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`);
    }
  }
  m.el.querySelector('#mp-shop').addEventListener('change', (e) => { shopId = +e.target.value; selected = null; analysis = null; loadProducts(); });
  m.el.addEventListener('click', async (e) => {
    const card = e.target.closest('[data-pid]');
    if (card) { selected = card.dataset.pid; list.querySelectorAll('.prod').forEach((c) => c.classList.toggle('sel', c === card)); m.el.querySelector('#mp-id').value = ''; analysis = null; m.foot.querySelector('[data-x="save"]').disabled = true; analyze(); return; }
    const b = e.target.closest('[data-x]');
    if (!b) return;
    if (b.dataset.x === 'close') m.close();
    if (b.dataset.x === 'more') { page++; loadProducts(false); }
    if (b.dataset.x === 'analyze') analyze();
    if (b.dataset.x === 'save' && analysis) {
      const ok = await confirmBox({ title: 'Зробити цей продукт Master?', text: `«${analysis.title}» стане еталоном для всіх нових чернеток Printify. Сам продукт програма лише читає.`, confirm: 'Так, зробити Master' });
      if (!ok) return;
      try {
        const shop = shops.find((x) => x.id === shopId);
        await post('/api/printify/master/save', { analysis, shopId, shopTitle: shop?.title });
        m.close(); toast('Master-продукт збережено', 'success'); done();
      } catch (err) { toast(err.message, 'error'); }
    }
  });
  loadProducts();
}
