"""The owner's own rules as settings, so a copy for someone else can switch them off: «Etsy only from the Kyiv computer»
(`security.etsyKyivOnly`) and «Printify is read-only from 1 October 2026» (`printify.readOnlyFrom`)."""
import unittest
from types import SimpleNamespace
from unittest import mock

from tests import __init__  # noqa: F401  (a test file run alone still gets the made-up data folder)
from studio import core, settings_api
from studio.server import ApiError


def open_url(url):
    return settings_api._open_url(SimpleNamespace(json={"url": url}))


class KyivRule(unittest.TestCase):
    def setUp(self):
        self.before = core.settings.section("security")
        self.addCleanup(core.settings.replace_section, "security", self.before)

    def test_on_by_default(self):
        core.settings.drop_section("security")
        self.assertTrue(core.etsy_kyiv_only())
        with mock.patch("webbrowser.open") as opened, self.assertRaises(ApiError):
            open_url("https://www.etsy.com/listing/1")
        opened.assert_not_called()

    def test_the_rule_is_not_fooled_by_a_dot_at_the_end_or_the_short_links(self):
        core.settings.drop_section("security")
        for url in ("https://www.etsy.com./listing/1", "https://ETSY.COM/x", "https://etsy.me/abc", "https://shop.etsy.me./abc"):
            with mock.patch("webbrowser.open") as opened, self.assertRaises(ApiError, msg=url):
                open_url(url)
            opened.assert_not_called()
        with mock.patch("webbrowser.open") as opened:
            open_url("https://notetsy.com/")                      # a different site is not Etsy
        opened.assert_called_once()

    def test_off_etsy_opens_like_any_site(self):
        core.settings.replace_section("security", {"etsyKyivOnly": False})
        self.assertFalse(core.etsy_kyiv_only())
        with mock.patch("webbrowser.open") as opened:
            open_url("https://www.etsy.com/your/orders/sold")
            open_url("https://www.etsy.com/oauth/connect?response_type=code")
        self.assertEqual(opened.call_count, 2)

    def test_the_settings_page_gets_the_rule(self):
        core.settings.replace_section("security", {"etsyKyivOnly": False})
        self.assertEqual(settings_api._settings(SimpleNamespace(json={}))["security"], {"etsyKyivOnly": False})

    def test_the_first_run_note_about_kyiv_goes_with_the_rule(self):
        from studio import portable
        for rule, said in ((True, True), (False, False)):
            core.settings.replace_section("security", {"etsyKyivOnly": rule})
            with mock.patch.object(portable, "root", return_value=object()), \
                    mock.patch.object(core, "write_json"), mock.patch.object(core, "read_json", return_value={}):
                notes = portable.first_run_notes()
            self.assertEqual(any("київськ" in n for n in notes), said)



class PrintifyDay(unittest.TestCase):
    """The day Printify turns read-only is the owner's; a copy for someone who still prints on Printify switches it off."""

    def setUp(self):
        from studio import printify
        self.printify = printify
        self.before = core.settings.section("printify")
        self.addCleanup(core.settings.replace_section, "printify", self.before)

    def set(self, value):
        cfg = core.settings.section("printify")
        cfg["readOnlyFrom"] = value
        core.settings.replace_section("printify", cfg)

    def test_a_date_in_the_settings_is_the_day(self):
        from datetime import date
        self.set("2026-10-01")
        self.assertFalse(self.printify.retired(date(2026, 9, 30)))
        self.assertTrue(self.printify.retired(date(2026, 10, 1)))

    def test_null_means_never(self):
        from datetime import date
        self.set(None)
        self.assertIsNone(self.printify.read_only_from())
        self.assertFalse(self.printify.retired(date(2099, 1, 1)))

    def test_a_broken_value_falls_back_to_the_owners_day(self):
        self.set("not a date")
        self.assertEqual(self.printify.read_only_from(), self.printify.READ_ONLY_FROM)


if __name__ == "__main__":
    unittest.main()
