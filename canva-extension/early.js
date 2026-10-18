/* Book Studio → Canva: an order handed over in the link. The order card opens the book's template with `#bs=<data>` (the
   receipt, the child's name, the copy's name); this runs before Canva's own code, keeps the order for the panel (order.js)
   — one per book, an order of two books keeps two — and takes it off the address. */
(function () {
  'use strict';
  const m = /[#&]bs=([A-Za-z0-9_-]+)/.exec(location.hash || '');
  if (!m) return;
  try {
    const b64 = m[1].replace(/-/g, '+').replace(/_/g, '/');
    const bytes = Uint8Array.from(atob(b64 + '==='.slice((b64.length + 3) % 4)), c => c.charCodeAt(0));
    const order = JSON.parse(new TextDecoder().decode(bytes));
    if (order && order.receipt && order.child && order.title) {
      const parts = location.pathname.split('/');
      const all = JSON.parse(localStorage.getItem('bs-canva:orders') || '{}');
      all[`${order.receipt}|${order.title}`] = { receipt: order.receipt, child: order.child, title: order.title, book: order.book || '',
        at: Date.now(),
        // a design link names the template; a folder link (some books keep one) leaves it to the design opened from it
        template: parts[1] === 'design' ? parts[2] : '', fromFolder: parts[1] !== 'design' };
      localStorage.setItem('bs-canva:orders', JSON.stringify(all));
    }
  } catch (_) { /* a broken link: the panel simply shows no order */ }
  history.replaceState(history.state, '', location.pathname + location.search);
})();
