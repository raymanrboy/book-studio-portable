"""The mockups' made-up world for the preview server: templates under the owner's file names (small pictures), a
Canva demo book as a ZIP, a folder for the pictures, and a pretend Photoshop that plays the scripts — nothing real is
opened, and the mockups' Windows dialogs answer by themselves."""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path


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
    made-up Canva demo book as a ZIP, a folder for the pictures, and a pretend Photoshop."""
    import types
    import zipfile
    from PIL import Image, ImageDraw, ImageFont
    from studio import core, desktop, mockups
    mockups.find_photoshop = lambda base: {"exe": Path("Photoshop.exe"), "launcher": Path("Photoshop.exe")}
    mockups.running = lambda: True
    mockups.launch = pretend_photoshop
    # The mockups' Windows dialogs answer by themselves and no window flashes or sounds — only theirs: the rest of
    # the program keeps its own dialogs.
    fake = types.SimpleNamespace(**{k: getattr(desktop, k) for k in dir(desktop) if not k.startswith("__")})
    fake.pick_folder = lambda title, initial="": str(data / "out")
    fake.pick_zip = lambda title, initial="": str(data / "Goose demo.zip")
    fake.attention = lambda title_part: False
    mockups.desktop = fake
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
        if status["opened"] and work.get("cover") and Path(work["cover"]).is_file():
            status["coverOpened"] = True  # the book's cover "opened" beside the templates, as the real script does
        status["state"] = "done"
        report()

    threading.Thread(target=run, daemon=True).start()
