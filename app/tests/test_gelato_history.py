"""The printer's history in an order's card: what is read from a full Gelato order, when it is asked for, and for which
orders — one order at a time, at the card's opening, never in bulk. All made up: no key, no network."""
import time
import unittest
from types import SimpleNamespace
from unittest import mock

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import gelato, orders, stages
from studio.vault import vault

FULL = {
    "fulfillmentStatus": "in_transit", "createdAt": "2026-09-28T10:00:00+00:00", "shippedAt": "2026-10-02T09:00:00+00:00",
    "items": [{"eventLog": [
        {"status": "created", "createdAt": "2026-09-28T10:00:05+00:00"},
        {"status": "in_production", "createdAt": "2026-09-30T08:00:00+00:00", "message": "Printing started"},
        {"status": "in_transit", "createdAt": "2026-10-03T12:00:00Z", "message": "in_transit"},
        {"status": "in_production", "createdAt": "2026-09-30T08:00:00+00:00", "message": "Printing started"},  # twice
    ]}],
    "shipment": {"shipmentMethodName": "USPS Ground Advantage", "minDeliveryDate": "2026-10-07", "maxDeliveryDate": "2026-10-09",
                 "packages": [{"trackingCode": "9200", "trackingUrl": "https://t.example/9200"}]},
}


class Reading(unittest.TestCase):
    def test_events_come_newest_first_without_repeats_and_with_what_the_log_lacks(self):
        got = gelato.history(FULL)
        self.assertEqual([(e["status"], e["text"]) for e in got["events"]],
                         [("in_transit", ""),               # a text that only repeats the status is dropped
                          ("shipped", ""),                  # not in the log: taken from the order's own `shippedAt`
                          ("in_production", "Printing started"),
                          ("created", "")])                 # the log has it: not added a second time from `createdAt`
        self.assertEqual(got["status"], "in_transit")
        self.assertEqual(got["due"], ["2026-10-07", "2026-10-09"])
        self.assertEqual(got["shipments"][0]["number"], "9200")

    def test_an_empty_log_still_has_the_orders_own_dates(self):
        got = gelato.history({"fulfillmentStatus": "draft", "createdAt": "2026-10-03T00:58:01+00:00",
                              "items": [{"eventLog": []}], "shipment": {"packages": []}})
        self.assertEqual([(e["status"], e["at"]) for e in got["events"]], [("created", "2026-10-03T00:58:01+00:00")])
        self.assertEqual((got["due"], got["shipments"]), ([], []))

    def test_odd_entries_do_not_break_it(self):
        got = gelato.history({"items": [{"eventLog": ["Label printed", {}, {"foo": "bar"}, None]}, {}, {"eventLog": None}]})
        self.assertEqual([e["text"] for e in got["events"]], ["Label printed", "None"])

    def test_the_shape_of_the_log_is_written_down_without_its_values(self):
        with mock.patch.object(gelato, "_audit_log") as log:
            gelato.history(FULL)
        line = log.return_value.info.call_args.args[1]
        self.assertIn("createdAt,message,status", line)
        self.assertNotIn("Printing started", line)


class Asking(unittest.TestCase):
    def setUp(self):
        gelato._history.clear()
        self.read = []

    def get_order(self, order_id, account="main"):
        self.read.append((order_id, account))
        return {**FULL, "fulfillmentStatus": self.status}

    status = "in_transit"

    def ask(self, **kw):
        with mock.patch.object(gelato, "get_order", self.get_order):
            return gelato.cached_history("g1", **kw)

    def test_a_read_is_kept_for_a_minute_and_a_button_asks_again(self):
        self.ask(account="old")
        self.ask()
        self.assertEqual(self.read, [("g1", "old")])
        self.ask(fresh=True)
        self.assertEqual(len(self.read), 2)
        gelato._history["g1"] = (time.monotonic() - gelato.HISTORY_FRESH - 1, gelato._history["g1"][1])
        self.ask()
        self.assertEqual(len(self.read), 3)

    def test_a_delivered_order_is_not_asked_about_again(self):
        self.status = "delivered"
        self.ask()
        gelato._history["g1"] = (time.monotonic() - 99999, gelato._history["g1"][1])
        self.ask()
        self.assertEqual(len(self.read), 1)

    def test_the_old_accounts_orders_are_read_with_the_old_key(self):
        vault.set(gelato.KEYS["main"], "made-up-main-key")
        vault.set(gelato.KEYS["old"], "made-up-old-key")
        try:
            self.assertEqual(gelato.slot_of({"account": gelato.account_id("made-up-old-key")}), "old")
            self.assertEqual(gelato.slot_of({"account": gelato.account_id("made-up-main-key")}), "main")
            vault.set(gelato.KEYS["old"], None)
            self.assertEqual(gelato.slot_of({"account": "whatever"}), "main")
        finally:
            vault.set(gelato.KEYS["main"], None)
            vault.set(gelato.KEYS["old"], None)


class Route(unittest.TestCase):
    """GET /api/orders/<receipt>/history: only a placed Gelato order is asked about."""

    def call(self, stage, provider, fresh=False):
        placed = {"stage": stage, "order": {"provider": provider, "id": "g1", "order": {"account": None}}}
        req = SimpleNamespace(groups=("4100000102",), param=lambda name, default=None: "1" if fresh and name == "fresh" else default)
        with mock.patch.object(stages, "facts", return_value={"receipts": {"4100000102": placed}}), \
             mock.patch.object(gelato, "cached_history", return_value={"status": "in_transit", "events": []}) as asked:
            return orders._history(req), asked

    def test_a_placed_gelato_order_is_read(self):
        got, asked = self.call("sent", "gelato")
        self.assertEqual(got, {"available": True, "status": "in_transit", "events": []})
        asked.assert_called_once_with("g1", "main", fresh=False)
        self.call("work", "gelato", fresh=True)[1].assert_called_once_with("g1", "main", fresh=True)

    def test_nothing_is_asked_for_a_new_order_or_a_printify_one(self):
        for stage, provider in (("new", "gelato"), ("closed", "gelato"), ("sent", "printify")):
            with self.subTest(stage=stage, provider=provider):
                got, asked = self.call(stage, provider)
                self.assertEqual(got, {"available": False})
                asked.assert_not_called()

    def test_an_unknown_receipt_is_not_an_error(self):
        req = SimpleNamespace(groups=("4100000999",), param=lambda name, default=None: default)
        with mock.patch.object(stages, "facts", return_value={"receipts": {}}):
            self.assertEqual(orders._history(req), {"available": False})


if __name__ == "__main__":
    unittest.main()
