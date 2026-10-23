import unittest

from ubuntu_ble_fixer.catalog import DeviceCatalog


class DeviceCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = DeviceCatalog()

    def test_recognizes_popular_families(self):
        cases = {
            "MOMENTUM 4": ("Sennheiser", "M4"),
            "WH-1000XM5": ("Sony", "XM"),
            "Bose QuietComfort Ultra": ("Bose", "QC"),
            "AirPods Max": ("Apple", "APM"),
            "Galaxy Buds3 Pro": ("Samsung", "Buds"),
            "JBL Tour One M2": ("JBL", "JBL"),
            "soundcore Space One": ("Anker", "SC"),
        }
        for name, expected in cases.items():
            with self.subTest(name=name):
                family = self.catalog.identify(name)
                self.assertEqual((family.vendor, family.tray_label), expected)

    def test_unknown_devices_still_work(self):
        family = self.catalog.identify("Studio Headphones")

        self.assertEqual(family.vendor, "Unknown")
        self.assertEqual(family.family, "Studio Headphones")


if __name__ == "__main__":
    unittest.main()
