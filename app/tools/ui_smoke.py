"""A robot that clicks through the interface (06.10.2026): it starts Book Studio on made-up data (dev_server.py
--sample, its own folder .tmp\\bsui), opens every page in a hidden Edge, presses the pages' tabs, and reports what
broke — a script error, a red message, a page left empty, a request the program answered with an error.

  python app/tools/ui_smoke.py          every page; exit code 0 when nothing broke
  python app/tools/ui_smoke.py -v       and what it opened

Nothing real is touched: the made-up data has no keys (nothing reaches Etsy, Printify or Gelato), Edge runs with a
throwaway profile, and both folders go when it is done. The test suite runs it too (tests/test_ui_smoke.py)."""
from __future__ import annotations

import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))

DATA = (APP.parent / ".tmp" / "bsui").resolve()
EDGE_PROFILE = (APP.parent / ".tmp" / "bsui-edge").resolve()
MARK = ".book-studio-sample"            # dev_server.py marks the folders it made — only such a folder is cleared here

# The pages and what is pressed on them. `{order}`, `{book}`, `{work}` — the first of each from the made-up data.
PAGES = [
    ("#/orders", ".seg button"),
    ("#/orders/{order}", None),
    ("#/books/work", ".seg button"),
    ("#/books/shop", None),
    ("#/books/archive", None),
    ("#/book/{book}", None),
    ("#/workshop/{work}", "[data-act=step]"),
    ("#/tools", None),
    ("#/creator", None),
    ("#/archive", None),
    ("#/profit", None),
    ("#/settings", None),
    ("#/mockups", None),
    ("#/photos", None),
    ("#/slides/template/1", None),
]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def find_edge() -> str | None:
    from studio import desktop
    found = desktop.find_browser()
    return found if found and found.lower().endswith("msedge.exe") else found


def _clear(folder: Path) -> None:
    """Only a folder this tool (or dev_server.py) made: the made-up data or the throwaway Edge profile."""
    if folder.exists() and ((folder / MARK).exists() or folder == EDGE_PROFILE):
        shutil.rmtree(folder, ignore_errors=True)


