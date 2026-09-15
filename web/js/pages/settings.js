// Settings: keys (encrypted with Windows DPAPI), Etsy connection, Printify Master, Gelato, appearance.
import {
  api, html, ic, setHtml, on, modal, toast, confirmBox, copyText, openExternal, segHtml, syncSeg, setSeg,
  dateTime, sleep,
} from '../lib.js';
import { refreshInfo, applyTheme, applyMotion } from '../app.js';

const SECRET_LABELS = {
  etsy_keystring: ['Etsy Keystring', 'Etsy Developers → Your apps → Keystring'],
  etsy_shared_secret: ['Etsy Shared Secret', 'Там само, поле Shared Secret'],
  printify_token: ['Printify Personal Access Token', 'Printify → My account → Connections → API'],
  gelato_api_key: ['Gelato API-ключ', 'Gelato Dashboard → Developer → API keys'],
};

export async function mount(view, [section]) {
  let s;
  const editing = new Set();

  async function load() {
    s = await api('/api/settings');
  }

  function secretField(name) {
    const st = s.secrets[name];
    const [label, hint] = SECRET_LABELS[name];
    const edit = editing.has(name) || !st.configured;
    return html`<div class="field">
      <label class="field-label">${label}</label>
      ${edit ? html`<div class="secret-row"><input class="input mono" type="password" data-secret-input="${name}" placeholder="Вставте значення…" autocomplete="off" spellcheck="false">
          <button class="btn btn-primary" data-secret-save="${name}">Зберегти</button>
          ${st.configured ? html`<button class="btn btn-ghost" data-secret-cancel="${name}">Скасувати</button>` : ''}</div>`
        : html`<div class="secret-row"><div class="secret-state">${ic('lock', 'icon-s')}<span>Збережено</span><span class="mono">${st.hint}</span></div>
          <button class="btn" data-secret-edit="${name}">Змінити</button>
          <button class="btn btn-ghost btn-icon" data-secret-clear="${name}" title="Видалити">${ic('trash', 'icon-s')}</button></div>`}
      <div class="field-hint">${hint}</div>
    </div>`;
  }

  // ---------------------------------------------------------------- sections
  function legacyCard() {
    const items = (s.legacy?.items || []).filter((i) => !i.alreadySet);
    const cache = s.legacy?.uploadCache || 0;
    if (!items.length) return '';
    return html`<section class="card card-pad" style="grid-column:1/-1;border-color:var(--accent-line);background:linear-gradient(135deg,var(--accent-soft),transparent 60%),var(--surface)">
      <div class="row" style="align-items:flex-start;gap:14px">
        <div class="int-logo int-etsy">${ic('sparkle', 'icon-l')}</div>
        <div class="grow">
          <div class="card-title">Швидкий старт: знайдено ключі з ваших попередніх програм</div>
          <div class="card-sub" style="margin-bottom:10px">Програма може одразу перенести їх у своє зашифроване сховище — вводити нічого не потрібно.</div>
          <div class="row-wrap">${items.map((i) => html`<span class="chip chip-lg">${ic('key', 'icon-s')}${i.label}<span class="faint" style="font-weight:500">· ${i.source}</span></span>`)}
            ${cache ? html`<span class="chip chip-lg">${ic('database', 'icon-s')}Кеш завантажень Printify · ${cache}</span>` : ''}</div>
        </div>
        <button class="btn btn-primary" data-act="legacy-import">${ic('download', 'icon-s')}Імпортувати</button>
      </div></section>`;
  }

  function etsyCard() {
    const e = s.etsy;
    const connected = e.connected;
    return html`<section class="card card-pad" id="set-etsy" style="grid-column:1/-1">
      <div class="int-head" style="margin-bottom:18px">
        <div class="int-logo int-etsy">E</div>
        <div class="grow"><div class="card-title">Etsy <span class="faint mono" style="font-size:11.5px;font-weight:500">OAuth 2.0 PKCE · лише читання</span></div>
          <div class="card-sub">Замовлення, податки США та чистий виторг для сторінки «Прибуток», перевірка лістингів для бібліотеки</div></div>
        ${connected ? html`<span class="chip chip-green chip-lg"><span class="dot"></span>Підключено</span>`
          : html`<span class="chip chip-amber chip-lg"><span class="dot"></span>${e.keysConfigured ? 'Очікує входу' : 'Немає ключів'}</span>`}
      </div>
      <div class="settings-grid" style="gap:22px">
        <div class="stack">
          ${secretField('etsy_keystring')}
          ${secretField('etsy_shared_secret')}
        </div>
        <div class="stack">
          ${connected ? html`
            <div class="card-soft row" style="padding:14px">
              <span class="check-ico ok" style="width:34px;height:34px;border-radius:10px">${ic('shield')}</span>
              <div class="grow"><div style="font-weight:650">${e.shopName || 'Магазин Etsy'} <span class="faint mono" style="font-weight:500">#${e.shopId || '—'}</span></div>
                <div class="faint" style="font-size:12px">Токен оновлюється автоматично · доступ лише на читання${e.expiresAt ? ` · чинний до ${dateTime(new Date(e.expiresAt).toISOString())}` : ''}</div></div>
              <button class="btn btn-ghost" data-act="etsy-disconnect" style="color:var(--red)">Відключити</button>
            </div>
            <div class="card-soft row" style="padding:14px">
              <span class="check-ico" style="width:34px;height:34px;border-radius:10px;color:var(--accent)">${ic('laptop')}</span>
              <div class="grow"><div style="font-weight:600">Перенести доступ на інший комп'ютер</div>
                <div class="faint" style="font-size:12px">Ключ сесії підходить і для Book Studio на іншому ПК, і для Etsy Profit Calculator</div></div>
              <button class="btn" data-act="etsy-export">${ic('copy', 'icon-s')}Скопіювати ключ сесії</button>
            </div>`
          : html`
            <div class="card-soft stack-s" style="padding:14px">
              <div style="font-weight:600" class="row">${ic('laptop', 'icon-s')}Вже авторизували Etsy в Profit Calculator?</div>
              <div class="faint" style="font-size:12px">Відкрийте там Налаштування → «Скопіювати лінк доступу» і вставте посилання або ключ сюди.</div>
              <div class="row" style="margin-top:4px"><input class="input mono" id="etsy-key" placeholder="https://…/?sync=… або ключ сесії" autocomplete="off" spellcheck="false">
                <button class="btn btn-primary" data-act="etsy-import" ${e.keysConfigured ? '' : 'disabled'}>Активувати</button></div>
              ${e.secretConfigured ? '' : html`<div class="field-hint" style="color:var(--amber)">Для розшифрування ключа потрібен той самий Shared Secret, що й у Profit Calculator.</div>`}
            </div>
            <div class="card-soft row" style="padding:14px">
              <div class="grow"><div style="font-weight:600">Первинна авторизація через Etsy</div>
                <div class="faint" style="font-size:12px">Вхід на сторінці Etsy виконується виключно з віддаленого комп'ютера в Києві</div></div>
              <button class="btn btn-primary" data-act="etsy-oauth" ${e.keysConfigured ? '' : 'disabled'}>${ic('login', 'icon-s')}Авторизуватися в Etsy (Київ)</button>
            </div>`}
          <div class="info-box">
            <div class="row" style="margin-bottom:4px"><b style="font-size:12.5px">Callback URL (Redirect URI)</b><span class="spacer"></span>
              <button class="btn btn-ghost btn-xs" data-copy-text="${e.redirectUri}">${ic('copy', 'icon-s')}Скопіювати</button>
              <button class="btn btn-ghost btn-xs" data-act="redirect-edit">${ic('edit', 'icon-s')}Змінити</button></div>
            <code>${e.redirectUri}</code>
            <div class="faint" style="margin-top:6px;font-size:11.5px">Цю адресу треба один раз додати в Etsy Developers → Your apps → Callback URLs.</div>
          </div>
          ${e.portWarning ? html`<div class="notice notice-warn">${ic('alert')}<div>${e.portWarning}</div></div>` : ''}
        </div>
      </div>
    </section>`;
  }

  function printifyCard() {
    const p = s.printify;
    const m = p.master || {};
    const enabled = (m.variants || []).filter((v) => v.is_enabled).map((v) => v.title || v.id);
    const cover = (m.placements || {}).cover;
    return html`<section class="card card-pad" id="set-printify">
      <div class="int-head" style="margin-bottom:18px">
        <div class="int-logo int-printify">P</div>
        <div class="grow"><div class="card-title">Printify <span class="faint mono" style="font-size:11.5px;font-weight:500">Personal Access Token</span></div>
          <div class="card-sub">Собівартість замовлень і створення неопублікованих чернеток книг</div></div>
        ${s.secrets.printify_token.configured ? html`<span class="chip chip-green chip-lg"><span class="dot"></span>Токен є</span>` : html`<span class="chip chip-amber chip-lg">Немає токена</span>`}
      </div>
      <div class="stack">
        ${secretField('printify_token')}
        <div class="row"><button class="btn" data-act="printify-test" ${s.secrets.printify_token.configured ? '' : 'disabled'}>${ic('refresh', 'icon-s')}Перевірити зв'язок</button><span id="printify-test" class="faint" style="font-size:12.5px"></span></div>
        <hr class="divider" style="margin:6px 0">
        <div class="row"><b class="grow">Магазин і Master-продукт</b>
          <button class="btn btn-sm" data-act="master-pick" ${s.secrets.printify_token.configured ? '' : 'disabled'}>${ic('grid', 'icon-s')}Обрати Master…</button>
          <button class="btn btn-sm" data-act="master-recheck" ${s.secrets.printify_token.configured ? '' : 'disabled'}>${ic('refresh', 'icon-s')}Перечитати</button></div>
        <dl class="master-card card-soft" style="padding:12px 14px;margin:0">
          <dt>Магазин</dt><dd>${p.shopTitle || '—'} <span class="faint mono">#${p.shopId || '—'}</span></dd>
          <dt>Master</dt><dd>${m.title || '—'}</dd>
          <dt>Product ID</dt><dd class="mono" style="font-size:11.5px">${m.productId || '—'}</dd>
          <dt>Blueprint / постачальник</dt><dd>${m.blueprintId || '—'} / ${m.printProviderId || '—'}</dd>
          <dt>Увімкнені варіанти</dt><dd>${enabled.join(', ') || '—'}</dd>
          <dt>Позиції</dt><dd>cover + page_1…page_${p.pageCount}</dd>
          <dt>Обкладинка x / y</dt><dd class="mono" style="font-size:11.5px">${cover ? `${cover.x} / ${cover.y}` : '—'}</dd>
          <dt>Проаналізовано</dt><dd>${m.analyzedAt ? dateTime(m.analyzedAt) : 'еталонні значення'}</dd>
        </dl>
        <div class="row-wrap" style="gap:14px">
          <div class="field"><label class="field-label">Розмір Cover.png, px</label><div class="row"><input class="input" style="width:90px" id="pz-cw" value="${p.coverSize[0]}">×<input class="input" style="width:90px" id="pz-ch" value="${p.coverSize[1]}"></div></div>
          <div class="field"><label class="field-label">Розмір сторінок, px</label><div class="row"><input class="input" style="width:90px" id="pz-pw" value="${p.pageSize[0]}">×<input class="input" style="width:90px" id="pz-ph" value="${p.pageSize[1]}"></div></div>
          <button class="btn" data-act="sizes-save" style="align-self:flex-end">Зберегти розміри</button>
        </div>
        <div class="field-hint">Master лише читається: програма ніколи не змінює, не публікує і не видаляє його.</div>
      </div>
    </section>`;
  }

  function gelatoCard() {
    const g = s.gelato;
    return html`<section class="card card-pad" id="set-gelato">
      <div class="int-head" style="margin-bottom:18px">
        <div class="int-logo int-gelato">G</div>
        <div class="grow"><div class="card-title">Gelato <span class="faint mono" style="font-size:11.5px;font-weight:500">API v4 · X-API-KEY</span></div>
          <div class="card-sub">Собівартість замовлень і створення чернеток замовлень (draft)</div></div>
        ${s.secrets.gelato_api_key.configured ? html`<span class="chip chip-green chip-lg"><span class="dot"></span>Ключ є</span>` : html`<span class="chip chip-amber chip-lg">Немає ключа</span>`}
      </div>
      <div class="stack">
        ${secretField('gelato_api_key')}
        <div class="row"><button class="btn" data-act="gelato-test" ${s.secrets.gelato_api_key.configured ? '' : 'disabled'}>${ic('refresh', 'icon-s')}Перевірити зв'язок</button><span id="gelato-test" class="faint" style="font-size:12.5px"></span></div>
        <hr class="divider" style="margin:6px 0">
        <b>Формати фотокниг</b>
        <div class="card-soft" style="padding:4px 12px">${Object.entries(g.formats).map(([k, f]) => html`<div style="padding:8px 0;border-bottom:1px solid var(--border)">
          <div class="row"><b style="font-size:13px">${f.label}</b><span class="spacer"></span><span class="faint mono" style="font-size:11px">${k}</span></div>
          <div class="faint mono" style="font-size:10.5px;word-break:break-all">${f.productUid}</div></div>`)}</div>
        <div class="row-wrap" style="gap:14px">
          <div class="field"><label class="field-label">Курс EUR → USD</label><input class="input" style="width:110px" id="gl-rate" value="${g.eurUsdRate}"></div>
          <div class="field"><label class="field-label">Посилання на файли діє, хв</label><input class="input" style="width:110px" id="gl-keep" value="${Math.round(g.tunnelKeepAliveSeconds / 60)}"></div>
          <button class="btn" data-act="gelato-save" style="align-self:flex-end">Зберегти</button>
        </div>
        <div class="field-hint">Курс використовується для собівартості Gelato у євро (як у Profit Calculator: 1.085). Внутрішній блок: ${g.pageCount} сторінок.</div>
      </div>
    </section>`;
  }

  function uiCard() {
    const theme = localStorage.getItem('bs-theme') || s.ui.theme || 'dark';
    return html`<section class="card card-pad">
      <div class="int-head" style="margin-bottom:16px"><div class="int-logo int-ui">${ic('sun')}</div>
        <div class="grow"><div class="card-title">Вигляд</div><div class="card-sub">Тема та анімації інтерфейсу</div></div></div>
      <div class="stack">
        <div class="row"><span class="grow">Тема</span>${segHtml([{ value: 'dark', label: 'Темна', icon: 'moon' }, { value: 'light', label: 'Світла', icon: 'sun' }, { value: 'system', label: 'Як у Windows', icon: 'monitor' }], theme, { name: 'theme' })}</div>
        <label class="row" style="cursor:pointer"><span class="grow">Мінімум анімацій</span><span class="switch"><input type="checkbox" id="ui-motion" ${s.ui.reduceMotion ? 'checked' : ''}></span></label>
      </div></section>`;
  }

  function dataCard() {
    return html`<section class="card card-pad">
      <div class="int-head" style="margin-bottom:16px"><div class="int-logo int-ui">${ic('database')}</div>
        <div class="grow"><div class="card-title">Дані програми</div><div class="card-sub">Бібліотека, знімки замовлень, кеш і журнали зберігаються локально</div></div></div>
      <div class="info-box"><code>${s.dataDir}</code></div>
      <div class="row" style="margin-top:12px"><button class="btn" data-act="open-data">${ic('folder', 'icon-s')}Відкрити папку даних</button><span class="spacer"></span>
        <span class="faint" style="font-size:12px">Ключі зашифровані Windows (DPAPI) — працюють лише для вашого користувача Windows</span></div>
    </section>`;
  }

  function render() {
    setHtml(view, html`
      <div class="page-head"><div><h1 class="page-title">Налаштування</h1><div class="page-sub">Підключення до Etsy, Printify та Gelato, параметри книг і вигляд програми</div></div></div>
      <div class="settings-grid">
        ${legacyCard()}
        ${etsyCard()}
        ${printifyCard()}
        ${gelatoCard()}
        ${uiCard()}
        ${dataCard()}
      </div>`);
    requestAnimationFrame(() => view.querySelectorAll('.seg').forEach(syncSeg));
  }

  async function reload() {
    const y = document.getElementById('main').scrollTop;
    await load();
    render();
    document.getElementById('main').scrollTop = y;
    refreshInfo();
  }

  // ---------------------------------------------------------------- Etsy OAuth flow
  async function oauthFlow() {
    const confirmed = await new Promise((resolve) => {
      let ok = false;
      const safety = modal({
        title: 'Перевірка безпеки Etsy',
        sub: 'Захист від блокування через сторонній IP',
        body: html`<div class="stack">
          <div class="notice notice-warn">${ic('alert')}<div>Ви збираєтеся перейти на офіційну сторінку авторизації Etsy.<br><b>Переконайтеся, що ви зараз працюєте через віддалений київський комп'ютер</b>, де зареєстрований магазин. Якщо ви на польському ноутбуці чи телефоні — закрийте це вікно.</div></div>
          <label class="check card-soft" style="padding:12px"><input type="checkbox" id="kyiv-ok"><span style="font-weight:600">Я підтверджую, що відкриватиму вхід в Etsy на віддаленому київському комп'ютері</span></label>
        </div>`,
        foot: html`<button class="btn btn-ghost" data-c>Скасувати (я на звичайному ПК)</button><button class="btn btn-primary" data-go disabled>${ic('login', 'icon-s')}Продовжити</button>`,
        onClose: () => resolve(ok),
      });
      const go = safety.foot.querySelector('[data-go]');
      safety.el.querySelector('#kyiv-ok').addEventListener('change', (e) => { go.disabled = !e.target.checked; });
      safety.foot.querySelector('[data-c]').onclick = () => safety.close();
      go.onclick = () => { ok = true; safety.close(); };
    });
    if (!confirmed) return;

    let start;
    try { start = await api('/api/etsy/oauth/start', { method: 'POST', body: {} }); }
    catch (err) { toast(err.message, 'error'); return; }
    let polling = true;
    const m = modal({
      title: 'Авторизація Etsy',
      sub: 'Оберіть, де ви зараз працюєте',
      size: 'l',
      body: html`<div class="stack">
        <div class="card-soft stack-s" style="padding:14px">
          <b>Варіант 1 — програма запущена на київському комп'ютері</b>
          <div class="faint" style="font-size:12.5px">Сторінка входу відкриється у вашому браузері. Після підтвердження Etsy поверне вас у програму автоматично.</div>
          <div><button class="btn btn-primary btn-sm" data-x="open">${ic('external', 'icon-s')}Відкрити сторінку входу Etsy</button></div>
        </div>
        <div class="card-soft stack-s" style="padding:14px">
          <b>Варіант 2 — програма на цьому ПК, а вхід робите на київському</b>
          <div class="faint" style="font-size:12.5px">1) Скопіюйте посилання і відкрийте його в браузері на київському ПК. 2) Підтвердіть доступ. 3) Браузер перейде на адресу <span class="mono">localhost</span>, яка не відкриється — це нормально: скопіюйте повну адресу з рядка браузера й вставте нижче.</div>
          <div><button class="btn btn-sm" data-x="copy">${ic('copy', 'icon-s')}Скопіювати посилання для Києва</button></div>
          <div class="row" style="margin-top:4px"><input class="input mono" id="oauth-back" placeholder="${start.redirectUri}?code=…&state=…" autocomplete="off" spellcheck="false">
            <button class="btn btn-primary" data-x="finish">Завершити</button></div>
        </div>
        <div class="row faint" style="font-size:12px"><span class="spinner" style="width:14px;height:14px"></span>Очікування підтвердження від Etsy… Посилання дійсне 60 хвилин.</div>
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
          const res = await api('/api/etsy/oauth/complete', { method: 'POST', body: { url } });
          polling = false; m.close();
          toast(`Etsy підключено${res.shopName ? `: ${res.shopName}` : ''}`, 'success');
          reload();
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
          if (st.connected) { polling = false; m.close(); toast(`Etsy підключено${st.shopName ? `: ${st.shopName}` : ''}`, 'success'); reload(); }
        } catch { /* ignore */ }
      }
    })();
  }

  // ---------------------------------------------------------------- Printify master
  async function pickMaster() {
    let shops;
    try { shops = (await api('/api/printify/shops')).shops; } catch (err) { toast(err.message, 'error'); return; }
    let shopId = s.printify.shopId && shops.some((x) => x.id === s.printify.shopId) ? s.printify.shopId : shops[0]?.id;
    let selected = s.printify.master?.productId || null;
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
          <div><b style="display:block" class="truncate">${p.title}</b><span class="faint mono" style="font-size:10.5px">bp ${p.blueprintId} · ${p.id.slice(-6)}</span></div></button>`);
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
        analysis = await api('/api/printify/master/analyze', { method: 'POST', body: { shopId, productId } });
        const bad = analysis.pageCount !== 24;
        setHtml(m.el.querySelector('#mp-analysis'), html`<div class="card-soft" style="padding:14px">
          <div style="font-weight:650;margin-bottom:8px">${analysis.title}</div>
          <dl class="master-card">
            <dt>Blueprint / постачальник</dt><dd>${analysis.blueprintId} / ${analysis.printProviderId}</dd>
            <dt>Позиції</dt><dd>cover + ${analysis.pageCount} сторінок</dd>
            <dt>Увімкнені варіанти</dt><dd>${analysis.enabledVariants.join(', ') || '—'}</dd>
            <dt>Розміри artwork</dt><dd>обкладинка ${(analysis.coverSize || []).join('×') || '—'} · сторінки ${(analysis.pageSize || []).join('×') || '—'}</dd>
            <dt>Обкладинка x / y / scale</dt><dd class="mono" style="font-size:11.5px">${analysis.placements.cover.x} / ${analysis.placements.cover.y} / ${analysis.placements.cover.scale}</dd>
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
          await api('/api/printify/master/save', { method: 'POST', body: { analysis, shopId, shopTitle: shop?.title } });
          m.close(); toast('Master-продукт збережено', 'success'); reload();
        } catch (err) { toast(err.message, 'error'); }
      }
    });
    loadProducts();
  }

  async function recheckMaster() {
    const p = s.printify;
    toast('Читаю Master із Printify…', 'info', 1500);
    try {
      const analysis = await api('/api/printify/master/analyze', { method: 'POST', body: { shopId: p.shopId, productId: p.master.productId } });
      const cur = p.master;
      const same = analysis.blueprintId === cur.blueprintId && analysis.printProviderId === cur.printProviderId
        && JSON.stringify(analysis.placements) === JSON.stringify(cur.placements)
        && JSON.stringify(analysis.variants.map((v) => [v.id, v.price, v.is_enabled])) === JSON.stringify((cur.variants || []).map((v) => [v.id, v.price, v.is_enabled]));
      if (same) { toast('Master не змінився — конфігурація актуальна', 'success'); return; }
      const ok = await confirmBox({ title: 'Master у Printify відрізняється', text: 'Конфігурація продукту в Printify не збігається зі збереженою. Оновити збережену конфігурацію?', confirm: 'Оновити' });
      if (!ok) return;
      await api('/api/printify/master/save', { method: 'POST', body: { analysis, shopId: p.shopId, shopTitle: p.shopTitle } });
      toast('Конфігурацію Master оновлено', 'success');
      reload();
    } catch (err) { toast(err.message, 'error'); }
  }

  // ---------------------------------------------------------------- events
  const offs = [
    on(view, 'click', '[data-secret-edit]', (e, b) => { editing.add(b.dataset.secretEdit); render(); view.querySelector(`[data-secret-input="${b.dataset.secretEdit}"]`)?.focus(); }),
    on(view, 'click', '[data-secret-cancel]', (e, b) => { editing.delete(b.dataset.secretCancel); render(); }),
    on(view, 'click', '[data-secret-save]', async (e, b) => {
      const name = b.dataset.secretSave;
      const value = view.querySelector(`[data-secret-input="${name}"]`).value.trim();
      if (!value) { toast('Вставте значення', 'error'); return; }
      try { await api('/api/secrets', { method: 'POST', body: { name, value } }); editing.delete(name); toast('Збережено у зашифрованому сховищі', 'success'); reload(); }
      catch (err) { toast(err.message, 'error'); }
    }),
    on(view, 'click', '[data-secret-clear]', async (e, b) => {
      const ok = await confirmBox({ title: 'Видалити ключ?', text: 'Програма більше не зможе звертатися до цього сервісу, доки ви не збережете ключ знову.', confirm: 'Видалити', danger: true });
      if (!ok) return;
      try { await api('/api/secrets', { method: 'POST', body: { name: b.dataset.secretClear, value: '' } }); reload(); } catch (err) { toast(err.message, 'error'); }
    }),
    on(view, 'keydown', '[data-secret-input]', (e, i) => { if (e.key === 'Enter') view.querySelector(`[data-secret-save="${i.dataset.secretInput}"]`).click(); }),
    on(view, 'click', '[data-copy-text]', (e, b) => copyText(b.dataset.copyText)),
    on(view, 'click', '[data-seg="theme"] button', async (e, b) => {
      setSeg(b.closest('.seg'), b.dataset.value);
      applyTheme(b.dataset.value);
      await api('/api/settings/ui', { method: 'POST', body: { theme: b.dataset.value } }).catch(() => {});
      refreshInfo();
    }),
    on(view, 'click', '[data-act]', async (e, b) => {
      const a = b.dataset.act;
      if (a === 'legacy-import') {
        b.disabled = true;
        try {
          const r = await api('/api/settings/legacy/import', { method: 'POST', body: {} });
          toast(`Імпортовано: ${r.imported.length} ${r.imported.length === 1 ? 'ключ' : 'ключі'}${r.uploadCache ? `, кеш ${r.uploadCache} зображень` : ''}`, 'success');
          reload();
        } catch (err) { toast(err.message, 'error'); b.disabled = false; }
      } else if (a === 'etsy-import') {
        const key = view.querySelector('#etsy-key').value.trim();
        if (!key) { toast('Вставте посилання або ключ сесії', 'error'); return; }
        b.disabled = true;
        try {
          const r = await api('/api/etsy/session/import', { method: 'POST', body: { key } });
          toast(r.warning ? `Сесію збережено, але перевірити зараз не вдалося: ${r.warning}` : `Etsy підключено${r.shopName ? `: ${r.shopName}` : ''}`, r.warning ? 'info' : 'success', 6000);
          reload();
        } catch (err) { toast(err.message, 'error', 8000); b.disabled = false; }
      } else if (a === 'etsy-oauth') oauthFlow();
      else if (a === 'etsy-disconnect') {
        const ok = await confirmBox({ title: 'Відключити Etsy?', text: 'Токени доступу буде видалено з цього комп’ютера. Дані в Etsy не змінюються.', confirm: 'Відключити', danger: true });
        if (!ok) return;
        await api('/api/etsy/disconnect', { method: 'POST', body: {} }).catch((er) => toast(er.message, 'error'));
        reload();
      } else if (a === 'etsy-export') {
        try { const r = await api('/api/etsy/session/export'); copyText(r.key, 'Ключ сесії скопійовано — зберігайте його як пароль'); }
        catch (err) { toast(err.message, 'error'); }
      } else if (a === 'redirect-edit') {
        const m = modal({
          title: 'Адреса повернення (Redirect URI)',
          body: html`<div class="stack"><input class="input mono" id="ru" value="${s.etsy.redirectUri}"><div class="field-hint">За замовчуванням: <span class="mono">${s.etsy.defaultRedirectUri}</span>. Адреса має точно збігатися з доданою в Etsy Developers. Порожнє поле — повернути стандартну.</div></div>`,
          foot: html`<button class="btn btn-ghost" data-c>Скасувати</button><button class="btn btn-primary" data-ok>Зберегти</button>`,
        });
        m.foot.querySelector('[data-c]').onclick = () => m.close();
        m.foot.querySelector('[data-ok]').onclick = async () => {
          let v = m.el.querySelector('#ru').value.trim();
          if (v === s.etsy.defaultRedirectUri) v = '';
          try { await api('/api/settings/etsy', { method: 'POST', body: { redirectUri: v } }); m.close(); reload(); } catch (err) { toast(err.message, 'error'); }
        };
      } else if (a === 'printify-test') {
        const out = view.querySelector('#printify-test');
        out.innerHTML = '<span class="spinner" style="width:14px;height:14px;display:inline-block;vertical-align:middle"></span> Перевірка…';
        try { const r = await api('/api/printify/test', { method: 'POST', body: {} }); setHtml(out, html`<span style="color:var(--green)">${ic('checkCircle', 'icon-s')} З'єднання успішне! Магазин: <b>${r.shopTitle}</b> · замовлень: ${r.ordersCount ?? '—'}</span>`); }
        catch (err) { setHtml(out, html`<span style="color:var(--red)">${err.message}</span>`); }
      } else if (a === 'gelato-test') {
        const out = view.querySelector('#gelato-test');
        out.innerHTML = '<span class="spinner" style="width:14px;height:14px;display:inline-block;vertical-align:middle"></span> Перевірка…';
        try { const r = await api('/api/gelato/test', { method: 'POST', body: {} }); setHtml(out, html`<span style="color:var(--green)">${ic('checkCircle', 'icon-s')} ${r.message}</span>`); }
        catch (err) { setHtml(out, html`<span style="color:var(--red)">${err.message}</span>`); }
      } else if (a === 'master-pick') pickMaster();
      else if (a === 'master-recheck') recheckMaster();
      else if (a === 'sizes-save') {
        const n = (id) => parseInt(view.querySelector(id).value, 10);
        try { await api('/api/settings/printify', { method: 'POST', body: { coverSize: [n('#pz-cw'), n('#pz-ch')], pageSize: [n('#pz-pw'), n('#pz-ph')] } }); toast('Розміри збережено', 'success'); reload(); }
        catch (err) { toast(err.message, 'error'); }
      } else if (a === 'gelato-save') {
        try {
          await api('/api/settings/gelato', { method: 'POST', body: { eurUsdRate: view.querySelector('#gl-rate').value.replace(',', '.'), tunnelKeepAliveSeconds: parseInt(view.querySelector('#gl-keep').value, 10) * 60 } });
          toast('Збережено', 'success'); reload();
        } catch (err) { toast(err.message, 'error'); }
      } else if (a === 'open-data') api('/api/app/open-data', { method: 'POST', body: {} }).catch((er) => toast(er.message, 'error'));
    }),
  ];
  view.addEventListener('change', async (e) => {
    if (e.target.id === 'ui-motion') {
      applyMotion(e.target.checked);
      await api('/api/settings/ui', { method: 'POST', body: { reduceMotion: e.target.checked } }).catch(() => {});
    }
  });

  await load();
  render();
  return {
    shown() {
      const target = section && view.querySelector(`#set-${section}`);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },
    unmount() { offs.forEach((f) => f()); },
  };
}

