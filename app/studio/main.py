"""Entry point: start the local server, open the app window, stop when it closes."""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from typing import Callable

from . import core


def _running_instance(port: int, app: str = core.APP_NAME) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/ping", timeout=1.5) as resp:
            return json.loads(resp.read().decode("utf-8")).get("app") == app
    except Exception:
        return False


def run_until_closed(proc, busy: Callable[[], bool]) -> None:
    """Returns once the app window is gone for good (a reload is not a close) and busy() says nothing is left
    to finish. Shared with the listing-mockups utility (mockups_app.py)."""
    from . import server
    started = time.time()
    try:
        while True:
            time.sleep(1.0)
            now = time.time()
            st = server.state
            window_alive = proc is not None and proc.poll() is None
            closed = False
            # The page said goodbye (window closed) and did not come back (reload).
            if st.bye_at and now - st.bye_at > 6 and st.last_heartbeat < st.bye_at:
                closed = True
            # Our window process ended and no page has pinged us recently.
            if proc is not None and not window_alive and now - max(st.last_heartbeat, started) > 12:
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

    from . import desktop, server

    if _running_instance(args.port):
        core.log.info("Instance already running — opening another window")
        if not args.no_window:
            desktop.open_app_window(f"http://127.0.0.1:{args.port}/")
        return 0

    core.own_temp()  # the window, the dialogs and cloudflared keep their temp files on drive D, not C

    # Register all API routes.
    from . import archive, creator, drops, etsy, gelato, images, library, orders, printify, profit, sendlog, settings_api, textcheck, tunnel  # noqa: F401

    tunnel.cleanup_stale()
    creator.forget_old_form()
    drops.clear_drops()
    httpd = server.start(args.port)
    profit.startup_sync()  # the one automatic refresh of orders; afterwards only the refresh button
    # The order archive tidies up on its own (again after every sync): books whose 14 days are over go.
    import threading
    threading.Thread(target=archive.refresh_quietly, daemon=True).start()
    threading.Thread(target=images.prune_cache_quietly, daemon=True).start()  # old previews go
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
    # Finish background work first: uploads, drafts, and Gelato file links still in use
    # (a text check only reads — it is not waited for).
    run_until_closed(proc, lambda: jobs.any_running(ignore=("textcheck",)) or bool(tunnel.registry.active()))
    core.log.info("Shutting down")
    tunnel.registry.close_all()
    httpd.shutdown()
    core.clear_own_temp()
    return 0


if __name__ == "__main__":
    sys.exit(main())
