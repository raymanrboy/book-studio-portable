"""Entry point: start the local server, open the app window, stop when it closes."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from typing import Callable

from . import core


def _running_instance(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=1.5) as resp:
            answer = json.loads(resp.read().decode("utf-8"))
        return answer.get("app") == core.APP_NAME and answer.get("data") == core.data_id()
    except Exception:
        return False


_mutex = None             # kept for the life of the process: the one-copy lock below


def _another_copy_starting() -> bool:
    """True when another process of this program on the SAME data is already up or just starting — a named Windows mutex, so two quick
    double-clicks cannot start two servers on one data folder (the second would run the start-up clean-ups under the first)."""
    global _mutex
    if os.name != "nt":
        return False
    import ctypes
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateMutexW.restype = ctypes.c_void_p
    _mutex = kernel.CreateMutexW(None, False, "Local\\BookStudio-" + core.data_id())
    return ctypes.get_last_error() == 183          # ERROR_ALREADY_EXISTS


SILENCE = 90   # seconds without a page's ping before a window handed over to another Edge process counts as closed
GRACE = 12     # ... and when the window's own process was seen running and then ended


def _stop_ollama() -> None:
    """The portable copy's own Ollama goes with the program: it would hold `runtime/Ollama` (no moving, renaming or ejecting the drive) and the
    graphics card, and another copy's Ollama could answer in its place. A PC's own Ollama is never touched."""
    from . import modules, portable
    folder = portable.ollama_folder()
    if folder and folder.is_dir():
        try:
            modules._stop_processes(folder)
        except Exception:
            core.log.exception("Ollama was not stopped")


def run_until_closed(proc, busy: Callable[[], bool]) -> None:
    """Returns once the app window is gone for good (a reload is not a close) and busy() says nothing is left
    to finish."""
    from . import server
    started = time.time()
    seen_alive = False        # our own window process was running when looked at: its end is the window closing
    try:
        while True:
            time.sleep(1.0)
            now = time.time()
            st = server.state
            window_alive = proc is not None and proc.poll() is None
            seen_alive = seen_alive or window_alive
            closed = False
            # The page said goodbye (window closed) and did not come back (reload). Not while our window's process is still
            # there: a goodbye from a page Edge froze or reloaded is not a closed window (04.10.2026).
            if st.bye_at and now - st.bye_at > 6 and st.last_heartbeat < st.bye_at and not window_alive:
                closed = True
            # Our window process ended and no page has pinged us recently. Edge may hand the window to a process that was
            # already running and end ours at once (never seen running): a covered window's page then pings slowly, so the silence
            # must be long. A process seen running that ends is the window closed: 12 s.
            if proc is not None and not window_alive and now - max(st.last_heartbeat, started) > (GRACE if seen_alive else SILENCE):
                closed = True
            # Fallback browser without process tracking: stop after a long silence.
            if proc is None and st.last_heartbeat and now - st.last_heartbeat > 600:
                closed = True
            if closed and not busy():
                break
    except KeyboardInterrupt:
        pass


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="book-studio")
    parser.add_argument("--port", type=int, default=core.DEFAULT_PORT)
    parser.add_argument("--no-window", action="store_true", help="only run the server (development)")
    args = parser.parse_args(argv)

    core.ensure_dirs()
    core.setup_logging()

    from . import portable
    portable.rebase_paths()   # the portable copy was moved: the paths kept inside the data follow it

    from . import desktop, server

    if _running_instance(args.port):
        core.log.info("Instance already running — opening another window")
        if not args.no_window:
            desktop.open_app_window(f"http://127.0.0.1:{args.port}/")
        return 0

    if _another_copy_starting():
        for _ in range(60):                        # the first one is still starting: wait for it, then only open its window
            if _running_instance(args.port):
                break
            time.sleep(0.5)
        core.log.info("Another copy on this data is starting — opening its window")
        if not args.no_window:
            desktop.open_app_window(f"http://127.0.0.1:{args.port}/")
        return 0

    core.own_temp()  # the window, the dialogs and cloudflared keep their temp files on drive D, not C

    # Register all API routes.
    from . import archive, backup, creator, drops, etsy, gelato, gelato_accounts, images, library, library_files, mockups, modules, orders, printify, profit, sendlog, settings_api, slides, sync, textcheck, transfer, tunnel, workshop  # noqa: F401

    core.sweep_tmp()          # uploads, upscale copies and an import's opened keys that a crash left in data/tmp
    transfer.sweep()
    tunnel.cleanup_stale()
    drops.clear_drops()
    mockups.clear_books()
    slides.store.clean_temporary()  # the slides' cut-out cache and the bake's browser files (29.09.2026)
    httpd = server.start(args.port)
    sync.startup_sync()  # the one automatic refresh of orders; afterwards only the refresh button
    # The order archive tidies up on its own (again after every sync): books whose 14 days are over go.
    import threading
    threading.Thread(target=archive.refresh_quietly, daemon=True).start()
    threading.Thread(target=images.prune_cache_quietly, daemon=True).start()  # old previews go
    threading.Thread(target=mockups.clean_runs, daemon=True).start()  # runs Photoshop no longer needs go
    threading.Thread(target=core.daily_snapshot, name="daily-snapshot", daemon=True).start()   # yesterday's state is always on the disk
    threading.Thread(target=textcheck.run.prime, name="textcheck-prime", daemon=True).start()  # the model read in quietly, for the first check
    # A Workshop book passed on before 27.09.2026 kept a copy of its pages in the library: it takes them from the
    # Workshop instead, its copies to the Recycle Bin (once; a copy that differs keeps its book as it is).
    threading.Thread(target=library.link_workshop_books, daemon=True).start()
    backup.schedule()  # a copy to Google Drive when the last one is 3 days old (the window waits for it on close)
    url = f"{server.base_url()}/"
    if args.no_window:
        print(f"Book Studio: {url}", flush=True)
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            pass
        httpd.shutdown()
        core.clear_own_temp()
        return 0

    proc = desktop.open_app_window(url)
    from .jobs import jobs
    # Finish background work first: uploads, drafts, Gelato file links still in use and a mockup run still
    # watching Photoshop (a text check only reads — it is not waited for).
    from .workshop import upscale
    run_until_closed(proc, lambda: jobs.any_running(ignore=("textcheck",)) or bool(tunnel.registry.active()) or upscale.busy())
    core.log.info("Shutting down")
    tunnel.registry.close_all()
    httpd.shutdown()
    _stop_ollama()
    # The unpacked demo book goes, and so do the mockup runs Photoshop can no longer have open (the copies of
    # templates still open in it wait for the next launch or a day).
    mockups.clear_books()
    slides.store.clean_temporary()  # the slides' cut-out cache and the bake's browser files (29.09.2026)
    mockups.clean_runs()
    core.clear_own_temp()
    return 0


if __name__ == "__main__":
    sys.exit(main())
