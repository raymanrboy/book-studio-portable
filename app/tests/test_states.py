"""Cancelled / refunded / replaced orders, provider-side cancellations and incremental Etsy sync."""
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import core, etsy, gelato, outcomes, printify, profit, reconcile
from studio.fees import r2
from studio.jobs import Job
from studio.server import ApiError
from studio.vault import vault

GOLDEN = json.loads((Path(__file__).parent / "golden_profit.json").read_text(encoding="utf-8"))


def money(v):
    return {"amount": int(round(v * 100)), "divisor": 100, "currency_code": "USD"}


def receipt(rid, name, total=49.98, items=44.99, ship=4.99, status="Completed", refunds=(), ts=1757000000, updated=None):
    return {"receipt_id": rid, "create_timestamp": ts, "update_timestamp": updated or ts, "name": name,
            "status": status, "is_paid": True, "is_shipped": status == "Completed",
            "grandtotal": money(total), "subtotal": money(items), "total_price": money(items),
            "total_shipping_cost": money(ship), "transactions": [{"transaction_id": rid * 10}],
            "refunds": [{"amount": money(a), "created_timestamp": ts + 99, "reason": "r", "note_from_issuer": "",
                         "status": "SUCCESS"} for a in refunds]}


def porder(pid, first, last, cost_cents=1195, status="fulfilled", shop_order_id=None, created="2025-09-04 12:00:00+00:00"):
    return {"id": pid, "app_order_id": pid[-6:].upper(), "total_price": cost_cents - 400, "total_shipping": 400,
            "total_tax": 0, "created_at": created, "status": status,
            "metadata": {"shop_order_id": shop_order_id}, "address_to": {"first_name": first, "last_name": last},
            "line_items": []}


def view(receipts, p_orders=(), g_orders=(), states=None, links=None):
    """Runs the same pipeline as build_view without touching the snapshot."""
    norm = [profit.normalize_receipt(r) for r in receipts]
    states = states or {}
    orders = {f"printify:{p['id']}": p for p in p_orders}
    orders.update({f"gelato:{g['id']}": g for g in g_orders})
    rows = reconcile.match(norm, list(p_orders), list(g_orders), links or {}, 1.085,
                           reserved=profit.reserved_orders(states))
    by_id = {r["receipt_id"]: r for r in norm}
    for row in rows:
        outcomes.apply(row, by_id[row["id"]], states.get(row["id"]), orders, 1.085)
    return {r["id"]: r for r in rows}


class NormalOrdersUnchanged(unittest.TestCase):
    def test_golden_rows_keep_original_numbers(self):
        fx = GOLDEN["fixture"]
        links = {k: {"provider": "printify", "orderId": v} for k, v in fx["manual"].items()}
        norm = [profit.normalize_receipt(r) for r in fx["receipts"]]
        plain = {r["id"]: dict(r) for r in reconcile.match(norm, fx["printify"], fx["gelato"], links, 1.085)}
        with_states = view(fx["receipts"], fx["printify"], fx["gelato"], links=links)
        for rid, row in with_states.items():
            with self.subTest(receipt=rid):
                self.assertEqual(row["state"], "normal")
                for key in ("etsy_net", "profit", "profit_margin", "pod_total_cost", "printify_order_id", "gelato_order_id"):
                    self.assertEqual(row.get(key), plain[rid].get(key), key)


