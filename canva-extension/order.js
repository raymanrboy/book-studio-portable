/* Book Studio → Canva: the order mode's Canva driver (2026-10-18, rewritten smaller). What it does for an order handed over
   by the order card (early.js): makes the copy of the book's template, names it «<receipt> - <child>» and deletes the copy's
   first page. The PNG download stays the owner's own press; the card takes the ZIP from Downloads by itself.
   The words it looks for are in `UI` — if Canva renames a button, that is the line to change. NOT yet tried live in Canva
   (the first version's file was lost): the first run on a real order is the test. */
(function () {
  'use strict';
  const NS = (window.BSOrder = window.BSOrder || {});
  const Bot = window.BSCanva;

  const UI = {
    file: 'Файл',                                          // the editor's menu
    copyItems: /^(Створити копію|Копіювати|Зробити копію|Make a copy)$/i,
    nameField: /^Назва дизайну$|^Design name$/i,           // the name field inside the «Файл» menu (aria-label)
    deletePage: /^Видалити сторінку|^Delete page/i,       // the page toolbar's trash
    confirm: /^(Видалити|Delete)$/i,                       // a confirm button, if Canva asks
  };
  const KEY = 'bs-canva:orders';
  const KEEP = 12 * 3600 * 1000;          // an order is kept 12 hours
  const FRESH = 5 * 60 * 1000;            // a copy opened within 5 minutes of the press is the order's
  const COPY_SUFFIX = /(,\s*копія|\s*\(копія\)| copy)$/i;

  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const shown = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const here = () => location.pathname.split('/')[2] || '';

  async function waitFor(fn, what, timeout = 10000) {
    const t0 = Date.now();
    for (;;) {
      const v = fn();
      if (v) return v;
      if (Date.now() - t0 > timeout) throw new Error('Не дочекався: ' + what);
      await sleep(150);
    }
  }
  function click(el) {
    const r = el.getBoundingClientRect();
    const base = { bubbles: true, cancelable: true, composed: true, clientX: r.x + r.width / 2, clientY: r.y + r.height / 2,
      button: 0, pointerId: 1, pointerType: 'mouse', isPrimary: true, view: window, detail: 1 };
    el.dispatchEvent(new PointerEvent('pointerdown', { ...base, buttons: 1 }));
    el.dispatchEvent(new MouseEvent('mousedown', { ...base, buttons: 1 }));
    el.dispatchEvent(new PointerEvent('pointerup', { ...base, buttons: 0 }));
    el.dispatchEvent(new MouseEvent('mouseup', { ...base, buttons: 0 }));
    el.dispatchEvent(new MouseEvent('click', { ...base, buttons: 0 }));
  }

  // ---- the orders kept in the browser profile (put there by early.js)
  function load() {
    let all = {};
    try { all = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (_) { /* a broken store: no orders */ }
    const now = Date.now();
    let changed = false;
    for (const k of Object.keys(all)) if (!all[k] || now - all[k].at > KEEP) { delete all[k]; changed = true; }
    if (changed) { try { localStorage.setItem(KEY, JSON.stringify(all)); } catch (_) { /* ignore */ } }
    return all;
  }
  function save(o) {
    const all = load();
    all[`${o.receipt}|${o.title}`] = o;
    try { localStorage.setItem(KEY, JSON.stringify(all)); } catch (_) { /* ignore */ }
  }
  function clear(o) {
    const all = load();
    delete all[`${o.receipt}|${o.title}`];
    try { localStorage.setItem(KEY, JSON.stringify(all)); } catch (_) { /* ignore */ }
  }

  // ---- the design's name: the field «Назва дизайну» lives inside the «Файл» menu (seen live, 2026-10-18); outside it the name
  // is read from the tab's title («BS 4k Трафарет – Multi-design»).
  const nameInput = () => $$('input').find(i => shown(i) && UI.nameField.test(i.getAttribute('aria-label') || '')) || null;
  const title = () => { const i = nameInput(); return (i ? i.value : document.title.replace(/\s+[–-]\s+[^–-]*$/, '')).trim(); };

  // ---- which order is this tab's
  const isCopyFor = o => Boolean(o.copyDesign) && o.copyDesign === here() && title() === o.title;
  const isTemplateFor = o => (Boolean(o.template) && o.template === here()) || Boolean(o.fromFolder);
  // Only Canva's own copy of the order's template — its name «<template>, копія», opened within 5 minutes of the press —
  // is taken on: any other design opened meanwhile (a master template too) is never renamed or edited.
  function isFreshCopy(o) {
    if (o.copyDesign || Date.now() - o.at > FRESH || here() === o.template) return false;
    const t = title();
    if (!t || !COPY_SUFFIX.test(t)) return false;
    return !o.templateName || t.startsWith(o.templateName);
  }
  function current() {
    const list = Object.values(load()).sort((a, b) => b.at - a.at);
    const id = here();
    return list.find(o => o.copyDesign === id)
      || list.find(o => !o.copyDesign && o.template && o.template === id)
      || list.find(o => !o.copyDesign && o.fromFolder && Date.now() - o.at < KEEP)
      || null;
  }

  // ---- steps
  // «Файл → Копіювати»: Canva opens the copy in a new tab (the owner's own press lets the tab open).
  async function makeCopy(o) {
    const tn = title();
    if (tn && !o.templateName) save({ ...o, templateName: tn });
    click(await waitFor(fileButton, `меню «${UI.file}»`));
    const item = await waitFor(() => $$('[role=menuitem], button, [role=option]').find(b => shown(b) && UI.copyItems.test(b.innerText.trim())),
      'пункт «Створити копію» у меню «Файл»');
    click(item);
    await sleep(800);
  }

  const fileButton = () => $$('button, [role=button], [role=tab]').find(b => shown(b) && b.innerText.trim() === UI.file);

  async function rename(name) {
    if (!nameInput()) {
      click(await waitFor(fileButton, `меню «${UI.file}»`));
    }
    const input = await waitFor(nameInput, 'поле «Назва дизайну» в меню «Файл»');
    input.focus();
    input.select();
    if (document.activeElement !== input) throw new Error('Поле назви не взяло фокус — нічого не вписано');
    document.execCommand('insertText', false, name);
    for (const type of ['keydown', 'keyup']) {
      input.dispatchEvent(new KeyboardEvent(type, { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true, composed: true }));
    }
    input.blur();
    await sleep(500);
    if (nameInput()) click(fileButton());      // the menu closes by the same button (a script's Escape does not close it — seen live)
    await waitFor(() => !nameInput() && title() === name, `назву «${name}»`, 6000);
  }

  // The counter in the bottom bar: «1 з 32» → 32; null when it isn't seen.
  function pageCount() {
    const c = $$('span, div, p').find(el => el.childElementCount === 0 && /^\d+\s+з\s+\d+$/.test(el.textContent.trim()) && shown(el)
      && el.getBoundingClientRect().y > innerHeight - 120);
    return c ? parseInt(c.textContent.split('з')[1], 10) : null;
  }

  // The first page of the copy out. Only on a design that is verified to be the order's copy (named after it), and only once.
  async function deleteFirstPage(o) {
    if (!isCopyFor(o)) throw new Error(`Це не копія «${o.title}» — першу сторінку не чіпаю`);
    const before = pageCount();
    await Bot.openPage(1);
    const trash = await waitFor(() => $$('button, [role=button]').find(b => shown(b)
      && UI.deletePage.test(`${b.getAttribute('aria-label') || ''} ${b.innerText.trim()}`.trim())),
      'кнопку «Видалити сторінку» (позначте першу сторінку й видаліть її самі)');
    click(trash);
    await sleep(500);
    const sure = $$('button').find(b => shown(b) && UI.confirm.test(b.innerText.trim()));
    if (sure) click(sure);
    if (before) await waitFor(() => pageCount() === before - 1, 'що сторінок стало менше', 8000);
    else await sleep(1000);
  }

  Object.assign(NS, { UI, current, save, clear, title, isCopyFor, isTemplateFor, isFreshCopy, makeCopy, rename, deleteFirstPage, pageCount });
})();
