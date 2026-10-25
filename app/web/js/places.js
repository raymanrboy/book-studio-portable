// Where things are (2026-09-30, wiki/decisions.md): the tools that work on their own as well as inside their object —
// the «Інструменти» page's list, so a tool is named and drawn the same way everywhere.

/** The tools: `area` is their ink (orders — orange, books — cyan); `for` says which object they serve. */
export const TOOLS = [
  { id: 'creator', label: 'Order Creator', sub: 'Чернетка в Gelato з папки файлів', icon: 'printer', hash: '#/creator', area: 'orders',
    for: 'Для замовлень' },
  { id: 'archive', label: 'Архів друку', sub: 'Що пішло в друк · передрук', icon: 'orderArchive', hash: '#/archive', area: 'orders',
    for: 'Для замовлень' },
  { id: 'cover', label: 'Обкладинка', sub: 'Два квадрати → обкладинка Gelato без генерації', icon: 'coverSquares', hash: '#/cover', area: 'books',
    for: 'Для книг' },
  { id: 'mockups', label: 'Мокапи', sub: 'ZIP із Canva → картинки в Photoshop', icon: 'mockup', hash: '#/mockups', area: 'books',
    for: 'Для книг' },
  { id: 'photos', label: 'Фотомокапи', sub: 'Заготовки й промпти для фото з книгою', icon: 'camera', hash: '#/photos', area: 'books',
    for: 'Для книг' },
  { id: 'slides', label: 'Слайди лістингу', sub: 'Слайди книги з Майстерні · схема для нових книг', icon: 'template', hash: '#/slides/template/1', area: 'books',
    for: 'Для книг' },
];
