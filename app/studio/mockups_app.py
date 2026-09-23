"""The listing-mockups utility as a program of its own: its own window, port and data folder (app/data/mockups).

Only the parts it needs are loaded — the dropped files, the mockups, the lifecycle routes — so this process
never touches keys, orders or the library. Started from app/Mockups.pyw (the desktop shortcut «Мокапи»).
Moving it into Book Studio later: import `mockups` in main.py and give pages/mockups.js a route there.
"""
from __future__ import annotations

import argparse
import sys
import threading
import time

from . import core

APP = "Book Studio · Мокапи"   # what /api/ping answers here: a second launch only opens another window
PORT = 47831


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="mockups")
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--no-window", action="store_true", help="only run the server (development)")
    args = parser.parse_args(argv)
    if core.DATA_DIR == (core.ROOT / "data").resolve():
        # Book Studio's own folder: its dropped files would be wiped here (app/Mockups.pyw sets the right one).
        print("The mockups keep a data folder of their own (app/data/mockups): start them from their .pyw.", file=sys.stderr)
        return 1

    core.setup_logging()

    from . import desktop, server
    from .main import _running_instance, run_until_closed

    if _running_instance(args.port, APP):
        core.log.info("Mockups already running — opening another window")
        if not args.no_window:
            desktop.open_app_window(f"http://127.0.0.1:{args.port}/")
        return 0

    core.own_temp()  # the window, the dialogs and Photoshop keep their temp files on drive D, not C
    from . import drops, images, mockups  # noqa: F401 — the import registers the routes
    from .jobs import jobs

    server.state.app = APP
    server.state.page = "mockups.html"
    # The window wears Book Studio's theme (read only; this program keeps its own data folder).
    if not core.SAMPLE:  # the preview server (app/tools/dev_server.py) reads nothing of the real data
        mockups.BOOK_SETTINGS = core.ROOT / "data" / "settings.json"
    drops.clear_drops()
    mockups.clean_runs()
    httpd = server.start(args.port)
    threading.Thread(target=images.prune_cache_quietly, daemon=True).start()
    url = f"{server.base_url()}/"
    if args.no_window:
        print(f"Mockups: {url}", flush=True)
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass
        httpd.shutdown()
        core.clear_own_temp()
        return 0

    proc = desktop.open_app_window(url)
    run_until_closed(proc, jobs.any_running)  # a run still copying or watching Photoshop is let finish
    core.log.info("Mockups: shutting down")
    httpd.shutdown()
    # Nothing waits for the window any more: the unpacked demo book goes, and so do the runs Photoshop can no
    # longer have open (the copies of templates still open in it wait for the next launch or a day).
    drops.clear_drops()
    mockups.clean_runs()
    core.clear_own_temp()
    return 0


if __name__ == "__main__":
    sys.exit(main())
