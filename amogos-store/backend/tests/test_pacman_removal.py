# Verify reviewed recursive removals, protected dependencies and execution revalidation.
import contextlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from amogos_store import pacman_transactions as transactions, runtime


class RemovalReviewTests(unittest.TestCase):
    def test_full_review_lists_dependencies_and_changes_fingerprint(self):
        local = {"demo": "1", "unused": "2"}
        with patch.object(transactions.pacman_catalog, "installed", return_value=local), patch.object(transactions, "run", return_value=SimpleNamespace(stdout="demo\n")):
            regular = transactions.resolve(dict(id="demo", operation="remove"))
        with patch.object(transactions.pacman_catalog, "installed", return_value=local), patch.object(transactions, "run", return_value=SimpleNamespace(stdout="unused\ndemo\n")):
            full = transactions.resolve(dict(id="demo", operation="remove", fullUninstall=True))
        self.assertNotEqual(regular["fingerprint"], full["fingerprint"])
        self.assertEqual([item["id"] for item in full["changes"]], ["demo", "unused"])
        self.assertTrue(full["changes"][1]["automatic"])
        self.assertTrue(full["fullUninstall"])
        self.assertIn("home folder", full["note"])

    def test_protected_transitive_dependency_and_invalid_option_are_rejected(self):
        with patch.object(transactions.pacman_catalog, "installed", return_value={"demo": "1", "glibc": "1"}), patch.object(transactions, "run", return_value=SimpleNamespace(stdout="demo\nglibc\n")):
            with self.assertRaisesRegex(runtime.StoreError, "required"):
                transactions.resolve(dict(id="demo", operation="remove", fullUninstall=True))
        for value in ("true", 1, None):
            with self.assertRaisesRegex(runtime.StoreError, "Invalid full uninstall"):
                transactions.resolve(dict(id="demo", operation="remove", fullUninstall=value))

    def test_changed_dependency_list_prevents_execution(self):
        original = dict(source="pacman", operation="remove", id="demo", fullUninstall=True, fingerprint="previous")
        with patch.object(transactions, "transaction_lock", contextlib.nullcontext), patch.object(transactions, "consume_plan", return_value=original), patch.object(transactions, "resolve", return_value={**original, "fingerprint": "changed"}), patch.object(transactions, "stream") as stream:
            with self.assertRaisesRegex(runtime.StoreError, "dependencies changed"):
                transactions.apply(dict(token="review"))
        stream.assert_not_called()


@unittest.skipUnless(shutil.which("pacman") and os.geteuid() == 0, "Native Arch Pacman as root required")
class NativeRemovalTests(unittest.TestCase):
    def test_regular_and_full_removal_preserve_shared_and_explicit_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            root = stage / "root"
            (root / "var/lib/pacman").mkdir(parents=True)
            config = stage / "pacman.conf"
            config.write_text("[options]\nArchitecture = auto\nSigLevel = Never\n")
            prefix = ["pacman", "--root", str(root), "--config", str(config)]
            def native(command):
                result = subprocess.run(prefix + command[1:], capture_output=True, text=True, check=False)
                if result.returncode:
                    raise AssertionError(result.stdout + result.stderr)
                return result
            def package(name, dependencies=(), backup=False):
                path = stage / (name + ".pkg.tar")
                metadata = f"pkgname = {name}\npkgver = 1.0-1\npkgdesc = Removal fixture\narch = any\nsize = 16\n"
                metadata += "".join(f"depend = {item}\n" for item in dependencies)
                if backup:
                    metadata += "backup = etc/amogos-removal-test.conf\n"
                with tarfile.open(path, "w") as archive:
                    content = metadata.encode()
                    entry = tarfile.TarInfo(".PKGINFO")
                    entry.size = len(content)
                    archive.addfile(entry, io.BytesIO(content))
                    content = b"original setting\n"
                    entry = tarfile.TarInfo("etc/amogos-removal-test.conf" if backup else "usr/share/amogos-removal-test/" + name)
                    entry.size = len(content)
                    entry.mode = 0o644
                    archive.addfile(entry, io.BytesIO(content))
                return str(path)
            unused, shared, explicit = ("amogos-test-unused", "amogos-test-shared", "amogos-test-explicit")
            target, retainer = "amogos-test-target", "amogos-test-retainer"
            dependencies = [package(name) for name in (unused, shared, explicit)]
            app = package(target, (unused, shared, explicit), backup=True)
            keeper = package(retainer, (shared,))
            native(["pacman", "-U", "--noconfirm", "--asdeps", *dependencies])
            native(["pacman", "-D", "--asexplicit", explicit])
            native(["pacman", "-U", "--noconfirm", app, keeper])
            def installed():
                return dict(line.split(maxsplit=1) for line in native(["pacman", "-Q"]).stdout.splitlines())
            def execute(command):
                return native(command)
            config_file = root / "etc/amogos-removal-test.conf"
            saved = config_file.with_suffix(".conf.pacsave")
            with patch.object(transactions, "run", native), patch.object(transactions, "stream", execute), patch.object(transactions.pacman_catalog, "installed", installed), patch.object(transactions, "transaction_lock", contextlib.nullcontext), patch.object(runtime, "PLAN_DIRECTORY", stage / "plans"), patch.object(runtime, "require_root"), contextlib.redirect_stdout(io.StringIO()):
                config_file.write_text("personal setting\n")
                review = transactions.plan(dict(id=target, operation="remove"))
                self.assertEqual([item["id"] for item in review["changes"]], [target])
                transactions.apply(dict(token=review["token"]))
                self.assertIn(unused, installed())
                self.assertTrue(saved.exists())
                native(["pacman", "-U", "--noconfirm", app])
                saved.unlink()
                config_file.write_text("personal setting again\n")
                review = transactions.plan(dict(id=target, operation="remove", fullUninstall=True))
                self.assertEqual({item["id"] for item in review["changes"]}, {target, unused})
                self.assertIn("-Rns", review["command"])
                new_consumer = package("amogos-test-new-consumer", (unused,))
                native(["pacman", "-U", "--noconfirm", new_consumer])
                with self.assertRaisesRegex(runtime.StoreError, "dependencies changed"):
                    transactions.apply(dict(token=review["token"]))
                self.assertIn(target, installed())
                native(["pacman", "-R", "--noconfirm", "amogos-test-new-consumer"])
                review = transactions.plan(dict(id=target, operation="remove", fullUninstall=True))
                transactions.apply(dict(token=review["token"]))
                remaining = installed()
                self.assertNotIn(target, remaining)
                self.assertNotIn(unused, remaining)
                self.assertTrue({shared, explicit, retainer}.issubset(remaining))
                self.assertFalse(config_file.exists())
                self.assertFalse(saved.exists())


if __name__ == "__main__":
    unittest.main()
