"""The move to the owner's own Gelato account (27.09.2026): two made-up accounts, a switch in the middle of work, the
old account only read, its orders never lost — with its key or without."""
import unittest
from types import SimpleNamespace
from unittest import mock

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import archive, core, gelato, gelato_accounts, httpc, printorders, records, sync
from studio.jobs import Job
from studio.server import ApiError
from studio.vault import vault

OLD_KEY, NEW_KEY = "made-up-old-account-key-1111", "made-up-new-account-key-2222"
BASE = {"totalInclVat": 20, "currency": "USD", "financialStatus": "paid", "orderType": "order"}


def order(oid, status="printed", created="2026-09-28T10:00:00Z", **extra):
    return {**BASE, "id": oid, "orderReferenceId": f"41000000{oid[-2:]} - Emma", "firstName": "Emma", "lastName": "Hart",
            "fulfillmentStatus": status, "createdAt": created, **extra}


REAL_CHECK_KEY = gelato.check_key  # the tests below stand in for it; one checks the real one
FULL = {"shipment": {"shipmentMethodName": "UPS", "packages": [{"trackingCode": "1Z9", "trackingUrl": ""}]}}


class Accounts(unittest.TestCase):
    def setUp(self):
        records.SNAPSHOT.unlink(missing_ok=True)
        vault.set(gelato.KEYS["main"], OLD_KEY)
        vault.set(gelato.KEYS["old"], None)
        self.lists = {}      # account slot -> the orders Gelato returns (an exception — it fails)
        self.reads = []      # (order id, account slot) read one by one for tracking
        patches = [mock.patch.object(gelato, "all_orders", self.all_orders),
                   mock.patch.object(gelato, "get_order", self.get_order),
                   mock.patch.object(gelato, "check_key", lambda key: None),
                   mock.patch.object(gelato_accounts, "_resync", lambda: None)]  # no real sync in the background
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def tearDown(self):
        vault.set(gelato.KEYS["main"], None)
        vault.set(gelato.KEYS["old"], None)
        core.settings.update({"gelato": {"firstAccount": None, "switchedAt": None}})
        records.SNAPSHOT.unlink(missing_ok=True)

    def all_orders(self, progress=None, cap=5000, account="main"):
        found = self.lists.get(account, [])
        if isinstance(found, Exception):
            raise found
        return found if isinstance(found, httpc.Listing) else httpc.Listing(found)

    def get_order(self, order_id, account="main"):
        self.reads.append((order_id, account))
        return FULL

    def sync(self):
        return sync._sync(Job("t"))

    def gelato_orders(self):
        return {g["id"]: g for g in records.load_snapshot()["gelato"]}

    def switch(self, key=NEW_KEY):
        return gelato_accounts._switch(SimpleNamespace(json={"key": key}))

    # ------------------------------------------------------------------

    def test_a_switch_in_the_middle_of_work(self):
        self.lists["main"] = [order("o1"), order("d1", status="draft", orderType="draft", financialStatus="draft")]
        self.sync()                                                           # before: one account, tagged as read
        old_id = gelato.account_id(OLD_KEY)
        self.assertEqual({g["account"] for g in self.gelato_orders().values()}, {old_id})

        self.switch()
        self.assertEqual((vault.get(gelato.KEYS["main"]), vault.get(gelato.KEYS["old"])), (NEW_KEY, OLD_KEY))
        self.assertEqual(core.settings.section("gelato")["firstAccount"], old_id)

        # the old account's book ships after the switch; the new account has its first draft
        self.lists = {"main": [order("n1", status="draft", orderType="draft", financialStatus="draft")],
                      "old": [order("o1", status="shipped"), order("d1", status="draft", orderType="draft",
                                                                        financialStatus="draft")]}
        self.sync()
        got = self.gelato_orders()
        self.assertEqual(sorted(got), ["d1", "n1", "o1"])
        self.assertEqual(got["n1"]["account"], gelato.account_id(NEW_KEY))
        self.assertEqual(got["o1"]["account"], old_id)
        self.assertEqual(got["o1"]["shipments"][0]["number"], "1Z9")
        self.assertEqual(self.reads, [("o1", "old")])                        # its tracking read with the old key
        self.assertIn("gelato", records.load_snapshot()["loaded"])

    def test_the_old_accounts_orders_stay_when_its_key_goes(self):
        self.lists["main"] = [order("o1")]
        self.sync()
        self.switch()
        self.lists = {"main": [order("n1")], "old": [order("o1", status="shipped")]}
        self.sync()
        gelato_accounts._forget(SimpleNamespace(json={}))
        self.assertIsNone(vault.get(gelato.KEYS["old"]))
        self.lists = {"main": [order("n1")]}
        self.sync()
        got = self.gelato_orders()
        self.assertEqual(sorted(got), ["n1", "o1"])                          # o1 kept as last seen
        self.assertEqual((got["o1"]["fulfillmentStatus"], got["o1"]["shipments"][0]["number"]), ("shipped", "1Z9"))
        self.assertIn("gelato", records.load_snapshot()["loaded"])

        # the archive keeps its book: the order is still known, placed and paid
        snap = records.load_snapshot()
        facts = {"placed": printorders.all_facts(snap, printorders.rates()), "loaded": {"gelato": 9e12}}
        entry = {"provider": "gelato", "orderId": "o1", "sentAt": "2026-09-28T10:00:00Z", "receiptId": "4100000001"}
        self.assertEqual(archive.standing(entry, facts), "counted")

    def test_a_deleted_draft_still_goes(self):
        """Only its own account's whole list can say an order is gone."""
        self.lists["main"] = [order("o1"), order("d1", status="draft", orderType="draft", financialStatus="draft")]
        self.sync()
        self.switch()
        self.lists = {"main": [order("n1"), order("n2", status="draft", orderType="draft", financialStatus="draft")],
                      "old": [order("o1")]}
        self.sync()
        self.lists = {"main": [order("n1")], "old": [order("o1")]}           # d1 and n2 deleted in Gelato
        self.sync()
        self.assertEqual(sorted(self.gelato_orders()), ["n1", "o1"])

    def test_an_account_that_fails_keeps_its_orders(self):
        self.lists["main"] = [order("o1")]
        self.sync()
        self.switch()
        loaded = records.load_snapshot()["loaded"].get("gelato")
        self.lists = {"main": [order("n1")], "old": gelato.GelatoError("немає з'єднання з Gelato", 502)}
        result = self.sync()
        self.assertEqual(sorted(self.gelato_orders()), ["n1", "o1"])
        self.assertTrue(any(w.startswith(gelato.OLD_NAME) for w in result["warnings"]))
        self.assertEqual(records.load_snapshot()["loaded"].get("gelato"), loaded)  # not trusted as whole

        self.lists = {"main": gelato.GelatoError("немає з'єднання з Gelato", 502), "old": [order("o1", status="shipped")]}
        self.sync()
        got = self.gelato_orders()
        self.assertEqual(sorted(got), ["n1", "o1"])                          # the new account's order stays too
        self.assertEqual(got["o1"]["fulfillmentStatus"], "shipped")

    def test_a_cut_list_keeps_the_older_orders(self):
        self.lists["main"] = [order("o1"), order("o2")]
        self.sync()
        cut = httpc.Listing([order("o1")])
        cut.complete = False
        self.lists["main"] = cut
        self.sync()
        self.assertEqual(sorted(self.gelato_orders()), ["o1", "o2"])

    def test_nothing_can_be_created_with_the_old_key(self):
        url = f"{gelato.ORDER_API}/orders"
        self.assertTrue(gelato._allowed("POST", url, {"orderType": "draft"}))
        self.assertFalse(gelato._allowed("POST", url, {"orderType": "draft"}, "old"))
        self.assertTrue(gelato._allowed("POST", f"{gelato.ORDER_API}/orders:search", {}, "old"))
        self.assertTrue(gelato._allowed("GET", f"{url}/abc", None, "old"))
        vault.set(gelato.KEYS["old"], OLD_KEY)
        with mock.patch.object(httpc, "request_json", side_effect=AssertionError("must not be sent")):
            with self.assertRaises(gelato.GelatoError) as caught:
                gelato.call("POST", url, {"orderType": "draft"}, account="old")
            self.assertEqual(caught.exception.status, 403)
            with self.assertRaises(gelato.GelatoError):                      # a key being checked only reads too
                gelato.call("POST", url, {"orderType": "draft"}, key=NEW_KEY)

    def test_a_new_key_is_checked_by_reading_one_order(self):
        seen = []
        with mock.patch.object(httpc, "request_json",
                               lambda method, url, headers=None, json_body=None, **kw: seen.append(
                                   (method, url, headers["X-API-KEY"], json_body["limit"])) or {"orders": []}):
            REAL_CHECK_KEY(NEW_KEY)
        self.assertEqual(seen, [("POST", f"{gelato.ORDER_API}/orders:search", NEW_KEY, 1)])

    def test_the_switch_refuses_what_would_lose_track(self):
        with self.assertRaises(ApiError):
            self.switch(OLD_KEY)                                              # the same key
        with self.assertRaises(ApiError):
            self.switch("short")
        self.switch()
        with self.assertRaises(ApiError):
            self.switch("made-up-third-account-key-3333")                    # one move at a time
        self.assertEqual(vault.get(gelato.KEYS["old"]), OLD_KEY)
        vault.set(gelato.KEYS["old"], None)
        vault.set(gelato.KEYS["main"], None)
        with self.assertRaises(ApiError):
            self.switch()                                                     # nothing to move from

    def test_the_preview_server_never_checks_a_key_at_gelato(self):
        with mock.patch.object(core, "SAMPLE", True), \
                mock.patch.object(gelato, "check_key", side_effect=AssertionError("must not reach Gelato")):
            with self.assertRaises(ApiError):
                self.switch()

    def test_a_bad_new_key_changes_nothing(self):
        with mock.patch.object(gelato, "check_key", side_effect=gelato.GelatoError("Gelato: перевірте API-ключ", 401)):
            with self.assertRaises(ApiError):
                self.switch()
        self.assertEqual((vault.get(gelato.KEYS["main"]), vault.get(gelato.KEYS["old"])), (OLD_KEY, None))


