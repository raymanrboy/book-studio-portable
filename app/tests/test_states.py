"""Cancelled / refunded / replaced orders, provider-side cancellations and incremental Etsy sync."""
import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import core, etsy, gelato, outcomes, printify, printorders, profit, reconcile, records, stages, sync
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


RATES = {"EUR": 1.085, "CZK": 0.0468}


def view(receipts, p_orders=(), g_orders=(), states=None, links=None, sent=None, real=None):
    """Runs the same pipeline as build_view without touching the snapshot."""
    norm = [sync.normalize_receipt(r) for r in receipts]
    rows = outcomes.rows(norm, list(p_orders), list(g_orders), links or {}, states or {}, sent or {}, RATES, real)
    return {r["id"]: r for r in rows}


class OnTheSnapshot(unittest.TestCase):
    """Tests that read the real view: their own snapshot, no links, states or sends of another test."""
    FILES = (records.SNAPSHOT, records.STATES, records.LINKS, records.SENDS)

    def setUp(self):
        for path in self.FILES:
            path.unlink(missing_ok=True)

    def tearDown(self):
        for path in self.FILES:
            path.unlink(missing_ok=True)

    def synced(self, receipts, p_orders=(), g_orders=()):
        core.write_json(records.SNAPSHOT, {"receipts": [sync.normalize_receipt(r) for r in receipts],
                                           "printify": list(p_orders), "gelato": list(g_orders)})


class NormalOrdersUnchanged(unittest.TestCase):
    def test_golden_rows_keep_original_numbers(self):
        fx = GOLDEN["fixture"]
        links = {k: {"provider": "printify", "orderId": v} for k, v in fx["manual"].items()}
        norm = [sync.normalize_receipt(r) for r in fx["receipts"]]
        plain = {r["id"]: dict(r) for r in reconcile.match(norm, fx["printify"], fx["gelato"], links, RATES)}
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


def lines(**cents):
    return [{"type": k, "label": k, "amount": v / 100} for k, v in cents.items()]


class LedgerMoney(unittest.TestCase):
    """Once Etsy's ledger has the sale, its money is the Etsy Net (2026-10-13); until then the formula forecasts."""
    def setUp(self):
        self.p = porder("a" * 24, "Amelia", "Lewis", shop_order_id="1")

    def test_a_sale_not_posted_yet_is_the_formulas_forecast(self):
        row = view([receipt(1, "Amelia Lewis")], [self.p])["1"]
        self.assertEqual(row["etsy_source"], "forecast")
        self.assertEqual(row["etsy_net"], row["etsy_net_formula"])
        self.assertEqual(row["etsy_extra"], [])

    def test_offsite_ads_come_off_the_net_the_fees_and_the_profit(self):
        formula = view([receipt(1, "Amelia Lewis")], [self.p])["1"]
        real = {"1": {"net": r2(formula["etsy_net"] - 5.72),
                      "lines": lines(PAYMENT_GROSS=4998, transaction=-300, offsite_ads_fee=-572)}}
        row = view([receipt(1, "Amelia Lewis")], [self.p], real=real)["1"]
        self.assertEqual(row["etsy_source"], "ledger")
        self.assertEqual(row["etsy_net"], r2(formula["etsy_net"] - 5.72))
        self.assertEqual(row["etsy_net_formula"], formula["etsy_net"])
        self.assertEqual(row["etsy_fees"], r2(formula["etsy_fees"] + 5.72))
        self.assertEqual(row["profit"], r2(row["etsy_net"] - 11.95))
        self.assertEqual([x["type"] for x in row["etsy_extra"]], ["offsite_ads_fee"])

    def test_a_cancellation_is_what_etsy_really_gave_back(self):
        # The owner's sale of 18.09.2026: Etsy kept the $0.20 listing fee, the formula said 0.
        real = {"1": {"net": -0.20, "lines": lines(PAYMENT_GROSS=2573, PAYMENT_PROCESSING_FEE=-184, transaction=-83,
                                                   shipping_transaction=-84, renew_sold_auto=-20, REFUND_GROSS=-2573,
                                                   REFUND_PROCESSING_FEE=184, transaction_refund=83,
                                                   shipping_transaction_refund=84)}}
        row = view([receipt(1, "Amelia Lewis", status="Canceled", refunds=[25.73])], [self.p], real=real)["1"]
        self.assertEqual(row["state"], "canceled")
        self.assertEqual(row["etsy_net"], -0.20)
        self.assertEqual(row["etsy_net_original"], 22.02)
        self.assertEqual((row["refund_amount"], row["revenue_back"], row["fee_credit"]), (25.73, 25.73, 3.51))
        self.assertAlmostEqual(row["etsy_net_original"] - row["revenue_back"] + row["fee_credit"], row["etsy_net"], places=2)
        self.assertEqual(row["profit"], r2(-0.20 - 11.95))
        self.assertEqual(row["impact"], r2(-0.20 - 11.95))

    def test_a_cancellation_etsy_has_not_posted_yet_is_forecast(self):
        real = {"1": {"net": 42.0, "lines": lines(PAYMENT_GROSS=4998, transaction=-798)}}
        row = view([receipt(1, "Amelia Lewis", status="Canceled", refunds=[49.98])], [self.p], real=real)["1"]
        self.assertEqual((row["etsy_source"], row["etsy_net"], row["impact"]), ("forecast", 0.0, -11.95))

    def test_without_a_ledger_the_states_keep_their_numbers(self):
        row = view([receipt(1, "Amelia Lewis", status="Canceled", refunds=[49.98])], [self.p])["1"]
        self.assertEqual((row["etsy_net"], row["impact"]), (0.0, -11.95))


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


