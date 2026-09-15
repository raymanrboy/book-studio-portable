// Order Creator: Printify unpublished photo books and Gelato draft orders from Canva PNG folders.
import {
  api, html, ic, raw, setHtml, on, media, modal, toast, runJob, segHtml, syncSeg, setSeg, bytes, dateTime,
  relTime, copyText, openExternal, debounce, keepFocus, fadeImages,
} from '../lib.js';
import { openLightbox } from '../lightbox.js';

const COUNTRIES = [
  ['US', 'США'], ['CA', 'Канада'], ['GB', 'Велика Британія'], ['AU', 'Австралія'], ['NZ', 'Нова Зеландія'], ['IE', 'Ірландія'],
  ['DE', 'Німеччина'], ['FR', 'Франція'], ['IT', 'Італія'], ['ES', 'Іспанія'], ['PT', 'Португалія'], ['NL', 'Нідерланди'],
  ['BE', 'Бельгія'], ['LU', 'Люксембург'], ['AT', 'Австрія'], ['CH', 'Швейцарія'], ['PL', 'Польща'], ['CZ', 'Чехія'],
  ['SK', 'Словаччина'], ['HU', 'Угорщина'], ['RO', 'Румунія'], ['BG', 'Болгарія'], ['GR', 'Греція'], ['HR', 'Хорватія'],
  ['SI', 'Словенія'], ['DK', 'Данія'], ['SE', 'Швеція'], ['NO', 'Норвегія'], ['FI', 'Фінляндія'], ['EE', 'Естонія'],
  ['LV', 'Латвія'], ['LT', 'Литва'], ['UA', 'Україна'], ['IL', 'Ізраїль'], ['AE', 'ОАЕ'], ['SG', 'Сінгапур'],
  ['JP', 'Японія'], ['KR', 'Південна Корея'], ['MX', 'Мексика'], ['BR', 'Бразилія'], ['ZA', 'ПАР'],
];
const ADDRESS_FIELDS = ['firstName', 'lastName', 'addressLine1', 'addressLine2', 'city', 'state', 'postCode', 'country', 'phone'];

