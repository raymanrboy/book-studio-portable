# eRank in the browser pane — the exact procedure

Checked 2026-10-09. The owner is signed in to eRank (shop MoonMeadowStories, **Pro: 200 searches a day**)
in Claude's built-in browser pane. He allows spending the whole daily limit when a listing needs it
(2026-10-09). **Never sign in, sign out, change settings, «Sync Listings», or click «See on Etsy».** Etsy
itself may be opened only as a visitor, never signed in (since 2026-10-11, [security](../../wiki/security.md)); the numbers
come from eRank. If eRank shows its login page, the session has ended — ask the owner to sign in (he can tick «Remember me»).

What one action costs (the counter "Searches: n/200" at the top of every eRank page):

| Page | URL | Cost | Gives |
|---|---|---|---|
| Bulk Keyword Tool | `https://members.erank.com/bulk-keyword-tool` | **1 search per batch of up to 20 phrases** | searches, clicks, CTR, competition, KD, Google for every phrase |
| Keyword Tool | `https://members.erank.com/keyword-tool?keyword=<phrase>&source=etsy&country=USA` | 1 search | ~100 related phrases ("Keyword Ideas") with numbers **and 15 months of monthly searches** |
| Top Listings | `https://members.erank.com/keyword-tool/top-listings?keyword=<phrase>&source=etsy&country=USA` | with the Keyword Tool page of the same phrase | the 10 top listings: title, shop, age, views, daily views, est. sales, price, hearts, **all 13 tags** |

Each snippet runs with `javascript_tool` (it only reads the page; Top Listings also opens the rows' tag
drawers) and returns **compact text**: a `#kind=…` header line, then one row per line, fields split by `|`.
Save the returned text as-is with the Write tool to `seo/data/inbox/<date>-<kind>-<slug>.txt`, then:

```
../runtime/python/python.exe seo/seo.py import-erank seo/data/inbox/<file>.txt
```