class SeveralPrintOrdersForOneReceipt(unittest.TestCase):
    """Books of one order can go in two goes (some ready now, the rest later) or to two printers. Every
    print order this program made then costs money, and all of it belongs to that one sale."""

    def gorder(self, gid, ref, cost=18.0, status="printed"):
        return {"id": gid, "orderReferenceId": ref, "firstName": "Dana", "lastName": "Reed",
                "totalInclVat": cost, "currency": "USD", "fulfillmentStatus": status,
                "orderType": "order", "createdAt": "2025-09-04T12:00:00Z"}

    def sent(self, *orders):
        return {"1": [{"provider": p, "orderId": o} for p, o in orders]}

    def test_the_second_printer_order_is_counted_too(self):
        first = {**porder("a" * 24, "Dana", "Reed", cost_cents=1195), "line_items": [{"title": "1 - Emma"}]}
        second = self.gorder("g-second", "1-later")
        rid = view([receipt(1, "Dana Reed")], [first], [second],
                   sent=self.sent(("printify", "a" * 24), ("gelato", "g-second")))["1"]
        self.assertEqual(rid["pod_provider"], "printify")               # the row still has one main order
        self.assertEqual([f["order_id"] for f in rid["further_orders"]], ["g-second"])
        self.assertEqual(rid["pod_total_cost"], r2(11.95 + 18.0))       # and the whole cost of the sale
        self.assertEqual(rid["profit"], r2(rid["etsy_net"] - rid["pod_total_cost"]))

    def test_without_the_second_order_nothing_changes(self):
        only = {**porder("a" * 24, "Dana", "Reed", cost_cents=1195), "line_items": [{"title": "1 - Emma"}]}
        rid = view([receipt(1, "Dana Reed")], [only], sent=self.sent(("printify", "a" * 24)))["1"]
        self.assertEqual(rid["further_orders"], [])
        self.assertEqual(rid["pod_total_cost"], 11.95)

    def test_a_draft_the_owner_has_not_confirmed_costs_nothing_yet(self):
        first = {**porder("a" * 24, "Dana", "Reed", cost_cents=1195), "line_items": [{"title": "1 - Emma"}]}
        draft = {**self.gorder("g-draft", "1-later", status="draft"), "orderType": "draft"}
        rid = view([receipt(1, "Dana Reed")], [first], [draft],
                   sent=self.sent(("printify", "a" * 24), ("gelato", "g-draft")))["1"]
        self.assertEqual(rid["further_orders"], [])
        self.assertEqual(rid["pod_total_cost"], 11.95)

    def test_a_cancelled_second_order_costs_nothing(self):
        first = {**porder("a" * 24, "Dana", "Reed", cost_cents=1195), "line_items": [{"title": "1 - Emma"}]}
        killed = self.gorder("g-dead", "1-later", status="canceled")
        rid = view([receipt(1, "Dana Reed")], [first], [killed],
                   sent=self.sent(("printify", "a" * 24), ("gelato", "g-dead")))["1"]
        self.assertEqual(rid["further_orders"], [])
        self.assertEqual(rid["pod_total_cost"], 11.95)

    def test_a_reprint_is_not_counted_as_a_further_order(self):
        """A reprint is a replacement, recorded elsewhere; counting it here would charge the sale twice."""
        first = {**porder("a" * 24, "Dana", "Reed", cost_cents=1195), "line_items": [{"title": "1 - Emma"}]}
        again = {**porder("b" * 24, "Dana", "Reed", cost_cents=1195), "line_items": [{"title": "1 - Emma"}]}
        states = {"1": {"status": "replacement",
                        "replacementOrders": [{"provider": "printify", "orderId": "b" * 24}]}}
        rid = view([receipt(1, "Dana Reed")], [first, again], states=states,
                   sent=self.sent(("printify", "a" * 24), ("printify", "b" * 24)))["1"]
        self.assertEqual(rid["further_orders"], [])
        self.assertEqual(rid["pod_total_cost"], 11.95)