class Socket:
    """The few WebSocket frames the DevTools protocol needs (text, masked from the client), without a library."""

    def __init__(self, url: str):
        host, rest = url.removeprefix("ws://").split("/", 1)
        name, port = host.split(":")
        self.sock = socket.create_connection((name, int(port)), timeout=20)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((f"GET /{rest} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                           f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        head = b""
        while b"\r\n\r\n" not in head:
            head += self.sock.recv(1)
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise ConnectionError(head.decode(errors="replace"))
        self.next_id = 0
        self.events: list[dict] = []

    def _read(self, n: int) -> bytes:
        out = b""
        while len(out) < n:
            part = self.sock.recv(n - len(out))
            if not part:
                raise ConnectionError("Edge closed the connection")
            out += part
        return out

    def receive(self) -> dict:
        data = b""
        while True:
            b1, b2 = self._read(2)
            size = b2 & 0x7F
            if size == 126:
                size = struct.unpack(">H", self._read(2))[0]
            elif size == 127:
                size = struct.unpack(">Q", self._read(8))[0]
            data += self._read(size)
            if b1 & 0x80:
                return json.loads(data)

    def send(self, method: str, **params) -> dict:
        self.next_id += 1
        payload = json.dumps({"id": self.next_id, "method": method, "params": params}).encode()
        mask = os.urandom(4)
        size = len(payload)
        head = bytes([0x81]) + (bytes([0x80 | size]) if size < 126 else
                                bytes([0x80 | 126]) + struct.pack(">H", size) if size < 65536 else
                                bytes([0x80 | 127]) + struct.pack(">Q", size))
        self.sock.sendall(head + mask + bytes(c ^ mask[i % 4] for i, c in enumerate(payload)))
        while True:
            message = self.receive()
            if message.get("id") == self.next_id:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message.get("result") or {}
            self.events.append(message)

    def js(self, expression: str):
        result = self.send("Runtime.evaluate", expression=expression, awaitPromise=True, returnByValue=True)
        if result.get("exceptionDetails"):
            raise RuntimeError(result["exceptionDetails"].get("text"))
        return result.get("result", {}).get("value")

    def drain(self, seconds: float) -> None:
        """Collects what the page says (errors, failed requests) while it settles."""
        end = time.monotonic() + seconds
        self.sock.settimeout(0.1)
        try:
            while time.monotonic() < end:
                try:
                    self.events.append(self.receive())
                except (socket.timeout, TimeoutError):
                    continue
        finally:
            self.sock.settimeout(20)


SETTLED = """new Promise((done) => {
  let last = '', same = 0;
  const end = Date.now() + 6000;
  const tick = () => {
    const view = document.getElementById('view');
    const now = view ? view.innerText.length + ':' + view.querySelectorAll('*').length : '';
    same = now && now === last ? same + 1 : 0; last = now;
    if (same >= 3 || Date.now() > end) done(now); else setTimeout(tick, 120);
  };
  tick();
})"""

STATE = """(() => {
  const view = document.getElementById('view');
  return {
    empty: !view || !view.innerText.trim(),
    toasts: [...document.querySelectorAll('.toast-error')].map((t) => t.innerText.trim()),
  };
})()"""

IDS = """(async () => {
  const token = document.querySelector('meta[name="studio-token"]').content;
  const get = (path) => fetch(path, { headers: { 'X-Studio-Token': token } }).then((r) => r.json());
  const [orders, lib, work] = await Promise.all([get('/api/orders'), get('/api/library/books'), get('/api/workshop/books')]);
  return { order: orders.orders?.[0]?.receiptId, book: lib.books?.[0]?.id, work: work.books?.[0]?.id };
})()"""


def problems_in(events: list[dict], base: str) -> list[str]:
    out = []
    for e in events:
        method, params = e.get("method"), e.get("params") or {}
        if method == "Runtime.exceptionThrown":
            d = params.get("exceptionDetails") or {}
            out.append("помилка скрипту: " + ((d.get("exception") or {}).get("description") or d.get("text") or "?")
                       .splitlines()[0])
        elif method == "Runtime.consoleAPICalled" and params.get("type") == "error":
            out.append("console.error: " + " ".join(str(a.get("value") or a.get("description") or "")
                                                     for a in params.get("args") or [])[:200])
        elif method == "Network.responseReceived":
            r = params.get("response") or {}
            if r.get("url", "").startswith(base) and r.get("status", 200) >= 500:
                out.append(f"сервер відповів {r['status']}: {r['url'][len(base):]}")
    return out


def run(verbose: bool = False) -> list[str]:
    edge = find_edge()
    if not edge:
        raise RuntimeError("Edge не знайдено")
    port, debug = free_port(), free_port()
    _clear(DATA)
    _clear(EDGE_PROFILE)
    env = {**os.environ, "BOOK_STUDIO_DATA": str(DATA), "BOOK_STUDIO_DEV_PORT": str(port),
           "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
    no_window = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    server = subprocess.Popen([sys.executable, str(APP / "tools" / "dev_server.py"), "--sample"], env=env,
                              stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=no_window)
    browser = None
    base = f"http://127.0.0.1:{port}/"
    try:
        _wait(base, server)
        browser = subprocess.Popen([edge, "--headless=new", f"--remote-debugging-port={debug}",
                                    f"--user-data-dir={EDGE_PROFILE}", "--no-first-run", "--no-default-browser-check",
                                    "--disable-extensions", "--window-size=1400,900", "about:blank"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=no_window)
        page = _page(debug)
        ws = Socket(page)
        for domain in ("Runtime", "Network", "Page"):
            ws.send(f"{domain}.enable")
        ws.send("Page.navigate", url=base + "#/orders")
        ws.drain(1.5)
        ws.js(SETTLED)
        ws.js("fetch('/api/settings/ui', {method: 'POST', headers: {'X-Studio-Token': document.querySelector("
              "'meta[name=\"studio-token\"]').content, 'Content-Type': 'application/json'}, body: '{\"theme\":\"light\"}'})")
        ids = ws.js(IDS) or {}
        found = problems_in(ws.events, base)
        ws.events.clear()
        for address, press in PAGES:
            if "{" in address:
                key = address.split("{")[1].rstrip("}")
                if not ids.get(key):
                    found.append(f"{address}: у вигаданих даних немає {key}")
                    continue
                address = address.replace("{" + key + "}", str(ids[key]))
            ws.js(f"location.hash = {json.dumps(address)}")
            ws.js(SETTLED)
            pressed = 0
            if press:
                count = ws.js(f"document.querySelectorAll('#view {press}').length") or 0
                for i in range(min(count, 6)):
                    ws.js(f"document.querySelectorAll('#view {press}')[{i}]?.click()")
                    ws.js(SETTLED)
                    pressed += 1
            ws.drain(0.3)
            state = ws.js(STATE) or {}
            here = problems_in(ws.events, base) + [f"червоне повідомлення: {t}" for t in state.get("toasts") or []]
            if state.get("empty"):
                here.append("сторінка порожня")
            ws.events.clear()
            found += [f"{address}: {p}" for p in here]
            if verbose:
                print(f"{'✗' if here else '✓'} {address}" + (f" · натиснуто {pressed}" if pressed else ""))
        return found
    finally:
        if browser:
            browser.kill()
            browser.wait(10)
        server.kill()
        server.wait(10)
        time.sleep(0.3)                     # Windows lets go of the files a moment after the processes end
        _clear(DATA)
        _clear(EDGE_PROFILE)


def _wait(base: str, server: subprocess.Popen) -> None:
    end = time.monotonic() + 60
    while time.monotonic() < end:
        if server.poll() is not None:
            raise RuntimeError("сервер не запустився: " + (server.stderr.read() or b"").decode(errors="replace")[-800:])
        try:
            urllib.request.urlopen(base, timeout=2).read()
            return
        except OSError:
            time.sleep(0.3)
    raise RuntimeError("сервер не відповів за хвилину")


def _page(debug: int) -> str:
    end = time.monotonic() + 30
    while time.monotonic() < end:
        try:
            targets = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{debug}/json/list", timeout=2).read())
            for t in targets:
                if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
                    return t["webSocketDebuggerUrl"]
        except OSError:
            pass
        time.sleep(0.3)
    raise RuntimeError("Edge не відкрив сторінку")


def main(argv: list[str]) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    started = time.monotonic()
    found = run("-v" in argv)
    for p in found:
        print("✗", p)
    print(f"{len(PAGES)} сторінок, {len(found)} проблем, {time.monotonic() - started:.0f} с")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
