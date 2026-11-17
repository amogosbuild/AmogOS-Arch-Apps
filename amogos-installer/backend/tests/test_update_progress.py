# Verify online and offline update milestones and single-worker initramfs generation.
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from amogos_install.installer import Installer
from amogos_install.kernels import prepare_kernels
from amogos_install.runtime import InstallError


class UpdateProgressTests(unittest.TestCase):
    def installer(self, desktop="plasma", upgrade=False):
        reporter = Mock()
        installer = Installer(dict(desktop=desktop, upgrade=upgrade), {}, reporter)
        installer.target = Path("/test-target")
        installer.runner = Mock()
        installer.runner.stream.side_effect = lambda arguments, callback: callback("upgrading example")
        return installer

    def test_online_updates_match_the_ui_stage_before_boot(self):
        installer = self.installer(upgrade=True)
        installer._packages()
        calls = installer.report.emit.call_args_list
        self.assertEqual([call.args[0] for call in calls], ["drivers", "updates", "updates", "updates"])
        self.assertEqual([call.args[1] for call in calls], [.69, .72, .77, .83])
        self.assertEqual(calls[-1].args[2], "Arch packages are up to date")
        self.assertIn("-Syu", installer.runner.stream.call_args.args[0])
        self.assertFalse(any(call.kwargs.get("skipped") for call in calls))

    def test_offline_plasma_explicitly_skips_updates(self):
        installer = self.installer()
        installer._packages()
        installer.runner.stream.assert_not_called()
        skipped = installer.report.emit.call_args_list[-1]
        self.assertEqual(skipped.args[:2], ("updates", .83))
        self.assertTrue(skipped.kwargs["skipped"])
        installer.runner.run.assert_called_once()

    def test_alternative_desktop_runs_full_updates_even_without_upgrade_option(self):
        installer = self.installer(desktop="gnome")
        installer._packages()
        command = installer.runner.stream.call_args.args[0]
        self.assertIn("-Syu", command)
        self.assertIn("gnome-shell", command)
        self.assertEqual(installer.report.emit.call_args.args[2], "Arch packages are up to date")

    def test_failed_updates_are_not_reported_as_complete(self):
        installer = self.installer(upgrade=True)
        installer.runner.stream.side_effect = InstallError("repository unavailable")
        with self.assertRaisesRegex(InstallError, "repository unavailable"):
            installer._packages()
        self.assertFalse(any(call.args[1] == .83 for call in installer.report.emit.call_args_list))

    def test_initramfs_uses_one_compression_worker_and_preserves_the_kernel(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)
            (target / "boot").mkdir()
            kernel = target / "boot/vmlinuz-linux-zen"
            kernel.write_bytes(b"kernel")
            (target / "etc/mkinitcpio.conf.d").mkdir(parents=True)
            runner = Mock()
            prepare_kernels(runner, target)
            config = (target / "etc/mkinitcpio.conf.d/10-amogos.conf").read_text()
            self.assertIn('COMPRESSION="zstd"', config)
            self.assertIn("COMPRESSION_OPTIONS=(-T1 -3)", config)
            self.assertIn("plymouth", config)
            self.assertEqual(kernel.read_bytes(), b"kernel")
            runner.run.assert_called_once_with(
                ["chroot", str(target), "mkinitcpio", "-p", "linux-zen"], timeout=1800,
            )


if __name__ == "__main__":
    unittest.main()
