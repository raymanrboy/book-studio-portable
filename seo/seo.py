"""Etsy SEO studio: the keyword database and the checks behind the `/etsy-seo` skill.

Everything is local: eRank numbers come in as files (the owner's Tag Report CSVs, or JSON the agent
extracts from eRank pages in the browser pane). Nothing here talks to Etsy or eRank.

    python seo/seo.py import-tagreport <csv>...        eRank "Shop tags" exports (duplicates skipped)
    python seo/seo.py import-legacy <old.sqlite>       competitor listings of the old seo-intelligence
    python seo/seo.py import-erank <file>...           bulk / ideas / top text from seo/knowledge/erank-browser.md
    python seo/seo.py import-own <tsv> [--period P]    the shop's own Etsy Stats search terms (term<TAB>visits)
    python seo/seo.py known <phrase>... [--file f]     latest numbers + what still needs an eRank lookup
    python seo/seo.py related <word>...                known keywords that contain all the words
    python seo/seo.py competitors <word>...            competitor listings whose title has the words
    python seo/seo.py audit <listings.csv> [--sales items.csv...]   the shop's listings through the database (+ sales)
    python seo/seo.py pick <candidates.tsv>            choose 13 tags (phrase<TAB>A|B<TAB>facet)
    python seo/seo.py lint --title T --tags "a, b"     hard rules + exact phrases inside the title
    python seo/seo.py block <phrase> --reason R        never suggest this phrase again
    python seo/seo.py save <book> --title T --tags "a, b"   remember what went into a listing
    python seo/seo.py summary
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import math
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "data" / "seo.sqlite"
STALE_DAYS = 90          # numbers older than this are looked up again
LT20 = 10                # "< 20" searches counted as 10 (eRank cannot measure below 20)
NICHE_SLOTS = 5          # at most this many tags without measured demand (eRank shows nothing under 20/month)
UNSEEN_SCORE = 45.0
KEEP_SOLD = 3            # a listing that sold this many in the sales files given to `audit` is not rewritten (rules.md §0)
BOOK_NOUN_BONUS = 1.25   # a tag holding the item noun (book/storybook) — see rules.md §0
OWN_BOOST_MAX = 30.0     # the shop's own search-term visits outrank every eRank number (rules.md, level S)      # a tag eRank has never seen, when it describes the book exactly (relevance A)
FACET_CAP = 5            # at most this many tags of one buyer intent (facet)
TITLE_TARGET = (110, 140)

SCHEMA = """
CREATE TABLE IF NOT EXISTS keyword (
  id INTEGER PRIMARY KEY, text TEXT UNIQUE NOT NULL, grp TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS keyword_grp ON keyword(grp);
CREATE TABLE IF NOT EXISTS metric (
  id INTEGER PRIMARY KEY, keyword_id INTEGER NOT NULL REFERENCES keyword(id),
  source TEXT NOT NULL, observed_at TEXT NOT NULL,
  searches INTEGER, searches_flag TEXT, clicks INTEGER, ctr REAL,
  competition INTEGER, kd INTEGER, google INTEGER, monthly TEXT,
  UNIQUE(keyword_id, source, observed_at));
CREATE TABLE IF NOT EXISTS shop_tag (
  shop TEXT NOT NULL, keyword_id INTEGER NOT NULL REFERENCES keyword(id),
  occurrences INTEGER, observed_at TEXT NOT NULL, PRIMARY KEY(shop, keyword_id, observed_at));
CREATE TABLE IF NOT EXISTS listing (
  id INTEGER PRIMARY KEY, source TEXT NOT NULL, shop TEXT, title TEXT NOT NULL,
  age_days INTEGER, views INTEGER, daily_views REAL, est_sales INTEGER, price REAL, hearts INTEGER,
  query TEXT, observed_at TEXT NOT NULL, UNIQUE(shop, title));
CREATE TABLE IF NOT EXISTS listing_tag (
  listing_id INTEGER NOT NULL REFERENCES listing(id), keyword_id INTEGER NOT NULL REFERENCES keyword(id),
  PRIMARY KEY(listing_id, keyword_id));
CREATE TABLE IF NOT EXISTS block (phrase TEXT PRIMARY KEY, reason TEXT NOT NULL, added_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS my_listing (
  id INTEGER PRIMARY KEY, book TEXT NOT NULL, saved_at TEXT NOT NULL, title TEXT NOT NULL, tags TEXT NOT NULL,
  note TEXT);
CREATE TABLE IF NOT EXISTS own_search (
  keyword_id INTEGER NOT NULL REFERENCES keyword(id), visits INTEGER NOT NULL, period TEXT NOT NULL,
  observed_at TEXT NOT NULL, PRIMARY KEY(keyword_id, observed_at));
CREATE TABLE IF NOT EXISTS imported_file (sha TEXT PRIMARY KEY, name TEXT, imported_at TEXT);
"""


# ---------- text helpers ----------

def clean(phrase: str) -> str:
    return re.sub(r"\s+", " ", phrase.strip().lower())


def singular(word: str) -> str:
    if len(word) <= 3 or word.endswith(("ss", "us", "is")):
        return word
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith(("ches", "shes", "xes")):
        return word[:-2]
    if word.endswith("s"):
        return word[:-1]
    return word


def group_key(phrase: str) -> str:
    """Etsy matches plurals and ignores apostrophes, so 'christening gifts' = 'christening gift'."""
    words = re.sub(r"[^a-z0-9 ]", "", clean(phrase).replace("'", "")).split()
    return " ".join(singular(w) for w in words)


def num(value) -> int | None:
    if value is None:
        return None
    s = str(value).replace(",", "").replace("%", "").strip()
    try:
        return int(float(s))
    except ValueError:
        return None


def searches_of(raw) -> tuple[int | None, str | None]:
    s = str(raw or "").strip()
    if s.startswith("<"):
        return None, "lt20"
    n = num(s)
    return (n, None) if n is not None else (None, "unknown")


def today() -> str:
    return dt.date.today().isoformat()


# ---------- database ----------

def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    blocklist = HERE / "knowledge" / "blocklist.tsv"
    if blocklist.exists():
        for line in blocklist.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#") and "\t" in line:
                phrase, reason = line.split("\t", 1)
                con.execute("INSERT OR IGNORE INTO block VALUES(?,?,?)", (phrase.strip().lower(), reason.strip(), today()))
        con.commit()
    return con


def kid(con, phrase: str) -> int:
    text = clean(phrase)
    row = con.execute("SELECT id FROM keyword WHERE text=?", (text,)).fetchone()
    if row:
        return row["id"]
    return con.execute("INSERT INTO keyword(text, grp) VALUES(?,?)", (text, group_key(text))).lastrowid


def add_metric(con, phrase, source, observed, searches_raw, clicks=None, ctr=None, competition=None,
               kd=None, google=None, monthly=None):
    searches, flag = searches_of(searches_raw)
    con.execute(
        "INSERT OR REPLACE INTO metric(keyword_id, source, observed_at, searches, searches_flag, clicks, ctr,"
        " competition, kd, google, monthly) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
        (kid(con, phrase), source, observed, searches, flag, num(clicks), num(ctr), num(competition), num(kd),
         num(google), json.dumps(monthly) if monthly else None))


def already(con, path: Path) -> bool:
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if con.execute("SELECT 1 FROM imported_file WHERE sha=?", (sha,)).fetchone():
        return True
    con.execute("INSERT INTO imported_file VALUES(?,?,?)", (sha, path.name, today()))
    return False


def latest(con, phrase: str):
    """Newest measurement of exactly this phrase (any source), or None."""
    return con.execute(
        "SELECT m.* FROM metric m JOIN keyword k ON k.id=m.keyword_id WHERE k.text=?"
        " ORDER BY m.observed_at DESC, m.searches IS NULL LIMIT 1", (clean(phrase),)).fetchone()


def group_rows(con, phrase: str):
    """Newest measurement of every spelling in the phrase's plural group."""
    rows = []
    for k in con.execute("SELECT text FROM keyword WHERE grp=?", (group_key(phrase),)):
        m = latest(con, k["text"])
        if m:
            rows.append((k["text"], m))
    return rows


def evaluate(con, phrase: str) -> dict:
    """Numbers and score of a tag; demand is summed over the plural group (Etsy matches plurals)."""
    own = latest(con, phrase)
    group = group_rows(con, phrase)
    demand, measured = 0, False
    for _, m in group:
        if m["searches"] is not None:
            demand += m["searches"]
            measured = True
        elif m["searches_flag"] == "lt20":
            demand += LT20
    comps = [m["competition"] for _, m in group if m["competition"]]
    comp = (own["competition"] if own and own["competition"] else (min(comps) if comps else None))
    ctr = own["ctr"] if own and own["ctr"] is not None else None
    monthly = None
    for _, m in group:
        if m["monthly"]:
            monthly = json.loads(m["monthly"])
            break
    own_visits = con.execute(
        "SELECT COALESCE(SUM(o.visits),0) FROM own_search o JOIN keyword k ON k.id=o.keyword_id"
        " WHERE k.grp=? AND o.observed_at=(SELECT MAX(observed_at) FROM own_search)", (group_key(phrase),)).fetchone()[0]
    res = {"phrase": clean(phrase), "own": own_visits, "known": bool(group), "demand": demand, "measured": measured,
           "competition": comp, "ctr": ctr, "observed": own["observed_at"] if own else
           (group[0][1]["observed_at"] if group else None), "variants": [t for t, _ in group],
           "monthly": monthly, "score": 0.0}
    if group:
        d = max(demand, 1)
        s_dem = min(1.0, math.log10(d + 1) / math.log10(5000))
        ratio = comp / max(demand, LT20) if comp else None
        s_comp = (min(1.0, max(0.0, (math.log10(2000) - math.log10(max(ratio, 0.01))) / (math.log10(2000) - math.log10(2))))
                  if ratio is not None else 0.3)
        s_ctr = min(1.0, ctr / 110) if ctr is not None else 0.6
        score = 100 * (0.45 * s_dem + 0.40 * s_comp + 0.15 * s_ctr)
        if not measured:
            # eRank can't see below 20 searches a month — that is not "no demand" (the owner, 2026-10-09: books
            # sell on such tags; we may be the first with this product). Judge it by how few listings compete.
            score = 25 + 35 * s_comp
        res.update(ratio=round(ratio, 1) if ratio is not None else "?", score=round(score, 1))
    return res


def stale(observed: str | None) -> bool:
    if not observed:
        return True
    return (dt.date.today() - dt.date.fromisoformat(observed[:10])).days > STALE_DAYS


def blocked(con, phrase: str):
    """A blocked phrase matches its plural group; one saved with a leading '~' matches inside longer phrases too."""
    g = group_key(phrase)
    for row in con.execute("SELECT phrase, reason FROM block"):
        contains = row["phrase"].startswith("~")
        b = group_key(row["phrase"].lstrip("~"))
        if b == g or (contains and re.search(rf"(^| ){re.escape(b)}( |$)", g)):
            return row["reason"]
    return None


def peak(monthly) -> str:
    if not monthly:
        return ""
    vals = sorted(v for _, v in monthly if v is not None)
    if not vals or vals[-1] <= 20:
        return ""
    top, median = vals[-1], vals[len(vals) // 2]
    if top < 2 * max(median, 20):
        return "all-year"
    return "peak " + "/".join(m for m, v in monthly if v and v >= 0.6 * top)


# ---------- commands ----------

def cmd_import_tagreport(a):
    con = connect()
    for f in a.files:
        p = Path(f)
        shop = re.sub(r" - Shop tags.*$", "", p.stem).strip()
        if already(con, p):
            print(f"skip (same file already imported): {p.name}")
            continue
        observed = a.date or dt.date.fromtimestamp(p.stat().st_mtime).isoformat()
        n = 0
        for r in csv.DictReader(p.open(encoding="utf-8-sig")):
            phrase = r["Keywords"]
            add_metric(con, phrase, "erank-tagreport", observed, r["Average Searches"], r["Average Clicks"],
                       r["CTR"], r["Competition"], r["Keyword Difficulty"], r.get("Searches"))
            con.execute("INSERT OR REPLACE INTO shop_tag VALUES(?,?,?,?)",
                        (shop, kid(con, phrase), num(r["Tag Occurrences"]), observed))
            n += 1
        print(f"{shop}: {n} tags ({observed})")
    con.commit()


def cmd_import_legacy(a):
    con = connect()
    old = sqlite3.connect(a.db)
    old.row_factory = sqlite3.Row
    observed = a.date
    n = 0
    for r in old.execute("SELECT l.*, s.shop_name FROM listings l JOIN shops s USING(shop_id)"):
        cur = con.execute(
            "INSERT OR IGNORE INTO listing(source, shop, title, age_days, views, daily_views, est_sales, price,"
            " observed_at) VALUES('legacy-intel',?,?,?,?,?,?,?,?)",
            (r["shop_name"], r["title_raw"], r["listing_age_days"], r["total_views"], r["daily_views_reported"],
             r["estimated_sales"], r["price_amount"], observed))
        if cur.rowcount:
            lid = cur.lastrowid
            for t in (r["tags_raw"] or "").split(","):
                if t.strip():
                    con.execute("INSERT OR IGNORE INTO listing_tag VALUES(?,?)", (lid, kid(con, t)))
            n += 1
    con.commit()
    print(f"{n} competitor listings imported")


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def monthly_pairs(value, observed: str):
    """eRank's trend: [[label, n], ...] or "n,n,…" (oldest first, the last one = the month before `observed`)."""
    if not value:
        return None
    if isinstance(value, list):
        return value
    vals = [int(v) if v.strip().isdigit() else None for v in str(value).split(",")]
    y, m = int(observed[:4]), int(observed[5:7]) - 1          # the last full month
    out = []
    for v in reversed(vals):
        if m == 0:
            y, m = y - 1, 12
        out.append([f"{MONTHS[m - 1]} {str(y)[2:]}", v])
        m -= 1
    return list(reversed(out))


def import_payload(con, data: dict) -> str:
    """JSON shapes (made by the snippets in seo/knowledge/erank-browser.md):
    {"kind":"bulk"|"ideas","date":"YYYY-MM-DD","rows":[{"keyword","searches","clicks","ctr","competition","kd","google","monthly"?}]}
    {"kind":"top","date":..,"query":..,"rows":[{"title","shop","age","views","daily","sales","price","hearts","tags":[..]}]}"""
    observed = data.get("date") or today()
    if data.get("kind") in ("bulk", "ideas"):
        for r in data["rows"]:
            add_metric(con, r["keyword"], f"erank-{data['kind']}", observed, r.get("searches"), r.get("clicks"),
                       r.get("ctr"), r.get("competition"), r.get("kd"), r.get("google"),
                       monthly_pairs(r.get("monthly"), observed))
        con.commit()
        return f"{data['kind']}: {len(data['rows'])} keywords"
    if data.get("kind") == "top":
        n = 0
        for r in data["rows"]:
            con.execute("DELETE FROM listing_tag WHERE listing_id IN (SELECT id FROM listing WHERE shop=? AND title=?)",
                        (r.get("shop"), r["title"]))
            con.execute(
                "INSERT OR REPLACE INTO listing(source, shop, title, age_days, views, daily_views, est_sales, price,"
                " hearts, query, observed_at) VALUES('erank-top',?,?,?,?,?,?,?,?,?,?)",
                (r.get("shop"), r["title"], num(r.get("age")), num(r.get("views")), num(r.get("daily")),
                 num(r.get("sales")), num(str(r.get("price", "")).replace("$", "")), num(r.get("hearts")),
                 data.get("query"), observed))
            lid = con.execute("SELECT id FROM listing WHERE shop=? AND title=?", (r.get("shop"), r["title"])).fetchone()[0]
            for t in r.get("tags", []):
                con.execute("INSERT OR IGNORE INTO listing_tag VALUES(?,?)", (lid, kid(con, t)))
            n += 1
        con.commit()
        return f"top: {n} listings for '{data.get('query')}' ({sum(1 for r in data['rows'] if r.get('tags'))} with tags)"
    raise ValueError(f"unknown kind: {data.get('kind')!r}")


def parse_compact(text: str) -> dict:
    """The snippets' compact text (one line per row, fields split by '|'), half the size of JSON:
        #kind=ideas|query=godparent book|date=2026-10-09
        godparent gift|608|621|102%|20038|76|2900|1130,10,…        (keyword|searches|clicks|ctr|comp|kd|google|monthly)
        #kind=top|query=train book|date=…
        Title|Shop|age|views|daily|sales|price|hearts|tag1;tag2;…"""
    lines = [l for l in text.splitlines() if l.strip()]
    head = dict(kv.split("=", 1) for kv in lines[0].lstrip("#").split("|"))
    data = {"kind": head["kind"], "query": head.get("query"), "date": head.get("date"), "rows": []}
    for l in lines[1:]:
        f = l.split("|")
        if data["kind"] == "top":
            data["rows"].append(dict(zip(["title", "shop", "age", "views", "daily", "sales", "price", "hearts"], f[:8]),
                                     tags=[t.strip() for t in f[8].split(";") if t.strip()] if len(f) > 8 else []))
        else:
            data["rows"].append(dict(zip(["keyword", "searches", "clicks", "ctr", "competition", "kd", "google", "monthly"], f)))
    return data


def cmd_import_erank(a):
    con = connect()
    for f in a.files:
        text = Path(f).read_text(encoding="utf-8")
        data = parse_compact(text) if text.lstrip().startswith("#") else json.loads(text)
        print(f"{Path(f).name}: " + import_payload(con, data))


def cmd_import_own(a):
    """The shop's own Etsy Stats → Search terms (copied from the screens): term<TAB>visits per line."""
    con = connect()
    observed = a.date or today()
    n = 0
    for line in Path(a.file).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#") or "	" not in line:
            continue
        term, visits = line.rsplit("	", 1)
        con.execute("INSERT OR REPLACE INTO own_search VALUES(?,?,?,?)", (kid(con, term), int(visits), a.period, observed))
        n += 1
    con.commit()
    print(f"{n} search terms of our shop ({a.period}, {observed})")


def cmd_own(a):
    con = connect()
    last = con.execute("SELECT MAX(observed_at) FROM own_search").fetchone()[0]
    rows = con.execute("SELECT k.text, o.visits FROM own_search o JOIN keyword k ON k.id=o.keyword_id"
                       " WHERE o.observed_at=? ORDER BY o.visits DESC", (last,)).fetchall()
    for r in rows:
        print(fmt(evaluate(con, r["text"])))


def read_phrases(a) -> list[str]:
    items = list(a.phrases or [])
    if getattr(a, "file", None):
        items += [l.split("\t")[0] for l in Path(a.file).read_text(encoding="utf-8").splitlines()]
    out, seen = [], set()
    for p in items:
        for part in p.split(","):
            c = clean(part)
            if c and c not in seen:
                seen.add(c)
                out.append(c)
    return out


def fmt(e: dict) -> str:
    own = f"  ★ OUR SHOP: {e['own']} visits" if e.get("own") else ""
    if not e["known"]:
        return f"{e['phrase']:<26} —  no eRank data{own}"
    dem = str(e["demand"]) if e["measured"] else ("<20" if e["demand"] else "unknown")
    comp = f"{e['competition']:,}" if e["competition"] else "?"
    ctr = f"{e['ctr']}%" if e["ctr"] is not None else "?"
    var = [v for v in e["variants"] if v != e["phrase"]]
    extra = f"  +{'/'.join(var)}" if var else ""
    return (f"{e['phrase']:<26} score {e['score']:5.1f} | demand {dem:>7} | comp {comp:>9} | ratio {e.get('ratio', '?'):>7}"
            f" | ctr {ctr:>5} | {e['observed']}{'  STALE' if stale(e['observed']) else ''}{extra}  {peak(e['monthly'])}{own}")


def cmd_known(a):
    con = connect()
    need = []
    for p in read_phrases(a):
        why = blocked(con, p)
        if why:
            print(f"{p:<26} BLOCKED: {why}")
            continue
        if len(p) > 20:
            print(f"{p:<26} (longer than 20 — title only, not a tag)")
        e = evaluate(con, p)
        print(fmt(e))
        if not latest(con, p) or stale(e["observed"]):
            need.append(p)
    if need:
        print(f"\nNEED eRank lookup ({len(need)}):")
        for i in range(0, len(need), 20):
            print("  " + ", ".join(need[i:i + 20]))


def cmd_related(a):
    con = connect()
    words = [clean(w) for w in a.words]
    rows = con.execute("SELECT text FROM keyword").fetchall()
    hits = []
    for r in rows:
        g = group_key(r["text"]).split()
        if all(group_key(w) in g or w in r["text"] for w in words) and not blocked(con, r["text"]):
            e = evaluate(con, r["text"])
            if e["known"]:
                hits.append(e)
    hits.sort(key=lambda e: -e["score"])
    for e in hits[: a.limit]:
        print(fmt(e))
    print(f"\n{len(hits)} known keywords contain: {' + '.join(words)}")


def cmd_competitors(a):
    con = connect()
    like = " AND ".join(["lower(title) LIKE ?"] * len(a.words))
    rows = con.execute(f"SELECT * FROM listing WHERE {like} ORDER BY COALESCE(daily_views,0) DESC",
                       [f"%{w.lower()}%" for w in a.words]).fetchall()
    tagcount: dict[str, float] = {}
    for r in rows[: a.limit]:
        tags = [t["text"] for t in con.execute(
            "SELECT k.text FROM listing_tag lt JOIN keyword k ON k.id=lt.keyword_id WHERE lt.listing_id=?", (r["id"],))]
        weight = 1 + math.log10(1 + (r["daily_views"] or 0))
        for t in tags:
            tagcount[t] = tagcount.get(t, 0) + weight
        print(f"[{r['shop']}] {r['title']}  ({len(r['title'])} ch)")
        print(f"   views {r['views']} · daily {r['daily_views']} · sales {r['est_sales']} · age {r['age_days']}d · ${r['price']}")
        print(f"   tags: {', '.join(tags)}")
    if tagcount:
        print("\nTags most used by these listings (weighted by daily views):")
        for t, w in sorted(tagcount.items(), key=lambda x: -x[1])[:30]:
            print(f"   {w:5.1f}  {t}")
    print(f"\n{len(rows)} listings match")


def word_set(p: str) -> set[str]:
    stop = {"for", "with", "and", "the", "a", "of", "to", "my", "your", "in"}
    return {w for w in group_key(p).split() if w not in stop}


def cmd_pick(a):
    """candidates.tsv: phrase<TAB>A|B<TAB>facet  (A = exactly this product, B = partly; C rows are dropped)."""
    con = connect()
    cands = []
    for line in Path(a.file).read_text(encoding="utf-8").splitlines():
        parts = [x.strip() for x in line.split("\t")]
        if not parts[0] or parts[0].startswith("#"):
            continue
        rel = (parts[1] if len(parts) > 1 else "A").upper()
        facet = parts[2] if len(parts) > 2 else "-"
        p = clean(parts[0])
        if rel == "C" or len(p) > 20 or blocked(con, p):
            continue
        e = evaluate(con, p)
        if not e["known"]:          # not in eRank at all: an intuitive / first-mover tag — judged by relevance only
            e["score"] = UNSEEN_SCORE
        own_boost = min(OWN_BOOST_MAX, 10 * math.log2(1 + e["own"]))   # buyers already reach us by it
        # our own Stats: "<occasion> book" phrases bring 10-100x more visits per search than "<occasion> gift" (rules.md §0)
        noun = BOOK_NOUN_BONUS if re.search(r"books?|storybook", p) else 1.0
        e.update(rel=rel, facet=facet, value=e["score"] * (1.0 if rel == "A" else 0.6) * noun + own_boost)
        cands.append(e)
    cands.sort(key=lambda e: -e["value"])
    chosen: list[dict] = []
    groups = set()

    def ok(e) -> bool:
        g = group_key(e["phrase"])
        if g in groups:
            return False
        ws = word_set(e["phrase"])
        for c in chosen:
            cs = word_set(c["phrase"])
            # near-duplicates, or one tag's words all inside another's (Etsy matches words across the whole
            # listing, so "baptism gift" adds nothing next to "baptism gift boy")
            if ws and cs and (len(ws & cs) / len(ws | cs) >= 0.75 or ws <= cs or cs <= ws):
                return False
        if not e["measured"] and sum(1 for c in chosen if not c["measured"]) >= NICHE_SLOTS:
            return False
        if sum(1 for c in chosen if c["facet"] == e["facet"]) >= FACET_CAP:
            return False
        return True

    def take(e):
        chosen.append(e)
        groups.add(group_key(e["phrase"]))

    for facet in dict.fromkeys(e["facet"] for e in cands):      # every facet gets its best tag first
        best = next((e for e in cands if e["facet"] == facet and ok(e)), None)
        if best and len(chosen) < 13:
            take(best)
    for e in cands:
        if len(chosen) >= 13:
            break
        if e not in chosen and ok(e):
            take(e)
    chosen.sort(key=lambda e: -e["value"])
    for e in chosen:
        print(f"{e['rel']} {e['facet']:<10} " + fmt(e))
    print("\nTAGS: " + ", ".join(e["phrase"] for e in chosen))
    left = [e for e in cands if e not in chosen][:10]
    if left:
        print("\nnext best (not chosen):")
        for e in left:
            print(f"  {e['rel']} {e['facet']:<10} " + fmt(e))


def title_phrases(con, title: str) -> list[dict]:
    """Known keywords that sit inside the title as an exact, contiguous phrase (Etsy may rank exact matches higher)."""
    norm = lambda s: re.sub(r"\s+", " ", " " + re.sub(r"[^a-z0-9' ]", " ", s.lower()) + " ")
    whole = norm(title)
    blocks = [norm(b) for b in re.split(r"[,|:;–]", title)]
    out = []
    for r in con.execute("SELECT DISTINCT k.text FROM keyword k JOIN metric m ON m.keyword_id=k.id"):
        if f" {r['text']} " in whole and " " in r["text"]:
            e = evaluate(con, r["text"])
            if e["measured"] and e["demand"] >= 20:
                # Etsy reads past punctuation, so words on both sides of a comma also form a phrase — wanted or not
                e["across"] = not any(f" {r['text']} " in b for b in blocks)
                out.append(e)
    out.sort(key=lambda e: -e["demand"])
    return out


def cmd_lint(a):
    con = connect()
    title = a.title.strip()
    tags = [clean(t) for t in (a.tags or "").split(",") if t.strip()]
    errors, warns = [], []
    if len(title) > 140:
        errors.append(f"title is {len(title)} characters (max 140)")
    lo, hi = TITLE_TARGET
    if len(title) < lo:
        warns.append(f"title is {len(title)} characters; the shop's strategy is {lo}-{hi}")
    for ch in "%:&":
        if title.count(ch) > 1:
            errors.append(f"'{ch}' may appear only once in an Etsy title")
    if re.search(r"[$^`]", title):
        errors.append("title has a character Etsy refuses ($ ^ `)")
    caps = [w for w in re.findall(r"[A-Za-z]{2,}", title) if w.isupper()]
    if len(caps) > 3:
        errors.append(f"more than 3 words in capitals: {caps}")
    words = re.findall(r"[a-z0-9']+", title.lower())
    stop = {"for", "with", "and", "the", "a", "of", "to", "or", "in", "my", "your", "book"}
    rep = sorted({w for w in words if words.count(w) > 1 and w not in stop})
    if rep:
        warns.append(f"repeated words in the title: {', '.join(rep)}")
    if not re.search(r"\bbook\b|storybook", title.lower()):
        errors.append("the title never says what the item is (book / storybook)")
    if len(tags) != 13:
        errors.append(f"{len(tags)} tags (Etsy allows 13 — use all of them)")
    for t in tags:
        if len(t) > 20:
            errors.append(f"tag longer than 20: '{t}' ({len(t)})")
        if re.search(r"[^a-z0-9 '\-™©®]", t):
            errors.append(f"tag has a character Etsy refuses: '{t}'")
        if " " not in t:
            warns.append(f"one-word tag (weak): '{t}'")
        why = blocked(con, t)
        if why:
            errors.append(f"blocked tag '{t}': {why}")
    gs = [group_key(t) for t in tags]
    dup = sorted({t for t, g in zip(tags, gs) if gs.count(g) > 1})
    if dup:
        errors.append(f"tags that are the same for Etsy (plural/apostrophe): {', '.join(dup)}")
    for phrase in re.split(r"[,|:–-]", title):
        why = blocked(con, phrase)
        if phrase.strip() and why:
            errors.append(f"blocked phrase in title '{phrase.strip()}': {why}")
    tag_words = {w for t in tags for w in group_key(t).split()}
    missing = sorted({singular(w) for w in words if w not in stop and len(w) > 2 and singular(w) not in tag_words})
    print(f"TITLE ({len(title)} ch, {len(words)} words): {title}")
    print(f"TAGS ({len(tags)}): {', '.join(tags)}\n")
    for e in errors:
        print("ERROR  " + e)
    for w in warns:
        print("warn   " + w)
    if missing:
        print(f"info   title words not in any tag (eRank flags these): {', '.join(missing)}")
    hits = title_phrases(con, title)
    print(f"\nExact buyer phrases inside the title ({len(hits)}), total demand {sum(e['demand'] for e in hits)}:")
    for e in hits[:15]:
        print(("   ACROSS A COMMA — is this buyer ours? " if e["across"] else "   ") + fmt(e))
    print("\nTags:")
    for t in tags:
        print("   " + fmt(evaluate(con, t)))
    print("\nREADY" if not errors else f"\nNOT READY: {len(errors)} error(s)")
    return 1 if errors else 0


def cmd_audit(a):
    """The shop's own listings (Etsy's «Currently for Sale Listings» CSV: TITLE, TAGS) through the database —
    the tool's own measure of each listing, made without looking at sales. --missing lists tags without numbers."""
    con = connect()
    rows = list(csv.DictReader(Path(a.file).open(encoding="utf-8-sig")))
    sold: dict[str, int] = {}
    for f in a.sales or []:        # Etsy «Order Items» CSVs: only the item name and quantity are read (no buyer data)
        for r in csv.DictReader(Path(f).open(encoding="utf-8-sig")):
            sold[r["Item Name"].strip()] = sold.get(r["Item Name"].strip(), 0) + int(r["Quantity"] or 1)
    missing, out = [], []
    for r in rows:
        title = r["TITLE"].strip()
        tags = [clean(t.replace("_", " ")) for t in r["TAGS"].split(",") if t.strip()]   # Etsy's export joins words with _
        evs = [evaluate(con, t) for t in tags]
        for t, e in zip(tags, evs):
            if not latest(con, t) and t not in missing:
                missing.append(t)
        hits = title_phrases(con, title)
        out.append({
            "title": title, "chars": len(title), "tags": len(tags),
            "tag_demand": sum(e["demand"] for e in evs if e["measured"]),
            "tag_score": round(sum(e["score"] for e in evs) / max(len(evs), 1), 1),
            "unmeasured": sum(1 for e in evs if not e["measured"]),
            "title_demand": sum(e["demand"] for e in hits if not e["across"]),
            "own": sum(e["own"] for e in evs),
            "sold": sold.get(title, 0),
        })
    if a.missing:
        print(f"tags without eRank numbers ({len(missing)}):")
        for i in range(0, len(missing), 20):
            print("  " + ", ".join(missing[i:i + 20]))
        return
    out.sort(key=lambda o: -(o["tag_score"] + o["title_demand"] / 200))
    if sold:
        out.sort(key=lambda o: -o["sold"])
    print(f"{'tag score':>9} {'tag demand':>10} {'title demand':>12} {'unmeas':>6} {'own':>4} {'chars':>5} {'sold':>5}  title")
    for o in out:
        keep = "  ← SELLING: keep its title and tags" if o["sold"] >= KEEP_SOLD else ""
        print(f"{o['tag_score']:>9} {o['tag_demand']:>10} {o['title_demand']:>12} {o['unmeasured']:>6} {o['own']:>4} {o['chars']:>5}"
              f" {o['sold'] if sold else '':>5}  {o['title'][:80]}{keep}")


def cmd_block(a):
    con = connect()
    phrase = ("~" if a.contains else "") + clean(a.phrase)
    con.execute("INSERT OR REPLACE INTO block VALUES(?,?,?)", (phrase, a.reason, today()))
    con.commit()
    print(f"blocked: {phrase} — {a.reason}")


def cmd_save(a):
    con = connect()
    con.execute("INSERT INTO my_listing(book, saved_at, title, tags, note) VALUES(?,?,?,?,?)",
                (a.book, dt.datetime.now().isoformat(timespec="minutes"), a.title.strip(),
                 ", ".join(clean(t) for t in a.tags.split(",")), a.note))
    con.commit()
    print(f"saved listing version for {a.book}")


def cmd_summary(a):
    con = connect()
    q = lambda s: con.execute(s).fetchone()[0]
    print(f"keywords: {q('SELECT COUNT(*) FROM keyword')}  (with measured searches: "
          f"{q('SELECT COUNT(DISTINCT keyword_id) FROM metric WHERE searches IS NOT NULL')})")
    print(f"measurements: {q('SELECT COUNT(*) FROM metric')}  newest {q('SELECT MAX(observed_at) FROM metric')}")
    for r in con.execute("SELECT source, COUNT(*) n, MAX(observed_at) d FROM metric GROUP BY source"):
        print(f"   {r['source']:<16} {r['n']:>6}  newest {r['d']}")
    print(f"competitor listings: {q('SELECT COUNT(*) FROM listing')}  shops in tag reports: "
          f"{q('SELECT COUNT(DISTINCT shop) FROM shop_tag')}")
    print(f"blocked phrases: {q('SELECT COUNT(*) FROM block')}  my saved listings: {q('SELECT COUNT(*) FROM my_listing')}")


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("import-tagreport"); s.add_argument("files", nargs="+"); s.add_argument("--date")
    s.set_defaults(fn=cmd_import_tagreport)
    s = sub.add_parser("import-legacy"); s.add_argument("db"); s.add_argument("--date", default="2026-07-11")
    s.set_defaults(fn=cmd_import_legacy)
    s = sub.add_parser("import-erank"); s.add_argument("files", nargs="+"); s.set_defaults(fn=cmd_import_erank)
    s = sub.add_parser("import-own"); s.add_argument("file"); s.add_argument("--period", default="as shown in Etsy Stats")
    s.add_argument("--date"); s.set_defaults(fn=cmd_import_own)
    s = sub.add_parser("own"); s.set_defaults(fn=cmd_own)
    s = sub.add_parser("known"); s.add_argument("phrases", nargs="*"); s.add_argument("--file"); s.set_defaults(fn=cmd_known)
    s = sub.add_parser("related"); s.add_argument("words", nargs="+"); s.add_argument("--limit", type=int, default=40)
    s.set_defaults(fn=cmd_related)
    s = sub.add_parser("competitors"); s.add_argument("words", nargs="+"); s.add_argument("--limit", type=int, default=12)
    s.set_defaults(fn=cmd_competitors)
    s = sub.add_parser("pick"); s.add_argument("file"); s.set_defaults(fn=cmd_pick)
    s = sub.add_parser("lint"); s.add_argument("--title", required=True); s.add_argument("--tags", default="")
    s.set_defaults(fn=cmd_lint)
    s = sub.add_parser("audit"); s.add_argument("file"); s.add_argument("--missing", action="store_true")
    s.add_argument("--sales", nargs="*", help="Etsy «Order Items» CSVs: adds the sold count, marks listings to keep")
    s.set_defaults(fn=cmd_audit)
    s = sub.add_parser("block"); s.add_argument("phrase"); s.add_argument("--reason", required=True)
    s.add_argument("--contains", action="store_true", help="also block longer phrases that contain it")
    s.set_defaults(fn=cmd_block)
    s = sub.add_parser("save"); s.add_argument("book"); s.add_argument("--title", required=True)
    s.add_argument("--tags", required=True); s.add_argument("--note"); s.set_defaults(fn=cmd_save)
    s = sub.add_parser("summary"); s.set_defaults(fn=cmd_summary)
    a = ap.parse_args(argv)
    return a.fn(a) or 0


if __name__ == "__main__":
    sys.exit(main())
