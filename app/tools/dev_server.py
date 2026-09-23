"""Book Studio server for looking at the interface during development — never on the real data.

  python app/tools/dev_server.py            empty program on http://127.0.0.1:47890/
  python app/tools/dev_server.py --sample   plus made-up orders and one library book to click through
  python app/tools/dev_server.py --mockups  the listing-mockups utility on http://127.0.0.1:47891/

The data folder is .tmp\\bsdev in the repository, on drive D (or BOOK_STUDIO_DATA when it is set): no keys
there, so nothing reaches Etsy, Printify or Gelato. The mockups get .tmp\\bsdev-mockups, made-up templates and a pretend
Photoshop: nothing real is opened, and no Windows dialog comes up. Stop it with Ctrl+C (or preview_stop).
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
PORT = 47890
MOCKUPS_PORT = 47891

# The sample book's texts (made up): the library passport and what Olivia's printed book carries — with
# one misspelt name and one forgotten {Name}, for the text check to find.
SAMPLE_TEXTS = {
    "cover": "Blessed Day\nfor {Name}",
    "page1": "Dear {Name},\n\nWishing you a lifetime filled with love.\n\nWith love,\n{Gifter}",
    "page30": "Made for {Name},\nwith love and prayer.",
    **{f"spread{n}": f"{line}\n{{Name}} {verb} with a happy heart,\n{end}" for n, (line, verb, end) in enumerate([
        ("The morning bells ring soft and clear,", "wakes", "a brand new day is here."),
        ("A little dove sits on the wall,", "waves", "the gentlest bird of all."),
        ("The chapel door is open wide,", "steps", "with family by the side."),
        ("The water shines like morning dew,", "smiles", "the sky is bright and blue."),
        ("A candle glows with golden light,", "watches", "the flame so warm and bright."),
        ("The garden path is lined with flowers,", "skips", "through sunny morning hours."),
        ("A lamb is resting by the gate,", "sings", "the evening will not wait."),
        ("The choir hums a quiet tune,", "claps", "beneath the silver moon."),
        ("The river hums along the stones,", "dances", "on grassy meadow zones."),
        ("A rainbow bends across the hill,", "listens", "the world is calm and still."),
        ("The picnic cloth is checked and red,", "laughs", "with honey on the bread."),
        ("The stars come out one by one,", "yawns", "the busy day is done."),
        ("The moon peeks through the window pane,", "rests", "and dreams of gentle rain."),
        ("Goodnight to every tree and bird,", "prays", "with every gentle word."),
    ], 2)},
}
SLIPS = {6: ("{Name}", "Olivai"), 10: ("{Name}", "{NAME}")}  # spread -> what Olivia's book prints instead


def _book_bought(rid: int, n: int, cover: str, child: str) -> dict:
    """One book of a receipt: Etsy calls it a transaction, the program — an item of the order."""
    money = lambda cents: {"amount": cents, "divisor": 100, "currency_code": "USD"}  # noqa: E731
    return {
        "transaction_id": rid * 10 + n, "title": "Personalized Baptism Storybook for Kids", "quantity": 1,
        "price": money(3990), "sku": "", "listing_id": 4100000900,
        "variations": [
            {"formatted_name": "Cover Type &amp; Size", "formatted_value": cover},
            {"formatted_name": "Child's Name", "formatted_value": child},
            {"formatted_name": "Dedication", "formatted_value": "DEFAULT"},
            {"formatted_name": "From whom", "formatted_value": "Grandma &amp; Grandpa"},
        ],
    }


def _receipt(rid: int, name: str, country: str, city: str, state: str, cover: str, child: str,
             shipped: bool = False, days_ago: int = 0, also: tuple[str, ...] = ()) -> dict:
    """A made-up Etsy receipt in the shape the Etsy API returns (see profit.normalize_receipt).
    `also`: more children of the same order — an order of several books, one address."""
    money = lambda cents: {"amount": cents, "divisor": 100, "currency_code": "USD"}  # noqa: E731
    return {
        "receipt_id": rid, "name": name, "first_line": "12 Example St", "second_line": "", "city": city,
        "state": state, "zip": "10001", "country_iso": country, "status": "Completed" if shipped else "Paid",
        "is_shipped": shipped, "is_paid": True, "create_timestamp": int(time.time()) - days_ago * 86400,
        "message_from_buyer": "Could you ship before the baptism? Thank you!" if rid % 2 else "",
        "grandtotal": money(4990), "total_price": money(3990), "subtotal": money(3990),
        "total_shipping_cost": money(1000), "total_tax_cost": money(0), "discount_amt": money(0),
        "transactions": [_book_bought(rid, i, cover, kid) for i, kid in enumerate([child, *also])],
    }


def _printify(rid: int, status: str, tracking: str = "") -> dict:
    """A made-up Printify order (slim, as saved at sync) carrying the receipt number."""
    return {"id": f"{rid:024x}", "app_order_id": str(rid)[-6:], "total_price": 1995, "total_shipping": 500,
            "total_tax": 0, "created_at": time.strftime("%Y-%m-%d %H:%M:%S+00:00", time.gmtime()), "status": status,
            "metadata": {"shop_order_id": str(rid)}, "address_to": {}, "line_items": [],
            "shipments": [{"carrier": "usps", "number": tracking, "url": ""}] if tracking else []}


def _gelato(rid: int, status: str, carrier: str = "", tracking: str = "") -> dict:
    """A made-up Gelato order (slim, tracking already read) carrying the receipt number."""
    return {"id": f"00000000-0000-4000-8000-{rid:012d}", "orderReferenceId": f"{rid}-sample", "firstName": "",
            "lastName": "", "totalInclVat": "21.50", "currency": "EUR", "fulfillmentStatus": status,
            "financialStatus": "draft" if status == "draft" else "paid",
            "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime()),
            "orderType": "draft" if status == "draft" else "order",
            "shipments": [{"carrier": carrier, "number": tracking, "url": ""}] if tracking else []}


def seed(data: Path) -> None:
    from studio import core, profit  # imported after BOOK_STUDIO_DATA is set

    hard, soft = "Hardcover 8&quot; x 8&quot;", "Softcover 8&quot; x 8&quot;"
    receipts = [
        _receipt(4100000101, "Jane Doe", "US", "Springfield", "IL", hard, "Emma"),
        _receipt(4100000102, "Maria Example", "CA", "Toronto", "ON", soft, "Noah", days_ago=1),
        _receipt(4100000103, "Alex Sample", "GB", "Leeds", "", "Softcover 5.5&quot; x 5.5&quot;", "Olivia", days_ago=2),
        _receipt(4100000104, "Sam Test", "US", "Austin", "TX", hard, "Liam", shipped=True, days_ago=9),
        _receipt(4100000105, "Chris Demo", "US", "Denver", "CO", hard, "Ava", days_ago=4),
        _receipt(4100000106, "Pat Example", "US", "Salem", "OR", hard, "Mia", days_ago=1),
        _receipt(4100000107, "Lee Sample", "US", "Dayton", "OH", hard, "Leo", days_ago=3),
        # An order of two books to one address: each book has its own child and its own files, and they
        # go to the printer in one draft (owner, 20.09.2026).
        _receipt(4100000108, "Robin Sample", "US", "Madison", "WI", soft, "Sofia", days_ago=1, also=("Jack",)),
    ]
    printify_orders = [
        _printify(4100000104, "fulfilled", "9400100000000000000001"),
        _printify(4100000105, "fulfilled", "9400100000000000000002"),   # sent: waits for the mark on Etsy
        _printify(4100000106, "in-production"),
        _printify(4100000107, "has-issues"),
        {**_printify(4100000104, "in-production"), "id": "e" * 20 + "0104"},  # Liam's reprint from the archive
    ]
    gelato_orders = [
        _gelato(4100000102, "in_transit", "Canada Post Tracked Packet", "7023210000000003"),  # sent
        _gelato(4100000103, "draft"),
        _gelato(4100000107, "printed"),   # Leo's order was split: one book here, one in Printify
    ]
    snapshot = {"receipts": [profit.normalize_receipt(r) for r in receipts], "printify": printify_orders,
                "gelato": gelato_orders, "shopName": "Sample shop", "syncedAt": core.now_iso(), "warnings": [],
                "loaded": {source: core.now_iso() for source in ("etsy", "printify", "gelato")}}
    core.write_json(profit.SNAPSHOT, snapshot, backup=False)
    # One receipt with two print orders: what the queue and the profit row look like when the books of an
    # order went in two goes, or to two printers.
    core.write_json(profit.SENDS, {"4100000107": [
        {"provider": "printify", "orderId": f"{4100000107:024x}", "at": core.now_iso()},
        {"provider": "gelato", "orderId": f"00000000-0000-4000-8000-{4100000107:012d}", "at": core.now_iso()},
    ]}, backup=False)
    book_id = "0" * 31 + "1"
    folder = data / "library" / "books" / book_id
    if not (folder / "book.json").exists():
        from studio import library
        book = {"id": book_id, "schema": 1, "rev": 0, "createdAt": core.now_iso(),
                "title": "Personalized Baptism Storybook (sample)",
                "listing": {"id": "4100000900", "title": "Personalized Baptism Storybook for Kids", "state": "active"},
                "canvaUrl": "https://www.canva.com/design/sample", "notes": "", "archived": False,
                "cover": None, "thumbnail": None, "slots": library._empty_slots(),
                "text": {k: "" for k in library.TEXT_KEYS}}
        folder.mkdir(parents=True, exist_ok=True)
        library.save(book)
    from studio import library
    book = library.load(book_id)
    if book["text"] != SAMPLE_TEXTS:
        book["text"] = dict(SAMPLE_TEXTS)
        library.save(book)
    from studio import archive
    if not archive.entries():
        _seed_archive(data)
    print(f"Sample data: {len(receipts)} orders, 1 book, {len(archive.entries())} archived books", flush=True)


def _sample_book(folder: Path, name: str, pages: int, hue: int, story: bool = False) -> list:
    """Made-up print files (small, numbered) in the order archive's shape: Cover.png + 1..N.png. With
    `story`, a 30-page book carries SAMPLE_TEXTS as a printed book would (one text page per spread)."""
    from PIL import Image, ImageDraw, ImageFont

    def font(size):
        try:
            return ImageFont.truetype("arialbd.ttf", size)
        except OSError:
            return ImageFont.load_default()

    folder.mkdir(parents=True, exist_ok=True)
    cover = Image.new("RGB", (934, 492), (235, 225 - hue % 40, 205))
    d = ImageDraw.Draw(cover)
    d.rectangle([462, 0, 472, 492], fill=(150, 120, 90))
    d.text((233, 246), "BACK", font=font(60), fill=(80, 60, 50), anchor="mm")
    if story:
        d.text((700, 200), "Blessed Day", font=font(56), fill=(80, 60, 50), anchor="mm")
        d.text((700, 290), f"for {name}", font=font(56), fill=(80, 60, 50), anchor="mm")
    else:
        d.text((700, 220), name, font=font(80), fill=(80, 60, 50), anchor="mm")
        d.text((700, 300), "sample book", font=font(34), fill=(150, 60, 60), anchor="mm")
    cover.save(folder / "Cover.png")
    files = [(folder / "Cover.png", "Cover.png")]
    for n in range(1, pages + 1):
        page = Image.new("RGB", (480, 480), (200 + (n * 13 + hue) % 55, 215, 245 - (n * 7) % 50))
        d = ImageDraw.Draw(page)
        text = _printed(n, pages, name) if story else None
        if text is None:
            d.text((240, 200), str(n), font=font(170), fill=(40, 40, 40), anchor="mm")
            d.text((240, 380), f"Dear {name}" if n == 1 else f"page {n}", font=font(34), fill=(40, 40, 40), anchor="mm")
        else:
            lines = text.split("\n")
            for i, line in enumerate(lines):
                d.text((240, 240 + (i - len(lines) / 2) * 30), line, font=font(20), fill=(40, 40, 40), anchor="mm")
        page.save(folder / f"{n}.png")
        files.append((folder / f"{n}.png", f"{n}.png"))
    return files


def _printed(n: int, pages: int, name: str) -> str | None:
    """What page n of the sample story book says, or None for a picture page."""
    fill = lambda t: t.replace("{Gifter}", "Grandma & Grandpa").replace("{Name}", name)  # noqa: E731
    if n == 1:
        return fill(SAMPLE_TEXTS["page1"])
    if n == pages:
        return fill(SAMPLE_TEXTS["page30"])
    spread = n // 2 + 1
    if n != (2 * spread - 1 if spread % 2 == 0 else 2 * spread - 2):
        return None
    text = SAMPLE_TEXTS[f"spread{spread}"]
    if spread in SLIPS:
        text = text.replace(*SLIPS[spread])
    return fill(text)


def _seed_archive(data: Path) -> None:
    """Four archived books — counting down, waiting for Etsy, kept, a reprint of the first — and a Gelato draft
    that never went to print: not in the archive, but Olivia's order card offers its files."""
    from studio import archive
    src = data / "tmp" / "sample-archive"
    day = 86400
    address = {"firstName": "Sam", "lastName": "Test", "addressLine1": "12 Example St", "city": "Austin",
               "state": "TX", "postCode": "10001", "country": "US"}
    liam = archive.store("printify", _sample_book(src / "liam", "Liam", 24, 0), {
        "title": "4100000104 - Liam", "productId": "sample-product-1", "orderId": f"{4100000104:024x}",
        "url": "https://printify.com/app/products", "variant": "8x8 / Matte", "address": address})
    archive.update(liam, sentAt=archive._iso(time.time() - 12 * day), shippedAt=archive._iso(time.time() - 3 * day))
    noah = archive.store("gelato", _sample_book(src / "noah", "Noah", 28, 40), {
        "title": "4100000102 - Noah", "format": "softcover_8x8", "formatLabel": "Softcover 8×8",
        "orderId": "00000000-0000-4000-8000-004100000102", "address": {**address, "firstName": "Maria",
                                                                     "lastName": "Example", "country": "CA", "state": "ON"}})
    archive.update(noah, sentAt=archive._iso(time.time() - 1 * day))
    ava = archive.store("printify", _sample_book(src / "ava", "Ava", 24, 80), {
        "title": "4100000105 - Ava", "productId": "sample-product-2", "orderId": f"{4100000105:024x}", "address": address})
    archive.update(ava, sentAt=archive._iso(time.time() - 5 * day), keep=True)
    kept = archive.folder(liam)
    reprint = archive.store("printify", [(kept / f["file"], f["file"]) for f in archive.get(liam)["files"]], {
        "title": "4100000104 - Liam", "productId": "sample-product-1", "orderId": "e" * 20 + "0104",
        "address": address, "reprintOf": liam})
    archive.update(reprint, sentAt=archive._iso(time.time() - 2 * 3600))
    olivia = archive.store("gelato", _sample_book(src / "olivia", "Olivia", 30, 120, story=True), {
        "title": "4100000103 - Olivia", "format": "softcover_5x5", "formatLabel": "Softcover 5.5×5.5",
        "orderId": "00000000-0000-4000-8000-004100000103", "address": {**address, "country": "GB", "state": ""}})
    archive.update(olivia, sentAt=archive._iso(time.time() - 2 * day))