class EtsyStates(unittest.TestCase):
    def setUp(self):
        self.p = porder("a" * 24, "Amelia", "Lewis", shop_order_id="1")

    def test_cancelled_after_printing_loses_the_print_cost(self):
        rows = view([receipt(1, "Amelia Lewis", status="Canceled", refunds=[49.98])], [self.p])
        row = rows["1"]
        self.assertEqual(row["state"], "canceled")
        self.assertEqual(row["etsy_net"], 0.0)            # buyer refunded, every Etsy fee credited back
        self.assertEqual(row["cost_total"], 11.95)
        self.assertEqual(row["profit"], -11.95)
        self.assertEqual(row["impact"], -11.95)
        self.assertIsNone(row["profit_margin"])

    def test_cancelled_everywhere_costs_nothing(self):
        dead = porder("a" * 24, "Amelia", "Lewis", status="canceled", shop_order_id="1")
        row = view([receipt(1, "Amelia Lewis", status="Canceled", refunds=[49.98])], [dead])["1"]
        self.assertEqual(row["pod_dead"], "canceled")
        self.assertEqual((row["etsy_net"], row["cost_total"], row["profit"]), (0.0, 0.0, 0.0))

    def test_cancelled_before_any_print_order(self):
        row = view([receipt(1, "Nobody Here", status="Canceled", refunds=[49.98])])["1"]
        self.assertEqual(row["match_type"], "unmatched")
        self.assertEqual(row["profit"], 0.0)   # nothing printed, nothing lost

    def test_full_refund_keeps_only_the_listing_fee(self):
        row = view([receipt(1, "Amelia Lewis", status="Fully Refunded", refunds=[49.98])], [self.p])["1"]
        fb = row["fee_breakdown"]
        listing = r2(fb["listing_renew_fee"] + fb["vat_listing_renew"])
        self.assertEqual(row["state"], "refund_full")
        self.assertEqual(row["etsy_net"], -listing)
        self.assertEqual(row["profit"], r2(-listing - 11.95))
        # The explained lines add up: Etsy Net before − money back + fees credited = Etsy Net after.
        self.assertAlmostEqual(row["etsy_net_original"] - row["revenue_back"] + row["fee_credit"], row["etsy_net"], places=2)

    def test_partial_refund_is_proportional(self):
        row = view([receipt(1, "Amelia Lewis", status="Partially Refunded", refunds=[10.0])], [self.p])["1"]
        self.assertEqual(row["state"], "refund_partial")
        self.assertEqual(row["refund_amount"], 10.0)
        share = 10.0 / 49.98
        fb = row["fee_breakdown"]
        variable = r2(fb["trans_item_fee"] + fb["vat_trans_item"] + fb["trans_ship_fee"] + fb["vat_trans_ship"]
                      + fb["processing_fee"] + fb["vat_processing"])
        self.assertEqual(row["fee_credit"], r2(variable * share))
        self.assertEqual(row["etsy_net"], r2(row["etsy_net_original"] - r2(49.98 * share) + r2(variable * share)))
        self.assertEqual(row["profit"], r2(row["etsy_net"] - 11.95))
        self.assertEqual(row["impact"], r2(row["etsy_net"] - row["etsy_net_original"]))

    def test_manual_state_overrides_etsy(self):
        states = {"1": {"status": "refund_partial", "refundAmount": 20}}
        row = view([receipt(1, "Amelia Lewis")], [self.p], states=states)["1"]
        self.assertTrue(row["state_manual"])
        self.assertEqual(row["state_auto"], "normal")
        self.assertEqual(row["refund_amount"], 20.0)


class Replacement(unittest.TestCase):
    def test_reprint_cost_is_added_and_kept_out_of_matching(self):
        original = porder("a" * 24, "Mia", "Stone", shop_order_id="1", created="2025-09-04 12:00:00+00:00")
        reprint = porder("b" * 24, "Mia", "Stone", cost_cents=1500, created="2025-09-20 12:00:00+00:00")
        # A second order from the same buyer would otherwise grab the reprint by name.
        receipts = [receipt(1, "Mia Stone"), receipt(2, "Mia Stone", ts=1758300000)]
        before = view(receipts, [original, reprint])
        self.assertEqual(before["2"]["printify_order_id"], "b" * 24)
        states = {"1": {"status": "replacement", "replacementOrders": [{"provider": "printify", "orderId": "b" * 24}],
                        "replacementCost": 3.5}}
        rows = view(receipts, [original, reprint], states=states)
        row = rows["1"]
        self.assertEqual(row["printify_order_id"], "a" * 24)
        self.assertEqual(row["replacement_cost"], 18.5)          # 15.00 reprint + 3.50 other costs
        self.assertEqual(row["cost_total"], r2(row["pod_total_cost"] + 18.5))
        self.assertEqual(row["profit"], r2(row["etsy_net"] - row["cost_total"]))
        self.assertEqual(row["impact"], -18.5)
        self.assertNotEqual(rows["2"].get("printify_order_id"), "b" * 24)   # the reprint is never matched to others


