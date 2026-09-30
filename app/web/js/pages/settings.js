// Settings: keys (encrypted with Windows DPAPI), Etsy connection, Printify Master, Gelato, the text check
// by a local model (Ollama), the backup to Google Drive, data folder.
// Every block is collapsed to one line with its status; the rare technical values live one more
// click away, behind the details toggle, so the page stays quiet. Theme lives only in the rail.
import {
  api, post, html, ic, ib, setHtml, on, modal, toast, confirmBox, copyText, dateTime, slide, menu, remembered,
  remember, runJob, setProgress, bytes, relTime, plural, markMissing,
} from '../lib.js';
import { refreshInfo } from '../info.js';
import { oauthFlow, pickMaster } from './settings-dialogs.js';

const SECRET_LABELS = {
  etsy_keystring: ['Etsy Keystring', 'Etsy Developers → Your apps → Keystring'],
  etsy_shared_secret: ['Etsy Shared Secret', 'Там само, поле Shared Secret'],
  printify_token: ['Printify Personal Access Token', 'Printify → My account → Connections → API'],
  gelato_api_key: ['Gelato API-ключ', 'Gelato Dashboard → Developer → API keys'],
};
const OPEN_KEY = 'bs-settings-open';

export async function mount(view, [section]) {
  let s;
  let bk = null; // the backup: password set, where the copies go, the last one (backup.py)
  let bkJob = null; // a copy being made: its step and percent
  let bkPassword = false; // the password field open to change it
  let tc = null; // text check: on/off, model, whether Ollama answers (asked separately — never slows the page)
  const editing = new Set();
  const openCards = new Set(remembered(OPEN_KEY, []));
  const openDetails = new Set();
  if (section) openCards.add(section);
  const persistOpen = () => remember(OPEN_KEY, [...openCards]);

  async function load() {
    [s, bk] = await Promise.all([api('/api/settings'), api('/api/backup')]);
    if (!bk.passwordSet || (bk.error && !bk.jobId)) openCards.add('backup');
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

  /** A saved key with «Замінити» and «Видалити»; `switchAccount` — the Gelato key, whose replacement is a move to a
   *  new account (the current one stays readable, gelato_accounts.py), not an overwrite. */
  function secretField(name, { switchAccount = false } = {}) {
    const st = s.secrets[name];
    const [label, hint] = SECRET_LABELS[name];
    const edit = editing.has(name) || !st.configured;
    return html`<div class="field">
      <label class="field-label">${label}</label>
      ${edit ? html`<div class="secret-row"><input class="input mono" type="password" data-secret-input="${name}" placeholder="Вставте значення" autocomplete="off" spellcheck="false" aria-label="${label}">
          ${ib('check', 'Зберегти', `data-secret-save="${name}"`, { cls: 'primary', kbd: 'Enter' })}
          ${st.configured ? ib('x', 'Скасувати', `data-secret-cancel="${name}"`) : ''}</div>`
        : html`<div class="secret-row"><div class="secret-state">${ic('lock', 'icon-s')}<span>Збережено</span><span class="mono">${st.hint}</span></div>
          ${switchAccount ? ib('swap', 'Перейти на новий акаунт Gelato', 'data-act="gelato-switch"') : ib('edit', 'Замінити ключ', `data-secret-edit="${name}"`)}
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
    // From 1 October only Gelato prints: Printify is read for its earlier orders (stage, tracking, cost) and nothing more.
    const ro = !!p.readOnly;
    return card('printify', {
      logo: ic('printify'), logoClass: 'int-printify', title: 'Printify',
      summary: !has ? 'Потрібен токен' : ro ? `${p.shopTitle || 'Магазин'} · лише читання старих замовлень` : `${p.shopTitle || 'Магазин не обрано'} · ${m.title || 'шаблон не обрано'}`,
      mark: stateMark(has, has ? 'Підключено' : 'Немає токена'),
      body: html`<div class="stack">
        ${secretField('printify_token')}
        <div class="set-row">${ic('book')}<span class="grow">${ro ? html`Нові книги друкує Gelato <span class="faint">· з Printify програма лише читає старі замовлення</span>` : html`${m.title || 'Шаблон не обрано'} <span class="faint">· <span class="num">${p.pageCount}</span> стор.</span>`}</span>
          ${m.productId || ro ? '' : ib('template', 'Обрати шаблон (Master)', `data-act="master-pick" ${has ? '' : 'disabled'}`)}
          ${ib('pulse', 'Перевірити зв\'язок', `data-act="printify-test" ${has ? '' : 'disabled'}`)}</div>
        <div id="printify-test" class="faint" style="font-size: var(--fs)" hidden></div>
      </div>`,
    });
  }

  // After the move to a new account the old one is only read, until the owner's orders there are done.
  const openWord = (n) => `${n} ${plural(n, ['замовлення', 'замовлення', 'замовлень'])}`;
  function oldAccountField(old) {
    return html`<div class="field">
      <label class="field-label">Старий акаунт · лише читання</label>
      <div class="secret-row"><div class="secret-state">${ic('lock', 'icon-s')}<span>${old.open ? `Ще ${openWord(old.open)} в роботі` : 'Його замовлення завершено'}</span><span class="mono">${old.hint}</span></div>
        ${ib('pulse', 'Перевірити старий акаунт', 'data-act="gelato-old-test"')}
        ${ib('trash', 'Прибрати старий акаунт', 'data-act="gelato-old-forget"', { cls: 'danger' })}</div>
      <div class="field-hint">${old.open
        ? 'Програма стежить за цими замовленнями, доки вони не доїдуть. Нове створюється лише в новому акаунті.'
        : 'Ключ більше не потрібен — його можна прибрати. Замовлення залишаться в програмі як є.'}</div>
    </div>`;
  }

  function gelatoCard() {
    const g = s.gelato;
    const has = s.secrets.gelato_api_key.configured;
    const formats = Object.values(g.formats).map((f) => f.label);
    return card('gelato', {
      logo: ic('gelato'), logoClass: 'int-gelato', title: 'Gelato',
      summary: !has ? 'Потрібен ключ' : g.old ? `Новий акаунт · старий лише читається${g.old.open ? ` · ${openWord(g.old.open)} в роботі` : ''}` : formats.join(' · '),
      mark: stateMark(has, has ? 'Підключено' : 'Немає ключа'),
      body: html`<div class="stack">
        ${secretField('gelato_api_key', { switchAccount: has && !g.old })}
        ${g.old ? oldAccountField(g.old) : ''}
        <div class="set-row">${ic('book')}<span class="grow">${formats.join(' · ')} <span class="faint">· <span class="num">${(g.pageCounts || []).join(' або ')}</span> стор.</span></span>
          ${ib('pulse', 'Перевірити зв\'язок', `data-act="gelato-test" ${has ? '' : 'disabled'}`)}</div>
        <div id="gelato-test" class="faint" style="font-size: var(--fs)" hidden></div>
      </div>`,
    });
  }

  function switchGelato() {
    const m = modal({
      title: 'Перехід на новий акаунт Gelato',
      body: html`<div class="stack">
        <div>Вставте API-ключ нового акаунта. Теперішній ключ програма залишить як старий акаунт — лише для читання: стежитиме за його замовленнями, доки вони не доїдуть. Нові чернетки й передруки — тільки в новому акаунті.</div>
        <input class="input mono" type="password" id="gl-new" placeholder="API-ключ нового акаунта" autocomplete="off" spellcheck="false" aria-label="API-ключ нового акаунта Gelato">
        <div class="field-hint">Gelato Dashboard нового акаунта → Developer → API keys</div></div>`,
      foot: html`<button class="btn btn-ghost" data-c>Скасувати</button><button class="btn btn-primary" data-ok>Перейти</button>`,
    });
    const input = m.el.querySelector('#gl-new');
    const ok = m.foot.querySelector('[data-ok]');
    input.focus();
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') ok.click(); });
    m.foot.querySelector('[data-c]').onclick = () => m.close();
    ok.onclick = async () => {
      const key = input.value.trim();
      if (!key) { toast('Вставте ключ', 'error'); return; }
      ok.disabled = true;
      try {
        await post('/api/gelato/switch', { key });
        m.close();
        toast('Готово: новий акаунт Gelato працює, старий лише читається', 'success', 6000);
        reload();
      } catch (err) { toast(err.message, 'error', 8000); ok.disabled = false; }
    };
  }

  async function forgetOldGelato() {
    const n = s.gelato.old?.open || 0;
    const sure = await confirmBox({
      title: 'Прибрати старий акаунт Gelato?', danger: !!n, confirm: 'Прибрати',
      text: n ? `Ще ${openWord(n)} в роботі в старому акаунті — програма більше не побачить, коли їх надрукують і відправлять. Уже відомі замовлення залишаться.`
        : 'Його замовлення залишаться в програмі такими, як вони є зараз.',
    });
    if (!sure) return;
    try { await post('/api/gelato/old/forget', {}); toast('Старий акаунт прибрано', 'success'); reload(); }
    catch (err) { toast(err.message, 'error'); }
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
        <div id="tc-test" class="faint" style="font-size: var(--fs)" hidden></div>
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

  // Every 3 days on launch the whole program folder and the mockup templates go to Google Drive as one 7-Zip archive
  // under the owner's password (backup.py). He sets the password; the rest runs by itself.
  function backupCard() {
    const failed = bk.error && (!bk.last || bk.error.at > bk.last.at);
    const summary = bkJob ? 'Робиться копія…' : !bk.passwordSet ? 'Задайте пароль' : !bk.driveFound ? 'Google Диск не знайдено'
      : failed ? 'Остання спроба не вдалася' : bk.last ? `Остання ${relTime(bk.last.at)} · ${bytes(bk.last.size)}` : 'Ще не робилася';
    const ok = bk.passwordSet && bk.driveFound && !failed;
    const editPw = bkPassword || !bk.passwordSet;
    const canRun = bk.passwordSet && bk.driveFound && bk.sevenZip && !bkJob;
    return card('backup', {
      logo: ic('shield'), logoClass: 'int-ui', title: 'Резервна копія', summary,
      mark: bkJob ? '' : stateMark(ok, ok ? 'Налаштовано' : summary),
      body: html`<div class="stack">
        <div class="field"><label class="field-label">Пароль архіву</label>
          ${editPw ? html`<div class="secret-row"><input class="input mono" type="password" id="bk-pw" placeholder="Щонайменше 8 символів" autocomplete="new-password" spellcheck="false" aria-label="Пароль резервної копії">
              ${ib('check', 'Зберегти пароль', 'data-act="bk-pw-save"', { cls: 'primary', kbd: 'Enter' })}
              ${bk.passwordSet ? ib('x', 'Скасувати', 'data-act="bk-pw-cancel"') : ''}</div>`
            : html`<div class="secret-row"><div class="secret-state">${ic('lock', 'icon-s')}<span>Збережено</span></div>
              ${ib('edit', 'Змінити пароль', 'data-act="bk-pw-edit"')}</div>`}
          <div class="field-hint">Запишіть його окремо: без пароля копію не відкрити, а відновити його неможливо.${bk.passwordSet ? ' Старі копії відкриваються тим паролем, з яким були зроблені.' : ''}</div></div>
        <div class="set-row">${ic('folderOpen')}<code class="grow code-line">${bk.folder || 'Google Диск не знайдено — запустіть його й увійдіть'}</code>
          ${bk.driveFound ? ib('folderOpen', 'Відкрити папку копій', 'data-act="bk-open"') : ''}</div>
        <div class="set-row"><span class="grow">Уся папка програми й трафарети мокапів <span class="faint">· раз на <span class="num">${bk.everyDays}</span> дні, при запуску · ключі всередині · лишаються останні 7 і по одній на місяць за рік</span></span>
          <button class="btn btn-sm" data-act="bk-run" ${canRun ? '' : 'disabled'}>${ic('upload', 'icon-s')}Зробити копію зараз</button></div>
        ${bkJob ? html`<div><div class="row" style="margin-bottom:6px"><span id="bk-step" class="grow" style="font-size: var(--fs)">${bkJob.step}</span><span id="bk-pct" class="mono faint">${Math.round(bkJob.percent)}%</span></div>
          <div class="progress"><i id="bk-bar" style="transform:scaleX(${bkJob.percent / 100})"></i></div></div>` : ''}
        ${bk.last && !bkJob ? html`<div class="faint" style="font-size: var(--fs)">Остання копія: ${dateTime(bk.last.at)} · ${bytes(bk.last.size)} · <span class="mono">${bk.last.file}</span>${bk.last.skippedCount ? ` · пропущено файлів, відкритих іншими програмами: ${bk.last.skippedCount}` : ''}</div>` : ''}
        ${failed && !bkJob ? html`<div class="notice notice-warn">${ic('alert')}<div>${dateTime(bk.error.at)}: ${bk.error.message}</div></div>` : ''}
      </div>`,
    });
  }

  function redrawBackup() {
    const old = view.querySelector('#set-backup');
    if (old && bk) old.outerHTML = String(backupCard());
  }

  /** Follows a copy being made (started here or on launch) and redraws the block when it ends. */
  async function watchBackup(jobId) {
    bkJob = { step: 'Підготовка…', percent: 0 };
    redrawBackup();
    let stopped = false;
    try {
      await runJob(Promise.resolve({ jobId }), (j) => {
        bkJob = { step: j.step, percent: j.percent };
        const bar = view.querySelector('#bk-bar');
        if (!bar) return;
        setProgress(bar, j.percent);
        view.querySelector('#bk-step').textContent = j.step;
        view.querySelector('#bk-pct').textContent = `${Math.round(j.percent)}%`;
      }, 1000, () => view.isConnected);
      toast('Резервну копію зроблено — Google Диск завантажить її сам', 'success', 5000);
    } catch (err) {
      stopped = !view.isConnected;
      if (!stopped) toast(err.message, 'error', 8000);
    }
    bkJob = null;
    if (stopped) return;
    bk = await api('/api/backup').catch(() => bk);
    redrawBackup();
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
      <div class="page-head"><div><h1 class="page-title">Налаштування</h1></div></div>
      <div class="set-list">
        ${legacyCard()}
        ${etsyCard()}
        ${printifyCard()}
        ${gelatoCard()}
        ${textcheckCard()}
        ${backupCard()}
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

  // ---------------------------------------------------------------- events
  const offs = [
    on(view, 'click', '[data-card]', (e, b) => toggleCard(b.dataset.card)),
    on(view, 'click', '[data-details]', (e, b) => toggleDetails(b.dataset.details, b)),
    on(view, 'click', '[data-secret-edit]', (e, b) => { editing.add(b.dataset.secretEdit); render(); view.querySelector(`[data-secret-input="${b.dataset.secretEdit}"]`)?.focus(); }),
    on(view, 'click', '[data-secret-cancel]', (e, b) => { editing.delete(b.dataset.secretCancel); render(); }),
    on(view, 'click', '[data-secret-save]', async (e, b) => {
      const name = b.dataset.secretSave;
      const value = view.querySelector(`[data-secret-input="${name}"]`).value.trim();
      if (!value) { toast('Вставте значення ключа', 'info'); markMissing([view.querySelector(`[data-secret-input="${name}"]`)]); return; }
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
      } else if (a === 'etsy-oauth') oauthFlow(reload);
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
      } else if (a === 'gelato-old-test') {
        const out = view.querySelector('#gelato-test');
        out.hidden = false;
        setHtml(out, html`<span class="row"><span class="spinner" style="width:14px;height:14px"></span>Перевірка старого акаунта…</span>`);
        b.disabled = true;
        try {
          const r = await post('/api/gelato/test', { account: 'old' });
          setHtml(out, html`<span class="row" style="color:var(--green)">${ic('checkCircle', 'icon-s')}${r.message}</span>`);
        } catch (err) { setHtml(out, html`<span class="row" style="color:var(--red)">${ic('alertCircle', 'icon-s')}${err.message}</span>`); }
        finally { b.disabled = false; }
      } else if (a === 'gelato-switch') switchGelato();
      else if (a === 'gelato-old-forget') forgetOldGelato();
      else if (a === 'master-pick') pickMaster(s.printify, reload);
      else if (a === 'open-data') post('/api/app/open-data', {}).catch((er) => toast(er.message, 'error'));
      else if (a === 'bk-pw-edit') { bkPassword = true; redrawBackup(); view.querySelector('#bk-pw')?.focus(); }
      else if (a === 'bk-pw-cancel') { bkPassword = false; redrawBackup(); }
      else if (a === 'bk-pw-save') {
        const value = view.querySelector('#bk-pw').value;
        try { bk = await post('/api/backup/password', { value }); bkPassword = false; toast('Пароль збережено — запишіть його окремо', 'success', 5000); redrawBackup(); }
        catch (err) { toast(err.message, 'error'); }
      } else if (a === 'bk-open') post('/api/backup/open', {}).catch((er) => toast(er.message, 'error'));
      else if (a === 'bk-run') {
        b.disabled = true;
        try { const { jobId } = await post('/api/backup/run', {}); watchBackup(jobId); }
        catch (err) { toast(err.message, 'error'); b.disabled = false; }
      }
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
  view.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return;
    if (e.target.id === 'etsy-key') view.querySelector('[data-act="etsy-import"]')?.click();
    if (e.target.id === 'bk-pw') view.querySelector('[data-act="bk-pw-save"]')?.click();
  });

  await load();
  render();
  loadTextcheck();
  if (bk.jobId) watchBackup(bk.jobId); // a copy started on launch is still being made
  return {
    shown() {
      const target = section && view.querySelector(`#set-${section}`);
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    },
    unmount() { offs.forEach((f) => f()); },
  };
}

