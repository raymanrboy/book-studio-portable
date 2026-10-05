"""Etsy's payment ledger (ledger.py): each entry finds its receipt, a receipt's real money against the fee formula, the
balance against what the program expects since the last payout. Made-up entries in the shape the API returns."""
import unittest
from unittest import mock

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import core, etsy, ledger, profit


def entry(eid, kind, rtype, ref, cents, at, parent=0, balance=0, seq=None):
    return {"entry_id": eid, "sequence_number": seq or eid, "create_date": at, "ledger_type": kind,
            "reference_type": rtype, "reference_id": ref, "amount": cents, "balance": balance, "parent_entry_id": parent}


def receipt(rid, at, listing=55, tx=None):
    return {"receipt_id": rid, "create_timestamp": at, "items": [{"listing_id": listing, "transaction_id": tx}]}


class Assign(unittest.TestCase):
    def test_every_kind_of_entry_finds_its_receipt(self):
        receipts = [receipt("101", 1000, tx=9001), receipt("102", 5000, tx=9002)]
        raw = [
            entry(1, "PAYMENT_GROSS", "shop_payment", 700, 3000, 1000),
            entry(2, "PAYMENT_PROCESSING_FEE", "processing_fee", 700, -210, 1000),
            entry(3, "transaction", "transaction", 9001, -150, 1000),
            entry(4, "vat_seller_services", "etsy", 0, -30, 1001, parent=3),
            entry(5, "shipping_transaction", "receipt", "101", -40, 1000),
            entry(6, "renew_sold_auto", "listing", 55, -20, 1000),
            entry(7, "transaction", "transaction", 777, -160, 5000),   # an item the snapshot doesn't name: by the moment
            entry(8, "prolist", "prolist", 1, -100, 5001),            # the ads: the shop's
            entry(9, "vat_seller_services", "etsy", 0, -20, 5001, parent=8),
            entry(10, "renew_sold_auto", "listing", 55, -20, 5000),
        ]
        own = ledger.assign([ledger._slim(e) for e in raw], {"700": "101"}, receipts)
        self.assertEqual({k: own.get(k) for k in range(1, 11)},
                         {1: "101", 2: "101", 3: "101", 4: "101", 5: "101", 6: "101", 7: "102", 8: None, 9: None, 10: "102"})

    def test_a_listing_sold_twice_at_once_gives_each_sale_its_own_renewal(self):
        receipts = [receipt("201", 1000), receipt("202", 1000)]
        raw = [entry(1, "renew_sold_auto", "listing", 55, -20, 1000), entry(2, "renew_sold_auto", "listing", 55, -20, 1000)]
        own = ledger.assign([ledger._slim(e) for e in raw], {}, receipts)
        self.assertEqual(sorted(own.values()), ["201", "202"])


class BalanceCheck(unittest.TestCase):
    def setUp(self):
        self.addCleanup(lambda: ledger.LEDGER.unlink(missing_ok=True))

    def test_the_payout_is_what_was_left_plus_the_sales_between(self):
        real = {"balance": 30.0, "at": 900, "payouts": [{"at": 100, "amount": 50.0, "left": 10.0},
                                                        {"at": 500, "amount": 90.0, "left": 0.0}]}
        rows = [{"id": "a", "created_at": "1970-01-01T00:05:00Z", "etsy_net": 40.0},
                {"id": "b", "created_at": "1970-01-01T00:06:40Z", "etsy_net": 41.0},  # 400 s: before the second payout
                {"id": "c", "created_at": "1970-01-01T00:10:00Z", "etsy_net": 30.0}]  # 600 s: after it
        with mock.patch.object(profit, "OVERHEAD_PER_DAY", 0), mock.patch.object(profit.time, "time", return_value=900):
            out = profit._balance_check(real, rows)
        self.assertEqual(out["lastPayout"]["expected"]["amount"], 91.0)  # 10 left + 40 + 41
        self.assertEqual(out["expected"]["amount"], 30.0)
        self.assertEqual(out["expected"]["orders"], 1)

    def test_a_receipt_gets_its_real_money_and_the_difference(self):
        core.write_json(ledger.LEDGER, {"payments": {"700": "301"}, "entries": [ledger._slim(e) for e in [
            entry(1, "PAYMENT_GROSS", "shop_payment", 700, 3000, 1000, balance=3000),
            entry(2, "offsite_ads_fee", "receipt", "301", -450, 1100, balance=2550),
        ]]})
        view = ledger.view([receipt("301", 1000)])
        got = view["receipts"]["301"]
        self.assertEqual(got["net"], 25.5)
        self.assertIn({"type": "offsite_ads_fee", "label": "Offsite Ads", "amount": -4.5}, got["lines"])
        self.assertEqual(view["balance"], 25.5)


class Refresh(unittest.TestCase):
    def setUp(self):
        self.addCleanup(lambda: ledger.LEDGER.unlink(missing_ok=True))

    def test_reads_in_31_day_windows_and_asks_each_payment_once(self):
        calls = []

        def fake_get(path, params=None, action=""):
            calls.append((path, dict(params or {})))
            if path.endswith("/payments"):
                return {"results": [{"payment_id": 700, "receipt_id": 401, "payment_adjustments": []}]}
            if params["offset"] == 0 and not any(c[0].endswith("ledger-entries") for c in calls[:-1]):
                return {"results": [entry(1, "PAYMENT_GROSS", "shop_payment", 700, 3000, 1000)]}
            return {"results": []}

        with mock.patch.object(etsy, "ensure_shop", return_value=(5, "s")), mock.patch.object(etsy, "get", fake_get):
            ledger.refresh()
            ledger.refresh()
        reads = [p for path, p in calls if path.endswith("ledger-entries")]
        self.assertTrue(all(p["max_created"] - p["min_created"] <= ledger.WINDOW for p in reads))
        self.assertEqual(sum(1 for path, _ in calls if path.endswith("/payments")), 1)
        self.assertEqual(ledger.load()["payments"], {"700": "401"})


if __name__ == "__main__":
    unittest.main()
