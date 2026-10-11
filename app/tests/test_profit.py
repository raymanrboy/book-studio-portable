import json
import unittest
from pathlib import Path

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import fees, reconcile, sync

GOLDEN = json.loads((Path(__file__).parent / "golden_profit.json").read_text(encoding="utf-8"))
STATUS = {"auto": "matched", "manual": "manual", "unmatched": "unmatched"}


RATES = {"EUR": 1.085, "GBP": 1.325}
# The Profit Calculator counted an order billed in pounds as dollars; converted since 26.09.2026 (the rows below keep
# every other number of it).
IN_POUNDS = {"4100002931": 27.48, "4100034195": 22.23}
# The Calculator matched by name with no time limit: one buyer's receipts months apart shared one print order (the cost
# split between them, a July sale holding a September order). Since 2026-10-08 a name finds only an order made within a
# month of the receipt; these rows keep the Calculator's Etsy money, their print-order part is whatever matching now says.
NAME_ACROSS_MONTHS = {"4100014655", "4100021494", "4100023448", "4100026379", "4100042988", "4100044942"}


class ProfitParity(unittest.TestCase):
    """Every number must equal what Etsy Profit Calculator produced for the same data."""

    @classmethod
    def setUpClass(cls):
        fx = GOLDEN["fixture"]
        orders = [sync.normalize_receipt(r) for r in fx["receipts"]]
        links = {k: {"provider": "printify", "orderId": v} for k, v in fx["manual"].items()}
        cls.rows = {r["id"]: r for r in reconcile.match(orders, fx["printify"], fx["gelato"], links, RATES)}

    def test_an_order_in_pounds_is_counted_in_dollars(self):
        for rid, pounds in IN_POUNDS.items():
            row = self.rows[rid]
            with self.subTest(receipt=rid):
                self.assertEqual((row["gelato_cost"], row["gelato_currency"]), (pounds, "GBP"))
                self.assertEqual(row["pod_total_cost"], fees.r2(pounds * RATES["GBP"]))
                self.assertEqual(row["profit"], fees.r2(row["etsy_net"] - row["pod_total_cost"]))

    def test_a_print_order_found_by_name_is_never_shared_across_months(self):
        by_order = {}
        for row in self.rows.values():
            order = row.get("printify_order_id") or row.get("gelato_order_id")
            if order and row["match_type"] == "auto":
                by_order.setdefault(order, []).append(reconcile.parse_time(row["created_at"]))
        for order, times in by_order.items():
            with self.subTest(order=order):
                self.assertLessEqual(max(times) - min(times), 31 * reconcile.DAY_MS)

    def test_every_receipt(self):
        for exp in GOLDEN["expected"]:
            row = self.rows[exp["id"]]
            if exp["id"] in IN_POUNDS:
                exp = {**exp, "cost": row["pod_total_cost"], "profit": row["profit"], "margin": row["profit_margin"]}
            if exp["id"] in NAME_ACROSS_MONTHS:
                exp = {**exp, "status": STATUS[row["match_type"]], "provider": row["pod_provider"],
                       "p": row.get("printify_order_id"), "g": row.get("gelato_order_id"),
                       "cost": row["pod_total_cost"], "prod": row["printify_production_cost"],
                       "ship": row["printify_shipping_cost"], "profit": row["profit"],
                       "margin": row["profit_margin"], "bundle": row.get("bundle_count")}
            with self.subTest(receipt=exp["id"]):
                self.assertAlmostEqual(row["etsy_net"], exp["net"], places=9)
                self.assertAlmostEqual(row["etsy_fees"], exp["fees"], places=9)
                self.assertAlmostEqual(row["etsy_gross"], exp["gross"], places=9)
                for key, value in exp["fb"].items():
                    self.assertAlmostEqual(row["fee_breakdown"][key], value, places=9, msg=key)
                self.assertEqual(STATUS[row["match_type"]], exp["status"])
                self.assertEqual(row["pod_provider"], exp["provider"])
                self.assertEqual(row.get("printify_order_id"), exp["p"])
                self.assertEqual(row.get("gelato_order_id"), exp["g"])
                self.assertAlmostEqual(row["pod_total_cost"], exp["cost"], places=9)
                self.assertAlmostEqual(row["printify_production_cost"], exp["prod"], places=9)
                self.assertAlmostEqual(row["printify_shipping_cost"], exp["ship"], places=9)
                if row["match_type"] != "unmatched":
                    self.assertAlmostEqual(row["profit"], exp["profit"], places=9)
                    self.assertAlmostEqual(row["profit_margin"], exp["margin"], places=9)
                self.assertEqual(row.get("bundle_count"), exp["bundle"])


