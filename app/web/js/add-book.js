// «Нова книга» and the Workshop's «Передати в бібліотеку»: one dialog. A Listings page opens it without loading the Library page (27.09.2026).
import { api, post, html, ic, ib, setHtml, modal, toast, raw, markMissing, listingState } from './lib.js';
import { store, refreshInfo } from './info.js';

// ------------------------------------------------------------------ add book dialog
/** «Нова книга» — and, with `transfer`, the Workshop's «Передати в бібліотеку»: the same Etsy listing field and
 *  check (read only), for a book that already has its title and pictures. transfer = {summary, send(body, say),
 *  done(result)}: `send` passes the book on (`say` shows its progress on the button). */
export function openAddBook(existing = [], transfer = null) {
  const keysReady = !!store.info?.integrations?.etsy?.keysConfigured;
  let listing = null;
  let unverified = !keysReady;
  const noCheck = transfer ? 'Книгу можна передати без перевірки' : 'Книгу можна додати без перевірки — вкажіть назву вручну';

  const m = modal({
    title: transfer ? 'Передати в бібліотеку' : 'Нова книга',
    sub: transfer ? 'Книга переходить у бібліотеку замовлень: за лістингом Etsy її знаходитимуть замовлення.'
      : 'Книга прив’язується до лістингу Etsy. Усе інше можна додати пізніше.',
    body: html`<div class="stack">
      ${transfer ? transfer.summary : ''}
      <div class="field">
        <label class="field-label">Посилання на лістинг Etsy або його ID</label>
        <div class="input-group">
          <input class="input" id="nb-ref" placeholder="https://www.etsy.com/listing/4542179572/…" autofocus autocomplete="off" style="padding-right:40px">
          ${keysReady ? ib('search', 'Перевірити лістинг', 'id="nb-verify"', { kbd: 'Enter' }) : ''}
        </div>
      </div>
      <div id="nb-result"></div>
      <div id="nb-manual" ${unverified ? '' : 'hidden'}>
        <div class="notice notice-warn" ${transfer ? '' : raw('style="margin-bottom:12px"')}>${ic('alert')}<div>${keysReady
          ? `Лістинг не вдалося перевірити. ${noCheck}, а перевірити пізніше.`
          : raw(`Ключі Etsy ще не налаштовано (Налаштування → Etsy). ${noCheck}.`)}</div></div>
        ${transfer ? '' : html`<div class="field"><label class="field-label">Назва книги</label><input class="input" id="nb-title" placeholder="Напр.: Personalized Baptism Storybook"></div>`}
      </div>
      ${transfer ? '' : html`<div class="field"><label class="field-label">Посилання на макет Canva <span class="faint">(необов'язково)</span></label>
        <input class="input" id="nb-canva" placeholder="https://www.canva.com/design/…" autocomplete="off"></div>`}
      <label class="check" id="nb-photo-wrap" hidden><input type="checkbox" id="nb-photo" checked><span>Взяти головне фото лістингу як заставку книги</span></label>
    </div>`,
    foot: html`<button class="btn btn-ghost" data-close2>Скасувати</button><button class="btn btn-primary" id="nb-create">${transfer
      ? html`${ic('shelf')}Передати в бібліотеку` : html`${ic('plus')}Створити книгу`}</button>`,
  });
  const $ = (s) => m.el.querySelector(s);
  const ref = $('#nb-ref'), result = $('#nb-result'), create = $('#nb-create');
  m.foot.querySelector('[data-close2]').onclick = () => m.close();

  const listingIdOf = (text) => (text.match(/\/listing\/(\d{5,})/) || text.trim().match(/^(\d{5,})$/) || [])[1] || null;

  function refresh() {
    const id = listingIdOf(ref.value);
    const dup = id && existing.find((b) => String(b.listingId) === id);
    if (dup) {
      setHtml(result, html`<div class="notice notice-info">${ic('info')}<div>${transfer ? 'Цей лістинг уже має книга в бібліотеці' : 'Ця книга вже є в бібліотеці'}${dup.archived ? ' (в архіві)' : ''}: <b>${dup.title}</b>.
        <div style="margin-top:8px"><button class="btn btn-sm" data-open-dup="${dup.id}">${transfer ? 'Відкрити ту книгу' : 'Відкрити книгу'}</button></div></div></div>`);
      return;
    }
  }
  // The button always answers (2026-09-30; it was grey and silent until a listing was checked): it says what is
  // missing and lights the field up.
  function missing() {
    const id = listingIdOf(ref.value);
    const dup = id && existing.find((b) => String(b.listingId) === id);
    if (dup) return ['Ця книга вже є — відкрийте її вище', null];
    if (listing) return null;
    if (!id) return ['Вставте посилання на лістинг Etsy або його номер', ref];
    if (!unverified) return keysReady ? ['Спершу перевірте лістинг — Enter або лупа', ref] : null;
    if (!transfer && !$('#nb-title').value.trim()) return ['Вкажіть назву книги', $('#nb-title')];
    return null;
  }

  async function verify() {
    const id = listingIdOf(ref.value);
    if (!id) { toast('Вставте посилання на лістинг або його числовий ID', 'error'); return; }
    if (existing.find((b) => String(b.listingId) === id)) { refresh(); return; }
    const btn = $('#nb-verify');
    btn.disabled = true; btn.innerHTML = '<span class="spinner"></span>';
    listing = null;
    const asked = ref.value;
    try {
      const got = await api(`/api/etsy/listing?ref=${encodeURIComponent(asked)}`);
      if (ref.value !== asked) return;               // the field changed meanwhile: this answer is for a link no longer there
      listing = got;
      unverified = false;
      $('#nb-manual').hidden = true;
      const shopId = store.info?.integrations?.etsy?.shopId;
      const otherShop = shopId && listing.shopId && String(shopId) !== String(listing.shopId);
      setHtml(result, html`<div class="card-soft" style="padding:12px;display:flex;gap:12px;align-items:center">
        ${listing.imageUrl ? html`<img src="${listing.imageUrl}" alt="" style="width:64px;height:64px;border-radius: var(--r-grp);object-fit:cover;flex:none">` : ''}
        <div class="grow"><div style="font-weight:650;line-height:1.35">${listing.title}</div>
          <div class="row-wrap" style="margin-top:6px">
            <span class="chip ${listing.state === 'active' ? 'chip-green' : 'chip-amber'}">${listing.state ? listingState(listing.state) : 'невідомо'}</span>
            <span class="chip chip-mono">#${listing.id}</span>
            ${listing.shopId ? html`<span class="chip chip-mono">магазин ${listing.shopId}</span>` : ''}
          </div></div></div>
        ${otherShop ? html`<div class="notice notice-warn" style="margin-top:10px">${ic('alert')}<div>Цей лістинг належить іншому магазину (${listing.shopId}), ніж підключений (${shopId}).</div></div>` : ''}`);
      $('#nb-photo-wrap').hidden = !listing.imageUrl;
    } catch (err) {
      unverified = true;
      setHtml(result, html`<div class="notice notice-error">${ic('alertCircle')}<div>${err.message}</div></div>`);
      $('#nb-manual').hidden = false;
    } finally {
      btn.disabled = false; btn.innerHTML = `${ic('search')}`;
      refresh();
    }
  }

  ref.addEventListener('input', () => { listing = null; result.innerHTML = ''; $('#nb-photo-wrap').hidden = true; refresh(); });
  ref.addEventListener('keydown', (e) => { if (e.key === 'Enter') { e.preventDefault(); keysReady ? verify() : $('#nb-title')?.focus(); } });
  ref.addEventListener('paste', () => setTimeout(() => { if (keysReady && listingIdOf(ref.value)) verify(); }, 30));
  if ($('#nb-verify')) $('#nb-verify').onclick = verify;
  $('#nb-title')?.addEventListener('input', refresh);
  m.el.addEventListener('click', (e) => {
    const d = e.target.closest('[data-open-dup]');
    if (d) { m.close(); location.hash = `#/book/${d.dataset.openDup}`; }
  });

  const label = create.innerHTML;
  create.onclick = async () => {
    const why = missing();
    if (why) { toast(why[0], 'info'); markMissing([why[1]]); return; }
    create.style.minWidth = `${create.offsetWidth}px`;   // the label changes while it works: the button keeps its width
    create.disabled = true;
    create.innerHTML = `<span class="spinner"></span>${transfer ? 'Передаю…' : 'Створення…'}`;
    try {
      if (transfer) {
        const result = await transfer.send(
          listing ? { listing, useListingImage: !!(listing.imageUrl && $('#nb-photo').checked) } : { listingRef: ref.value },
          (text) => { create.innerHTML = `<span class="spinner"></span>${text}`; },
        );
        m.close();
        refreshInfo();
        transfer.done(result);
        return;
      }
      const book = await post('/api/library/books', listing
        ? { listing, canvaUrl: $('#nb-canva').value, useListingImage: !!(listing.imageUrl && $('#nb-photo').checked) }
        : { listingRef: ref.value, title: $('#nb-title').value, canvaUrl: $('#nb-canva').value });
      m.close();
      toast('Книгу додано до бібліотеки', 'success');
      refreshInfo();
      location.hash = `#/book/${book.id}`;
    } catch (err) {
      toast(err.message, 'error');
      if (err.data?.bookId && !transfer) { m.close(); location.hash = `#/book/${err.data.bookId}`; }
      create.disabled = false;
      create.innerHTML = label;
    }
  };
}