class ProviderCancellations(unittest.TestCase):
    def test_live_order_wins_over_cancelled_one(self):
        dead = porder("a" * 24, "Lily", "Park", status="canceled", created="2025-09-04 12:05:00+00:00")
        live = porder("b" * 24, "Lily", "Park", created="2025-09-05 09:00:00+00:00")
        row = view([receipt(1, "Lily Park", ts=1756987200)], [dead, live])["1"]
        self.assertEqual(row["printify_order_id"], "b" * 24)
        self.assertIsNone(row["pod_dead"])

    def test_only_a_cancelled_order_found_asks_for_a_link(self):
        dead = porder("a" * 24, "Lily", "Park", status="canceled")
        row = view([receipt(1, "Lily Park")], [dead])["1"]
        self.assertTrue(row["needs_link"])
        self.assertIsNone(row["profit"])

    def test_gelato_draft_is_not_a_cost(self):
        draft = {"id": "g1", "orderReferenceId": "1", "firstName": "Ann", "lastName": "Lee", "totalInclVat": 20,
                 "currency": "USD", "fulfillmentStatus": "draft", "orderType": "draft", "createdAt": "2025-09-04T12:00:00Z"}
        row = view([receipt(1, "Ann Lee", status="Canceled", refunds=[49.98])], g_orders=[draft])["1"]
        self.assertEqual(row["pod_dead"], "draft")
        self.assertEqual(row["profit"], 0.0)


class PickerStages(unittest.TestCase):
    """Order Creator picker: brand-new orders apart from ones already ordered from a print provider.
    Only a print order really placed counts (owner, 18.09.2026): a draft, an order on hold or unpaid, or a
    cancelled one leaves the Etsy order in "new"."""
    AFTER = "2025-09-05 10:00:00+00:00"  # receipts below are from 2025-09-04 15:33 UTC

    def orders(self):
        printed = {**porder("a" * 24, "Zed", "Moss", status="in-production", created=self.AFTER),
                   "line_items": [{"title": "1002 - Emma", "metadata": {"title": "1002 - Emma"}}]}
        earlier = porder("b" * 24, "Mia", "Stone", created="2025-08-01 10:00:00+00:00")  # her previous book
        cancelled = {**porder("c" * 24, "Kai", "Lund", status="canceled", created=self.AFTER),
                     "line_items": [{"title": "1004 - Kai"}]}
        on_hold = {**porder("d" * 24, "Di", "Hale", status="on-hold", created=self.AFTER),
                   "line_items": [{"title": "1009 - Di"}]}
        gelato = {"totalInclVat": 20, "currency": "USD", "createdAt": "2025-09-05T10:00:00Z"}
        draft = {**gelato, "id": "g1", "orderReferenceId": "1005", "firstName": "Eve", "lastName": "Hart",
                 "fulfillmentStatus": "draft", "orderType": "draft", "financialStatus": "draft"}
        paid = {**gelato, "id": "g2", "orderReferenceId": "1008-ab12cd34", "firstName": "Lu", "lastName": "Park",
                "fulfillmentStatus": "passed", "orderType": "order", "financialStatus": "paid"}
        unpaid = {**gelato, "id": "g3", "orderReferenceId": "1010", "firstName": "Jo", "lastName": "Kim",
                  "fulfillmentStatus": "created", "orderType": "order", "financialStatus": "pending"}
        receipts = [receipt(1001, "Ann Lee", status="Paid"), receipt(1002, "Zed Moss", status="Paid"),
                    receipt(1003, "Mia Stone", status="Paid"), receipt(1004, "Kai Lund", status="Paid"),
                    receipt(1005, "Eve Hart", status="Paid"), receipt(1006, "Bo Ray"),
                    receipt(1007, "Cy Fox", status="Canceled", refunds=[49.98]), receipt(1008, "Lu Park", status="Paid"),
                    receipt(1009, "Di Hale", status="Paid"), receipt(1010, "Jo Kim", status="Paid")]
        return receipts, [printed, earlier, cancelled, on_hold], [draft, paid, unpaid]

    def test_each_order_lands_in_its_stage(self):
        receipts, p_orders, g_orders = self.orders()
        placed = profit.placed_orders({"printify": p_orders, "gelato": g_orders})
        got = {rid: profit.order_stage(row, placed) for rid, row in view(receipts, p_orders, g_orders).items()}
        self.assertEqual(got, {
            "1001": ("new", None),            # nothing ordered yet
            "1002": ("work", "printify"),     # Printify order carries the receipt number
            "1003": ("new", None),            # only an older order of the same buyer
            "1004": ("new", None),            # the print order was cancelled
            "1005": ("new", None),            # only a Gelato draft: not ordered until confirmed and paid
            "1006": ("shipped", None),
            "1007": ("closed", None),
            "1008": ("work", "gelato"),       # the draft confirmed and paid in Gelato
            "1009": ("new", None),            # Printify order on hold: not submitted yet
            "1010": ("new", None),            # Gelato order awaiting payment
        })

    def test_picker_leaves_out_cancelled_orders_and_shows_waiting_drafts(self):
        receipts, p_orders, g_orders = self.orders()
        snap = {"receipts": [profit.normalize_receipt(r) for r in receipts], "printify": p_orders, "gelato": g_orders}
        rows = view(receipts, p_orders, g_orders)
        with mock.patch.object(profit, "load_snapshot", lambda: snap),                 mock.patch.object(profit, "cached_view", lambda: {"full": rows}):
            picked = {o["receiptId"]: o for o in profit.picker_orders()}
        self.assertNotIn("1007", picked)
        self.assertEqual(sorted(o["stage"] for o in picked.values()).count("new"), 6)
        waiting = {rid: (o["provider"], o["printStatus"]) for rid, o in picked.items() if o["stage"] == "new"}
        self.assertEqual(waiting, {                     # in "new", a draft waiting at the printer shows its status
            "1001": (None, ""), "1003": (None, ""), "1004": (None, ""),  # nothing, an old order, a cancelled one
            "1005": ("gelato", "draft"), "1009": ("printify", "on-hold"), "1010": ("gelato", "created")})