export async function mount(view) {
  let status;
  try { status = await api('/api/creator/status'); }
  catch (err) { setHtml(view, html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`); return null; }

  const prefs = status.creator || {};
  const st = {
    mode: prefs.mode === 'gelato' ? 'gelato' : 'printify',
    printify: { folder: prefs.printifyFolder || '', title: '', validation: null, validating: 0, running: false, result: null, error: null },
    gelato: {
      folder: prefs.gelatoFolder || '', title: '', validation: null, validating: 0, running: false, result: null, error: null,
      format: prefs.gelatoFormat || status.gelato.formats[0]?.key, address: { ...(prefs.gelatoAddress || {}) },
    },
  };
  let tunnelTimer = null;
  const cur = () => st[st.mode];

  setHtml(view, html`<div class="creator" id="cr">
    <div class="page-head">
      <div><h1 class="page-title">Order Creator</h1>
        <div class="page-sub">Чернетки фотокниг у Printify та Gelato прямо з експортованих файлів Canva — без публікації й без запуску у виробництво</div></div>
      <div class="page-actions" id="cr-switch"></div>
    </div>
    <div class="row-wrap" id="cr-status" style="margin-bottom:18px"></div>
    <div id="cr-tunnels"></div>
    <div class="creator-grid">
      <div class="stack-l" id="cr-left"></div>
      <div class="stack-l" id="cr-right"></div>
    </div></div>`);
  const $ = (s) => view.querySelector(s);
  const root = $('#cr');

  // ---------------------------------------------------------------- persistence
  const savePrefs = debounce(() => {
    api('/api/creator/prefs', { method: 'POST', body: {
      mode: st.mode, printifyFolder: st.printify.folder, gelatoFolder: st.gelato.folder,
      gelatoFormat: st.gelato.format, gelatoAddress: st.gelato.address,
    } }).catch(() => {});
  }, 500);

  // ---------------------------------------------------------------- header / status
  function renderSwitch() {
    setHtml($('#cr-switch'), html`<div class="mode-switch">${segHtml([
      { value: 'printify', label: 'Printify' }, { value: 'gelato', label: 'Gelato' }], st.mode, { name: 'mode' })}</div>`);
    requestAnimationFrame(() => syncSeg($('#cr-switch .seg')));
  }

  function renderStatus() {
    const p = status.printify, g = status.gelato;
    root.classList.toggle('mode-gelato', st.mode === 'gelato');
    if (st.mode === 'printify') {
      setHtml($('#cr-status'), html`
        <span class="status-pill ${p.tokenConfigured ? 'ok' : 'bad'}"><span class="dot"></span>Printify: ${p.tokenConfigured ? `онлайн (${p.shopTitle || p.shopId})` : html`немає токена — <a href="#/settings/printify">налаштувати</a>`}</span>
        <span class="status-pill" title="Еталон лише читається й ніколи не змінюється">${ic('lock', 'icon-s')}Master: ${p.masterTitle || p.masterId || 'не обрано'}</span>
        <span class="status-pill">${ic('book', 'icon-s')}${p.pageCount} стор. · обкладинка ${(p.coverSize || []).join('×')} · сторінки ${(p.pageSize || []).join('×')}</span>
        ${p.enabledVariants?.length ? html`<span class="status-pill">${ic('layers', 'icon-s')}${p.enabledVariants.join(' · ')}</span>` : ''}`);
    } else {
      setHtml($('#cr-status'), html`
        <span class="status-pill ${g.keyConfigured ? 'ok' : 'bad'}"><span class="dot"></span>Gelato: ${g.keyConfigured ? 'ключ налаштовано' : html`немає ключа — <a href="#/settings/gelato">налаштувати</a>`}</span>
        <span class="status-pill ${g.cloudflared ? '' : 'bad'}">${ic('globe', 'icon-s')}${g.cloudflared ? 'Тимчасове посилання для файлів готове' : 'Не знайдено bin/cloudflared.exe'}</span>
        <span class="status-pill">${ic('book', 'icon-s')}Внутрішній блок: ${g.pageCount} сторінок</span>`);
    }
  }

  function renderTunnels() {
    const active = status.gelato.activeTunnels || [];
    if (!active.length || st.mode !== 'gelato' || st.gelato.result) { setHtml($('#cr-tunnels'), ''); return; }
    setHtml($('#cr-tunnels'), html`<div class="notice notice-warn" style="margin-bottom:16px">${ic('globe')}<div class="grow">
      Активне тимчасове посилання для файлів чернетки Gelato (${active.map((t) => `${t.key.slice(0, 8)}… — ${Math.ceil(t.secondsLeft / 60)} хв`).join(', ')}).
      Відкрийте чернетку в Gelato Dashboard, поки посилання працює.</div>
      ${active.map((t) => html`<button class="btn btn-sm" data-close-tunnel="${t.key}">Закрити</button>`)}</div>`);
  }

  // ---------------------------------------------------------------- left column
  function folderCard(num) {
    const s = cur();
    const v = s.validation;
    const expected = st.mode === 'printify' ? status.printify.pageCount : status.gelato.pageCount;
    let badge;
    if (s.validating) badge = html`<span class="v-badge run"><span class="spinner" style="width:12px;height:12px;border-width:2px"></span>Перевірка… ${Math.round(s.validating)}%</span>`;
    else if (!v) badge = html`<span class="v-badge">Очікування вибору</span>`;
    else if (v.ok) badge = html`<span class="v-badge ok">${ic('check', 'icon-s')}${v.found}/${v.expected} файлів у порядку</span>`;
    else badge = html`<span class="v-badge bad">${ic('x', 'icon-s')}Є проблеми</span>`;
    return html`<section class="card card-pad stack">
      <div class="row"><span class="step-no">${num}</span><h3 class="card-title grow">Папка з ілюстраціями</h3>${badge}</div>
      <div class="input-group">
        <input class="input path-input" id="cr-folder" placeholder="Папку ще не вибрано…" value="${s.folder}" spellcheck="false" autocomplete="off">
        <button class="btn btn-sm input-action" data-act="browse">${ic('folder', 'icon-s')}Огляд…</button>
      </div>
      <div class="field-hint">Папка має містити <b>Cover.png</b> та <b>1.png–${expected}.png</b>${st.mode === 'printify' ? ` — точні розміри: обкладинка ${(status.printify.coverSize || []).join('×')}, сторінки ${(status.printify.pageSize || []).join('×')} px` : ' — розміри контролюються шаблонами Gelato'}.</div>
      ${v && !s.validating ? html`
        ${v.errors.length ? html`<div class="notice notice-error">${ic('alertCircle')}<div><b>Перевірка не пройдена</b><ul>${v.errors.slice(0, 12).map((e) => html`<li>${e}</li>`)}</ul>${v.errors.length > 12 ? html`<div>…та ще ${v.errors.length - 12}</div>` : ''}</div></div>` : ''}
        ${v.warnings.length ? html`<div class="notice notice-warn">${ic('alert')}<div>${v.warnings.map((w) => html`<div>${w}</div>`)}</div></div>` : ''}
        ${v.ok ? html`<div class="row-wrap faint" style="font-size:12.5px"><span class="row" style="gap:6px;color:var(--green)">${ic('checkCircle', 'icon-s')}Усі PNG повністю прочитано й перевірено</span><span class="mono">${bytes(v.totalBytes)}</span><span class="spacer"></span><button class="btn btn-ghost btn-xs" data-act="open-folder">${ic('folder', 'icon-s')}Відкрити</button><button class="btn btn-ghost btn-xs" data-act="revalidate">${ic('refresh', 'icon-s')}Перевірити знову</button></div>`
          : html`<div class="row"><span class="spacer"></span><button class="btn btn-ghost btn-xs" data-act="revalidate">${ic('refresh', 'icon-s')}Перевірити знову</button></div>`}` : ''}
    </section>`;
  }

  function titleCard(num) {
    const s = cur();
    return html`<section class="card card-pad stack">
      <div class="row"><span class="step-no">${num}</span><h3 class="card-title grow">Назва ${st.mode === 'printify' ? 'нової книги' : 'книги'}</h3>
        <button class="btn btn-ghost btn-xs" data-act="from-etsy">${ic('receipt', 'icon-s')}З замовлення Etsy</button></div>
      <input class="input input-lg" id="cr-title" placeholder="Напр.: 4174712220 - Caleb" value="${s.title}" autocomplete="off">
      <div class="field-hint">${st.mode === 'printify' ? 'Ця назва з’явиться в Printify → My Products.' : 'Назва зберігається в метаданих чернетки Gelato.'}</div>
    </section>`;
  }

  function formatCard(num) {
    return html`<section class="card card-pad stack">
      <div class="row"><span class="step-no">${num}</span><h3 class="card-title">Формат книги</h3></div>
      <div class="fmt-pills">${status.gelato.formats.map((f) => html`<button class="fmt-pill ${st.gelato.format === f.key ? 'active' : ''}" data-format="${f.key}">${f.label}</button>`)}</div>
      <div class="field-hint">Внутрішній блок: ${status.gelato.pageCount} сторінок (мінімум Gelato — 28, крок 2).</div>
    </section>`;
  }

  function addressCard(num) {
    const a = st.gelato.address;
    const inp = (key, ph, span = '') => html`<input class="input ${span}" id="addr-${key}" data-addr="${key}" placeholder="${ph}" value="${a[key] || ''}" autocomplete="off">`;
    return html`<section class="card card-pad stack">
      <div class="row"><span class="step-no">${num}</span><h3 class="card-title grow">Адреса отримувача</h3>
        <button class="btn btn-ghost btn-xs" data-act="from-etsy">${ic('receipt', 'icon-s')}З замовлення Etsy</button></div>
      <div class="addr-grid">
        ${inp('firstName', "Ім'я *")}${inp('lastName', 'Прізвище *')}
        ${inp('addressLine1', 'Адреса, рядок 1 *', 'span2')}${inp('addressLine2', 'Адреса, рядок 2', 'span2')}
        ${inp('city', 'Місто *')}${inp('state', 'Штат / провінція (US, CA, AU)')}
        ${inp('postCode', 'Індекс *')}
        <select class="select" data-addr="country">${COUNTRIES.map(([c, n]) => html`<option value="${c}" ${(a.country || 'US') === c ? 'selected' : ''}>${c} — ${n}</option>`)}</select>
        ${inp('phone', 'Телефон (необов’язково)', 'span2')}
      </div>
      <div class="field-hint">* — обов'язкові поля. Адреса зберігається лише на цьому комп'ютері.</div>
    </section>`;
  }

  function createCard(num) {
    const s = cur();
    const pr = st.mode === 'printify';
    return html`<section class="card card-pad stack">
      <div class="row"><span class="step-no">${num}</span><h3 class="card-title grow">Створення чернетки</h3><span class="faint mono" style="font-size:12px">1 клік</span></div>
      <div id="cr-alert">${s.error ? html`<div class="notice notice-error">${ic('alertCircle')}<div style="white-space:pre-line">${s.error}</div></div>` : ''}</div>
      <div class="row" style="justify-content:center;padding:4px 0">
        <button class="btn btn-xl create-btn" id="cr-create" style="width:min(360px,100%)" ${s.running ? 'disabled' : ''}>
          ${s.running ? html`<span class="spinner" style="border-color:rgba(255,255,255,.35);border-top-color:#fff"></span>Створення…` : html`${ic('plus', 'icon-l')}${pr ? 'Створити чернетку' : 'Створити чернетку Gelato'}`}</button>
      </div>
      <div id="cr-progress" ${s.running ? '' : 'hidden'}>
        <div class="row" style="margin-bottom:6px;font-size:12.5px"><span id="cr-step" style="font-weight:600" class="grow">Підготовка…</span><span class="mono" id="cr-pct" style="color:var(--mode);font-weight:700">0%</span></div>
        <div class="progress"><i id="cr-bar" style="background:var(--mode)"></i></div>
        <div class="faint mono truncate" id="cr-detail" style="font-size:11.5px;margin-top:6px"></div>
      </div>
      <div id="cr-result">${resultHtml()}</div>
      <div class="row faint" style="font-size:12.5px;align-items:flex-start;border-top:1px solid var(--border);padding-top:12px">${ic('shield')}
        <span>${pr ? raw('<b>Безпечний режим:</b> програма не публікує товар на Etsy і не запускає виробництво. Книга створюється як неопублікована чернетка в Printify, Master-продукт лише читається.')
          : raw('<b>Безпечний режим:</b> створюється лише чернетка замовлення (orderType: draft). У виробництво вона не потрапить, поки ви самі не підтвердите її в Gelato.')}</span></div>
    </section>`;
  }

  function resultHtml() {
    const s = cur();
    const r = s.result;
    if (!r) return '';
    if (st.mode === 'printify') {
      return html`<div class="result-card">
        <h4>${ic('checkCircle')}Чернетку успішно створено у Printify!</h4>
        <dl class="kv">
          <dt>Назва</dt><dd>${r.title}</dd>
          <dt>Product ID</dt><dd class="mono">${r.productId}</dd>
          <dt>Статус</dt><dd>Неопублікована чернетка (Unpublished)</dd>
          <dt>Ілюстрації</dt><dd>${r.total}/${r.total} на позиціях Master${r.reused ? ` · ${r.reused} вже були завантажені` : ''}</dd>
          <dt>Перевірка</dt><dd>${r.verified ? '✓ позиції збігаються' : '— не підтверджено'} · Master ${r.masterSafe === true ? '✓ не змінено' : r.masterSafe === false ? '⚠ змінився' : '—'}</dd>
        </dl>
        ${(r.warnings || []).map((w) => html`<div class="notice notice-warn" style="margin-top:10px">${ic('alert')}<div>${w}</div></div>`)}
        <div class="row" style="margin-top:14px"><button class="btn btn-success grow" data-act="open-product" style="height:42px">${ic('external', 'icon-s')}Відкрити в Printify Product Creator</button>
          <button class="btn btn-icon" data-act="copy-id" title="Копіювати ID" style="height:42px;width:42px">${ic('copy', 'icon-s')}</button></div>
      </div>`;
    }
    return html`<div class="result-card">
      <h4>${ic('checkCircle')}Чернетку замовлення створено в Gelato!</h4>
      <dl class="kv">
        <dt>Назва</dt><dd>${r.title}</dd>
        <dt>Order ID</dt><dd class="mono">${r.orderId}</dd>
        <dt>Reference</dt><dd class="mono">${r.orderReferenceId}</dd>
        <dt>Тип</dt><dd class="mono">${r.orderType || 'draft'}</dd>
        <dt>Формат</dt><dd>${r.format}</dd>
      </dl>
      <div class="notice notice-warn" style="margin-top:12px" id="cr-tunnel">${ic('clock')}<div class="grow">
        <b>Важливо:</b> Gelato завантажує файли лише коли ви відкриєте чернетку в Dashboard. Зробіть це зараз, поки тимчасове посилання працює — лишилось <b class="mono" id="cr-countdown">--:--</b>.
        <div class="row-wrap" style="margin-top:8px"><button class="btn btn-sm" data-act="open-gelato">${ic('external', 'icon-s')}Gelato Dashboard</button>
          <button class="btn btn-sm" data-act="copy-order">${ic('copy', 'icon-s')}Копіювати Order ID</button>
          <button class="btn btn-sm" data-act="close-tunnel">Я перевірив — закрити посилання</button></div></div></div>
    </div>`;
  }

  function historyCard() {
    const items = (status.history || []).filter((h) => h.mode === st.mode).slice(0, 6);
    if (!items.length) return '';
    return html`<section class="card card-pad">
      <div class="card-head" style="margin-bottom:6px"><div class="card-title">Останні чернетки</div></div>
      <div class="hist">${items.map((h) => html`<div class="hist-row">
        <span class="chip ${h.mode === 'gelato' ? 'chip-blue' : 'chip-green'}">${h.mode === 'gelato' ? 'Gelato' : 'Printify'}</span>
        <span class="grow truncate" title="${h.title}"><b>${h.title}</b><span class="faint mono" style="font-size:11px"> · ${h.id}</span></span>
        <span class="faint nowrap" style="font-size:11.5px">${relTime(h.at)}</span>
        ${h.url ? html`<button class="btn btn-ghost btn-xs btn-icon" data-open-url="${h.url}" title="Відкрити">${ic('external', 'icon-s')}</button>`
          : html`<button class="btn btn-ghost btn-xs btn-icon" data-copy="${h.id}" title="Копіювати ID">${ic('copy', 'icon-s')}</button>`}
      </div>`)}</div></section>`;
  }

  function renderLeft() {
    const blocks = st.mode === 'printify'
      ? [folderCard(1), titleCard(2), createCard(3), historyCard()]
      : [formatCard(1), folderCard(2), titleCard(3), addressCard(4), createCard(5), historyCard()];
    keepFocus(() => setHtml($('#cr-left'), blocks));
    if (st.mode === 'gelato' && st.gelato.result) startCountdown();
  }

  // ---------------------------------------------------------------- right column (structure)
  function spreadsList(total) {
    const list = [{ left: null, right: 1 }];
    for (let f = 2; f <= total; f += 2) list.push({ left: f, right: f + 1 <= total ? f + 1 : null });
    return list;
  }
  const fileState = (name) => {
    const v = cur().validation;
    if (!v) return null;
    const row = v.files.find((r) => r.file.toLowerCase() === name.toLowerCase());
    return row ? (row.ok ? 'ok' : 'bad') : 'missing';
  };
  const thumb = (name, w = 420) => media('/media/folder', { path: cur().folder, file: name, w });

  function renderRight() {
    const s = cur();
    const pr = st.mode === 'printify';
    const total = pr ? status.printify.pageCount : status.gelato.pageCount;
    const v = s.validation;
    const has = (n) => v && v.files.some((r) => r.file.toLowerCase() === n.toLowerCase());
    const coverRow = v?.files.find((r) => r.position === 'cover');
    const ratio = coverRow?.width ? `${coverRow.width} / ${coverRow.height}` : pr ? `${status.printify.coverSize[0]} / ${status.printify.coverSize[1]}` : '464 / 249';
    const spreads = spreadsList(total);
    const count = v ? v.found : 0;
    const expectedCount = total + 1;
    const fmtLabel = pr ? 'Hardcover 8×8' : (status.gelato.formats.find((f) => f.key === st.gelato.format)?.label || '');
    const half = (n, side, blankLabel) => {
      if (n === null) return html`<div class="half blank"><span>${blankLabel}</span></div>`;
      const name = `${n}.png`;
      const stt = fileState(name);
      return html`<div class="half ${stt === 'bad' ? 'bad' : ''}">${has(name) ? html`<img data-fade loading="lazy" decoding="async" src="${thumb(name)}" alt="">` : html`<span class="ph-num">${n}</span>`}</div>`;
    };
    setHtml($('#cr-right'), html`<section class="card card-pad stack-l">
      <div class="row" style="align-items:flex-end;border-bottom:1px solid var(--border);padding-bottom:16px">
        <div class="grow"><h2 style="font-size:21px;font-weight:700">Структура книги <span class="faint" style="font-weight:600">· ${fmtLabel}</span></h2>
          <div class="faint" style="font-size:12.5px;margin-top:3px">1 розворот обкладинки + ${spreads.length} книжкових розворотів (${total} сторінок)</div></div>
        <span class="chip chip-lg mono ${count === expectedCount && v?.ok ? 'chip-green' : ''}">${count}/${expectedCount} зображень</span>
      </div>
      <div class="stack">
        <div class="row" style="font-size:13px"><b class="grow">Повний розворот обкладинки (Cover.png)</b>
          <span class="faint mono" style="font-size:11.5px">${coverRow?.width ? `${coverRow.width} × ${coverRow.height} px · ` : ''}натисніть, щоб збільшити</span></div>
        <div class="structure-cover" data-lb="0" style="aspect-ratio:${ratio}">
          ${has('Cover.png') ? html`<img data-fade decoding="async" src="${thumb(coverRow.file, 1400)}" alt="">` : html`<div class="cover-ph"><div>Задня сторона</div><div>Лицьова обкладинка</div></div>`}
          <div class="gutter"></div>
          ${coverRow && !coverRow.ok ? html`<div class="page-tag" style="background:var(--red);left:auto;right:10px">${coverRow.error}</div>` : ''}
        </div>
      </div>
      <div class="stack">
        <div class="row" style="font-size:13px"><b class="grow">Внутрішні розвороти</b><span class="faint" style="font-size:12px">клікніть на розворот для перегляду</span></div>
        <div class="spread-grid">${spreads.map((sp, i) => {
          const lp = i === 0 ? 1 : sp.left + 1;
          const rp = i === 0 ? 2 : lp + 1;
          const lf = sp.left ? `${sp.left}.png` : null, rf = sp.right ? `${sp.right}.png` : null;
          const mark = (f) => { if (!f) return html`<span class="faint">${i === 0 ? 'Форзац' : 'Нахзац'}</span>`; const x = fileState(f); return html`<span class="${x === 'ok' ? 'file-ok' : x ? 'file-bad' : ''}">${f}</span>`; };
          return html`<div class="spread-card enter" data-lb="${i + 1}" style="animation-delay:${Math.min(i * 25, 300)}ms">
            <div class="spread-card-head"><span class="spread-no">${i + 1}</span><b class="grow">Розворот ${i + 1}</b><span class="chip chip-mono">стор. ${lp}–${rp}</span></div>
            <div class="spread-view">${half(sp.left, 'left', 'Форзац')}${half(sp.right, 'right', 'Нахзац')}<div class="gutter-s"></div></div>
            <div class="spread-files">${mark(lf)}${mark(rf)}</div></div>`;
        })}</div>
      </div>
      <div class="row faint" style="font-size:12.5px;border-top:1px solid var(--border);padding-top:12px">${ic('info', 'icon-s')}
        <span>${pr ? 'Cover.png → cover, N.png → page_N. Координати беруться з Master-продукту без округлення.' : 'Сторінки 1–' + total + ' збираються в один PDF без перестиснення; обкладинка передається окремим файлом.'}</span></div>
    </section>`);
    fadeImages(view.querySelector('#cr-right'));
  }

  function openStructure(index) {
    const s = cur();
    if (!s.validation || !s.folder) { toast('Спершу оберіть папку з ілюстраціями', 'info'); return; }
    const total = st.mode === 'printify' ? status.printify.pageCount : status.gelato.pageCount;
    const items = [{ src: media('/media/folder', { path: s.folder, file: 'Cover.png', w: 2600 }),
      full: media('/media/folder', { path: s.folder, file: 'Cover.png', w: 4096 }), title: 'Обкладинка', sub: s.folder }];
    spreadsList(total).forEach((sp, i) => {
      const q = { path: s.folder, h: 1400 };
      if (sp.left) q.left = `${sp.left}.png`;
      if (sp.right) q.right = `${sp.right}.png`;
      const lp = i === 0 ? 1 : sp.left + 1;
      items.push({ src: media('/media/folder-spread', q), full: media('/media/folder-spread', { ...q, h: 2400 }),
        title: `Розворот ${i + 1} · стор. ${lp}–${lp + 1}`, sub: `${sp.left ? sp.left + '.png' : 'форзац'} · ${sp.right ? sp.right + '.png' : 'нахзац'}` });
    });
    openLightbox(items, index);
  }

  function renderAll() {
    renderSwitch(); renderStatus(); renderTunnels(); renderLeft(); renderRight();
  }

  // ---------------------------------------------------------------- validation
  let validateSeq = 0;
  async function validate() {
    const s = cur();
    const mode = st.mode;
    if (!s.folder.trim()) { s.validation = null; renderLeft(); renderRight(); return; }
    const my = ++validateSeq;
    s.validating = 1; s.error = null;
    renderLeft();
    try {
      const res = await runJob(api('/api/creator/validate', { method: 'POST', body: { mode, folder: s.folder } }), (j) => {
        if (my !== validateSeq || st.mode !== mode) return;
        s.validating = Math.max(1, j.percent);
        const badge = view.querySelector('.v-badge.run');
        if (badge) badge.lastChild.textContent = `Перевірка… ${Math.round(s.validating)}%`;
      }, 300);
      if (my !== validateSeq) return;
      s.validation = res;
    } catch (err) {
      if (my !== validateSeq) return;
      s.validation = { ok: false, errors: [err.message], warnings: [], files: [], found: 0, expected: 0 };
    } finally {
      if (my === validateSeq) {
        s.validating = 0;
        if (st.mode === mode) { renderLeft(); renderRight(); }
      }
    }
  }
  const validateSoon = debounce(validate, 600);

  // ---------------------------------------------------------------- create
  async function create() {
    const s = cur();
    const mode = st.mode;
    s.title = ($('#cr-title')?.value || '').trim();
    const problems = [];
    if (!s.folder) problems.push('Оберіть папку з ілюстраціями.');
    else if (s.validating) problems.push('Зачекайте завершення перевірки файлів.');
    else if (s.validation && !s.validation.ok) problems.push('Виправте помилки у файлах (див. крок «Папка з ілюстраціями»).');
    if (!s.title) problems.push('Введіть назву книги.');
    if (mode === 'gelato') {
      const a = st.gelato.address;
      const req = { firstName: "Ім'я", lastName: 'Прізвище', addressLine1: 'Адреса', city: 'Місто', postCode: 'Індекс', country: 'Країна' };
      const miss = Object.entries(req).filter(([k]) => !(a[k] || '').trim()).map(([, v]) => v);
      if (miss.length) problems.push(`Заповніть адресу: ${miss.join(', ')}.`);
      if (['US', 'CA', 'AU'].includes((a.country || '').toUpperCase()) && !(a.state || '').trim()) problems.push('Для цієї країни потрібен штат/провінція.');
    }
    if (problems.length) {
      setHtml($('#cr-alert'), html`<div class="notice notice-warn">${ic('alert')}<div>${problems.map((p) => html`<div>${p}</div>`)}</div></div>`);
      return;
    }
    s.running = true; s.result = null; s.error = null;
    renderLeft();
    const url = mode === 'printify' ? '/api/creator/printify/create' : '/api/creator/gelato/create';
    const body = mode === 'printify' ? { folder: s.folder, title: s.title }
      : { folder: s.folder, title: s.title, format: st.gelato.format, address: st.gelato.address };
    try {
      s.result = await runJob(api(url, { method: 'POST', body }), (j) => {
        if (st.mode !== mode) return;
        const bar = $('#cr-bar');
        if (!bar) return;
        $('#cr-step').textContent = j.step;
        $('#cr-pct').textContent = `${Math.round(j.percent)}%`;
        $('#cr-detail').textContent = j.detail || '';
        bar.style.width = `${j.percent}%`;
      });
      toast(mode === 'printify' ? 'Чернетку створено в Printify' : 'Чернетку створено в Gelato', 'success');
      status = await api('/api/creator/status');
    } catch (err) {
      s.error = err.message;
    } finally {
      s.running = false;
      if (st.mode === mode) { renderStatus(); renderLeft(); }
    }
  }

  function startCountdown() {
    clearInterval(tunnelTimer);
    const r = st.gelato.result;
    if (!r) return;
    const until = r._until || (r._until = Date.now() + r.keepAliveSeconds * 1000);
    const tick = () => {
      const left = Math.max(0, Math.round((until - Date.now()) / 1000));
      const node = $('#cr-countdown');
      if (node) node.textContent = `${String(Math.floor(left / 60)).padStart(2, '0')}:${String(left % 60).padStart(2, '0')}`;
      if (!left) { clearInterval(tunnelTimer); const t = $('#cr-tunnel'); if (t) setHtml(t, html`${ic('info')}<div>Тимчасове посилання закрито. Якщо Gelato ще не завантажив файли — створіть чернетку повторно.</div>`); }
    };
    tick();
    tunnelTimer = setInterval(tick, 1000);
  }

  // ---------------------------------------------------------------- Etsy order picker
  async function fromEtsy() {
    let data;
    try { data = await api('/api/creator/etsy-orders'); } catch (err) { toast(err.message, 'error'); return; }
    if (!data.orders.length) {
      toast('Замовлень Etsy ще немає. Синхронізуйте їх на сторінці «Прибуток».', 'info', 5000);
      return;
    }
    let term = '';
    const m = modal({
      title: 'Заповнити із замовлення Etsy',
      sub: `Останні замовлення з синхронізації ${relTime(data.syncedAt)}`,
      size: 'l',
      body: html`<div class="stack"><div class="input-group">${ic('search')}<input class="input" id="eo-q" placeholder="Ім'я покупця або номер чека…" autofocus></div>
        <div class="cand-list" id="eo-list" style="max-height:440px"></div></div>`,
      foot: null,
    });
    const list = m.el.querySelector('#eo-list');
    const render = () => {
      const t = term.trim().toLowerCase();
      const rows = data.orders.filter((o) => !t || o.name.toLowerCase().includes(t) || o.receiptId.includes(t));
      setHtml(list, rows.length ? rows.map((o) => html`<div class="cand" data-rid="${o.receiptId}" style="align-items:flex-start">
        <div class="grow" style="min-width:0">
          <div class="row" style="gap:8px"><b>${o.name}</b><span class="chip chip-mono">#${o.receiptId}</span>${o.isShipped ? html`<span class="chip chip-green">відправлено</span>` : html`<span class="chip chip-amber">не відправлено</span>`}</div>
          <div class="faint" style="font-size:12px;margin-top:3px">${dateTime(o.createdAt)} · ${o.coverLabel} · ${[o.address.city, o.address.country_iso].filter(Boolean).join(', ')}</div>
          ${o.items.flatMap((i) => i.variations || []).length ? html`<div style="font-size:12px;margin-top:4px;color:var(--text-2)">${o.items.flatMap((i) => i.variations || []).map((v) => `${v.name}: ${v.value}`).join(' · ')}</div>` : ''}
        </div>
        ${o.childName ? html`<span class="chip chip-accent">${o.childName}</span>` : ''}</div>`) : html`<div class="empty" style="padding:30px">Нічого не знайдено</div>`);
    };
    render();
    m.el.querySelector('#eo-q').addEventListener('input', (e) => { term = e.target.value; render(); });
    list.addEventListener('click', (e) => {
      const row = e.target.closest('[data-rid]');
      if (!row) return;
      const o = data.orders.find((x) => x.receiptId === row.dataset.rid);
      m.close();
      const s = cur();
      s.title = `${o.receiptId} - ${o.childName || ''}`.trim().replace(/-$/, '- ');
      if (st.mode === 'gelato') {
        const a = o.address || {};
        const parts = (a.name || o.name || '').trim().split(/\s+/);
        st.gelato.address = {
          ...st.gelato.address,
          firstName: parts[0] || '', lastName: parts.slice(1).join(' ') || '',
          addressLine1: a.first_line || '', addressLine2: a.second_line || '', city: a.city || '',
          state: a.state || '', postCode: a.zip || '', country: (a.country_iso || 'US').toUpperCase(),
        };
        savePrefs();
      }
      renderLeft();
      const ti = $('#cr-title');
      if (ti) { ti.focus(); ti.setSelectionRange(ti.value.length, ti.value.length); }
      toast(o.childName ? 'Заповнено із замовлення — перевірте назву' : 'Допишіть ім’я дитини в назві', 'info', 3500);
    });
  }

  // ---------------------------------------------------------------- events
  const offs = [
    on(view, 'click', '[data-seg="mode"] button', (e, b) => {
      if (st.mode === b.dataset.value) return;
      const t = $('#cr-title'); if (t) cur().title = t.value;
      st.mode = b.dataset.value; setSeg(b.closest('.seg'), st.mode); savePrefs();
      renderStatus(); renderTunnels(); renderLeft(); renderRight();
      if (cur().folder && !cur().validation && !cur().validating) validate();
    }),
    on(view, 'click', '[data-act]', async (e, t) => {
      const a = t.dataset.act;
      const s = cur();
      if (a === 'browse') {
        try {
          const { path } = await api('/api/creator/pick-folder', { method: 'POST', body: { title: `Оберіть папку з Cover.png та 1–${st.mode === 'printify' ? status.printify.pageCount : status.gelato.pageCount}.png`, initial: s.folder } });
          if (path) { s.folder = path; s.validation = null; savePrefs(); renderLeft(); validate(); }
        } catch (err) { toast(err.message, 'error'); }
      } else if (a === 'revalidate') validate();
      else if (a === 'open-folder') api('/api/creator/open-folder', { method: 'POST', body: { path: s.folder } }).catch((er) => toast(er.message, 'error'));
      else if (a === 'from-etsy') fromEtsy();
      else if (a === 'open-product') openExternal(st.printify.result?.url);
      else if (a === 'copy-id') copyText(st.printify.result?.productId || '', 'Product ID скопійовано');
      else if (a === 'copy-order') copyText(st.gelato.result?.orderId || '', 'Order ID скопійовано');
      else if (a === 'open-gelato') openExternal('https://dashboard.gelato.com/');
      else if (a === 'close-tunnel') {
        try { await api('/api/creator/gelato/close-tunnel', { method: 'POST', body: { orderId: st.gelato.result.orderId } }); } catch {}
        clearInterval(tunnelTimer);
        const box = $('#cr-tunnel');
        if (box) setHtml(box, html`${ic('check')}<div>Тимчасове посилання закрито.</div>`);
      }
    }),
    on(view, 'click', '#cr-create', () => create()),
    on(view, 'click', '[data-format]', (e, b) => { st.gelato.format = b.dataset.format; savePrefs(); renderLeft(); renderRight(); }),
    on(view, 'click', '[data-lb]', (e, c) => openStructure(+c.dataset.lb)),
    on(view, 'click', '[data-open-url]', (e, b) => openExternal(b.dataset.openUrl)),
    on(view, 'click', '[data-copy]', (e, b) => copyText(b.dataset.copy, 'ID скопійовано')),
    on(view, 'click', '[data-close-tunnel]', async (e, b) => {
      await api('/api/creator/gelato/close-tunnel', { method: 'POST', body: { orderId: b.dataset.closeTunnel } }).catch(() => {});
      status = await api('/api/creator/status'); renderTunnels();
    }),
  ];
  view.addEventListener('input', (e) => {
    const s = cur();
    if (e.target.id === 'cr-folder') { s.folder = e.target.value.trim().replace(/^"|"$/g, ''); s.validation = null; savePrefs(); validateSoon(); }
    if (e.target.id === 'cr-title') { s.title = e.target.value; const al = $('#cr-alert'); if (al && !s.error) al.innerHTML = ''; }
    if (e.target.dataset.addr) { st.gelato.address[e.target.dataset.addr] = e.target.value; savePrefs(); }
  });
  view.addEventListener('change', (e) => {
    if (e.target.dataset.addr === 'country') { st.gelato.address.country = e.target.value; savePrefs(); }
  });
  view.addEventListener('keydown', (e) => { if (e.target.id === 'cr-title' && e.key === 'Enter') { e.preventDefault(); create(); } });

  if (!st.gelato.address.country) st.gelato.address.country = 'US';
  renderAll();
  if (cur().folder) validate();
  return { unmount() { offs.forEach((f) => f()); clearInterval(tunnelTimer); savePrefs.flush(); } };
}

