"""The listing slides from the command line — for the agent (the skill `listing-slides`) and the tests; works with
Book Studio's window closed (it starts its own small server for the drawing).

    python app/tools/slides.py list                               the schemes, the books' slides (Workshop books first)
    python app/tools/slides.py path  <slide> [--set ID]           the scene's file (to read and edit)
    python app/tools/slides.py render <slide> [--set ID] --to X.png   one slide drawn at 2000×2000 into X.png (a look)
    python app/tools/slides.py bake [slide …] --set ID            baked (Listing N.png): a Workshop book's etsy/, else beside its mockups
    python app/tools/slides.py cutout <mockup.png …>              cut out without background (into no-background/)

--set: a Workshop book's folder name (25.sleepy-trucks-bedtime), an older set's id, or "template" (the default) —
the default scheme, drawn with the newest book's pictures.
"""
from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))


def _server():
    from studio import server, slides  # noqa: F401  (the slides' routes)
    server.start(0)
    return server.base_url(), server.SESSION_TOKEN


def main(argv: list[str]) -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["list", "path", "render", "bake", "cutout"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--set", default="template")
    ap.add_argument("--to")
    a = ap.parse_args(argv)
    from studio.slides import bake, cutout, store, work
    from studio.jobs import UserError
    try:
        if a.command == "list":
            for x in store.list_schemes():
                print(f"scheme:{x['key']}\t{x['name']}{' — for new books (--set template edits it)' if x['default'] else ''}"
                      f"\t{store.SCHEMES / x['key']}")
            for rec in store.list_sets():
                print(f"{rec['id']}\t{rec.get('name')}\t{rec.get('folder')}\tbooks: {', '.join(rec.get('books', {}))}"
                      f"\tpictures: {', '.join(rec.get('pictures', {}))}\tnumbers: {rec.get('numbers')}")
            return 0
        where = store.valid_where(a.set)
        if a.command == "path":
            slide = store.valid_slide(a.args[0] if a.args else "")
            path = store.scene_path(where, slide)
            if not path.is_file():   # the template's slide not touched yet: its first design is written out to edit
                scene, _ = store.load(where, slide)
                store.save(where, slide, scene, None)
            print(path)
            return 0
        if a.command == "render":
            slide = store.valid_slide(a.args[0] if a.args else "")
            if not a.to:
                raise UserError("Куди малювати? --to <файл.png>")
            base, token = _server()
            out = bake.bake(where, [slide], {slide: Path(a.to).resolve()}, base, token)
            print(out[slide])
            return 0
        if a.command == "bake":
            if where == store.TEMPLATE:
                raise UserError("Запікаються слайди книги: --set <id> (python app/tools/slides.py list).")
            slides = [store.valid_slide(s) for s in a.args] or store.SLIDES
            base, token = _server()
            quiet = types.SimpleNamespace(progress=lambda *x, **k: None, share=lambda *x: None)
            for p in work.bake_set(quiet, store.read_set(where), slides, base, token):
                print(Path(store.read_set(where)["folder"]) / p["name"])
            return 0
        if a.command == "cutout":
            from studio import mockups
            for name in a.args:
                folder = cutout.ensure(Path(name), mockups.places()["templates"])
                print(Path(name).parent / cutout.NO_BG / Path(name).name, "·", folder)
            return 0
    except UserError as err:   # ApiError is one too
        print(f"Помилка: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