class OpenOrders(unittest.TestCase):
    """The old key is no longer needed once none of the owner's orders there waits, prints or travels."""

    def setUp(self):
        for path in (records.SNAPSHOT, records.STATES, records.LINKS, records.SENDS):
            path.unlink(missing_ok=True)
        vault.set(gelato.KEYS["main"], NEW_KEY)
        vault.set(gelato.KEYS["old"], OLD_KEY)

    def tearDown(self):
        vault.set(gelato.KEYS["main"], None)
        vault.set(gelato.KEYS["old"], None)
        for path in (records.SNAPSHOT, records.STATES, records.LINKS, records.SENDS):
            path.unlink(missing_ok=True)

    def synced(self, shipped_on_etsy):
        from tests.test_states import receipt
        g = {**order("o1"), "orderReferenceId": "4100000001 - Emma", "account": gelato.account_id(OLD_KEY)}
        status = "Completed" if shipped_on_etsy else "Paid"
        core.write_json(records.SNAPSHOT, {"receipts": [sync.normalize_receipt(receipt(4100000001, "Emma Hart", status=status))],
                                           "printify": [], "gelato": [g]})

    def test_counted_while_in_work_then_not(self):
        self.synced(shipped_on_etsy=False)
        self.assertEqual(gelato_accounts.status()["old"]["open"], 1)
        self.synced(shipped_on_etsy=True)
        self.assertEqual(gelato_accounts.status()["old"]["open"], 0)

    def test_no_old_account(self):
        vault.set(gelato.KEYS["old"], None)
        self.assertEqual(gelato_accounts.status(), {"old": None})


if __name__ == "__main__":
    unittest.main()
