# Exercise graceful exit, lingering-process cleanup and account identity safeguards.
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from session_cleanup import stop_temporary_session


class SessionCleanupTests(unittest.TestCase):
    def simulate(self, lingering=False, stuck=False):
        calls = []
        killed = False
        def run(command, **options):
            nonlocal killed
            calls.append(command)
            if command[0] == "pkill":
                killed = True
            return SimpleNamespace(returncode=0 if command[0] != "pgrep" or stuck or (lingering and not killed) else 1)
        return calls, run

    def test_graceful_exit_does_not_force_kill(self):
        calls, run = self.simulate()
        stop_temporary_session(1500, run=run, sleep=lambda delay: None)
        self.assertFalse(any(command[0] == "pkill" for command in calls))

    def test_lingering_process_is_stopped_for_only_the_temporary_uid(self):
        calls, run = self.simulate(lingering=True)
        stop_temporary_session(1500, run=run, sleep=lambda delay: None)
        self.assertIn(["pkill", "-KILL", "-u", "1500"], calls)

    def test_stuck_process_prevents_account_deletion(self):
        calls, run = self.simulate(stuck=True)
        with self.assertRaisesRegex(RuntimeError, "still busy"):
            stop_temporary_session(1500, run=run, sleep=lambda delay: None)

    def test_root_and_invalid_identities_are_rejected(self):
        for uid in (0, -1, "1500", True):
            with self.assertRaises(ValueError):
                stop_temporary_session(uid, run=lambda *args, **kwargs: self.fail("An invalid account was touched"))


if __name__ == "__main__":
    unittest.main()