class PickerStages(OnTheSnapshot):
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
        placed = printorders.all_facts({"printify": p_orders, "gelato": g_orders}, RATES)
        got = {rid: stages.order_stage(row, placed) for rid, row in view(receipts, p_orders, g_orders).items()}
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
        self.synced(*self.orders())
        picked = {o["receiptId"]: o for o in stages.picker_orders()}
        self.assertNotIn("1007", picked)
        self.assertEqual(sorted(o["stage"] for o in picked.values()).count("new"), 6)
        waiting = {rid: (o["provider"], o["printStatus"]) for rid, o in picked.items() if o["stage"] == "new"}
        self.assertEqual(waiting, {                     # in "new", a draft waiting at the printer shows its status
            "1001": (None, ""), "1003": (None, ""), "1004": (None, ""),  # nothing, an old order, a cancelled one
            "1005": ("gelato", "draft"), "1009": ("printify", "on-hold"), "1010": ("gelato", "created")})


class QueueSignals(OnTheSnapshot):
    """2026-10-14: an order of two books with only one ordered is listed under «Нові» too («partial»), its stage kept; a
    refused Gelato payment — the shown order's or another send's — and Etsy's ship-by date reach the queue."""
    def two_books(self, rid, ship_by=None):
        r = receipt(rid, "Lu Park", status="Paid")
        r["transactions"] = [{"transaction_id": rid * 10, "expected_ship_date": ship_by},
                             {"transaction_id": rid * 10 + 1, "expected_ship_date": ship_by + 86400 if ship_by else None}]
        return r

    def gelato(self, gid, ref, financial="paid", status="passed"):
        return {"id": gid, "orderReferenceId": ref, "firstName": "Lu", "lastName": "Park", "totalInclVat": 20,
                "currency": "USD", "createdAt": "2025-09-05T10:00:00Z", "fulfillmentStatus": status,
                "orderType": "order", "financialStatus": financial}

    def test_one_of_two_books_ordered_is_partial(self):
        self.synced([self.two_books(1011, ship_by=1757500000)], [],
                    [self.gelato("g4", "1011 - Mia"), self.gelato("g8", "1011 - Jack", financial="refused", status="failed")])
        core.write_json(records.SENDS, {"1011": [{"provider": "gelato", "orderId": "g4", "books": 1},
                                                 {"provider": "gelato", "orderId": "g8", "books": 1}]})
        got = stages.picker_order("1011")
        self.assertEqual((got["stage"], got["partial"], got["booksInPrint"]), ("work", True, 1))  # the card keeps its print
        self.assertEqual(got["shipBy"], 1757500000)                 # the earliest of the items'
        self.assertEqual([(p["provider"], p["payment"]) for p in got["pending"]], [("gelato", "refused")])  # the second book's
        core.write_json(records.SENDS, {"1011": [{"provider": "gelato", "orderId": "g4", "books": 2}]})
        self.assertFalse(stages.picker_order("1011")["partial"])

    def test_a_send_without_its_books_counted_holds_them_all(self):
        self.synced([self.two_books(1012)], [], [self.gelato("g5", "1012 - Mia")])
        core.write_json(records.SENDS, {"1012": [{"provider": "gelato", "orderId": "g5"}]})   # sent before 14.10
        got = stages.picker_order("1012")
        self.assertEqual((got["stage"], got["partial"], got["shipBy"]), ("work", False, None))

    def test_a_refused_payment_reaches_the_queue(self):
        self.synced([receipt(1013, "Lu Park", status="Paid")], [],
                    [self.gelato("g6", "1013 - Mia", financial="refused", status="failed")])
        got = stages.picker_order("1013")
        self.assertEqual((got["stage"], got["provider"], got["payment"]), ("new", "gelato", "refused"))

    def test_the_send_record_notes_its_books(self):
        records.remember_print_order("1014", "gelato", "g7", books=2)
        self.assertEqual(records.load_sends()["1014"][0]["books"], 2)


