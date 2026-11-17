# Verify migrations preserve personal settings and allow later performance opt-ins.
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "rootfs/usr/lib/amogos-arch"))
from plasma_defaults import apply_plasma_defaults


@unittest.skipUnless(shutil.which("kwriteconfig6"), "Plasma configuration tools required")
class PlasmaDefaultsTest(unittest.TestCase):
    def run_command(self, *args):
        return subprocess.run(args, check=False, capture_output=True).returncode == 0

    def read(self, root, file, group, key):
        return subprocess.check_output(["kreadconfig6", "--file", str(root / file),
                                        "--group", group, "--key", key], text=True).strip()

    def test_existing_theme_and_later_opt_in_survive(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / "kdeglobals").write_text("[General]\nColorScheme=BreezeLight\n")
            (root / "kwinrc").write_text("[Desktops]\nNumber=4\n[Plugins]\nblurEnabled=true\n")
            self.assertTrue(apply_plasma_defaults(root, self.run_command))
            self.assertEqual(self.read(root, "kdeglobals", "General", "ColorScheme"), "BreezeLight")
            self.assertEqual(self.read(root, "kwinrc", "Desktops", "Number"), "4")
            self.assertEqual(self.read(root, "kwinrc", "Plugins", "blurEnabled"), "false")
            self.assertEqual(self.read(root, "baloofilerc", "Basic Settings", "Indexing-Enabled"), "false")
            self.run_command("kwriteconfig6", "--file", str(root / "kwinrc"),
                             "--group", "Plugins", "--key", "blurEnabled", "true")
            self.assertTrue(apply_plasma_defaults(root, self.run_command))
            self.assertEqual(self.read(root, "kwinrc", "Plugins", "blurEnabled"), "true")

    def test_failed_migration_can_be_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            self.assertFalse(apply_plasma_defaults(root, lambda *args: False))
            self.assertFalse((root / "amogos-arch/plasma-performance-v1").exists())
            self.assertFalse(apply_plasma_defaults(root, Mock(side_effect=FileNotFoundError())))
            self.assertTrue(apply_plasma_defaults(root, self.run_command))


if __name__ == "__main__":
    unittest.main()
