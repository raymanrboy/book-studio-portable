"""Etsy's payment ledger (ledger.py): each entry finds its receipt, and a receipt's real money against the fee formula.
Made-up entries in the shape the API returns."""
import unittest
from datetime import datetime
from unittest import mock

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import core, etsy, ledger


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


class ReceiptCheck(unittest.TestCase):
    def setUp(self):
        self.addCleanup(lambda: ledger.LEDGER.unlink(missing_ok=True))

    def test_a_receipt_gets_its_real_money_and_the_difference(self):
        core.write_json(ledger.LEDGER, {"payments": {"700": "301"}, "entries": [ledger._slim(e) for e in [
            entry(1, "PAYMENT_GROSS", "shop_payment", 700, 3000, 1000, balance=3000),
            entry(2, "offsite_ads_fee", "receipt", "301", -450, 1100, balance=2550),
        ]]})
        view = ledger.view([receipt("301", 1000)])
        got = view["receipts"]["301"]
        self.assertEqual(got["net"], 25.5)
        self.assertIn({"type": "offsite_ads_fee", "label": "Offsite Ads", "amount": -4.5}, got["lines"])

    def test_the_vat_given_back_joins_the_fees_refund(self):
        # As in the owner's cancellation of 18.09.2026: the VAT refund points at the fee's own VAT entry.
        core.write_json(ledger.LEDGER, {"payments": {"700": "301"}, "entries": [ledger._slim(e) for e in [
            entry(1, "PAYMENT_GROSS", "shop_payment", 700, 3000, 1000),
            entry(2, "transaction", "receipt", "301", -83, 1000),
            entry(3, "vat_seller_services", "etsy", 0, -17, 1000, parent=2),
            entry(4, "vat_on_processing_fees", "receipt", "301", -37, 1000),
            entry(5, "transaction_refund", "receipt", "301", 83, 2000, parent=2),
            entry(6, "vat_seller_services_refund", "etsy", 0, 17, 2000, parent=3),
            entry(7, "vat_seller_services_refund", "etsy", 0, 37, 2000, parent=4),
        ]]})
        lines = {l["type"]: l["amount"] for l in ledger.view([receipt("301", 1000)])["receipts"]["301"]["lines"]}
        self.assertEqual(lines, {"PAYMENT_GROSS": 30.0, "transaction": -1.0, "PAYMENT_PROCESSING_FEE": -0.37,
                                 "transaction_refund": 1.0, "REFUND_PROCESSING_FEE": 0.37})


class Chain(unittest.TestCase):
    def chain(self, *rows):
        return [ledger._slim(entry(seq, "x", "etsy", 0, cents, 0, balance=bal, seq=seq)) for seq, cents, bal in rows]

    def test_a_whole_chain_has_no_gaps(self):
        self.assertEqual(ledger.gaps(self.chain((5, 100, 100), (6, -30, 70), (7, 10, 80))), 0)

    def test_a_missing_number_or_a_balance_that_does_not_follow_is_a_gap(self):
        self.assertEqual(ledger.gaps(self.chain((5, 100, 100), (7, -30, 70))), 1)
        self.assertEqual(ledger.gaps(self.chain((5, 100, 100), (6, -30, 60))), 1)


class Overhead(unittest.TestCase):
    """The ads and new listings by day: an ads charge pays for the day before it; the days not charged yet are forecast."""
    @staticmethod
    def at(day, hour=7):
        return int(datetime(2026, 10, day, hour, 40).timestamp())

    def test_ads_pay_for_the_day_before_and_the_days_not_charged_are_forecast(self):
        raw = [entry(1, "prolist", "prolist", 1, -100, self.at(11)),
               entry(2, "vat_seller_services", "etsy", 0, -20, self.at(11), parent=1),
               entry(3, "prolist", "prolist", 1, -496, self.at(12)),
               entry(4, "vat_seller_services", "etsy", 0, -99, self.at(12), parent=3),
               entry(5, "listing", "listing", 9, -20, self.at(12, 15)),
               entry(6, "vat_seller_services", "etsy", 0, -4, self.at(12, 15), parent=5),
               entry(7, "transaction", "transaction", 8, -150, self.at(12, 16))]   # a sale's fee: not the shop's
        days = ledger.overhead([ledger._slim(e) for e in raw], self.at(13, 3))
        self.assertEqual(days["2026-10-10"], {"amount": -1.2, "ads": -1.2, "forecast": False})
        self.assertEqual(days["2026-10-11"], {"amount": -5.95, "ads": -5.95, "forecast": False})
        self.assertEqual(days["2026-10-12"], {"amount": -6.19, "ads": -5.95, "forecast": True})   # the listing + the ads forecast
        self.assertEqual(days["2026-10-13"], {"amount": -5.95, "ads": -5.95, "forecast": True})

    def test_the_forecast_reaches_today_without_a_new_read(self):
        raw = [entry(1, "prolist", "prolist", 1, -100, self.at(11))]
        later = datetime(2026, 10, 15, 9)
        with mock.patch.object(ledger, "datetime", wraps=datetime) as clock:
            clock.now.return_value = later
            days = ledger.overhead([ledger._slim(e) for e in raw], self.at(12))
        self.assertEqual([d for d, v in days.items() if v["forecast"]], ["2026-10-11", "2026-10-12", "2026-10-13",
                                                                          "2026-10-14", "2026-10-15"])

    def test_ads_turned_off_are_not_forecast(self):
        raw = [entry(1, "prolist", "prolist", 1, -100, self.at(2))]
        days = ledger.overhead([ledger._slim(e) for e in raw], self.at(13))
        self.assertEqual(list(days), ["2026-10-01"])


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

    def test_a_gap_makes_the_next_read_start_from_the_beginning(self):
        def fake_get(path, params=None, action=""):
            if path.endswith("/payments") or params["offset"]:
                return {"results": []}
            return {"results": [entry(1, "x", "etsy", 0, 100, 1000, balance=100, seq=5),
                                entry(2, "x", "etsy", 0, 100, 1000, balance=200, seq=7)]}

        with mock.patch.object(etsy, "ensure_shop", return_value=(5, "s")), mock.patch.object(etsy, "get", fake_get):
            ledger.refresh()
        self.assertEqual(ledger.load()["readTo"], 0)


if __name__ == "__main__":
    unittest.main()
