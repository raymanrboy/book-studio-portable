"""The speed-ups of 2026-10-05: Edge's leftovers trimmed, the sync's parts side by side, the wiki check's word set."""
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import desktop, etsy, gelato, sync
from studio.server import ApiError


class EdgeProfile(unittest.TestCase):
    def make(self, tmp: str, locked: bool) -> Path:
        profile = Path(tmp)
        for name in (*desktop._EDGE_JUNK, "Default"):
            (profile / name).mkdir()
            (profile / name / "x.bin").write_bytes(b"x")
        if locked:
            (profile / "lockfile").write_bytes(b"")
        return profile

    def test_what_edge_stored_for_itself_goes_when_no_window_holds_the_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = self.make(tmp, locked=False)
            self.assertEqual(desktop.trim_profile(profile), len(desktop._EDGE_JUNK))
            self.assertFalse(any((profile / n).exists() for n in desktop._EDGE_JUNK))
            self.assertTrue((profile / "Default" / "x.bin").exists())      # the window's own cache stays

    def test_a_profile_in_use_is_left_alone(self):
        with tempfile.TemporaryDirectory() as tmp:
            profile = self.make(tmp, locked=True)
            self.assertEqual(desktop.trim_profile(profile), 0)
            self.assertTrue((profile / desktop._EDGE_JUNK[0]).exists())


class SideBySide(unittest.TestCase):
    def test_the_bar_only_moves_forward(self):
        job = mock.Mock()
        seen = []
        job.progress = lambda step=None, percent=None, detail=None: seen.append(percent)
        together = sync._Together(job)
        for p in (5, 48, 20, 78, 46):
            together.progress("s", p)
        self.assertEqual(seen, [5, 48, 48, 78, 78])

    def _run(self, etsy_error=None):
        calls = []
        gate = threading.Barrier(2, timeout=5)

        def etsy_part(job, snap, warnings, full):
            gate.wait()                     # returns only when the Gelato part is running at the same time
            calls.append("etsy")
            if etsy_error:
                raise etsy_error
            snap["receipts"] = []
            return 0

        def gelato_part(job, snap, warnings):
            gate.wait()
            calls.append("gelato")

        job = mock.Mock()
        with mock.patch.object(etsy, "tokens", return_value={"shop_id": 1}), \
                mock.patch.object(sync, "_etsy_part", etsy_part), mock.patch.object(sync, "_gelato_part", gelato_part), \
                mock.patch.object(sync.ledger, "refresh"), mock.patch.object(gelato, "accounts", return_value=[("main", "a")]), \
                mock.patch.object(sync.vault, "get", return_value=None), mock.patch.object(sync.records, "save"), \
                mock.patch.object(sync.archive, "refresh_quietly"), \
                mock.patch.object(sync.profit, "cached_view", return_value={"full": {}}):
            result = sync._sync(job)
        return calls, result

    def test_etsy_and_gelato_are_read_at_the_same_time(self):
        calls, result = self._run()
        self.assertEqual(sorted(calls), ["etsy", "gelato"])
        self.assertEqual(result["warnings"], [])

    def test_an_etsy_failure_still_fails_the_sync_after_the_others_are_through(self):
        with self.assertRaises(ApiError):
            self._run(etsy_error=ApiError("Etsy не відповідає"))


if __name__ == "__main__":
    unittest.main()
