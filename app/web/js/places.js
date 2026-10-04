// Where things are (2026-09-30, wiki/decisions.md): the places that hold the objects, and the tools that work
// on their own as well as inside their object. One list for the «Інструменти» page and the search (Ctrl+K), so a tool
// is named and drawn the same way everywhere.

/** The places of the rail — for the search. */
export const PLACES = [
  { label: 'Замовлення', sub: 'Черга замовлень Etsy', icon: 'inbox', hash: '#/orders', words: 'черга нові etsy' },
  { label: 'Книги', sub: 'Майстерня · бібліотека · архів', icon: 'shelf', hash: '#/books', words: 'бібліотека майстерня паспорт' },
  { label: 'Майстерня', sub: 'Книги · нові книги в розробці', icon: 'workshop', hash: '#/books/work', words: 'майстерня нова книга агент' },
  { label: 'Бібліотека', sub: 'Книги · готові книги лістингів', icon: 'shelf', hash: '#/books/shop', words: 'бібліотека лістинг паспорт' },
  { label: 'Прибуток', sub: 'Продажі від 1 жовтня', icon: 'chart', hash: '#/profit', words: 'гроші маржа комісії' },
  { label: 'Інструменти', sub: 'Усе, що працює й окремо', icon: 'tools', hash: '#/tools', words: '' },
  { label: 'Налаштування', sub: 'Ключі, сервіси, копія', icon: 'sliders', hash: '#/settings', words: 'ключ токен' },
];

/** The tools: `area` is their ink (orders — orange, books — cyan); `for` says which object they serve. */
export const TOOLS = [
  { id: 'creator', label: 'Order Creator', sub: 'Чернетка в Gelato з папки файлів', icon: 'printer', hash: '#/creator', area: 'orders',
    for: 'Для замовлень', words: 'друк чернетка gelato printify вручну' },
  { id: 'archive', label: 'Архів друку', sub: 'Що пішло в друк · передрук', icon: 'orderArchive', hash: '#/archive', area: 'orders',
    for: 'Для замовлень', words: 'архів передрук файли' },
  { id: 'mockups', label: 'Мокапи', sub: 'ZIP із Canva → картинки в Photoshop', icon: 'mockup', hash: '#/mockups', area: 'books',
    for: 'Для книг', words: 'photoshop шаблони лістинг' },
  { id: 'photos', label: 'Фотомокапи', sub: 'Заготовки й промпти для фото з книгою', icon: 'camera', hash: '#/photos', area: 'books',
    for: 'Для книг', words: 'фото промпт gemini бабуся полиця відео' },
  { id: 'slides', label: 'Слайди лістингу', sub: 'Схема шести слайдів для нових книг', icon: 'template', hash: '#/slides/template/1', area: 'books',
    for: 'Для книг', words: 'слайди схема редактор' },
];

/** Settings' blocks — found by the search, opened on their own. */
export const SETTINGS = [
  { label: 'Etsy', sub: 'Налаштування · ключі й вхід', icon: 'etsy', hash: '#/settings/etsy' },
  { label: 'Printify', sub: 'Налаштування · токен', icon: 'printify', hash: '#/settings/printify' },
  { label: 'Gelato', sub: 'Налаштування · ключ і акаунт', icon: 'gelato', hash: '#/settings/gelato' },
  { label: 'Модулі', sub: 'Налаштування · вичитка тексту, апскейл', icon: 'package', hash: '#/settings/modules' },
  { label: 'Перевірка тексту', sub: 'Налаштування · Модулі · модель Gemma', icon: 'textScan', hash: '#/settings/modules' },
  { label: 'Резервна копія', sub: 'Налаштування · Google Drive', icon: 'database', hash: '#/settings/backup' },
];