MARK = ".book-studio-sample"    # this folder was made by this tool and may be written over


def claim(data: Path, default: Path) -> str | None:
    """Sample data goes only into this tool's own folder or one it made itself. Any other folder may be
    the owner's real data — a copy, a backup, a moved folder — and refusing one exact path is not enough.
    Returns the reason to stop, or None when the folder may be used (and is marked as ours)."""
    if data == (APP / "data").resolve():
        return "це справжня папка даних програми"
    if (data / "vault.json").exists():
        # Also when a key was typed into this tool's own Settings: a real key never lives in sample data,
        # and the tool does not delete keys by itself — the folder is for the owner to remove.
        return ("у ній лежать ключі (vault.json) — це не тимчасові дані. Якщо ключ зберегли в налаштуваннях "
                "тестового сервера, видаліть цю папку вручну")
    if not (data / MARK).exists() and data != default and data.exists() and any(data.iterdir()):
        return "вона не порожня й не створена цим інструментом"
    data.mkdir(parents=True, exist_ok=True)
    (data / MARK).write_text("Sample data for app/tools/dev_server.py. Delete this folder any time.\n",
                             encoding="utf-8")
    return None


# ---------------------------------------------------------------- the listing-mockups utility

def _scene(size: tuple[int, int], shade: tuple[int, int, int], book: tuple[int, int, int, int]):
    """A made-up "template preview": a tinted table with a pale open book on it (the preview's own PSD stand-in)."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", size, shade)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = book
    d.rectangle([x0 + 14, y0 + 18, x1 + 14, y1 + 18], fill=tuple(max(0, c - 28) for c in shade))  # shadow
    d.rectangle([x0, y0, x1, y1], fill=(246, 244, 238))
    d.line([(x0 + x1) // 2, y0, (x0 + x1) // 2, y1], fill=(210, 206, 198), width=6)
    return im


def seed_mockups(data: Path) -> None:
    """Made-up templates (small pictures under the owner's file names — the page shows their previews), a
    made-up Canva demo book as a ZIP, and a folder for the pictures."""
    import zipfile
    from PIL import Image, ImageDraw, ImageFont
    from studio import core, mockups
    templates = data / "templates"
    templates.mkdir(parents=True, exist_ok=True)
    shades = [(196, 202, 214), (214, 206, 196), (200, 212, 204), (220, 214, 222), (206, 206, 206), (224, 210, 200)]
    for t, shade in zip(mockups.TEMPLATES, shades):
        _scene((900, 600), shade, (170, 150, 730, 450)).save(templates / t["file"], "PNG")  # read by content
    (data / "out").mkdir(exist_ok=True)
    core.write_json(mockups.PLACES, {"templates": str(templates), "photoshop": str(data / "photoshop")}, backup=False)
    demo = data / "Goose demo.zip"
    if not demo.exists():
        font = ImageFont.load_default(size=150)
        with zipfile.ZipFile(demo, "w") as zf:
            cover = Image.new("RGB", (1400, 700), (70, 120, 90))
            d = ImageDraw.Draw(cover)
            d.rectangle([700, 0, 1400, 700], fill=(236, 196, 80))
            d.rectangle([690, 0, 709, 700], fill=(40, 50, 70))
            d.text((1050, 350), "Goose", font=font, fill=(60, 40, 20), anchor="mm")
            zf.writestr("1.png", _png(cover))
            for n in range(1, 25):
                page = Image.new("RGB", (700, 700), ((n * 53) % 200 + 40, (n * 97) % 160 + 60, (n * 31) % 180 + 60))
                ImageDraw.Draw(page).text((350, 350), str(n), font=font, fill=(250, 250, 245), anchor="mm")
                zf.writestr(f"{n + 1}.png", _png(page))


def _png(im) -> bytes:
    import io
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return buf.getvalue()


def pretend_photoshop(script: Path) -> None:
    """Plays Photoshop running the script: reports progress into the status file the way mockups.jsx does and
    saves each picture as the template's made-up scene with the prepared pages laid on it (enough to see the
    page work). The second script («Зберегти відкриті») saves the templates it was given and "closes" them."""
    from PIL import Image
    finish = script.name == "finish.jsx"
    work = json.loads((script.parent / ("finish.json" if finish else "job.json")).read_text(encoding="utf-8"))
    status = {"state": "running", "step": 0, "title": "", "saved": [], "opened": [], "closed": [], "problems": [],
              "total": len(work["templates"]) if finish else sum(1 + len(t["shots"]) for t in work["templates"])}

    def report():
        Path(work["status"]).write_text(json.dumps(status), encoding="utf-8")

    def mockup(template: dict, fills: list, save: str) -> None:
        source = Path(template.get("source") or "")
        with Image.open(source if source.is_file() else next(Path(work["run"]).glob("templates/*"))) as scene:
            sheet = scene.convert("RGB").resize((1500, 1000))
        for i, f in enumerate(fills[:2]):
            with Image.open(f["image"]) as im:
                im = im.convert("RGB").resize((460, 460))
                sheet.paste(im, (290 + i * 460, 270))
        sheet.save(save)

    def run():
        time.sleep(2.5)  # the owner answers "run this script?"
        if finish:
            for t in work["templates"]:
                status["title"] = t["title"]
                report()
                time.sleep(0.6)
                Image.new("RGB", (1500, 1000), (120, 132, 150)).save(t["shots"][0]["save"])
                status["saved"].append(t["shots"][0]["save"])
                status["closed"].append(t["name"])
                status["step"] += 1
                report()
            status["state"] = "done"
            return report()
        for t in work["templates"]:
            if Path(work["cancel"]).exists():
                status["state"] = "cancelled"
                return report()
            status["title"] = t["title"]
            status["step"] += 1
            report()
            time.sleep(0.4)
            for shot in t["shots"]:
                status["title"] = shot["title"]
                report()
                mockup(t, shot["fills"] or t["fills"][-1:], shot["save"])
                status["saved"].append(shot["save"])
                status["step"] += 1
                report()
                time.sleep(0.4)
            if t["keepOpen"]:
                status["opened"].append(t["name"])
        status["state"] = "done"
        report()

    threading.Thread(target=run, daemon=True).start()


def main_mockups(data: Path) -> int:
    from studio import desktop, mockups
    seed_mockups(data)
    mockups.find_photoshop = lambda base: {"exe": Path("Photoshop.exe"), "launcher": Path("Photoshop.exe")}
    mockups.running = lambda: True
    mockups.launch = pretend_photoshop
    # no Windows dialog, no flashing window or sound in the preview
    desktop.pick_folder = lambda title, initial="": str(data / "out")
    desktop.pick_zip = lambda title, initial="": str(data / "Goose demo.zip")
    desktop.attention = lambda title_part: False
    from studio.mockups_app import main as run
    return run(["--no-window", "--port", str(MOCKUPS_PORT)])


def main(argv: list[str]) -> int:
    # On drive D beside the code, not in Windows' temp folder on drive C (the owner keeps drive C clean).
    default = (APP.parent / ".tmp" / ("bsdev-mockups" if "--mockups" in argv else "bsdev")).resolve()
    data = Path(os.environ.get("BOOK_STUDIO_DATA") or default).resolve()
    stop = claim(data, default)
    if stop:
        print(f"Не чіпаю {data}: {stop}.\nВиберіть іншу папку в BOOK_STUDIO_DATA або видаліть цю.",
              file=sys.stderr)
        return 1
    os.environ["BOOK_STUDIO_DATA"] = str(data)
    os.environ["BOOK_STUDIO_SAMPLE"] = "1"  # no key is stored or offered here (studio.core.SAMPLE)
    sys.path.insert(0, str(APP))
    if "--mockups" in argv:
        return main_mockups(data)
    if "--sample" in argv:
        seed(data)
    from studio.main import main as run
    return run(["--no-window", "--port", str(PORT)])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
