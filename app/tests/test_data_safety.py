"""What keeps the owner's data from being lost (04.10.2026): the history of every write, the daily snapshot, the guards on the send journal
and the snapshot, deletions to the Recycle Bin, tests that cannot reach the real data, and the tool that puts a version back."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import core, records

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import data_history  # noqa: E402


def versions_of(rel):
    folder = core.DATA_DIR / "history" / rel
    return sorted(folder.glob("*.json")) if folder.is_dir() else []


class History(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(core.DATA_DIR / "history", ignore_errors=True)
        shutil.rmtree(core.DATA_DIR / "profit", ignore_errors=True)
        self.addCleanup(shutil.rmtree, core.DATA_DIR / "history", True)
        self.addCleanup(shutil.rmtree, core.DATA_DIR / "profit", True)
        self.sends = core.DATA_DIR / "profit" / "print-orders.json"

    def test_a_write_keeps_the_file_as_it_was(self):
        core.write_json(self.sends, {"a": [1]})
        self.assertEqual(versions_of("profit/print-orders.json"), [])         # nothing to keep before the first write
        core.write_json(self.sends, {"a": [1], "b": [2]})
        kept = versions_of("profit/print-orders.json")
        self.assertEqual(len(kept), 1)
        self.assertEqual(json.loads(kept[0].read_text(encoding="utf-8")), {"a": [1]})

    def test_the_same_content_is_not_kept_twice_and_only_the_last_twenty_stay(self):
        core.write_json(self.sends, {"n": 0})
        for n in range(1, 30):
            core.write_json(self.sends, {"n": n})
            core.write_json(self.sends, {"n": n})                           # the same again: no new version
        self.assertEqual(len(versions_of("profit/print-orders.json")), core.HISTORY_KEEP)
        newest = json.loads(versions_of("profit/print-orders.json")[-1].read_text(encoding="utf-8"))
        self.assertEqual(newest, {"n": 29})                                  # the file as it was before the very last write

    def test_a_file_that_is_not_important_has_no_history(self):
        other = core.DATA_DIR / "cache" / "x.json"
        core.write_json(other, {"a": 1})
        core.write_json(other, {"a": 2})
        self.assertEqual(versions_of("cache/x.json"), [])

    def test_a_busy_file_is_kept_no_more_often_than_its_rule_says(self):
        settings = core.DATA_DIR / "settings.json"
        before = len(versions_of("settings.json"))
        core.write_json(settings, {"x": 1})
        core.write_json(settings, {"x": 2})
        core.write_json(settings, {"x": 3})
        self.assertLessEqual(len(versions_of("settings.json")) - before, 1)   # a burst of writes: one version, not three


class Guards(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(core.DATA_DIR / "profit", ignore_errors=True)         # another test may have left a journal here
        self.addCleanup(shutil.rmtree, core.DATA_DIR / "profit", True)
        self.addCleanup(shutil.rmtree, core.DATA_DIR / "history", True)

    def test_the_send_journal_is_only_added_to(self):
        records.save(records.SENDS, {"100": [{"orderId": "a"}], "200": [{"orderId": "b"}]})
        records.save(records.SENDS, {"100": [{"orderId": "a"}], "200": [{"orderId": "b"}], "300": [{"orderId": "c"}]})
        with self.assertRaises(records.DataGuard):
            records.save(records.SENDS, {"100": [{"orderId": "a"}]})            # two receipts would vanish
        with self.assertRaises(records.DataGuard):
            records.save(records.SENDS, {})                                    # the made-up replacement of 04.10.2026
        self.assertEqual(len(records.load_sends()), 3)

    def test_the_snapshot_does_not_shrink_to_a_fraction_of_itself(self):
        records.save(records.SNAPSHOT, {"receipts": [{"receipt_id": n} for n in range(100)]})
        records.save(records.SNAPSHOT, {"receipts": [{"receipt_id": n} for n in range(80)]})        # a few fewer: allowed
        with self.assertRaises(records.DataGuard):
            records.save(records.SNAPSHOT, {"receipts": [{"receipt_id": n} for n in range(8)]})
        self.assertEqual(len(records.load_snapshot().get("receipts")), 80)


class DailySnapshot(unittest.TestCase):
    def test_once_a_day_the_important_files_are_copied_and_old_days_go(self):
        data = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, data, True)
        (data / "profit").mkdir()
        (data / "profit" / "print-orders.json").write_text('{"a": 1}', encoding="utf-8")
        (data / "settings.json").write_text("{}", encoding="utf-8")
        (data / "cache").mkdir()
        (data / "cache" / "big.bin").write_bytes(b"x")
        old = data / "history" / "daily"
        for day in range(1, 20):
            (old / f"2026-09-{day:02d}").mkdir(parents=True)
        with mock.patch.object(core, "DATA_DIR", data), mock.patch.object(core, "SANDBOX", False), \
                mock.patch.object(core, "WORKSHOP_BOOKS", data / "no-books"):
            today = core.daily_snapshot()
            self.assertIsNotNone(today)
            self.assertTrue((today / "profit" / "print-orders.json").is_file())
            self.assertTrue((today / "settings.json").is_file())
            self.assertFalse((today / "cache").exists())                         # not what holds the owner's work
            self.assertIsNone(core.daily_snapshot())                             # today's exists
        self.assertEqual(len([p for p in old.iterdir() if p.is_dir()]), core.DAILY_KEEP)


class NotTheRealData(unittest.TestCase):
    def test_a_test_run_that_would_reach_the_real_data_is_refused(self):
        app = Path(__file__).resolve().parents[1]
        code = f"import unittest, sys; sys.path.insert(0, {str(app)!r}); import studio.core"
        env = {k: v for k, v in os.environ.items() if k not in ("BOOK_STUDIO_DATA", "BOOK_STUDIO_SANDBOX", "BOOK_STUDIO_SAMPLE")}
        run = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn(b"Tests must run on a data folder of their own", run.stderr)


class DeletedToTheBin(unittest.TestCase):
    def test_a_slide_set_goes_to_the_recycle_bin_not_away(self):
        from studio.slides import store
        set_id = "20260101-000000-abcdef"
        folder = store.set_dir(set_id)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "set.json").write_text("{}", encoding="utf-8")
        with mock.patch("studio.desktop.to_recycle_bin") as binned:
            store.delete_set(set_id)
        binned.assert_called_once_with(folder)
        shutil.rmtree(folder, ignore_errors=True)


class PuttingBack(unittest.TestCase):
    def setUp(self):
        self.data = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.data, True)
        self.rel = "profit/print-orders.json"
        (self.data / "profit").mkdir()
        hist = self.data / "history" / self.rel
        hist.mkdir(parents=True)
        (hist / "20261004-100000-001.json").write_text('{"v": 1}', encoding="utf-8")
        (hist / "20261004-110000-001.json").write_text('{"v": 2}', encoding="utf-8")
        (self.data / self.rel).write_text('{"v": "made-up"}', encoding="utf-8")

    def test_the_newest_version_comes_back_and_the_current_file_is_kept(self):
        data_history.restore(self.data, self.rel)
        self.assertEqual((self.data / self.rel).read_text(encoding="utf-8"), '{"v": 2}')
        aside = [p for p in (self.data / "history" / self.rel).glob("*-before-restore.json")]
        self.assertEqual([p.read_text(encoding="utf-8") for p in aside], ['{"v": "made-up"}'])

    def test_a_chosen_version_and_a_daily_snapshot_can_be_asked_for(self):
        data_history.restore(self.data, self.rel, version="20261004-100000-001")
        self.assertEqual((self.data / self.rel).read_text(encoding="utf-8"), '{"v": 1}')
        day = self.data / "history" / "daily" / "2026-10-03" / "profit"
        day.mkdir(parents=True)
        (day / "print-orders.json").write_text('{"v": "yesterday"}', encoding="utf-8")
        data_history.restore(self.data, self.rel, daily="2026-10-03")
        self.assertEqual((self.data / self.rel).read_text(encoding="utf-8"), '{"v": "yesterday"}')

    def test_what_is_not_there_is_said(self):
        with self.assertRaises(SystemExit):
            data_history.restore(self.data, "settings.json")
        with self.assertRaises(SystemExit):
            data_history.restore(self.data, self.rel, version="nope")


if __name__ == "__main__":
    unittest.main()
