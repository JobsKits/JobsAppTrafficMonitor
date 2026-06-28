import tempfile
import unittest
from pathlib import Path

from jobs_app_traffic_monitor.app_resolver import MacOSAppResolver


class AppResolverTests(unittest.TestCase):
    def test_bundle_name_reads_display_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            contents = Path(directory) / "Example.app" / "Contents"
            contents.mkdir(parents=True)
            (contents / "Info.plist").write_bytes(
                b'<?xml version="1.0" encoding="UTF-8"?>'
                b'<plist version="1.0"><dict><key>CFBundleDisplayName</key>'
                b'<string>Example App</string></dict></plist>'
            )

            self.assertEqual(MacOSAppResolver._bundle_name(contents.parent), "Example App")

    def test_system_path_classification(self) -> None:
        self.assertTrue(MacOSAppResolver._is_system_path("/System/Applications/Safari.app"))
        self.assertTrue(MacOSAppResolver._is_system_path("/usr/libexec/mDNSResponder"))
        self.assertTrue(MacOSAppResolver._is_system_path("/Library/Apple/System/Example"))
        self.assertFalse(MacOSAppResolver._is_system_path("/Applications/Google Chrome.app"))
        self.assertFalse(MacOSAppResolver._is_system_path("/opt/homebrew/bin/python3"))


if __name__ == "__main__":
    unittest.main()