class ReprintWithNewFiles(OnTheSnapshot):
    """18.10.2026: a shipped order reprinted at Gelato with a fixed cover. The first print stays the receipt's own even
    when the reprint carries the same name; while the reprint is made the order is «в роботі» again; the card has a
    tab per print; the money keeps the first print's cost and adds the reprint's."""
    def gelato(self, gid, created, status, cost):
        return {"id": gid, "orderReferenceId": "1021 - Noah", "firstName": "Jo", "lastName": "Bell", "totalInclVat": cost,
                "currency": "USD", "createdAt": created, "fulfillmentStatus": status, "orderType": "order",
                "financialStatus": "paid"}

    def setUp(self):
        super().setUp()
        self.first = self.gelato("g-first", "2025-09-05T10:00:00Z", "delivered", "10.47")
        self.again = self.gelato("g-again", "2025-09-20T10:00:00Z", "uploading", "18.30")
        self.synced([receipt(1021, "Jo Bell")], [], [self.again, self.first])   # Gelato lists the newest first

    def test_the_first_print_stays_the_receipts_own_without_a_mark(self):
        self.assertEqual(profit.cached_view()["full"]["1021"]["gelato_order_id"], "g-first")

    def test_a_marked_reprint_puts_the_order_back_in_work_with_a_tab_each(self):
        self.assertEqual(stages.picker_order("1021")["stage"], "shipped")
        self.assertTrue(stages.picker_order("1021")["alreadyPrinted"])   # a send of it now ticks «Передрук»
        records.add_replacement("1021", "gelato", "g-again")
        got = stages.picker_order("1021")
        self.assertEqual((got["stage"], got["reprint"], got["printStatus"]), ("work", True, "uploading"))
        known = stages.facts()
        prints = stages.prints(known["receipts"]["1021"]["row"], known["placed"])
        self.assertEqual([(p["kind"], p["id"]) for p in prints], [("first", "g-first"), ("reprint", "g-again")])
        row = profit.cached_view()["full"]["1021"]
        self.assertEqual((row["pod_total_cost"], row["replacement_cost"], row["cost_total"]), (10.47, 18.3, 28.77))

    def test_the_order_is_shipped_again_once_the_reprint_has_left(self):
        records.add_replacement("1021", "gelato", "g-again")
        self.synced([receipt(1021, "Jo Bell")], [], [{**self.again, "fulfillmentStatus": "in_transit"}, self.first])
        got = stages.picker_order("1021")
        self.assertEqual((got["stage"], got["reprint"]), ("shipped", False))


