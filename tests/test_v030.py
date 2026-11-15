import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import of_cli
from chimpi_features import NFCWallet, rounded_square
from of_cli import _verify, parse_command, parse_macos_version, validate_macos_environment


class FeatureTests(unittest.TestCase):
    def test_rounded_ui_corner_is_watertight(self):
        mesh = rounded_square()
        self.assertTrue(mesh.is_watertight)
        self.assertGreater(len(mesh.vertices), 20)
        self.assertAlmostEqual(mesh.extents[0], 2.0, places=4)
        self.assertAlmostEqual(mesh.extents[1], 2.0, places=4)

    def test_corner_rejects_invalid_radius(self):
        with self.assertRaises(ValueError):
            rounded_square(radius=-1)

    def test_redeem_nfc300_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nfc.json"
            wallet = NFCWallet(path)
            self.assertTrue(wallet.redeem("nfc300"))
            self.assertEqual(wallet.balance, 300)
            self.assertFalse(wallet.redeem("NFC300"))
            self.assertEqual(NFCWallet(path).balance, 300)
            identifier = wallet.issue()
            self.assertTrue(identifier.startswith("CHIMPI-NFC-"))
            self.assertEqual(wallet.balance, 299)
            self.assertTrue(wallet.return_tag(identifier))
            self.assertFalse(wallet.return_tag(identifier))
            self.assertEqual(wallet.balance, 300)

    def test_windows_command(self):
        cmd = parse_command("my pc --os Windows --os-version 11-NT install Chimpi3D".split())
        self.assertEqual(cmd["--os"], "Windows")
        self.assertEqual(cmd["--os-version"], "11-NT")

    def test_macos_command(self):
        cmd = parse_command("my pc --os macOS --os-version 27-GoldenGate install Chimpi3D --original".split())
        self.assertTrue(cmd["original"])

    def test_macos_12_to_27(self):
        examples = {
            12: "12-Monterey", 13: "13-Ventura", 14: "14-Sonoma",
            15: "15-Sequoia", 26: "26-Tahoe", 27: "27-GoldenGate",
        }
        for number, label in examples.items():
            self.assertEqual(parse_macos_version(label), number)
            arch = "arm64" if number == 27 else "x86_64"
            self.assertEqual(validate_macos_environment(label, str(number) + ".0", arch), number)

    def test_wrong_macos_names_or_installed_version(self):
        for label in ("28-GoldenGate", "27-Tahoe", "11-BigSur"):
            with self.assertRaises(ValueError):
                parse_macos_version(label)
        with self.assertRaises(ValueError):
            validate_macos_environment("27-GoldenGate", "12.7.6", "arm64")
        with self.assertRaises(ValueError):
            validate_macos_environment("27-GoldenGate", "27.0", "x86_64")

    def test_linux_mint_command(self):
        cmd = parse_command("my pc --os Linux --edition Linux Mint install Chimpi3D".split())
        self.assertEqual(cmd["--edition"], "Linux Mint")

    def test_checksum_rejects_tampering(self):
        import hashlib
        payload = b"chimpi"
        digest = hashlib.sha256(payload).hexdigest()
        _verify(digest + "  Chimpi3D.exe\n", "Chimpi3D.exe", digest)
        with self.assertRaises(ValueError):
            _verify(digest + "  Chimpi3D.exe\n", "Chimpi3D.exe", "a" * 64)


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.home.mkdir()
        self.home_patch = patch.object(Path, "home", return_value=self.home)
        self.home_patch.start()
        self.addCleanup(self.home_patch.stop)

    def destination(self, system):
        if system == "linux":
            return self.home / ".local" / "share" / "Chimpi3D"
        return self.home / "Applications" / "Chimpi3D.app"

    def install(self, system, version="new"):
        location = self.root / ("extract-" + system)
        if location.exists():
            shutil.rmtree(location)
        launcher = b"#!/bin/sh\necho new-of\n"
        if system == "linux":
            archive = self.root / "linux.tar.gz"
            with tarfile.open(archive, "w:gz") as package:
                for name, content in (("Chimpi3D", version.encode()), ("of", launcher)):
                    entry = tarfile.TarInfo("Chimpi3D/" + name)
                    entry.mode = 0o755
                    entry.size = len(content)
                    package.addfile(entry, io.BytesIO(content))
            of_cli._install_linux(archive, location)
        else:
            def extract(*_args, **_kwargs):
                app = location / "package" / "Chimpi3D.app" / "Contents" / "MacOS"
                app.mkdir(parents=True)
                (app / "Chimpi3D").write_text(version, encoding="utf-8")
                (location / "package" / "of").write_bytes(launcher)
            with patch("of_cli.subprocess.run", side_effect=extract):
                of_cli._install_macos(self.root / "macos.zip", location)

    def test_install_and_upgrade_keep_application_and_launchers(self):
        for system in ("linux", "macos"):
            with self.subTest(system=system):
                self.install(system, "first")
                self.install(system, "second")
                app = self.destination(system)
                binary = app / ("Chimpi3D" if system == "linux" else "Contents/MacOS/Chimpi3D")
                self.assertEqual(binary.read_text(encoding="utf-8"), "second")
                self.assertEqual((self.home / ".local/bin/of").read_bytes(), b"#!/bin/sh\necho new-of\n")

    @staticmethod
    def fail_copy(_source, destination, **_kwargs):
        Path(destination).mkdir(parents=True)
        (Path(destination) / "partial").write_text("incomplete", encoding="utf-8")
        raise OSError("simulated copy failure")

    def test_copy_failure_preserves_existing_installations(self):
        for system in ("linux", "macos"):
            with self.subTest(system=system):
                destination = self.destination(system)
                destination.mkdir(parents=True)
                (destination / "old-version").write_text("keep", encoding="utf-8")
                with patch("of_cli.shutil.copytree", side_effect=self.fail_copy):
                    with self.assertRaises(OSError):
                        self.install(system)
                self.assertEqual((destination / "old-version").read_text(encoding="utf-8"), "keep")
                self.assertFalse((destination / "partial").exists())

    def test_failed_fresh_copy_leaves_no_partial_installation(self):
        for system in ("linux", "macos"):
            with self.subTest(system=system):
                with patch("of_cli.shutil.copytree", side_effect=self.fail_copy):
                    with self.assertRaises(OSError):
                        self.install(system)
                self.assertFalse(self.destination(system).exists())

    def test_activation_failure_restores_previous_installation(self):
        real_rename = Path.rename
        for system in ("linux", "macos"):
            with self.subTest(system=system):
                destination = self.destination(system)
                destination.mkdir(parents=True)
                (destination / "old-version").write_text("keep", encoding="utf-8")
                failed = False
                def fail_once(source, target):
                    nonlocal failed
                    if Path(target) == destination and not failed:
                        failed = True
                        raise OSError("simulated activation failure")
                    return real_rename(source, target)
                with patch.object(Path, "rename", fail_once):
                    with self.assertRaises(OSError):
                        self.install(system)
                self.assertEqual((destination / "old-version").read_text(encoding="utf-8"), "keep")

    def test_failed_restore_keeps_previous_backup_outside_temporary_directory(self):
        destination = self.destination("linux")
        destination.mkdir(parents=True)
        (destination / "old-version").write_text("keep", encoding="utf-8")
        real_rename = Path.rename
        def fail_activation_and_restore(source, target):
            if Path(target) == destination:
                raise OSError("simulated destination failure")
            return real_rename(source, target)
        with patch.object(Path, "rename", fail_activation_and_restore):
            with self.assertRaisesRegex(RuntimeError, "preservada"):
                self.install("linux")
        backups = list(destination.parent.glob(".Chimpi3D.backup-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / "old-version").read_text(encoding="utf-8"), "keep")

    @unittest.skipUnless(sys.platform.startswith("linux") and shutil.which("sleep"),
                         "Requer executável Linux para reproduzir ETXTBSY")
    def test_running_linux_of_can_be_updated(self):
        running = self.home / ".local" / "bin" / "of"
        running.parent.mkdir(parents=True)
        shutil.copy2(shutil.which("sleep"), running)
        process = subprocess.Popen([str(running), "30"], stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        try:
            self.assertIsNone(process.poll())
            self.install("linux")
            self.assertEqual(running.read_bytes(), b"#!/bin/sh\necho new-of\n")
            self.assertTrue(os.access(running, os.X_OK))
            self.assertIsNone(process.poll())
        finally:
            process.terminate()
            process.wait(timeout=2)


if __name__ == "__main__":
    unittest.main()
