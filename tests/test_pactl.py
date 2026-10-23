import subprocess
import unittest

from ubuntu_ble_fixer.pactl import AudioBackendError, PactlBackend
from tests.fixtures import PACTL_CARDS


class PactlParserTests(unittest.TestCase):
    def test_parses_only_bluetooth_cards(self):
        devices = PactlBackend.parse_cards(PACTL_CARDS)

        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0].display_name, "MOMENTUM 4")
        self.assertEqual(devices[1].display_name, "WH-1000XM5")

    def test_parses_address_and_active_codec(self):
        device = PactlBackend.parse_cards(PACTL_CARDS)[0]

        self.assertEqual(device.address, "80:C3:BA:70:A6:62")
        self.assertEqual(device.active.codec, "aptX")

    def test_exposes_available_a2dp_profiles(self):
        sony = PactlBackend.parse_cards(PACTL_CARDS)[1]

        self.assertEqual([profile.codec for profile in sony.selectable_profiles], ["SBC"])
        self.assertFalse(sony.connected)

    def test_accepts_pulseaudio_underscore_profile_names(self):
        output = PACTL_CARDS.replace("a2dp-sink-sbc", "a2dp_sink_sbc")
        device = PactlBackend.parse_cards(output)[0]

        self.assertIn("SBC", [profile.codec for profile in device.selectable_profiles])

    def test_backend_reports_command_errors(self):
        def failing_runner(_arguments):
            return subprocess.CompletedProcess([], 1, "", "PulseAudio unavailable")

        with self.assertRaisesRegex(AudioBackendError, "PulseAudio unavailable"):
            PactlBackend(failing_runner).list_devices()


if __name__ == "__main__":
    unittest.main()