class SentStage(unittest.TestCase):
    """The truck tab: the printer has shipped the book, Etsy is not marked yet."""
    AFTER = "2025-09-05 10:00:00+00:00"

    def orders(self):
        usps = [{"carrier": "usps", "number": "9400111", "url": "https://t.example/9400111"}]
        p_sent = {**porder("a" * 24, "Zed", "Moss", status="fulfilled", shop_order_id="1001", created=self.AFTER),
                  "shipments": usps}
        p_work = porder("b" * 24, "Ann", "Lee", status="in-production", shop_order_id="1002", created=self.AFTER)
        p_done = {**porder("c" * 24, "Bo", "Ray", status="fulfilled", shop_order_id="1004", created=self.AFTER),
                  "shipments": usps}
        g_sent = {"id": "g1", "orderReferenceId": "1003-x", "firstName": "Eve", "lastName": "Hart", "totalInclVat": 20,
                  "currency": "USD", "fulfillmentStatus": "in_transit", "orderType": "order",
                  "createdAt": "2025-09-05T10:00:00Z",
                  "shipments": [{"carrier": "UPS Surepost", "number": "1Z999", "url": ""}]}
        receipts = [receipt(1001, "Zed Moss", status="Paid"), receipt(1002, "Ann Lee", status="Paid"),
                    receipt(1003, "Eve Hart", status="Paid"), receipt(1004, "Bo Ray")]
        return receipts, [p_sent, p_work, p_done], [g_sent]

    def picked(self):
        receipts, p_orders, g_orders = self.orders()
        snap = {"receipts": [profit.normalize_receipt(r) for r in receipts], "printify": p_orders, "gelato": g_orders}
        rows = view(receipts, p_orders, g_orders)
        with mock.patch.object(profit, "load_snapshot", lambda: snap), \
                mock.patch.object(profit, "cached_view", lambda: {"full": rows}):
            return {o["receiptId"]: o for o in profit.picker_orders()}

    def test_shipped_by_the_printer_waits_in_the_truck_until_etsy_is_marked(self):
        got = {rid: (o["stage"], o["provider"]) for rid, o in self.picked().items()}
        self.assertEqual(got, {
            "1001": ("sent", "printify"),     # fulfilled with tracking, Etsy not marked
            "1002": ("work", "printify"),
            "1003": ("sent", "gelato"),       # Gelato in transit
            "1004": ("shipped", "printify"),  # marked on Etsy: out of the truck, printer still known
        })

    def test_status_is_the_printers_word_and_tracking_has_a_readable_carrier(self):
        picked = self.picked()
        self.assertEqual(picked["1002"]["printStatus"], "in-production")
        self.assertEqual(picked["1002"]["tracking"], [])
        self.assertEqual(picked["1001"]["tracking"],
                         [{"carrier": "USPS", "number": "9400111", "url": "https://t.example/9400111"}])
        self.assertEqual(picked["1003"]["printStatus"], "in_transit")
        self.assertEqual(picked["1003"]["tracking"][0]["carrier"], "UPS Surepost")

    def test_shipped_status_alone_is_enough(self):
        placed = {"gelato:g1": {"created": None, "status": "shipped", "tracking": []}}
        row = {"pod_provider": "gelato", "gelato_order_id": "g1", "match_type": "manual"}
        self.assertEqual(profit.order_stage(row, placed), ("sent", "gelato"))
        placed["gelato:g1"]["status"] = "printed"
        self.assertEqual(profit.order_stage(row, placed), ("work", "gelato"))

    def test_carrier_labels(self):
        self.assertEqual([profit.carrier_label(c) for c in ("usps", "fedex", "royal-mail", "asendia", "")],
                         ["USPS", "FedEx", "Royal Mail", "asendia", ""])

    def test_printify_snapshot_keeps_tracking(self):
        slim = printify.slim_order({"id": "p1", "status": "fulfilled", "shipments": [
            {"carrier": "usps", "number": "9400", "url": "u", "delivered_at": None},
            {"carrier": "usps", "number": "", "url": ""}]})
        self.assertEqual(slim["shipments"], [{"carrier": "usps", "number": "9400", "url": "u"}])


