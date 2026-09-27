// The viewer of a book's print folder. A page can be replaced right there by a file from the computer (the owner
// fixed it in Canva and downloaded that page again) and put back while the page is open. The order card and the
// Order Creator open this one — the flow was written in both until 27.09.2026; each keeps its own question and its
// own next step.
import { post, toast, confirmBox } from './lib.js';
import { openLightbox } from './lightbox.js';
import { folderViewerItems } from './order-bits.js';

export const pageNo = (file) => (/^cover/i.test(file) ? 0 : parseInt(file, 10));
export const pageWord = (file) => (pageNo(file) ? `сторінку ${pageNo(file)}` : 'обкладинку');

/**
 * `book` — the page's own record of the folder: `{ folder, versions, replaced }`; its `versions` (a page's pictures
 * fetched anew) and `replaced` (pages that can be put back) are kept up to date here. `opts`:
 *   total          how many pages the book has;
 *   label          the folder's name under each picture;
 *   sent()         a draft or an order was already made from the old page — then the owner is asked first;
 *   again          the question's end («…надіслати замовлення ще раз?»);
 *   decorate(items) the page's own additions (the order card: what the text check read on each spread);
 *   changed(file)  after a page was replaced or put back (the files are checked again).
 */
export function openFolderViewer(book, start, opts) {
  const items = [];
  const build = () => {
    const list = folderViewerItems(book.folder, opts.total, opts.label, book.versions);
    for (const it of list) it.actions = (it.files || []).flatMap(actions);
    opts.decorate?.(list);
    return list;
  };

  function actions(file) {
    const num = pageNo(file) ? String(pageNo(file)) : '';
    const acts = [{ icon: 'swap', label: num, tip: `Замінити ${pageWord(file)} — обрати файл на комп'ютері`,
      run: (lb) => replace(file, lb) }];
    if (book.replaced.has(file.toLowerCase())) {
      acts.push({ icon: 'restore', label: num, on: true, tip: `Повернути попередню ${pageWord(file)}`,
        run: (lb) => change(file, lb, '/api/creator/restore-page', { folder: book.folder, file }, `Повернено ${pageWord(file)}`) });
    }
    return acts;
  }

  /** A page fixed in Canva takes the place of the old one; the old one waits for «Повернути». */
  async function replace(file, lb) {
    let path;
    try {
      path = (await post('/api/creator/pick-file', { title: `Оберіть ${pageWord(file)} (${file})`, initial: book.folder })).path;
    } catch (err) { toast(err.message, 'error'); return; }
    if (!path) return;
    if (opts.sent() && !(await confirmBox({ title: 'Чернетку вже створено',
      text: `У друкарні лежить стара сторінка. Замінити її тут і ${opts.again}`,
      confirm: 'Замінити', cancel: 'Не чіпати' }))) return;
    await change(file, lb, '/api/creator/replace-page', { folder: book.folder, file, path }, `Замінено ${pageWord(file)}`);
  }

  async function change(file, lb, url, body, message) {
    let res;
    try { res = await post(url, body); } catch (err) { toast(err.message, 'error'); return; }
    // The server says whether this page still has a previous version (an older one may still be there).
    if (res.canRestore) book.replaced.add(file.toLowerCase());
    else book.replaced.delete(file.toLowerCase());
    book.versions[file] = (book.versions[file] || 0) + 1;  // only this page's pictures are fetched anew
    toast(message, 'success');
    items.splice(0, items.length, ...build());
    lb.refresh();
    opts.changed(file);
  }

  items.push(...build());
  openLightbox(items, start);
}
