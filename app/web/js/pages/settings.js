// Settings: keys (encrypted with Windows DPAPI), Etsy connection, Printify Master, Gelato, the text check
// by a local model (Ollama), data folder.
// Every block is collapsed to one line with its status; the rare technical values live one more
// click away, behind the details toggle, so the page stays quiet. Theme lives only in the rail.
import {
  api, post, html, ic, ib, setHtml, on, modal, toast, confirmBox, copyText, openExternal,
  dateTime, sleep, slide, menu, remembered, remember, confirmChecked,
} from '../lib.js';
import { refreshInfo } from '../info.js';

const SECRET_LABELS = {
  etsy_keystring: ['Etsy Keystring', 'Etsy Developers → Your apps → Keystring'],
  etsy_shared_secret: ['Etsy Shared Secret', 'Там само, поле Shared Secret'],
  printify_token: ['Printify Personal Access Token', 'Printify → My account → Connections → API'],
  gelato_api_key: ['Gelato API-ключ', 'Gelato Dashboard → Developer → API keys'],
};
const OPEN_KEY = 'bs-settings-open';

export async function mount(view, [section]) {
  let s;
  let tc = null; // text check: on/off, model, whether Ollama answers (asked separately — never slows the page)
  const editing = new Set();
  const openCards = new Set(remembered(OPEN_KEY, []));
  const openDetails = new Set();
  if (section) openCards.add(section);
  const persistOpen = () => remember(OPEN_KEY, [...openCards]);

  async function load() {
    s = await api('/api/settings');
    // The text-check block is drawn at once from the settings; whether Ollama answers comes a moment later.
    if (!tc) tc = { ...s.textcheck, models: [], pending: true };
    // A block that needs the user's attention opens by itself.
    if (!s.etsy.connected || s.etsy.portWarning) openCards.add('etsy');
    if (!s.secrets.printify_token.configured) openCards.add('printify');
    if (!s.secrets.gelato_api_key.configured) openCards.add('gelato');
  }

  // Connection state as a mark, not a word: green = works, amber = needs something.
  const stateMark = (ok, tip) => html`<span class="state-mark ${ok ? 'ok' : 'warn'}" data-tip="${tip}" aria-label="${tip}">${ic(ok ? 'checkCircle' : 'alertCircle')}</span>`;

  /** One collapsible block: header line with a status, body with the essentials. */
  function card(id, { logo, logoClass, title, summary, mark = '', body }) {
    const open = openCards.has(id);
    return html`<section class="set-card ${open ? 'open' : ''}" id="set-${id}">
      <button class="set-head" data-card="${id}" aria-expanded="${open ? 'true' : 'false'}">
        <span class="int-logo ${logoClass}">${logo}</span>
        <span class="grow">
          <span class="set-title">${title}</span>
          <span class="set-sum truncate">${summary}</span>
        </span>
        ${mark}
        <span class="chev">${ic('chevDown', 'icon-s')}</span>
      </button>
      <div class="acc ${open ? 'open' : ''}" data-body="${id}"><div class="set-body">${body}</div></div>
    </section>`;
  }

  /** Rarely needed values, hidden behind one more click inside a block. */
  function details(id, content) {
    const open = openDetails.has(id);
    return html`<div class="set-details">
      ${ib('chevDown', open ? 'Сховати подробиці' : 'Подробиці', `data-details="${id}" aria-expanded="${open}"`, { cls: `sm details-toggle ${open ? 'on' : ''}` })}
      <div class="acc ${open ? 'open' : ''}" data-details-body="${id}"><div class="stack" style="padding-top:10px">${content}</div></div>
    </div>`;
  }

  function secretField(name) {
    const st = s.secrets[name];
    const [label, hint] = SECRET_LABELS[name];
    const edit = editing.has(name) || !st.configured;
    return html`<div class="field">
      <label class="field-label">${label}</label>
      ${edit ? html`<div class="secret-row"><input class="input mono" type="password" data-secret-input="${name}" placeholder="Вставте значення" autocomplete="off" spellcheck="false" aria-label="${label}">
          ${ib('check', 'Зберегти', `data-secret-save="${name}"`, { cls: 'primary', kbd: 'Enter' })}
          ${st.configured ? ib('x', 'Скасувати', `data-secret-cancel="${name}"`) : ''}</div>`
        : html`<div class="secret-row"><div class="secret-state">${ic('lock', 'icon-s')}<span>Збережено</span><span class="mono">${st.hint}</span></div>
          ${ib('edit', 'Замінити ключ', `data-secret-edit="${name}"`)}
          ${ib('trash', 'Видалити ключ', `data-secret-clear="${name}"`, { cls: 'danger' })}</div>`}
      <div class="field-hint">${hint}</div>
    </div>`;
  }

  // ---------------------------------------------------------------- sections
  function legacyCard() {
    const items = (s.legacy?.items || []).filter((i) => !i.alreadySet);
    const cache = s.legacy?.uploadCache || 0;
    if (!items.length) return '';
    return html`<section class="set-card set-hint">
      <div class="set-head" style="cursor:default">
        <span class="int-logo">${ic('key')}</span>
        <span class="grow"><span class="set-title">Знайдено ключі з попередніх програм</span>
          <span class="set-sum truncate">${items.map((i) => i.label).join(', ')}${cache ? ` · кеш Printify ${cache}` : ''}</span></span>
        <button class="btn btn-primary btn-sm" data-act="legacy-import">${ic('download', 'icon-s')}Перенести</button>
      </div></section>`;
  }

  function etsyCard() {
    const e = s.etsy;
    const connected = e.connected;
    // Keys that are still missing are the first thing to fill in; saved ones move to the details.
    const missing = ['etsy_keystring', 'etsy_shared_secret'].filter((n) => !s.secrets[n].configured);
    const saved = ['etsy_keystring', 'etsy_shared_secret'].filter((n) => s.secrets[n].configured);
    const main = connected
      ? html`<div class="set-row">
          <span class="grow">Магазин <b>${e.shopName || '—'}</b> <span class="faint">· лише читання · доступ оновлюється сам</span></span>
          ${ib('unplug', 'Відключити Etsy', 'data-act="etsy-disconnect"', { cls: 'danger' })}
        </div>`
      : html`<div class="stack-s">
          <div class="input-group">${ic('link')}<input class="input mono" id="etsy-key" placeholder="Лінк доступу з Etsy Profit Calculator (…/?sync=…)" autocomplete="off" spellcheck="false" aria-label="Лінк доступу Etsy" style="padding-right:40px">
            ${ib('check', 'Підключити за лінком', `data-act="etsy-import" ${e.keysConfigured ? '' : 'disabled'}`, { cls: 'primary', kbd: 'Enter' })}</div>
          <div class="set-row"><span class="grow faint">або вхід в Etsy з київського комп'ютера</span>
            ${ib('login', 'Увійти в Etsy (лише з київського ПК)', `data-act="etsy-oauth" ${e.keysConfigured ? '' : 'disabled'}`)}</div>
        </div>`;
    return card('etsy', {
      logo: ic('etsy'), logoClass: 'int-etsy', title: 'Etsy',
      summary: connected ? `${e.shopName || 'Магазин'} · замовлення й лістинги` : (e.keysConfigured ? 'Потрібен вхід' : 'Немає ключів'),
      mark: stateMark(connected, connected ? 'Підключено' : 'Не підключено'),
      body: html`<div class="stack">
        ${missing.map(secretField)}
        ${main}
        ${e.portWarning ? html`<div class="notice notice-warn">${ic('alert')}<div>${e.portWarning}</div></div>` : ''}
        ${details('etsy', html`
          ${saved.map(secretField)}
          <div class="field"><label class="field-label">Адреса повернення (Callback URL)</label>
            <div class="row"><code class="grow code-line">${e.redirectUri}</code>
              ${ib('copy', 'Копіювати адресу', `data-copy-text="${e.redirectUri}"`)}
              ${ib('edit', 'Змінити адресу', 'data-act="redirect-edit"')}</div>
            <div class="field-hint">Має бути додана в Etsy Developers → Your apps → Callback URLs.</div></div>
          ${connected ? html`<div class="set-row"><span class="grow">Ключ сесії для іншого комп'ютера${e.expiresAt ? html` <span class="faint">· токен до ${dateTime(e.expiresAt)}</span>` : ''}</span>
            ${ib('key', 'Копіювати ключ сесії', 'data-act="etsy-export"')}</div>` : ''}`)}
      </div>`,
    });
  }

  // Printify and Gelato show only the key and the book templates in use; the technical values
  // (Master placements, artwork sizes, product UIDs, link lifetime) stay fixed and out of sight.
  function printifyCard() {
    const p = s.printify;
    const m = p.master || {};
    const has = s.secrets.printify_token.configured;
    return card('printify', {
      logo: ic('printify'), logoClass: 'int-printify', title: 'Printify',
      summary: has ? `${p.shopTitle || 'Магазин не обрано'} · ${m.title || 'шаблон не обрано'}` : 'Потрібен токен',
      mark: stateMark(has, has ? 'Підключено' : 'Немає токена'),
      body: html`<div class="stack">
        ${secretField('printify_token')}
        <div class="set-row">${ic('book')}<span class="grow">${m.title || 'Шаблон не обрано'} <span class="faint">· <span class="num">${p.pageCount}</span> стор.</span></span>
          ${m.productId ? '' : ib('template', 'Обрати шаблон (Master)', `data-act="master-pick" ${has ? '' : 'disabled'}`)}
          ${ib('pulse', 'Перевірити зв\'язок', `data-act="printify-test" ${has ? '' : 'disabled'}`)}</div>
        <div id="printify-test" class="faint" style="font-size:12.5px" hidden></div>
      </div>`,
    });
  }

  function gelatoCard() {
    const g = s.gelato;
    const has = s.secrets.gelato_api_key.configured;
    const formats = Object.values(g.formats).map((f) => f.label);
    return card('gelato', {
      logo: ic('gelato'), logoClass: 'int-gelato', title: 'Gelato',
      summary: has ? formats.join(' · ') : 'Потрібен ключ',
      mark: stateMark(has, has ? 'Підключено' : 'Немає ключа'),
      body: html`<div class="stack">
        ${secretField('gelato_api_key')}
        <div class="set-row">${ic('book')}<span class="grow">${formats.join(' · ')} <span class="faint">· <span class="num">${(g.pageCounts || []).join(' або ')}</span> стор.</span></span>
          ${ib('pulse', 'Перевірити зв\'язок', `data-act="gelato-test" ${has ? '' : 'disabled'}`)}</div>
        <div id="gelato-test" class="faint" style="font-size:12.5px" hidden></div>
      </div>`,
    });
  }

  // The text check reads the order's pages with a model in Ollama on this computer (textcheck/).
  function textcheckCard() {
    if (!tc) return '';
    const ready = tc.running && tc.installed;
    const summary = !tc.enabled ? 'Вимкнено' : tc.pending ? `${tc.model} · перевірка стану…` : !tc.running ? 'Ollama не запущена'
      : !tc.installed ? `Немає моделі ${tc.model}` : `${tc.model} · на цьому комп'ютері`;
    return card('textcheck', {
      logo: ic('textScan'), logoClass: 'int-ui', title: 'Перевірка тексту', summary,
      mark: tc.enabled && !tc.pending ? stateMark(ready, ready ? 'Працює' : summary) : '',
      body: html`<div class="stack">
        <label class="set-row"><span class="grow">Перевіряти текст сторінок у картці замовлення</span>
          <span class="switch"><input type="checkbox" data-tc-enabled ${tc.enabled ? 'checked' : ''} aria-label="Перевіряти текст сторінок"></span></label>
        <label class="set-row"><span class="grow">Спершу швидко дивитися, на яких сторінках узагалі є текст<span class="faint"> — модель читає лише їх</span></span>
          <span class="switch"><input type="checkbox" data-tc-prescan ${tc.prescan ? 'checked' : ''} aria-label="Швидкий огляд сторінок перед перевіркою"></span></label>
        <div class="set-row">${ic('sparkle')}<span class="grow">Модель <b>${tc.model}</b>${tc.loaded ? html` <span class="faint">· у відеокарті</span>` : ''}</span>
          ${tc.models.length > 1 ? ib('swap', 'Обрати модель', 'data-act="tc-model"') : ''}
          ${ib('pulse', 'Перевірити зв\'язок', 'data-act="tc-test"')}</div>
        ${tc.pending ? '' : !tc.running ? html`<div class="notice notice-warn">${ic('alert')}<div class="grow">${tc.canStart
            ? 'Ollama не запущена — програма запустить її сама, коли прийде час перевірки.'
            : 'Ollama не знайдена на цьому комп\'ютері.'}</div>${tc.canStart ? html`<button class="btn btn-sm" data-act="tc-start">Запустити</button>` : ''}</div>`
          : !tc.installed ? html`<div class="notice notice-warn">${ic('alert')}<div>В Ollama немає моделі ${tc.model}${tc.models.length ? ' — оберіть іншу' : ''}.</div></div>` : ''}
        <div id="tc-test" class="faint" style="font-size:12.5px" hidden></div>
      </div>`,
    });
  }

  async function loadTextcheck() {
    try { tc = await api('/api/textcheck/status'); } catch { return; } // the block stays as drawn from the settings
    const old = view.querySelector('#set-textcheck');
    if (!view.isConnected || !tc) return;
    if (old) old.outerHTML = String(textcheckCard());
    else view.querySelector('#set-data')?.insertAdjacentHTML('beforebegin', String(textcheckCard()));
  }

  async function saveTextcheck(patch) {
    try { tc = await post('/api/settings/textcheck', patch); }
    catch (err) { toast(err.message, 'error'); }
    const old = view.querySelector('#set-textcheck');
    if (old && tc) old.outerHTML = String(textcheckCard());
  }

  function dataCard() {
    return card('data', {
      logo: ic('database'), logoClass: 'int-ui', title: 'Дані програми',
      summary: 'Книги, замовлення й ключі — лише на цьому комп\'ютері',
      body: html`<div class="set-row"><code class="grow code-line">${s.dataDir}</code>
        ${ib('folderOpen', 'Відкрити папку даних', 'data-act="open-data"')}</div>`,
    });
  }

  function render() {
    setHtml(view, html`
      <div class="page-head"><div><h1 class="page-title">Налаштування</h1><div class="page-sub">Підключення до сервісів і файли програми</div></div></div>
      <div class="set-list">
        ${legacyCard()}
        ${etsyCard()}
        ${printifyCard()}
        ${gelatoCard()}
        ${textcheckCard()}
        ${dataCard()}
      </div>`);
  }

  // Blocks open and close with real intermediate frames (measured height, Web Animations).
  function toggleCard(id) {
    const cardEl = view.querySelector(`#set-${id}`);
    const body = view.querySelector(`[data-body="${id}"]`);
    if (!cardEl || !body) return;
    const open = !openCards.has(id);
    if (open) openCards.add(id); else openCards.delete(id);
    persistOpen();
    cardEl.classList.toggle('open', open);
    cardEl.querySelector('.set-head').setAttribute('aria-expanded', open ? 'true' : 'false');
    slide(body, open);
  }
  function toggleDetails(id, btn) {
    const body = view.querySelector(`[data-details-body="${id}"]`);
    if (!body) return;
    const open = !openDetails.has(id);
    if (open) openDetails.add(id); else openDetails.delete(id);
    const tip = open ? 'Сховати подробиці' : 'Подробиці';
    btn.classList.toggle('on', open);
    btn.dataset.tip = tip; btn.setAttribute('aria-label', tip); btn.setAttribute('aria-expanded', String(open));
    slide(body, open);
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
          const res = await post('/api/etsy/oauth/complete', { url });
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
        analysis = await post('/api/printify/master/analyze', { shopId, productId });
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
          await post('/api/printify/master/save', { analysis, shopId, shopTitle: shop?.title });
          m.close(); toast('Master-продукт збережено', 'success'); reload();
        } catch (err) { toast(err.message, 'error'); }
      }
    });
    loadProducts();
  }

  // ---------------------------------------------------------------- events
  const offs = [
    on(view, 'click', '[data-card]', (e, b) => toggleCard(b.dataset.card)),
    on(view, 'click', '[data-details]', (e, b) => toggleDetails(b.dataset.details, b)),
    on(view, 'click', '[data-secret-edit]', (e, b) => { editing.add(b.dataset.secretEdit); render(); view.querySelector(`[data-secret-input="${b.dataset.secretEdit}"]`)?.focus(); }),
    on(view, 'click', '[data-secret-cancel]', (e, b) => { editing.delete(b.dataset.secretCancel); render(); }),
    on(view, 'click', '[data-secret-save]', async (e, b) => {
      const name = b.dataset.secretSave;
      const value = view.querySelector(`[data-secret-input="${name}"]`).value.trim();
      if (!value) { toast('Вставте значення', 'error'); return; }
      try { await post('/api/secrets', { name, value }); editing.delete(name); toast('Збережено у зашифрованому сховищі', 'success'); reload(); }
      catch (err) { toast(err.message, 'error'); }
    }),
    on(view, 'click', '[data-secret-clear]', async (e, b) => {
      const ok = await confirmBox({ title: 'Видалити ключ?', text: 'Програма більше не зможе звертатися до цього сервісу, доки ви не збережете ключ знову.', confirm: 'Видалити', danger: true });
      if (!ok) return;
      try { await post('/api/secrets', { name: b.dataset.secretClear, value: '' }); reload(); } catch (err) { toast(err.message, 'error'); }
    }),
    on(view, 'keydown', '[data-secret-input]', (e, i) => { if (e.key === 'Enter') view.querySelector(`[data-secret-save="${i.dataset.secretInput}"]`).click(); }),
    on(view, 'click', '[data-copy-text]', (e, b) => copyText(b.dataset.copyText)),
    on(view, 'click', '[data-act]', async (e, b) => {
      const a = b.dataset.act;
      if (a === 'legacy-import') {
        b.disabled = true;
        try {
          const r = await post('/api/settings/legacy/import', {});
          toast(`Імпортовано: ${r.imported.length} ${r.imported.length === 1 ? 'ключ' : 'ключі'}${r.uploadCache ? `, кеш ${r.uploadCache} зображень` : ''}`, 'success');
          reload();
        } catch (err) { toast(err.message, 'error'); b.disabled = false; }
      } else if (a === 'etsy-import') {
        const key = view.querySelector('#etsy-key').value.trim();
        if (!key) { toast('Вставте посилання або ключ сесії', 'error'); return; }
        b.disabled = true;
        try {
          const r = await post('/api/etsy/session/import', { key });
          toast(r.warning ? `Сесію збережено, але перевірити зараз не вдалося: ${r.warning}` : `Etsy підключено${r.shopName ? `: ${r.shopName}` : ''}`, r.warning ? 'info' : 'success', 6000);
          reload();
        } catch (err) { toast(err.message, 'error', 8000); b.disabled = false; }
      } else if (a === 'etsy-oauth') oauthFlow();
      else if (a === 'etsy-disconnect') {
        const ok = await confirmBox({ title: 'Відключити Etsy?', text: 'Токени доступу буде видалено з цього комп’ютера. Дані в Etsy не змінюються.', confirm: 'Відключити', danger: true });
        if (!ok) return;
        await post('/api/etsy/disconnect', {}).catch((er) => toast(er.message, 'error'));
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
          try { await post('/api/settings/etsy', { redirectUri: v }); m.close(); reload(); } catch (err) { toast(err.message, 'error'); }
        };
      } else if (a === 'printify-test' || a === 'gelato-test') {
        const out = view.querySelector(`#${a}`);
        out.hidden = false;
        setHtml(out, html`<span class="row"><span class="spinner" style="width:14px;height:14px"></span>Перевірка зв'язку…</span>`);
        b.disabled = true;
        try {
          const r = await post(a === 'printify-test' ? '/api/printify/test' : '/api/gelato/test', {});
          setHtml(out, html`<span class="row" style="color:var(--green)">${ic('checkCircle', 'icon-s')}${a === 'printify-test' ? html`Працює · <b>${r.shopTitle}</b> · замовлень: <span class="num">${r.ordersCount ?? '—'}</span>` : r.message}</span>`);
        } catch (err) { setHtml(out, html`<span class="row" style="color:var(--red)">${ic('alertCircle', 'icon-s')}${err.message}</span>`); }
        finally { b.disabled = false; }
      } else if (a === 'master-pick') pickMaster();
      else if (a === 'open-data') post('/api/app/open-data', {}).catch((er) => toast(er.message, 'error'));
      else if (a === 'tc-model') {
        menu(b, tc.models.map((m) => ({ label: m, icon: 'sparkle', on: m === tc.model, onClick: () => saveTextcheck({ model: m }) })));
      } else if (a === 'tc-start') {
        b.disabled = true;
        try { tc = await post('/api/textcheck/start', {}); toast('Ollama запущено', 'success'); }
        catch (err) { toast(err.message, 'error'); }
        loadTextcheck();
      } else if (a === 'tc-test') {
        const out = view.querySelector('#tc-test');
        out.hidden = false;
        setHtml(out, html`<span class="row"><span class="spinner" style="width:14px;height:14px"></span>Перевірка зв'язку…</span>`);
        await loadTextcheck();
        const res = view.querySelector('#tc-test');
        if (!res) return;
        res.hidden = false;
        const ok = tc?.running && tc.installed;
        setHtml(res, ok
          ? html`<span class="row" style="color:var(--green)">${ic('checkCircle', 'icon-s')}Працює · Ollama <span class="num">${tc.version}</span> · модель на місці</span>`
          : html`<span class="row" style="color:var(--red)">${ic('alertCircle', 'icon-s')}${!tc?.running ? 'Ollama не відповідає' : `В Ollama немає моделі ${tc.model}`}</span>`);
      }
    }),
    on(view, 'change', '[data-tc-enabled]', (e, i) => saveTextcheck({ enabled: i.checked })),
    on(view, 'change', '[data-tc-prescan]', (e, i) => saveTextcheck({ prescan: i.checked })),
  ];
  view.addEventListener('keydown', (e) => { if (e.target.id === 'etsy-key' && e.key === 'Enter') view.querySelector('[data-act="etsy-import"]')?.click(); });

  await load();
  render();
  loadTextcheck();
  return {
    shown() {
      const target = section && view.querySelector(`#set-${section}`);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },
    unmount() { offs.forEach((f) => f()); },
  };
}

