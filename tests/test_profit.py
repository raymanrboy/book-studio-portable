import json
import unittest
from pathlib import Path

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import fees, profit, reconcile

GOLDEN = json.loads((Path(__file__).parent / "golden_profit.json").read_text(encoding="utf-8"))
STATUS = {"auto": "matched", "manual": "manual", "unmatched": "unmatched"}


class ProfitParity(unittest.TestCase):
    """Every number must equal what Etsy Profit Calculator produced for the same data."""

    @classmethod
    def setUpClass(cls):
        fx = GOLDEN["fixture"]
        orders = [profit.normalize_receipt(r) for r in fx["receipts"]]
        links = {k: {"provider": "printify", "orderId": v} for k, v in fx["manual"].items()}
        cls.rows = {r["id"]: r for r in reconcile.match(orders, fx["printify"], fx["gelato"], links, 1.085)}

    def test_every_receipt(self):
        for exp in GOLDEN["expected"]:
            row = self.rows[exp["id"]]
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

    def test_cover_label(self):
        items = [{"title": "Book", "quantity": 2, "variations": [{"name": "Cover", "value": "Hardcover"}]},
                 {"title": "Book softcover", "quantity": 1}]
        self.assertEqual(reconcile.cover_label(items), "2x Hardcover + Softcover книга")


if __name__ == "__main__":
    unittest.main()