class FeeRules(unittest.TestCase):
    def test_js_rounding(self):
        # Values checked against Node: Math.round(x * 100) / 100
        self.assertEqual(fees.r2(1.005), 1.0)
        self.assertEqual(fees.r2(2.675), 2.68)
        self.assertEqual(fees.r2(0.125), 0.13)
        self.assertEqual(fees.r2(1.255), 1.25)

    def test_ukrainian_fee_structure(self):
        m = lambda v: {"amount": round(v * 100), "divisor": 100}
        fb = fees.calculate_ukrainian_etsy_fees({
            "grandtotal": m(40.99), "subtotal": m(34.99), "total_price": m(34.99),
            "total_shipping_cost": m(6.0), "transactions": [{}],
        })
        self.assertEqual(fb["trans_item_fee"], 2.27)           # 6.5% of 34.99
        self.assertEqual(fb["processing_fee"], 2.76)           # 6% of 40.99 + 0.30
        self.assertEqual(fb["listing_renew_fee"], 0.2)
        self.assertEqual(fb["sales_tax"], 0.0)
        self.assertAlmostEqual(fb["net_payout"], fees.r2(40.99 - fb["total_etsy_fees"]))


class NameMatching(unittest.TestCase):
    def test_rules(self):
        self.assertTrue(reconcile.is_name_match("Jane M. Beck", "Jane Beck"))
        self.assertTrue(reconcile.is_name_match("Jane Beck", "jane beck-smith"))
        self.assertTrue(reconcile.is_name_match("  ZOË  o'neil ", "Zoë O'Neil"))
        self.assertFalse(reconcile.is_name_match("Al", "Al"[:1]))
        self.assertFalse(reconcile.is_name_match("Emma Stone", "Olivia Stone"))

    def test_the_name_index_finds_exactly_what_the_name_rule_finds(self):
        """The index that turns the name rule into lookups (_NameIndex) against the rule itself, on made-up names."""
        import random
        rnd = random.Random(26)
        parts = ["ann", "lee", "jo", "joann", "leeds", "mia", "stone", "o'neil", "zoë", "van", "der", "berg", "al"]
        names = [" ".join(rnd.choice(parts) for _ in range(rnd.randint(1, 3))) for _ in range(300)]
        index = reconcile._NameIndex(names)
        for query in names[:120] + ["Ann Lee", "Joann Leeds", "  ZOË  o'neil ", "Al"]:
            with self.subTest(query=query):
                self.assertEqual(index.candidates(query),
                                 [i for i, n in enumerate(names) if reconcile.is_name_match(query, n)])

    def test_the_cover_comes_only_from_what_the_buyer_chose(self):
        """A Gelato order named «4100000001 - Oscar» made a softcover of any book whose Etsy items said nothing."""
        self.assertEqual(reconcile.cover_label([{"title": "Personalized book", "quantity": 1}]), "Personalized book")
        self.assertEqual(reconcile.item_format({"title": "Book", "sku": "BK-HC-8"}), "hardcover")
        self.assertIsNone(reconcile.item_format({"title": "Book"}))

    def test_cover_label(self):
        items = [{"title": "Book", "quantity": 2, "variations": [{"name": "Cover", "value": "Hardcover"}]},
                 {"title": "Book softcover", "quantity": 1}]
        self.assertEqual(reconcile.cover_label(items), "2x Hardcover + Softcover книга")


class BookkeepingStart(unittest.TestCase):
    """Owner, 27.09.2026: bookkeeping starts on 1 October 2026 and must not include earlier orders at all — the queue
    still shows them."""

    def setUp(self):
        from studio import records
        self.records = records
        for path in (records.SNAPSHOT, records.STATES, records.LINKS, records.SENDS):
            path.unlink(missing_ok=True)
            self.addCleanup(path.unlink, missing_ok=True)

    def test_only_sales_from_the_first_day(self):
        from datetime import datetime
        from types import SimpleNamespace
        from studio import core, profit, stages
        from studio.server import ApiError
        from tests.test_states import receipt
        before = receipt(4100000001, "Ann Lee", status="Paid", ts=int(datetime(2026, 9, 30, 23, 59).timestamp()))
        after = receipt(4100000002, "Bo Ray", status="Paid", ts=int(datetime(2026, 10, 1, 0, 1).timestamp()))
        early = {"id": "g-sep", "orderReferenceId": "x", "totalInclVat": 20, "currency": "USD", "orderType": "order",
                 "financialStatus": "paid", "fulfillmentStatus": "printed", "createdAt": "2026-09-20T10:00:00Z"}
        late = {**early, "id": "g-oct", "createdAt": "2026-10-02T10:00:00Z"}
        core.write_json(self.records.SNAPSHOT, {"receipts": [sync.normalize_receipt(r) for r in (after, before)],
                                                "printify": [], "gelato": [late, early]})
        summary = profit._data(SimpleNamespace())
        self.assertEqual([r["id"] for r in summary["rows"]], ["4100000002"])
        self.assertEqual(summary["accountingFrom"], "2026-10-01")
        self.assertEqual([c["id"] for c in profit._candidates(SimpleNamespace())["candidates"]], ["g-oct"])
        with self.assertRaises(ApiError):
            profit._row(SimpleNamespace(param=lambda name: "4100000001"))
        self.assertEqual(profit._row(SimpleNamespace(param=lambda name: "4100000002"))["id"], "4100000002")
        self.assertEqual(sorted(o["receiptId"] for o in stages.picker_orders()), ["4100000001", "4100000002"])


if __name__ == "__main__":
    unittest.main()