class SentStage(OnTheSnapshot):
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
        self.synced(*self.orders())
        return {o["receiptId"]: o for o in stages.picker_orders()}

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
        self.assertEqual(stages.order_stage(row, placed), ("sent", "gelato"))
        placed["gelato:g1"]["status"] = "printed"
        self.assertEqual(stages.order_stage(row, placed), ("work", "gelato"))

    def test_carrier_labels(self):
        self.assertEqual([printorders.carrier_label(c) for c in ("usps", "fedex", "royal-mail", "asendia", "")],
                         ["USPS", "FedEx", "Royal Mail", "asendia", ""])

    def test_printify_snapshot_keeps_tracking(self):
        slim = printify.slim_order({"id": "p1", "status": "fulfilled", "shipments": [
            {"carrier": "usps", "number": "9400", "url": "u", "delivered_at": None},
            {"carrier": "usps", "number": "", "url": ""}]})
        self.assertEqual(slim["shipments"], [{"carrier": "usps", "number": "9400", "url": "u", "delivered_at": None}])

    def test_printify_fulfilled_shows_as_in_transit_then_delivered(self):
        def shown(status, *delivered):
            order = {"status": status, "shipments": [{"number": str(i), "delivered_at": d} for i, d in enumerate(delivered)]}
            return printorders.shown_status("printify", order)
        self.assertEqual(shown("fulfilled", None), "in_transit")
        self.assertEqual(shown("fulfilled", "2025-09-20 10:00:00+00:00", None), "in_transit")  # one parcel still on its way
        self.assertEqual(shown("fulfilled", "2025-09-20 10:00:00+00:00"), "delivered")
        self.assertEqual(shown("fulfilled"), "in_transit")
        self.assertEqual(shown("in-production"), "in-production")
        self.assertEqual(printorders.shown_status("gelato", {"fulfillmentStatus": "delivered"}), "delivered")

    def test_the_queue_shows_printify_fulfilled_as_in_transit_and_keeps_the_stage(self):
        picked = self.picked()
        self.assertEqual(picked["1001"]["printStatus"], "in_transit")
        self.assertEqual(picked["1001"]["stage"], "sent")


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

        def get_order(order_id, account="main"):
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
    def setUp(self):
        for path in (records.SNAPSHOT, records.STATES, records.LINKS):  # whatever another test synced before
            path.unlink(missing_ok=True)

    def tearDown(self):
        vault.set("printify_token", None)
        for path in (records.SNAPSHOT, records.STATES, records.LINKS):
            path.unlink(missing_ok=True)

    def test_a_receipt_read_twice_is_kept_once(self):
        """Audit 26.09.2026: a new order during a full read shifts Etsy's pages, and one receipt came twice — two
        rows in the queue, the money counted twice."""
        twice = [receipt(3, "C", ts=1757000300), receipt(2, "B", ts=1757000200), receipt(2, "B", ts=1757000200),
                 receipt(1, "A", ts=1757000100)]
        with mock.patch.object(etsy, "tokens", lambda: {"access_token": "1.x", "shop_id": 63208655}),                 mock.patch.object(etsy, "fetch_all_receipts",
                                  lambda progress=None, min_last_modified=None: (twice, 63208655, "Shop")):
            result = sync._sync(Job("t"), full=True)
        self.assertEqual(result["receipts"], 3)
        self.assertEqual([r["receipt_id"] for r in records.load_snapshot()["receipts"]], ["3", "2", "1"])

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
            sync._sync(Job("a"))
            cursor = records.load_snapshot()["etsyCursor"]
            result = sync._sync(Job("b"))
            snap = records.load_snapshot()
            self.assertIsNone(calls[0])                                   # first sync reads everything
            self.assertEqual(calls[1], cursor - sync.SYNC_OVERLAP)       # then only what changed since
            self.assertEqual(result["changed"], 2)
            self.assertEqual([r["receipt_id"] for r in snap["receipts"]], ["3", "2", "1"])
            self.assertEqual(snap["receipts"][2]["status"], "Canceled")
            sync._sync(Job("c"), full=True)
            self.assertIsNone(calls[2])

    def test_a_list_that_failed_or_was_cut_keeps_its_old_load_time(self):
        """The archive trusts a printer's orders only as of their last whole load (22.09.2026 audit: a stale
        Gelato list made a book that went to print look like a deleted draft)."""
        from studio import httpc
        keys = {"gelato_api_key": "fake-gelato-key"}
        fetch = lambda progress=None, min_last_modified=None: ([receipt(1, "A")], 63208655, "Shop")
        with mock.patch.object(etsy, "tokens", lambda: {"access_token": "1.x", "shop_id": 63208655}), \
                mock.patch.object(etsy, "fetch_all_receipts", fetch), \
                mock.patch.object(vault, "get", lambda name: keys.get(name)):
            with mock.patch.object(gelato, "all_orders", side_effect=gelato.GelatoError("немає з'єднання з Gelato", 502)):
                sync._sync(Job("a"))
            self.assertEqual(sorted(records.load_snapshot()["loaded"]), ["etsy"])
            cut = httpc.Listing([{"id": "g1", "fulfillmentStatus": "draft"}])
            cut.complete = False
            with mock.patch.object(gelato, "all_orders", lambda progress=None, account="main": cut):
                result = sync._sync(Job("b"))
            self.assertEqual(sorted(records.load_snapshot()["loaded"]), ["etsy"])
            self.assertTrue(any("лише останні" in w for w in result["warnings"]))
            with mock.patch.object(gelato, "all_orders", lambda progress=None, account="main": httpc.Listing(cut)):
                sync._sync(Job("c"))
            self.assertEqual(sorted(records.load_snapshot()["loaded"]), ["etsy", "gelato"])

    def test_an_open_receipt_without_its_ship_by_date_is_read_again_whole(self):
        """2026-10-14: the ship-by date is kept from now on; receipts read before have none — one full read fills it."""
        calls = []

        def fetch(progress=None, min_last_modified=None):
            calls.append(min_last_modified)
            r = receipt(1, "A", status="Paid")
            r["transactions"] = [{"transaction_id": 10, "expected_ship_date": 1757500000}]
            return [r], 63208655, "Shop"

        with mock.patch.object(etsy, "tokens", lambda: {"access_token": "1.x", "shop_id": 63208655}),                 mock.patch.object(etsy, "fetch_all_receipts", fetch):
            sync._sync(Job("a"))
            snap = records.load_snapshot()
            self.assertEqual(snap["receipts"][0]["ship_by"], 1757500000)
            del snap["receipts"][0]["ship_by"]                       # as a receipt kept before the date was
            records.save(records.SNAPSHOT, snap)
            sync._sync(Job("b"))
            self.assertIsNone(calls[1])                              # read whole again
            sync._sync(Job("c"))
            self.assertIsNotNone(calls[2])                           # then only what changed

    def test_the_snapshot_is_read_once_per_change(self):
        core.write_json(records.SNAPSHOT, {"receipts": [], "syncedAt": "2026-09-22T10:00:00Z"})
        first = records.load_snapshot()
        self.assertIs(records.load_snapshot(), first)                     # nothing changed: not parsed again
        core.write_json(records.SNAPSHOT, {"receipts": [], "syncedAt": "2026-09-22T11:00:00Z"})
        self.assertEqual(records.load_snapshot()["syncedAt"], "2026-09-22T11:00:00Z")


