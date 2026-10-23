import unittest
from dataclasses import replace

from ubuntu_ble_fixer.pactl import PactlBackend
from ubuntu_ble_fixer.service import CodecManager, DeviceSelectionError, ProfileSelectionError
from tests.fixtures import PACTL_CARDS


class FakeBackend:
    def __init__(self):
        self._devices = PactlBackend.parse_cards(PACTL_CARDS)
        self.changes = []

    def list_devices(self):
        return self._devices

    def set_profile(self, card_name, profile_name):
        self.changes.append((card_name, profile_name))


class DelayedBackend(FakeBackend):
    def __init__(self):
        super().__init__()
        self.requested_profile = None
        self.read_count = 0

    def list_devices(self):
        self.read_count += 1
        if self.requested_profile and self.read_count >= 3:
            first = replace(self._devices[0], active_profile=self.requested_profile)
            return (first, *self._devices[1:])
        return self._devices

    def set_profile(self, card_name, profile_name):
        super().set_profile(card_name, profile_name)
        self.requested_profile = profile_name


class CodecManagerTests(unittest.TestCase):
    def setUp(self):
        self.backend = FakeBackend()
        self.manager = CodecManager(self.backend)

    def test_selects_device_by_partial_name(self):
        device = self.manager.select_device("momentum")

        self.assertEqual(device.display_name, "MOMENTUM 4")

    def test_requires_device_when_more_than_one_exists(self):
        with self.assertRaisesRegex(DeviceSelectionError, "More than one"):
            self.manager.select_device()

    def test_changes_profile_by_codec_name(self):
        device = self.manager.select_device("momentum")
        profile = self.manager.change_profile(device, "aptx hd")

        self.assertEqual(profile.name, "a2dp-sink")
        self.assertEqual(self.backend.changes, [(device.card_name, "a2dp-sink")])

    def test_rejects_unavailable_profile(self):
        device = self.manager.select_device("WH-1000XM5")

        with self.assertRaisesRegex(ProfileSelectionError, "unavailable"):
            self.manager.change_profile(device, "LDAC")

    def test_rejects_unknown_codec(self):
        device = self.manager.select_device("momentum")

        with self.assertRaisesRegex(ProfileSelectionError, "not found"):
            self.manager.resolve_profile(device, "LC3")

    def test_waits_until_backend_reports_requested_profile(self):
        backend = DelayedBackend()
        manager = CodecManager(backend)
        device = manager.select_device("momentum")

        profile = manager.change_profile(
            device,
            "aptX HD",
            wait=True,
            timeout=1,
            poll_interval=0,
        )

        self.assertEqual(profile.name, "a2dp-sink")
        self.assertGreaterEqual(backend.read_count, 3)


if __name__ == "__main__":
    unittest.main()
