import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main()
