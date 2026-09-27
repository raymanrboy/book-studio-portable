"""What several test modules make the same way: made-up pictures and print folders, and Printify in memory (the
flows and the archive each had their own copy until 27.09.2026)."""
import json
from pathlib import Path

from PIL import Image

from studio import printify


def png(path: Path, size=(40, 40), color=(200, 180, 160)) -> None:
    Image.new("RGB", size, color).save(path, "PNG")


def book(folder: Path, pages: int = 24, cover_name: str = "Cover.png") -> Path:
    """A made-up print folder: a wide cover and pages 1..N, each page its own pixels."""
    folder.mkdir(parents=True, exist_ok=True)
    png(folder / cover_name, (60, 30), (10, 20, 30))
    for i in range(1, pages + 1):
        png(folder / f"{i}.png", (40, 40), (i * 9 % 255, 50, 90))
    return folder


class FakePrintify:
    """Printify in memory with one read-only Master: uploads, products (`created`; one can be "deleted" — `gone`),
    orders on hold (`order-on-hold-<n>`). The real allowlist still applies to every call."""

    def __init__(self, master_cfg):
        self.master = {
            "id": master_cfg["productId"], "title": master_cfg["title"], "updated_at": "2026-09-01 10:00:00+00:00",
            "blueprint_id": master_cfg["blueprintId"], "print_provider_id": master_cfg["printProviderId"],
            "visible": True, "print_areas": [{"placeholders": [{"position": "cover", "images": [{"id": "old"}]}]}],
        }
        self.uploads, self.created, self.orders, self.calls, self.gone = {}, [], [], [], set()

    def __call__(self, method, path, body=None, action="", timeout=60, retries=3, params="", order=False):
        printify._check(method, path, order)
        self.calls.append((method, path))
        if method == "POST" and path.endswith("/orders.json"):
            self.orders.append(body)
            return {"id": f"order-on-hold-{len(self.orders)}"}
        if method == "POST" and path == "uploads/images.json":
            body = json.loads(body)  # the upload's JSON comes already encoded (printify.upload_image)
            image_id = f"{len(self.uploads) + 1:024x}"
            self.uploads[image_id] = body["file_name"]
            return {"id": image_id, "file_name": body["file_name"]}
        if method == "GET" and path.startswith("uploads/"):
            return {"id": path.split("/")[1].split(".")[0]}
        if method == "POST" and path.endswith("/products.json"):
            pid = f"{900 + len(self.created):024x}"
            self.created.append({"id": pid, **body})
            return {"id": pid}
        if method == "GET" and path.endswith(f"/products/{self.master['id']}.json"):
            return self.master
        if method == "GET" and "/products/" in path:
            pid = path.rsplit("/", 1)[1].split(".")[0]
            product = next((p for p in self.created if p["id"] == pid), None)
            if pid in self.gone or product is None:
                raise printify.PrintifyError("Читання продукту Printify: Printify не знайшов об'єкт (404).", 404)
            return {"id": pid, "title": product.get("title"), "print_areas": product["print_areas"]}
        raise AssertionError(f"unexpected call {method} {path}")
