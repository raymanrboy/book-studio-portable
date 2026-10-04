"""The model read in quietly after the program starts (textcheck.run.prime)."""
import unittest
from unittest import mock

from tests import __init__  # noqa: F401  (sets a temporary data folder)
from studio import core, modules
from studio.textcheck import ollama, run


class Prime(unittest.TestCase):
    def setUp(self):
        core.settings.update({"textcheck": {"enabled": True}})
        self.addCleanup(core.settings.update, {"textcheck": {"enabled": True}})

    def test_the_model_is_read_and_let_go_at_once(self):
        with mock.patch.object(ollama, "_ready") as ready, mock.patch.object(ollama, "_release_model") as release:
            run.prime(delay=0)
        ready.assert_called_once()
        release.assert_called_once()

    def test_nothing_happens_when_the_check_is_off(self):
        core.settings.update({"textcheck": {"enabled": False}})
        with mock.patch.object(ollama, "_ready") as ready:
            run.prime(delay=0)
        ready.assert_not_called()

    def test_nothing_happens_when_the_module_is_not_installed(self):
        with mock.patch("studio.portable.root", return_value="x"), mock.patch.object(modules, "installed", return_value=False), \
                mock.patch.object(ollama, "_ready") as ready:
            run.prime(delay=0)
        ready.assert_not_called()

    def test_a_failure_is_swallowed(self):
        with mock.patch.object(ollama, "_ready", side_effect=ollama.ModelError("no")):
            run.prime(delay=0)            # must not raise


if __name__ == "__main__":
    unittest.main()