class MatchingOrder(unittest.TestCase):
    """Both receipt-number rules come before either name rule (audit 26.09.2026)."""

    def gorder(self, gid, ref, first, last, created="2025-09-05T10:00:00Z", **extra):
        return {"id": gid, "orderReferenceId": ref, "firstName": first, "lastName": last, "totalInclVat": 20,
                "currency": "USD", "fulfillmentStatus": "printed", "orderType": "order", "createdAt": created, **extra}

    def test_the_receipts_own_gelato_order_beats_a_printify_order_with_a_like_name(self):
        """"Ann Lee" is inside "Joann Leeds": the name rule used to hand Ann's receipt that order — its status and
        tracking showed on her card, while her own Gelato draft carried her number."""
        other = porder("a" * 24, "Joann", "Leeds", created="2025-09-05 10:00:00+00:00")
        own = self.gorder("g1", "1 - Emma", "Ann", "Lee")
        row = view([receipt(1, "Ann Lee")], [other], [own])["1"]
        self.assertEqual((row["pod_provider"], row.get("gelato_order_id")), ("gelato", "g1"))

    def test_a_name_still_finds_an_order_that_names_no_receipt(self):
        by_name = porder("a" * 24, "Ann", "Lee", created="2025-09-05 10:00:00+00:00")
        row = view([receipt(1, "Ann Lee")], [by_name])["1"]
        self.assertEqual(row["printify_order_id"], "a" * 24)

    def test_a_repeat_buyers_old_order_is_not_taken_by_her_new_receipt(self):
        """Diane's receipt of 8 Oct found her Gelato order of 5 Sep by name, and the two receipts split its cost."""
        old = self.gorder("g1", "G-260905174108", "Diane", "Lord", created="2025-09-05T15:41:09Z")
        rows = view([receipt(4164660299, "Diane Lord", ts=1757036000), receipt(4197522316, "Diane Lord", ts=1757036000 + 33 * 86400)],
                    g_orders=[old])
        self.assertEqual(rows["4164660299"]["gelato_order_id"], "g1")
        self.assertFalse(rows["4164660299"]["is_bundle"])
        self.assertEqual(rows["4197522316"]["match_type"], "unmatched")

    def test_a_manual_link_to_an_order_the_sync_does_not_have_falls_back_to_the_rules(self):
        own = self.gorder("g1", "1 - Emma", "Ann", "Lee")
        row = view([receipt(1, "Ann Lee")], g_orders=[own], links={"1": {"provider": "printify", "orderId": "gone"}})["1"]
        self.assertEqual((row["match_type"], row["gelato_order_id"]), ("auto", "g1"))


