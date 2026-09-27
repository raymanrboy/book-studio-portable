"""Order archive: exactly what went to print is kept, goes 14 days after the order reached the buyer,
"keep" holds it, and a reprint is made from it (all services faked, made-up buyers only)."""
import json
import os
import shutil
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from PIL import Image

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from tests.fixtures import FakePrintify, book, png
from studio import archive, core, creator, drops, gelato, images, outcomes, printify, printorders, records, stages, tunnel
from studio.jobs import Job, JobError
from studio.server import ApiError
from studio.vault import vault

DAY = 86400
ADDRESS = {"firstName": "Jane", "lastName": "Doe", "addressLine1": "12 Example St", "city": "Springfield",
           "state": "IL", "postCode": "62701", "country": "US"}


def facts(stages=None, placed=None, have=True, loaded=None, at=None):
    """Order facts as a sync leaves them; every list loaded whole at `at` (now) unless `loaded` says otherwise."""
    at = time.time() if at is None else at
    return {"stages": stages or {}, "placed": placed or {}, "names": {"4100000001": "Jane Doe"},
            "sent": printorders.SENT_STATUSES, "haveReceipts": have,
            "loaded": {"etsy": at, "printify": at, "gelato": at} if loaded is None else loaded}


class ArchiveCase(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(archive.ROOT, ignore_errors=True)
        # Previews are made in the background right after storing; here they would hold files open while
        # a test removes the book in the same second (in real use the files go 14 days later).
        warm = mock.patch.object(archive, "_warm_previews", lambda *a: None)
        warm.start()
        self.addCleanup(warm.stop)
        # states.json and its .bak (read when the main file is missing) start empty and are put back after
        self._states = {p: (p.read_bytes() if p.exists() else None)
                        for p in (records.STATES, records.STATES.with_name(records.STATES.name + ".bak"))}
        for p in self._states:
            p.unlink(missing_ok=True)
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()
        shutil.rmtree(archive.ROOT, ignore_errors=True)
        for p, data in self._states.items():
            p.unlink(missing_ok=True)
            if data is not None:
                p.write_bytes(data)

    def keep(self, title="4100000001 - Emma", provider="printify", pages=24, **meta) -> str:
        src = book(self.root / f"src-{time.time_ns()}", pages)
        files = [(src / "Cover.png", "Cover.png")] + [(src / f"{i}.png", f"{i}.png") for i in range(1, pages + 1)]
        return archive.store(provider, files, {"title": title, **meta})

    def refresh(self, now, **kw):
        with mock.patch.object(archive, "_facts", lambda: facts(**{"at": now, **kw})):
            return archive.refresh(now)


class Storing(ArchiveCase):
    def test_a_real_copy_under_the_printed_names(self):
        src = book(self.root / "Madelynn", cover_name="cover.png")          # the folder may say "cover.png"
        eid = archive.store("printify", [(src / "cover.png", "Cover.png"), (src / "1.png", "1.png")],
                            {"title": "4100000001 - Emma", "productId": "p1"})
        kept = archive.get(eid)
        self.assertEqual((kept["receiptId"], kept["pageCount"], kept["provider"], kept["keep"], kept["shippedAt"]),
                         ("4100000001", 1, "printify", False, None))
        self.assertEqual([f["file"] for f in kept["files"]], ["Cover.png", "1.png"])
        self.assertEqual((kept["files"][0]["width"], kept["files"][0]["height"]), (60, 30))
        folder = archive.folder(eid)
        self.assertFalse(os.path.samefile(folder / "1.png", src / "1.png"))  # a copy: editing the source later…
        png(src / "1.png", (40, 40), (0, 0, 0))
        with Image.open(folder / "1.png") as im:                             # …does not change what was printed
            self.assertEqual(im.getpixel((5, 5)), (9, 50, 90))

    def test_a_reprint_links_the_archived_files(self):
        first = self.keep()
        kept = archive.folder(first)
        second = archive.store("printify", [(kept / "Cover.png", "Cover.png")], {"title": "4100000001 - Emma", "reprintOf": first})
        self.assertTrue(os.path.samefile(archive.folder(second) / "Cover.png", kept / "Cover.png"))  # no extra space

    def test_previews_are_made_ahead_and_the_ones_already_made_are_copied(self):
        """The order card had decoded every sent page for its previews; the archive decoded them all once more
        after each send (26.09.2026). Now it copies what exists and makes only the rest."""
        from studio import images
        src = book(self.root / "sent", 1)
        images.preview(src / "Cover.png", 1400)
        images.preview(src / "Cover.png", 360)
        eid = archive.store("printify", [(src / "Cover.png", "Cover.png"), (src / "1.png", "1.png")],
                            {"title": "4100000001 - Emma"})
        mock.patch.stopall()  # the real _warm_previews again
        decoded = []
        real = images.preview

        def preview(path, side):
            if not images._cached(path, path.stat(), side)[1].exists():
                decoded.append(path.name)
            return real(path, side)
        with mock.patch.object(images, "preview", preview):
            archive._warm_previews(archive.folder(eid), [(src / "Cover.png", "Cover.png"), (src / "1.png", "1.png")])
        self.assertEqual(decoded, ["1.png", "1.png"])                   # the cover's came as copies
        for name in ("Cover.png", "1.png"):
            path = archive.folder(eid) / name
            self.assertTrue(images._cached(path, path.stat(), 360)[1].exists())
            self.assertTrue(images._cached(path, path.stat(), 1400)[1].exists())

    def test_ids_are_checked(self):
        for bad in ("..", "../vault", "20260918-101010-zzzzzz", ""):
            with self.subTest(bad=bad), self.assertRaises(ApiError):
                archive.folder(bad)
        with self.assertRaises(ApiError) as caught:
            archive.get("20260918-101010-abcdef")
        self.assertEqual(caught.exception.status, 404)

    def test_newest_first_with_the_buyer_and_the_folder(self):
        older = self.keep()
        archive.update(older, sentAt=archive._iso(time.time() - 60))  # sent a minute earlier (no waiting here)
        newer = self.keep(title="4100000002 - Noah", provider="gelato", pages=28, format="softcover_8x8")
        with mock.patch.object(archive, "_facts", lambda: facts()):
            listed = archive._list(SimpleNamespace())["entries"]
        self.assertEqual([e["id"] for e in listed], [newer, older])
        self.assertEqual(listed[1]["buyer"], "Jane Doe")
        self.assertEqual(listed[0]["pageCount"], 28)
        self.assertEqual(listed[0]["folder"], str(archive.folder(newer)))


class Removing(ArchiveCase):
    def test_14_days_after_the_order_was_shipped(self):
        eid = self.keep()
        t0 = time.time()
        self.assertEqual(self.refresh(t0, stages={"4100000001": "sent"}), [])     # the printer sent it — not yet
        self.assertIsNone(archive.get(eid)["shippedAt"])
        self.assertEqual(self.refresh(t0 + 60 * DAY, stages={"4100000001": "work"}), [])  # waiting never expires
        self.refresh(t0, stages={"4100000001": "shipped"})                           # "Відправлені" in the queue
        self.assertIsNotNone(archive.get(eid)["shippedAt"])
        self.assertEqual(self.refresh(t0 + 13 * DAY, stages={"4100000001": "shipped"}), [])
        self.assertEqual(self.refresh(t0 + 14 * DAY + 60, stages={"4100000001": "shipped"}), [eid])
        self.assertFalse(archive.folder(eid).exists())

    def test_a_closed_order_counts_like_a_shipped_one(self):
        eid = self.keep()
        t0 = time.time()
        self.refresh(t0, stages={"4100000001": "closed"})
        self.assertEqual(self.refresh(t0 + 15 * DAY, stages={"4100000001": "closed"}), [eid])

    def test_keep_holds_the_book_until_unmarked(self):
        eid = self.keep()
        t0 = time.time()
        self.refresh(t0, stages={"4100000001": "shipped"})
        with mock.patch.object(archive, "_facts", lambda: facts(stages={"4100000001": "shipped"})):
            shown = archive._keep(SimpleNamespace(groups=[eid], json={"keep": True}))
        self.assertEqual((shown["keep"], shown["clock"], shown["daysLeft"]), (True, "keep", None))
        self.assertEqual(self.refresh(t0 + 40 * DAY, stages={"4100000001": "shipped"}), [])
        with mock.patch.object(archive, "_facts", lambda: facts(stages={"4100000001": "shipped"})):
            archive._keep(SimpleNamespace(groups=[eid], json={"keep": False}))
        self.assertEqual(self.refresh(t0 + 40 * DAY, stages={"4100000001": "shipped"}), [eid])

    def test_a_book_the_program_cannot_follow_goes_30_days_after_sending(self):
        no_receipt = self.keep(title="Book for a friend")
        lost = self.keep(title="4199999999 - Nobody")                   # not among the synced orders
        t0 = time.time()
        self.assertEqual(self.refresh(t0 + 29 * DAY), [])
        self.assertEqual(sorted(self.refresh(t0 + 31 * DAY)), sorted([no_receipt, lost]))

    def test_nothing_goes_while_no_orders_are_known(self):
        eid = self.keep(title="4199999999 - Nobody")
        self.assertEqual(self.refresh(time.time() + 90 * DAY, have=False), [])   # Etsy not synced: never guess
        self.assertTrue(archive.folder(eid).exists())

    def test_nothing_goes_when_the_orders_cannot_be_read(self):
        eid = self.keep(title="Book for a friend")
        with mock.patch.object(archive, "_facts", side_effect=RuntimeError("broken snapshot")), \
                self.assertLogs("studio", "ERROR") as logged:
            self.assertEqual(archive.refresh(time.time() + 90 * DAY), [])
        self.assertIn("nothing removed", logged.output[0])
        self.assertTrue(archive.folder(eid).exists())

    def test_a_reprint_counts_from_its_own_print_order(self):
        eid = self.keep(reprintOf="20260101-101010-abcdef", orderId="o2")
        t0 = time.time()
        shipped_long_ago = {"4100000001": "shipped"}                        # the Etsy order shipped weeks ago
        self.refresh(t0, stages=shipped_long_ago, placed={"printify:o2": {"status": "in-production", "tracking": []}})
        self.assertIsNone(archive.get(eid)["shippedAt"])
        self.refresh(t0, stages=shipped_long_ago,
                     placed={"printify:o2": {"status": "fulfilled", "tracking": [{"number": "94001"}]}})
        self.assertIsNotNone(archive.get(eid)["shippedAt"])

    def test_a_reprint_whose_draft_was_deleted_goes_and_leaves_no_mark(self):
        eid = self.keep(reprintOf="20260101-101010-abcdef", orderId="deleted-draft")
        self.assertTrue(stages.mark_reprint("4100000001", "printify", "deleted-draft"))
        sent = archive._ts(archive.get(eid)["sentAt"])
        others = {"printify:o9": {"status": "fulfilled", "tracking": [], "placed": True}}  # without this one
        self.assertEqual(self.refresh(sent + DAY, placed=others), [])  # maybe not synced yet
        self.assertIsNone(archive.get(eid).get("droppedAt"))
        self.assertEqual(self.refresh(sent + 2 * DAY, placed=others), [])
        self.assertIsNotNone(archive.get(eid)["droppedAt"])                 # gone from the printer: deleted
        self.assertNotIn("4100000001", records.load_states())               # the replacement mark goes with it
        self.assertEqual(self.refresh(sent + 5 * DAY + 60, placed=others), [eid])

    def test_a_printer_list_that_stopped_loading_proves_nothing(self):
        """22.09.2026 audit: Gelato's orders failed to load for days while Printify's loaded — the book sent to
        Gelato was missing from the old list, counted as a deleted draft, and its files went after 5 days."""
        eid = self.keep(provider="gelato", orderId="g-new")
        sent = archive._ts(archive.get(eid)["sentAt"])
        others = {"gelato:g-old": {"status": "delivered", "tracking": [], "placed": True}}
        stale = lambda at: {"etsy": at, "printify": at, "gelato": sent - 3600}  # Gelato last loaded before the send
        for day in (3, 10, 31, 45):
            with self.subTest(day=day):
                self.assertEqual(self.refresh(sent + day * DAY, placed=others, loaded=stale(sent + day * DAY)), [])
                self.assertIsNone(archive.get(eid).get("droppedAt"))
        # Gelato loads again and the draft really is gone: now it goes, three days after that was seen.
        back = sent + 46 * DAY
        self.assertEqual(self.refresh(back, placed=others), [])
        self.assertIsNotNone(archive.get(eid)["droppedAt"])
        self.assertEqual(self.refresh(back + 3 * DAY + 60, placed=others), [eid])

    def test_an_unconfirmed_draft_goes_only_by_a_fresh_list(self):
        eid = self.keep(provider="gelato", orderId="g1")
        draft = {"gelato:g1": {"status": "draft", "placed": False, "tracking": []}}
        sent = archive._ts(archive.get(eid)["sentAt"])
        old_list = {"etsy": sent + 31 * DAY, "printify": sent + 31 * DAY, "gelato": sent + DAY}
        self.assertEqual(self.refresh(sent + 31 * DAY, placed=draft, loaded=old_list), [])  # maybe paid since
        self.assertEqual(self.refresh(sent + 31 * DAY, placed=draft), [eid])

    def test_a_picture_held_open_keeps_the_book_until_next_time(self):
        eid = self.keep(title="Book for a friend")
        real_unlink = Path.unlink

        def busy(path, *a, **kw):
            if path.name == "7.png":
                raise PermissionError("used by another program")
            return real_unlink(path, *a, **kw)

        with mock.patch.object(Path, "unlink", busy), self.assertLogs("studio", "WARNING") as logged:
            self.assertEqual(self.refresh(time.time() + 31 * DAY), [])
        self.assertIn("trying again next time", logged.output[0])
        self.assertEqual(archive.get(eid)["id"], eid)                    # still listed with its entry
        self.assertEqual(self.refresh(time.time() + 31 * DAY), [eid])     # the next refresh finishes it
        self.assertFalse(archive.folder(eid).exists())

    def test_the_page_shows_keep_and_a_started_countdown_without_order_facts(self):
        eid = self.keep()
        archive.update(eid, keep=True)
        self.assertEqual(archive.summary(archive.get(eid), None)["clock"], "keep")
        archive.update(eid, keep=False, shippedAt=archive._iso(time.time() - DAY))
        self.assertEqual(archive.summary(archive.get(eid), None)["daysLeft"], 13)

    def test_halves_of_an_interrupted_copy_are_cleared(self):
        old, fresh = archive.ROOT / ".tmp-old", archive.ROOT / ".tmp-fresh"
        old.mkdir(parents=True)
        fresh.mkdir(parents=True)
        long_ago = time.time() - 2 * 3600
        os.utime(old, (long_ago, long_ago))
        self.refresh(time.time())
        self.assertEqual((old.exists(), fresh.exists()), (False, True))

    def test_days_left_for_the_page(self):
        eid = self.keep()
        t0 = time.time()
        self.refresh(t0 - 3 * DAY, stages={"4100000001": "shipped"})
        shown = archive.summary(archive.get(eid), facts(stages={"4100000001": "shipped"}), now=t0)
        self.assertEqual((shown["clock"], shown["daysLeft"], shown["stage"]), ("shipped", 11, "shipped"))
        waiting = archive.summary(archive.get(eid) | {"shippedAt": None}, facts(stages={"4100000001": "work"}), now=t0)
        self.assertEqual((waiting["clock"], waiting["daysLeft"], waiting["deleteAt"]), ("waiting", None, None))


class OnlyWhatWentToPrint(ArchiveCase):
    """Only a send whose print order is really placed — ordered and paid — is in the archive (owner, 18.09.2026)."""

    def listed(self, **kw):
        with mock.patch.object(archive, "_facts", lambda: facts(**kw)):
            return [e["id"] for e in archive._list(SimpleNamespace())["entries"]]

    def test_a_draft_is_hidden_until_it_is_ordered_and_paid(self):
        eid = self.keep(provider="gelato", orderId="g1")
        draft = {"gelato:g1": {"status": "draft", "placed": False, "tracking": []}}
        paid = {"gelato:g1": {"status": "passed", "placed": True, "tracking": []}}
        self.assertEqual(self.listed(placed=draft), [])
        self.assertEqual(self.listed(placed=paid), [eid])
        with mock.patch.object(archive, "_facts", lambda: facts(placed=draft)), self.assertRaises(ApiError):
            archive._one(SimpleNamespace(groups=[eid]))                     # not even by its address
        t0 = archive._ts(archive.get(eid)["sentAt"])
        self.assertEqual(self.refresh(t0 + 29 * DAY, placed=draft), [])      # a draft left unconfirmed…
        self.assertEqual(self.refresh(t0 + 31 * DAY, placed=draft), [eid])   # …goes after 30 days

    def test_a_cancelled_send_goes_in_three_days_and_its_files_can_be_sent_again(self):
        eid = self.keep(title="4100000001 - Emma", provider="gelato", pages=30, orderId="g1")
        cancelled = {"gelato:g1": {"status": "canceled", "placed": False, "tracking": []}}
        t0 = time.time()
        self.assertEqual(self.refresh(t0, placed=cancelled), [])
        self.assertIsNotNone(archive.get(eid)["droppedAt"])
        self.assertEqual(self.listed(placed=cancelled), [])
        with mock.patch.object(archive, "_facts", lambda: facts(placed=cancelled)):
            offered = archive.card_facts("4100000001")["earlierSends"]
            self.assertEqual([(e["id"], e["provider"], e["pageCount"]) for e in offered], [(eid, "gelato", 30)])
            copy = Path(archive._reuse(SimpleNamespace(groups=[eid]))["path"])
        self.assertEqual(copy.parent, drops.DROPS)                         # a working copy for the order card
        self.assertEqual(sorted(p.name for p in copy.iterdir()), sorted(["Cover.png"] + [f"{i}.png" for i in range(1, 31)]))
        self.assertEqual(self.refresh(t0 + 3 * DAY + 60, placed=cancelled), [eid])
        self.assertTrue((copy / "1.png").exists())                          # the copy outlives the archived book
        shutil.rmtree(copy, ignore_errors=True)

    def test_the_card_knows_after_a_restart_that_a_draft_is_at_the_printer(self):
        """«Чернетку вже створено» before a page is replaced: the card's own memory is gone after a restart,
        the archive is not (22.09.2026 audit)."""
        self.keep(provider="gelato", orderId="g1")
        draft = {"gelato:g1": {"status": "draft", "placed": False, "tracking": []}}
        cancelled = {"gelato:g1": {"status": "canceled", "placed": False, "tracking": []}}
        with mock.patch.object(archive, "_facts", lambda: facts(placed=draft)):
            self.assertTrue(archive.card_facts("4100000001")["atPrinter"])
            self.assertFalse(archive.card_facts("4100000002")["atPrinter"])
        with mock.patch.object(archive, "_facts", lambda: facts(placed=cancelled)):
            self.assertFalse(archive.card_facts("4100000001")["atPrinter"])

    def test_a_placed_order_is_not_offered_again(self):
        self.keep(provider="gelato", orderId="g1")
        with mock.patch.object(archive, "_facts", lambda: facts(placed={"gelato:g1": {"status": "passed", "placed": True}})):
            self.assertEqual(archive.card_facts("4100000001")["earlierSends"], [])

    def test_keep_holds_even_a_cancelled_book(self):
        eid = self.keep(provider="gelato", orderId="g1", keep=True)
        cancelled = {"gelato:g1": {"status": "canceled", "placed": False, "tracking": []}}
        self.assertEqual(self.refresh(time.time() + 40 * DAY, placed=cancelled), [])
        self.assertEqual(self.listed(placed=cancelled), [eid])

    def test_nothing_synced_yet_shows_everything(self):
        eid = self.keep(provider="gelato", orderId="g1")
        self.assertEqual(self.listed(placed={}, have=False), [eid])
        with mock.patch.object(archive, "_facts", side_effect=RuntimeError("broken snapshot")), \
                self.assertLogs("studio", "ERROR"):
            self.assertEqual([e["id"] for e in archive._list(SimpleNamespace())["entries"]], [eid])


class ReprintMark(ArchiveCase):
    def test_recorded_as_a_replacement_without_touching_other_states(self):
        self.assertTrue(stages.mark_reprint("4100000001", "printify", "o2"))
        self.assertTrue(stages.mark_reprint("4100000001", "gelato", "g3"))      # a second reprint is added
        self.assertTrue(stages.mark_reprint("4100000001", "gelato", "g3"))      # the same one only once
        states = records.load_states()
        self.assertEqual(states["4100000001"]["status"], "replacement")
        self.assertEqual(states["4100000001"]["replacementOrders"],
                         [{"provider": "printify", "orderId": "o2"}, {"provider": "gelato", "orderId": "g3"}])
        self.assertIn("printify:o2", outcomes.reserved_orders(states))             # kept out of matching
        core.write_json(records.STATES, {"4100000009": {"status": "refund_full", "at": "x"}})
        self.assertFalse(stages.mark_reprint("4100000009", "printify", "o7"))   # the owner's refund stays
        self.assertEqual(records.load_states()["4100000009"]["status"], "refund_full")
        self.assertFalse(stages.mark_reprint(None, "printify", "o8"))

    def test_a_book_cancelled_at_the_printer_is_simply_made_again(self):
        """Its reprint is the only live print order, so it is matched as usual and the queue moves on."""
        row = {"pod_provider": "gelato", "gelato_order_id": "g1", "match_type": "manual"}

        def known(status, placed):
            return lambda: {"receipts": {"4100000002": {"row": row}},
                            "placed": {"gelato:g1": {"status": status, "placed": placed}}}
        with mock.patch.object(stages, "facts", known("canceled", False)):
            self.assertFalse(stages.mark_reprint("4100000002", "gelato", "g2"))
        self.assertNotIn("4100000002", records.load_states())
        with mock.patch.object(stages, "facts", known("shipped", True)):
            self.assertTrue(stages.mark_reprint("4100000002", "gelato", "g2"))    # the first book is out there


class PrintifyReprint(ArchiveCase):
    def setUp(self):
        super().setUp()
        self._saved = core.settings.get()
        core.settings.update({"printify": {"coverSize": [60, 30], "pageSize": [40, 40],
                                           "manualApprovalConfirmedAt": "2026-09-15T20:00:00Z"}})
        vault.set("printify_token", "fake-token-for-tests")
        creator.UPLOAD_CACHE.unlink(missing_ok=True)
        self.fake = FakePrintify(core.settings.section("printify")["master"])
        with mock.patch.object(printify, "call", self.fake):
            self.first = creator.create_printify_draft([{"folder": str(book(self.root / "Emma")), "title": "4100000001 - Emma"}],
                                                       Job("t"), ADDRESS)
        self.calls_before = len(self.fake.calls)

    def tearDown(self):
        core.settings.replace_section("printify", self._saved["printify"])
        vault.set("printify_token", None)
        super().tearDown()

    def test_a_new_order_for_the_same_book_and_nothing_else(self):
        with mock.patch.object(printify, "call", self.fake):
            res = creator.create_printify_reprint(self.first["archiveId"], "4100000001 - Emma", ADDRESS, Job("t"))
        new_calls = self.fake.calls[self.calls_before:]
        self.assertEqual([c for c in new_calls if c[0] == "POST"], [("POST", "shops/25329813/orders.json")])  # no upload, no product
        self.assertEqual((res["reprint"], res["productId"], res["order"]["id"]), (True, self.first["productId"], "order-on-hold-2"))
        sent = self.fake.orders[-1]
        self.assertEqual(sent["line_items"][0]["product_id"], self.first["productId"])
        self.assertFalse(sent["is_printify_express"])
        kept = archive.get(res["archiveId"])
        self.assertEqual((kept["reprintOf"], kept["orderId"], kept["sendLog"]), (self.first["archiveId"], "order-on-hold-2", res["sendLog"]))
        original = archive.folder(self.first["archiveId"])
        self.assertTrue(os.path.samefile(archive.folder(res["archiveId"]) / "12.png", original / "12.png"))
        self.assertEqual(records.load_states()["4100000001"]["replacementOrders"], [{"provider": "printify", "orderId": "order-on-hold-2"}])
        journal = json.loads((core.data_path("logs", "sends") / res["sendLog"]).read_text(encoding="utf-8"))
        self.assertEqual((journal["kind"], journal["ok"], journal["reprintOf"]), ("reprint", True, self.first["archiveId"]))
        self.assertEqual([s["step"] for s in journal["steps"]], ["product", "reprintMarked", "archive"])

    def test_a_failed_local_record_is_told_to_the_owner(self):
        """The order is already in Printify. If the program then cannot write it down as a reprint, the
        result must say so — quietly succeeding would invite a second, paid, order for the same book."""
        with mock.patch.object(printify, "call", self.fake), \
                mock.patch.object(stages, "mark_reprint", side_effect=OSError("states.json locked")):
            res = creator.create_printify_reprint(self.first["archiveId"], "4100000001 - Emma", ADDRESS, Job("t"))
        self.assertEqual(res["order"]["id"], "order-on-hold-2")                  # the printer did accept it
        warned = " ".join(res["warnings"])
        self.assertIn("вже створено", warned)
        self.assertIn("Не надсилайте ще раз", warned)
        journal = json.loads((core.data_path("logs", "sends") / res["sendLog"]).read_text(encoding="utf-8"))
        step = next(s for s in journal["steps"] if s["step"] == "reprintMarked")
        self.assertFalse(step["ok"])

    def test_a_book_deleted_in_printify_is_made_again_from_the_archive(self):
        self.fake.gone.add(self.first["productId"])
        with mock.patch.object(printify, "call", self.fake):
            res = creator.create_printify_reprint(self.first["archiveId"], "4100000001 - Emma", ADDRESS, Job("t"))
        self.assertNotEqual(res["productId"], self.first["productId"])
        self.assertTrue(res["reprint"])
        self.assertIn("створено заново", res["warnings"][0])
        self.assertEqual(len(self.fake.uploads), 25)                    # all images were already there: reused
        self.assertEqual(archive.get(res["archiveId"])["reprintOf"], self.first["archiveId"])

    def test_refused_without_an_address_or_for_another_printer(self):
        with mock.patch.object(printify, "call", self.fake):
            with self.assertRaises(JobError):
                creator.create_printify_reprint(self.first["archiveId"], "4100000001 - Emma", None, Job("t"))
            other = self.keep(provider="gelato", pages=28)
            with self.assertRaises(JobError):
                creator.create_printify_reprint(other, "4100000001 - Emma", ADDRESS, Job("t"))
        self.assertEqual(len(self.fake.orders), 1)                      # only the first book's order


class GelatoReprint(ArchiveCase):
    PRODUCT = {"validPageCounts": list(range(28, 202, 2)),
               "dimensions": {"Text block total width": {"value": "206"}, "Text block total height": {"value": "206"}}}
    COVER = {"pagesCount": 32, "wraparoundInsideSize": {"width": 458.0, "height": 246.0, "left": 0, "top": 0},
             "contentFrontSize": {"width": 198.0, "height": 206.0, "left": 240.0, "top": 20}}

    def test_a_new_draft_from_the_archived_files(self):
        first = self.keep(title="4100000002 - Noah", provider="gelato", pages=28, format="hardcover_8x8", orderId="g1")
        printed = facts(placed={"gelato:g1": {"status": "delivered", "placed": True, "tracking": []}})
        went = mock.patch.object(archive, "_facts", lambda: printed)
        went.start()
        self.addCleanup(went.stop)
        vault.set("gelato_api_key", "fake-gelato-key")
        gelato._geometry.clear()
        gelato._products.clear()
        sent = {}

        def fake_call(method, url, body=None, **kw):
            if method == "GET":
                return self.COVER if "/cover-dimensions" in url else ({} if "/orders/" in url else self.PRODUCT)
            sent.update(body)
            return {"id": "g2", "orderType": "draft"}

        started = []

        def start(kind, fn, exclusive=None):  # the route's job, run right here
            started.append(fn(Job("t")))
            return SimpleNamespace(id="job")

        try:
            with mock.patch.object(gelato, "call", fake_call), \
                    mock.patch.object(tunnel.FileTunnel, "start", lambda self: "https://fake.trycloudflare.com"), \
                    mock.patch.object(tunnel.registry, "keep", lambda *a, **kw: None), \
                    mock.patch.object(creator.jobs, "start", start):
                creator._create_gelato(SimpleNamespace(json={"books": [{"folder": "C:\\somewhere\\else", "title": "4100000002 - Noah",
                                                             "format": "hardcover_8x8"}], "address": ADDRESS, "reprintOf": first}))
        finally:
            vault.set("gelato_api_key", None)
            gelato._products.clear()
        res = started[0]
        self.assertEqual((res["orderId"], res["reprint"], sent["items"][0]["pageCount"]), ("g2", True, 28))
        kept = archive.get(res["archiveId"])
        self.assertEqual((kept["reprintOf"], kept["orderId"], kept["provider"]), (first, "g2", "gelato"))
        self.assertEqual(records.load_states()["4100000002"]["replacementOrders"], [{"provider": "gelato", "orderId": "g2"}])
        with self.assertRaises(ApiError):   # an unknown archive id is refused before anything starts
            creator._create_gelato(SimpleNamespace(json={"reprintOf": "20260101-101010-abcdef"}))
        printed_elsewhere = self.keep(provider="printify")
        with self.assertRaises(ApiError):   # a reprint stays with the printer that printed the book
            creator._create_gelato(SimpleNamespace(json={"reprintOf": printed_elsewhere}))

    def test_no_reprint_from_a_send_that_never_went_to_print(self):
        draft = self.keep(provider="gelato", orderId="g1")
        cancelled = self.keep(provider="printify", orderId="o1", productId="p1")
        not_placed = facts(placed={"gelato:g1": {"status": "draft", "placed": False},
                                   "printify:o1": {"status": "canceled", "placed": False}})
        with mock.patch.object(archive, "_facts", lambda: not_placed), \
                mock.patch.object(creator.jobs, "start", lambda *a, **kw: self.fail("nothing may start")):
            with self.assertRaises(ApiError) as caught:
                creator._create_gelato(SimpleNamespace(json={"reprintOf": draft, "books": [{"title": "4100000001 - Emma"}]}))
            self.assertEqual(caught.exception.status, 409)
            with self.assertRaises(ApiError):
                creator._reprint_printify(SimpleNamespace(json={"archiveId": cancelled, "title": "4100000001 - Emma"}))


class PreviewCache(unittest.TestCase):
    """The preview cache no longer grows for ever: unused previews go after three weeks, used ones stay."""

    def test_old_previews_go_and_used_ones_stay(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "1.png"
            png(page, (300, 300))
            used = images.preview(page, 120)
            old = core.data_path("cache", "thumbs", "zz", "gone.jpg")
            half = core.data_path("cache", "thumbs", "zz", "half.tmp")
            old.parent.mkdir(parents=True, exist_ok=True)
            old.write_bytes(b"x")
            half.write_bytes(b"x")
            month = time.time() - 30 * DAY
            for f in (used, old, half):
                os.utime(f, (month, month))
            images.preview(page, 120)                  # asked again: its date is fresh again
            self.assertGreaterEqual(images.prune_cache(), 2)
            self.assertTrue(used.exists())
            self.assertFalse(old.exists() or half.exists())

    def test_the_lock_table_forgets_finished_previews(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = Path(tmp) / "2.png"
            png(page, (300, 300))
            images.preview(page, 90)
            images.preview(page, 60)
            self.assertEqual(len(images._key_locks), 0)

    def test_the_viewer_zoom_reuses_a_kept_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            left, right = Path(tmp) / "2.png", Path(tmp) / "3.png"
            png(left, (3000, 3000))
            png(right, (3000, 3000))
            images.compose_spread(left, right, 2400)
            self.assertTrue(images._cached(left, left.stat(), 2600)[1].exists())
            self.assertFalse(images._cached(left, left.stat(), 2400)[1].exists())


if __name__ == "__main__":
    unittest.main()