class GelatoTracking(unittest.TestCase):
    """Gelato's order search has no tracking: shipped orders are read one by one, once."""

    FULL = {"shipment": {"shipmentMethodName": "USPS Ground Advantage",
                         "packages": [{"trackingCode": "9200", "trackingUrl": "https://t.example/9200"}]}}

    def test_tracking_from_packages_or_items(self):
        self.assertEqual(gelato.shipments_of(self.FULL),
                         [{"carrier": "USPS Ground Advantage", "number": "9200", "url": "https://t.example/9200"}])
        by_items = {"shipment": {"shipmentMethodName": "DHL", "packages": []},
                    "items": [{"fulfillments": [{"trackingCode": "D1", "trackingUrl": "", "shipmentMethodName": ""}]},
                              {"fulfillments": [{"trackingCode": "D1"}]}]}
        self.assertEqual(gelato.shipments_of(by_items), [{"carrier": "DHL", "number": "D1", "url": ""}])
        self.assertEqual(gelato.shipments_of({}), [])

    def test_each_shipped_order_is_read_once(self):
        read = []

        def get_order(order_id):
            read.append(order_id)
            if order_id == "bad":
                raise gelato.GelatoError("no", 502)
            return self.FULL if order_id == "s1" else {}

        orders = [{"id": "s1", "fulfillmentStatus": "shipped"}, {"id": "s2", "fulfillmentStatus": "delivered"},
                  {"id": "p1", "fulfillmentStatus": "printed"}, {"id": "bad", "fulfillmentStatus": "in_transit"}]
        with mock.patch.object(gelato, "get_order", get_order):
            failed = gelato.attach_shipments(orders, [])
            self.assertEqual((sorted(read), failed), (["bad", "s1", "s2"], 1))
            self.assertEqual(orders[0]["shipments"][0]["number"], "9200")
            self.assertEqual(orders[1]["shipments"], [])       # shipped, but no tracking yet
            self.assertNotIn("shipments", orders[2])           # still printing: not read

            read.clear()
            again = [{"id": "s1", "fulfillmentStatus": "delivered"}, {"id": "s2", "fulfillmentStatus": "delivered"},
                     {"id": "p1", "fulfillmentStatus": "shipped"}, {"id": "bad", "fulfillmentStatus": "in_transit"}]
            gelato.attach_shipments(again, orders)
            # s1 keeps its tracking, s2 is not re-read while its status stays; p1 has just shipped; bad is retried
            self.assertEqual(sorted(read), ["bad", "p1"])
            self.assertEqual(again[0]["shipments"], orders[0]["shipments"])

            read.clear()
            later = [{"id": "s2", "fulfillmentStatus": "returned"}]
            gelato.attach_shipments(later, again)
            self.assertEqual(read, ["s2"])                      # status changed and still no tracking

    def test_reading_one_order_is_allowed(self):
        self.assertTrue(gelato._allowed("GET", f"{gelato.ORDER_API}/orders/abc", None))