class MoneyRules(unittest.TestCase):
    """The accounting items deferred on 23.09.2026, fixed on 26.09.2026."""

    def gorder(self, gid, ref, cost=18.0, currency="USD", **extra):
        return {"id": gid, "orderReferenceId": ref, "firstName": "Dana", "lastName": "Reed", "totalInclVat": cost,
                "currency": currency, "fulfillmentStatus": "printed", "orderType": "order",
                "createdAt": "2025-09-04T12:00:00Z", **extra}

    def test_a_cancelled_first_order_keeps_the_second_ones_cost(self):
        """The refund of a sale whose first print order was cancelled wiped the cost of its second one too."""
        first = porder("a" * 24, "Dana", "Reed", status="canceled", shop_order_id="1")
        second = self.gorder("g2", "1-later")
        sent = {"1": [{"provider": "printify", "orderId": "a" * 24}, {"provider": "gelato", "orderId": "g2"}]}
        row = view([receipt(1, "Dana Reed", status="Fully Refunded", refunds=[49.98])], [first], [second], sent=sent)["1"]
        self.assertEqual(row["pod_dead"], "canceled")
        self.assertEqual([f["order_id"] for f in row["further_orders"]], ["g2"])
        self.assertEqual(row["cost_total"], 18.0)                    # the second print order still cost money
        self.assertEqual(row["profit"], r2(row["etsy_net"] - 18.0))

    def test_an_order_on_hold_or_unpaid_costs_nothing_yet(self):
        """Only a placed and paid print order counts (18.09.2026) — the money counted on-hold and unpaid ones."""
        on_hold = porder("a" * 24, "Dana", "Reed", status="on-hold", shop_order_id="1")
        unpaid = self.gorder("g2", "2 - Emma", financialStatus="pending")
        rows = view([receipt(1, "Dana Reed"), receipt(2, "Dana Reed", ts=1757000100)], [on_hold], [unpaid])
        for rid in ("1", "2"):
            with self.subTest(receipt=rid):
                row = rows[rid]
                self.assertEqual(row["pod_dead"], "unpaid")
                self.assertIsNone(row["profit"])                    # what the sale earns is not known yet
                self.assertFalse(row.get("needs_link"))             # it is the right order, only not paid
                self.assertEqual(row["cost_total"], 0.0)
                self.assertGreater(row["pod_cost_original"], 0)     # what it will cost is still shown

    def test_an_unpaid_further_order_is_not_counted(self):
        first = porder("a" * 24, "Dana", "Reed", shop_order_id="1")
        later = self.gorder("g2", "1-later", financialStatus="pending")
        sent = {"1": [{"provider": "printify", "orderId": "a" * 24}, {"provider": "gelato", "orderId": "g2"}]}
        row = view([receipt(1, "Dana Reed")], [first], [later], sent=sent)["1"]
        self.assertEqual((row["further_orders"], row["pod_total_cost"]), ([], 11.95))

    def test_every_currency_gelato_bills_in_is_converted(self):
        """Five orders in Czech crowns were counted as dollars (23.09.2026)."""
        for currency, rate in (("EUR", RATES["EUR"]), ("CZK", RATES["CZK"]), ("USD", 1)):
            with self.subTest(currency=currency):
                row = view([receipt(1, "Dana Reed")], g_orders=[self.gorder("g1", "1 - Emma", 500, currency)])["1"]
                self.assertEqual(row["pod_total_cost"], r2(500 * rate))
                self.assertEqual(row["profit"], r2(row["etsy_net"] - row["pod_total_cost"]))

    def test_a_currency_without_a_rate_is_never_counted_as_dollars(self):
        row = view([receipt(1, "Dana Reed")], g_orders=[self.gorder("g1", "1 - Emma", 500, "SEK")])["1"]
        self.assertTrue(row["cost_unknown"])
        self.assertIsNone(row["profit"])
        self.assertEqual((row["gelato_cost"], row["gelato_currency"]), (500, "SEK"))

    def test_a_split_bundle_is_shared_between_its_receipts(self):
        both = {**porder("a" * 24, "Dana", "Reed", cost_cents=2000), "line_items": [{"title": "1 and 2"}]}
        rows = view([receipt(1, "Dana Reed"), receipt(2, "Dana Reed")], [both])
        self.assertEqual([rows[r]["pod_total_cost"] for r in ("1", "2")], [10.0, 10.0])
        self.assertEqual({rows[r]["bundle_count"] for r in ("1", "2")}, {2})


