import tempfile
import unittest
from pathlib import Path

from ubuntu_ble_fixer.system_info import SystemInspector


class FakeBackend:
    def server_name(self):
        return "PulseAudio (on PipeWire 1.0.5)"


class SystemInspectorTests(unittest.TestCase):
    def test_reads_supported_ubuntu_release(self):
        with tempfile.TemporaryDirectory() as directory:
            release = Path(directory) / "os-release"
            release.write_text(
                'NAME="Ubuntu"\nID=ubuntu\nVERSION_ID="24.04"\nPRETTY_NAME="Ubuntu 24.04.4 LTS"\n',
                encoding="utf-8",
            )
            inspector = SystemInspector(FakeBackend(), release, {"XDG_CURRENT_DESKTOP": "GNOME"})

            snapshot = inspector.snapshot()

        self.assertTrue(snapshot.operating_system.supported)
        self.assertEqual(snapshot.audio_server, "PulseAudio (on PipeWire 1.0.5)")
        self.assertEqual(snapshot.desktop, "GNOME")

    def test_rejects_old_ubuntu_release(self):
        values = SystemInspector.parse_os_release("ID=ubuntu\nVERSION_ID=20.04\n")
        self.assertEqual(values["VERSION_ID"], "20.04")
        self.assertLess(SystemInspector._version_tuple(values["VERSION_ID"]), (22, 4))

    def test_parses_quoted_values(self):
        values = SystemInspector.parse_os_release('NAME="Ubuntu Linux"\nID=ubuntu\n')
        self.assertEqual(values["NAME"], "Ubuntu Linux")


if __name__ == "__main__":
    unittest.main()
