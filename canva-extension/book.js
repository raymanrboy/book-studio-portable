/* Book Studio → Canva: a Workshop book folder → the plan of the Canva template's pages.
   Pure logic (no Canva here): the panel uses it in the browser, app/tests/test_canva_extension.py runs it in node. */
(function (root) {
  'use strict';

  const SPREADS = [];
  for (let n = 2; n <= 15; n++) SPREADS.push(n);
  const COVER_PAGE = 31;        // the template: page 1, spreads 2–29, page 30, the cover as page 31
  const LAST_PAGE = COVER_PAGE;

  // The same as text_sections() in app/studio/workshop/rows.py — keep the two alike.
  function textSections(bookText) {
    const sections = {};
    let key = null;
    let lines = [];
    const close = () => {
      if (!key) return;
      let body = lines.join('\n').replace(/^\n+|\n+$/g, '').replace(/\n{3,}/g, '\n\n').trim();
      for (const word of ['Name', 'Gifter']) {
        body = body.split('[' + word + ']').join('{' + word + '}').split('`{' + word + '}`').join('{' + word + '}');
      }
      if (body) sections[key] = body;
    };
    for (const line of String(bookText || '').split(/\r\n|\r|\n/)) {
      if (line.startsWith('#')) {
        const m = /^##\s+(?:(cover)|spread\s+0*(\d+)|(afterword))\b/i.exec(line);
        close();
        key = null;
        lines = [];
        if (m && m[1]) key = 'cover';
        else if (m && m[2]) {
          const n = Number(m[2]);
          key = n === 1 ? 'page1' : SPREADS.includes(n) ? 'spread' + n : null;
        } else if (m && m[3]) key = 'page30';
        continue;
      }
      if (key && !['---', '***', '___'].includes(line.trim())) lines.push(line.replace(/\s+$/, ''));
    }
    close();
    return sections;
  }

  const spreadPages = n => [2 * n - 2, 2 * n - 1];

  // A spread's text sits on its right page; the mirrored spreads (book.json, or by default those whose left page
  // divides by 4 — rows.MIRRORED) have it on the left one.
  function textPageOf(n, rows) {
    const mark = rows && rows['spread' + n];
    const mirrored = mark && typeof mark.mirrored === 'boolean' ? mark.mirrored : spreadPages(n)[0] % 4 === 0;
    return spreadPages(n)[mirrored ? 0 : 1];
  }

  // "1.png" → "1", "Cover.png" → "cover"; anything else → null.
  function pictureKey(fileName) {
    const m = /^(\d+|cover)\.(png|jpe?g)$/i.exec(fileName);
    if (!m) return null;
    return /^cover$/i.test(m[1]) ? 'cover' : String(Number(m[1]));
  }

  // [{page, picture, text, textMissing}] for pages 1–31. `pictures` maps pictureKey() → File (or a name in tests).
  function buildPlan(pictures, sections, rows) {
    const plan = [];
    const add = (page, picKey, textKey) => plan.push({
      page,
      picture: pictures[picKey] || null,
      text: textKey ? sections[textKey] || null : null,
      textMissing: Boolean(textKey) && !sections[textKey],
    });
    add(1, '1', null);  // the dedication page: only the picture — the owner's choice (2026-10-08)
    for (const n of SPREADS) {
      const textPage = textPageOf(n, rows);
      for (const p of spreadPages(n)) add(p, String(p), p === textPage ? 'spread' + n : null);
    }
    add(30, '30', 'page30');
    add(COVER_PAGE, 'cover', null);  // the cover: only the picture, the owner sets the title
    return plan;
  }

  // "1-31", "3, 7, 12", "5-10 31" → sorted page numbers; null when it can't be read.
  function parsePages(spec, max = LAST_PAGE) {
    const out = new Set();
    const parts = String(spec || '').split(/[,;\s]+/).filter(Boolean);
    if (!parts.length) return null;
    for (const part of parts) {
      const m = /^(\d+)(?:[-–](\d+))?$/.exec(part);
      if (!m) return null;
      let a = Number(m[1]);
      let b = m[2] ? Number(m[2]) : a;
      if (a > b) [a, b] = [b, a];
      a = Math.max(a, 1);
      b = Math.min(b, max);  // «1-3111111111» typed halfway must not freeze the tab
      for (let i = a; i <= b; i++) out.add(i);
    }
    return out.size ? [...out].sort((x, y) => x - y) : null;
  }

  // The name the picture is uploaded under — the book, the page and the run's mark, so the owner's Uploads stay readable
  // and a run never takes an older upload of the same page.
  function uploadName(book, page, fileName, stamp) {
    const ext = (/\.(png|jpe?g)$/i.exec(fileName) || ['', 'png'])[1].toLowerCase();
    const label = page === COVER_PAGE ? 'cover' : 'p' + String(page).padStart(2, '0');
    return `${book}-${label}${stamp ? '-' + stamp : ''}.${ext}`;
  }

  const api = { textSections, textPageOf, pictureKey, buildPlan, parsePages, uploadName, COVER_PAGE, LAST_PAGE };
  root.BSBook = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof globalThis !== 'undefined' ? globalThis : this);
