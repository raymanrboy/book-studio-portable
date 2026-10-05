"""When the program decides the window is closed (main.run_until_closed): a covered or handed-over window is not a closed one."""
import unittest
from unittest import mock

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import main, server


class FakeClock:
    def __init__(self, on_second=None):
        self.now = 1000.0
        self.on_second = on_second

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds
        if self.on_second:
            self.on_second(self.now)


class FakeProc:
    def __init__(self, dies_at=None, clock=None):
        self.dies_at, self.clock = dies_at, clock

    def poll(self):
        return None if self.dies_at is None or self.clock.now < self.dies_at else 0


class Closing(unittest.TestCase):
    def run_loop(self, proc, clock, busy=lambda: False):
        server.state.last_heartbeat = 0.0
        server.state.bye_at = 0.0
        with mock.patch.object(main, "time", clock):
            main.run_until_closed(proc, busy)
        return clock.now - 1000.0

    def test_a_window_that_was_running_and_ended_is_closed_after_a_short_wait(self):
        clock = FakeClock()
        took = self.run_loop(FakeProc(dies_at=1005.0, clock=clock), clock)
        self.assertTrue(12 <= took <= 15, took)

    def test_a_window_handed_to_another_edge_process_is_not_taken_for_closed_while_the_page_pings(self):
        clock = FakeClock()
        last_ping = 1000.0 + 600

        def pings(now):
            if now < last_ping and int(now) % 20 == 0:
                server.state.last_heartbeat = now
        proc = FakeProc(dies_at=0.0, clock=clock)              # ended at once: the window lives in another process
        server.state.last_heartbeat = 0.0
        server.state.bye_at = 0.0
        clock.on_second = pings
        with mock.patch.object(main, "time", clock):
            main.run_until_closed(proc, lambda: False)
        took = clock.now - 1000.0
        self.assertGreaterEqual(took, 600, "closed while the page was still pinging")
        self.assertLessEqual(took, 600 + main.SILENCE + 25)

    def test_a_window_edge_holds_stays_open_though_its_page_is_silent(self):
        """04.10.2026: the started process ended at once (Edge took the window), the page stopped pinging for 90 s, and the program
        closed under the open window. Edge's profile in use is the window open; when Edge lets it go, the program closes."""
        clock = FakeClock()
        proc = FakeProc(dies_at=0.0, clock=clock)
        with mock.patch.object(main, "_profile_open", side_effect=lambda: clock.now < 1000.0 + 900):
            took = self.run_loop(proc, clock)
        self.assertGreaterEqual(took, 900, "closed while Edge still had the window")
        self.assertLessEqual(took, 900 + main.GRACE + 2)

    def test_edge_running_without_a_page_for_half_an_hour_is_a_closed_window(self):
        clock = FakeClock()
        with mock.patch.object(main, "_profile_open", return_value=True):
            took = self.run_loop(FakeProc(dies_at=0.0, clock=clock), clock)
        self.assertTrue(main.LOST <= took <= main.LOST + 2, took)

    def test_a_goodbye_from_a_page_is_not_a_closed_window_while_the_window_process_runs(self):
        clock = FakeClock()
        server.state.last_heartbeat = 0.0
        # the page says goodbye at 10 s and never pings again, but the process lives until 200 s
        def bye(now):
            if now == 1010.0:
                server.state.bye_at = now
        clock.on_second = bye
        proc = FakeProc(dies_at=1200.0, clock=clock)
        with mock.patch.object(main, "time", clock):
            main.run_until_closed(proc, lambda: False)
        self.assertGreaterEqual(clock.now - 1000.0, 200)


if __name__ == "__main__":
    unittest.main()
