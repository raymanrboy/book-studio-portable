"""«Скасувати» for what goes to the Recycle Bin (06.10.2026): the shelf, putting back, and the Recycle Bin after it."""
import shutil
import time
import unittest
from unittest import mock

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import aside, core
from studio.server import ApiError


class Shelf(unittest.TestCase):
    def setUp(self):
        for folder in (aside.SHELF, core.data_path("recycle-bin"), core.data_path("aside-test")):
            shutil.rmtree(folder, ignore_errors=True)
        self.place = core.data_path("aside-test", "book")
        (self.place / "pictures").mkdir(parents=True)
        (self.place / "pictures" / "1.png").write_bytes(b"page")
        timer = mock.patch.object(aside.threading, "Timer")    # no flush half a minute after the test is over
        timer.start()
        self.addCleanup(timer.stop)

    def test_cancel_puts_it_back_whole(self):
        token = aside.put(self.place, "test book")
        self.assertFalse(self.place.exists())
        self.assertEqual(aside.flush(), 0)                                   # too soon for the Recycle Bin
        self.assertEqual(aside.restore(token), self.place)
        self.assertEqual((self.place / "pictures" / "1.png").read_bytes(), b"page")
        self.assertEqual(list(aside.SHELF.iterdir()), [])                     # the shelf's note went with it

    def test_after_its_minutes_it_goes_to_the_recycle_bin_and_cannot_be_cancelled(self):
        token = aside.put(self.place, "test book")
        with mock.patch.object(aside.time, "time", return_value=time.time() + aside.KEEP_SECONDS + 1):
            self.assertEqual(aside.flush(), 1)
        self.assertTrue(any(core.data_path("recycle-bin").glob("book*")))   # never deleted for good
        with self.assertRaises(ApiError) as caught:
            aside.restore(token)
        self.assertIn("Кошик", str(caught.exception))

    def test_never_over_something_that_stands_there_now(self):
        token = aside.put(self.place, "test book")
        self.place.mkdir()
        (self.place / "new.txt").write_text("new")
        with self.assertRaises(ApiError):
            aside.restore(token)
        self.assertEqual([p.name for p in self.place.iterdir()], ["new.txt"])
        aside.flush(0)                                                        # still goes on to the Recycle Bin

    def test_a_made_up_token_brings_back_nothing(self):
        for token in ("", "../../etc", "zzzzzzzzzzzz", "0123456789ab"):
            with self.subTest(token=token), self.assertRaises(ApiError):
                aside.restore(token)


if __name__ == "__main__":
    unittest.main()