(Posting straight from the page to a local receiver doesn't work: the browser pane blocks pages from
reaching 127.0.0.1 — `ERR_BLOCKED_BY_CLIENT`, tried 2026-10-09. Don't try to get around it.)

## 1. Bulk — numbers for a list of phrases

Open the Bulk page, `find` the textbox «Enter keywords, separated by comma or line break.», click it, type
up to 20 phrases separated by `, `, click **Analyze**, then run:

```js
const ok=()=>[...document.querySelectorAll('table tbody tr')].some(tr=>tr.querySelectorAll('td').length>=10);
for (let i=0;i<40 && !ok();i++) await new Promise(r=>setTimeout(r,500));
const seen=new Set(), out=['#kind=bulk|date='+new Date().toISOString().slice(0,10)];
for (const tr of document.querySelectorAll('table tbody tr')) {
  const c=[...tr.querySelectorAll('td')].map(td=>td.innerText.trim().replace(/\s+/g,' '));
  if (c.length<10 || !c[2] || seen.has(c[2])) continue; seen.add(c[2]);
  out.push([c[2],c[4],c[5],c[6],c[7].replace(/,/g,''),c[8],c[9]].join('|'));
}
out.join('\n')
```

Check that the row count equals the phrases typed. `Unknown` searches is a real answer (no Etsy demand) —
keep it. To check a new batch, clear the textbox first (triple-click it, then type).

## 2. Ideas — related phrases with seasonality

Navigate to the Keyword Tool URL of a short seed phrase (the product's core: `train book`, `godparent
gift`), then run (it waits up to 20 s for the table):

```js
const ready=()=>[...document.querySelectorAll('table tbody tr')].some(tr=>tr.querySelectorAll('td').length>5 && tr.innerText.trim());
for (let i=0;i<40 && !ready();i++) await new Promise(r=>setTimeout(r,500));
// phrases that are never about a printed children's book — dropped here so they don't cost context
const SKIP=/\b(lamp|vase|necklace|pattern|shirt|bookmark|book ?mark|keychain|guest book|digital|download|printable|svg|png|pdf|art|coloring|folding|nook|shelf|ends?|bookends|decor|sign|mug|tumbler|ornament|sticker|embroidery|cross stitch|jewelry|earrings|bracelet|t-?shirt|sweatshirt|hoodie|onesie|bib|blanket|candle|card)\b|^(gift|christmas|baby|personalized|book|birthday gift|gift for (her|him))$/i;
const seen=new Set(), out=['#kind=ideas|query='+new URLSearchParams(location.search).get('keyword')+'|date='+new Date().toISOString().slice(0,10)];
for (const tb of document.querySelectorAll('table')) {
  const n=tb.querySelector('tbody tr')?.querySelectorAll('td').length||0;
  const heads=[...tb.querySelectorAll('thead th')].slice(0,n).map(t=>t.innerText.trim());
  const col=h=>heads.indexOf(h); if (col('Keywords')<0) continue;
  for (const tr of tb.querySelectorAll('tbody tr')) {
    const c=[...tr.querySelectorAll('td')].map(td=>td.innerText.trim().replace(/\s+/g,' '));
    const kw=c[col('Keywords')]; if (!kw || seen.has(kw) || SKIP.test(kw)) continue; seen.add(kw);
    const m=[...(c[col('Search Trend')]||'').matchAll(/([A-Z][a-z]{2}) ?(\d{2}) ?([\d,]*?)(?=[A-Z]|$)/g)].map(x=>x[3].replace(/,/g,''));
    const monthly=m.length>3 && m.some(v=>+v>20) ? m.join(',') : '';
    out.push([kw,c[col('Avg. Searches')],c[col('Avg. Clicks')],c[col('Avg. CTR')],(c[col('Etsy Competition')]||'').replace(/,/g,''),c[col('KD')],c[col('Google Searches')],monthly].join('|'));
  }
}
out.join('\n')
```

The page holds two copies of the table (the first with the 15-month trend); the snippet keeps the first copy
of each phrase. The list mixes in broad words (`gift`, `christmas`, `book lover gift`) — they're stored like
everything else; relevance is decided later, per book.

## 3. Top listings — what the best competitors use

After the Keyword Tool page of a phrase, `find` the tab **Top Listings** and click it (or open its URL),
then run. The rows' tag buttons **toggle**, so the snippet opens only the closed ones:

```js
const has=()=>[...document.querySelectorAll('table')].some(t=>[...t.querySelectorAll('thead th')].some(h=>h.innerText.trim()==='Daily Views') && t.querySelectorAll('tbody > tr').length>1);
for (let i=0;i<40 && !has();i++) await new Promise(r=>setTimeout(r,500));
const tb=[...document.querySelectorAll('table')].find(t=>[...t.querySelectorAll('thead th')].some(h=>h.innerText.trim()==='Daily Views') && t.querySelectorAll('tbody > tr').length>1);
const isMain=tr=>/^#\d+/.test(tr.querySelector('td')?.innerText.trim()||'');
for (const tr of [...tb.querySelectorAll('tbody > tr')].filter(isMain)) {
  const nxt=tr.nextElementSibling;
  if (!(nxt && !isMain(nxt) && /Copy Tags/.test(nxt.innerText))) tr.querySelector('td:last-child button')?.click();
}
await new Promise(r=>setTimeout(r,2500));
const rows=[]; let cur=null;
for (const tr of tb.querySelectorAll('tbody > tr')) {
  const tds=[...tr.querySelectorAll('td')];
  if (isMain(tr)) {
    const a=tds[1].querySelectorAll('a'), v=i=>tds[i].innerText.trim().replace(/[$,]/g,'');
    cur=[a[0]?.innerText.trim().replace(/\|/g,'/'), a[1]?.innerText.trim(), v(2), v(3), v(4), v(5), v(6), v(8), ''];
    rows.push(cur);
  } else if (cur && /Copy Tags/.test(tr.innerText)) {
    cur[8]=[...tr.querySelectorAll('span')].filter(s=>!s.children.length).map(s=>s.innerText.trim())
      .filter(t=>t && t!=='Tags' && t!=='Copy Tags').join(';');
  }
}
['#kind=top|query='+new URLSearchParams(location.search).get('keyword')+'|date='+new Date().toISOString().slice(0,10),
 ...rows.map(r=>r.join('|'))].join('\n')
```

Every row should end with its tags; a row ending in `|` means its drawer was toggled shut — run again.

## If a snippet returns nothing

eRank redesigned its pages in December 2025 and may again. Take one `read_page` of the table, fix the snippet
**here** (this file is the only copy), write the date at the top, and go on. Don't read numbers off
screenshots by eye for more than a few phrases — that is how wrong numbers get into the database.