class IncrementalSync(unittest.TestCase):
    def tearDown(self):
        vault.set("printify_token", None)
        for path in (profit.SNAPSHOT, profit.STATES, profit.LINKS):
            path.unlink(missing_ok=True)

    def test_second_sync_reads_only_changed_receipts(self):
        calls = []
        first = [receipt(2, "B", ts=1757000200), receipt(1, "A", ts=1757000100)]
        changed = [receipt(1, "A", ts=1757000100, status="Canceled", refunds=[49.98], updated=1757100000),
                   receipt(3, "C", ts=1757200000)]

        def fetch(progress=None, min_last_modified=None):
            calls.append(min_last_modified)
            return (first if min_last_modified is None else changed), 63208655, "Shop"

        with mock.patch.object(etsy, "tokens", lambda: {"access_token": "1.x", "shop_id": 63208655}), \
                mock.patch.object(etsy, "fetch_all_receipts", fetch):
            profit._sync(Job("a"))
            cursor = profit.load_snapshot()["etsyCursor"]
            result = profit._sync(Job("b"))
            snap = profit.load_snapshot()
            self.assertIsNone(calls[0])                                   # first sync reads everything
            self.assertEqual(calls[1], cursor - profit.SYNC_OVERLAP)       # then only what changed since
            self.assertEqual(result["changed"], 2)
            self.assertEqual([r["receipt_id"] for r in snap["receipts"]], ["3", "2", "1"])
            self.assertEqual(snap["receipts"][2]["status"], "Canceled")
            profit._sync(Job("c"), full=True)
            self.assertIsNone(calls[2])


class StateApi(unittest.TestCase):
    def setUp(self):
        self.p = porder("a" * 24, "Amelia", "Lewis", shop_order_id="1")
        self.other = porder("c" * 24, "Zed", "Q", created="2025-09-06 12:00:00+00:00")
        core.write_json(profit.SNAPSHOT, {"receipts": [profit.normalize_receipt(receipt(1, "Amelia Lewis"))],
                                          "printify": [self.p, self.other], "gelato": []})

    def tearDown(self):
        for path in (profit.SNAPSHOT, profit.STATES, profit.LINKS):
            path.unlink(missing_ok=True)

    def call(self, fn, body):
        return fn(SimpleNamespace(json=body))

    def test_replacement_cannot_reuse_the_primary_order(self):
        with self.assertRaises(ApiError):
            self.call(profit._set_state, {"receiptId": "1", "status": "replacement",
                                          "replacementOrders": [{"provider": "printify", "orderId": "a" * 24}]})

    def test_states_round_trip_and_reserved_orders_cannot_be_linked_elsewhere(self):
        res = self.call(profit._set_state, {"receiptId": "1", "status": "replacement",
                                            "replacementOrders": [{"provider": "printify", "orderId": "c" * 24}]})
        self.assertEqual(res["row"]["state"], "replacement")
        self.assertEqual(res["row"]["replacement_cost"], 11.95)
        with self.assertRaises(ApiError):
            self.call(profit._set_link, {"receiptId": "999", "provider": "printify", "orderId": "c" * 24})
        res = self.call(profit._set_state, {"receiptId": "1", "status": "auto"})
        self.assertEqual(res["row"]["state"], "normal")
        self.assertFalse(res["row"]["state_manual"])

    def test_bad_input_is_rejected(self):
        for body in ({"receiptId": "1", "status": "nope"}, {"receiptId": "404", "status": "canceled"},
                     {"receiptId": "1", "status": "refund_partial", "refundAmount": "abc"},
                     {"receiptId": "1", "status": "refund_partial", "refundAmount": 1000}):
            with self.subTest(body=body), self.assertRaises(ApiError):
                self.call(profit._set_state, body)


if __name__ == "__main__":
    unittest.main()