class PickerFacts(OnTheSnapshot):
    def test_one_order_reads_as_in_the_whole_list_and_the_facts_are_worked_out_once(self):
        receipts, p_orders, g_orders = PickerStages().orders()
        self.synced(receipts, p_orders, g_orders)
        everything = {o["receiptId"]: o for o in stages.picker_orders()}
        self.assertEqual(stages.picker_order("1005"), everything["1005"])
        self.assertIsNone(stages.picker_order("1007"))              # a cancelled Etsy order is closed
        key = stages.facts()["key"]
        self.assertEqual(stages.facts()["key"], key)                 # the same build of the view, the same facts
        core.write_json(records.SNAPSHOT, {**records.load_snapshot(), "syncedAt": "later"})
        self.assertNotEqual(stages.facts()["key"], key)              # a new sync: worked out again


class StateApi(unittest.TestCase):
    def setUp(self):
        self.p = porder("a" * 24, "Amelia", "Lewis", shop_order_id="1")
        self.other = porder("c" * 24, "Zed", "Q", created="2025-09-06 12:00:00+00:00")
        core.write_json(records.SNAPSHOT, {"receipts": [sync.normalize_receipt(receipt(1, "Amelia Lewis"))],
                                          "printify": [self.p, self.other], "gelato": []})

    def tearDown(self):
        for path in (records.SNAPSHOT, records.STATES, records.LINKS):
            path.unlink(missing_ok=True)

    def call(self, fn, body):
        return fn(SimpleNamespace(json=body))

    def test_replacement_cannot_reuse_a_primary_linked_by_hand(self):
        records.save(records.LINKS, {"1": {"provider": "printify", "orderId": "a" * 24}})
        with self.assertRaises(ApiError):
            self.call(profit._set_state, {"receiptId": "1", "status": "replacement",
                                          "replacementOrders": [{"provider": "printify", "orderId": "a" * 24}]})

    def test_a_primary_matching_found_may_be_ticked_as_the_reprint(self):
        """18.10.2026: two orders of one receipt, matching took the reprint — ticking it moves it to the replacement."""
        res = self.call(profit._set_state, {"receiptId": "1", "status": "replacement",
                                            "replacementOrders": [{"provider": "printify", "orderId": "a" * 24}]})
        self.assertEqual((res["row"]["state"], res["row"]["replacement_cost"]), ("replacement", 11.95))

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
