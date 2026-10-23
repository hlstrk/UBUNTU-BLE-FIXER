"""Recognition rules for common Bluetooth headphone families."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ubuntu_ble_fixer.models import DeviceFamily


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    pattern: re.Pattern[str]
    family: DeviceFamily


class DeviceCatalog:
    """Adds friendly vendor and family names without limiting device support."""

    def __init__(self) -> None:
        definitions = (
            (r"momentum\s*4", "Sennheiser", "MOMENTUM 4", "M4"),
            (r"wh-1000xm[3-6]", "Sony", "WH-1000XM series", "XM"),
            (r"wf-1000xm[3-6]", "Sony", "WF-1000XM series", "WF"),
            (r"quietcomfort|bose\s+qc", "Bose", "QuietComfort", "QC"),
            (r"airpods\s+max", "Apple", "AirPods Max", "APM"),
            (r"airpods", "Apple", "AirPods", "AP"),
            (r"galaxy\s+buds", "Samsung", "Galaxy Buds", "Buds"),
            (r"jbl\s+(tour|live|tune|quantum)", "JBL", "JBL headphones", "JBL"),
            (r"soundcore|space\s+(one|q\d+)", "Anker", "Soundcore", "SC"),
        )
        self._entries = tuple(
            CatalogEntry(re.compile(pattern, re.IGNORECASE), DeviceFamily(vendor, family, label))
            for pattern, vendor, family, label in definitions
        )

    def identify(self, device_name: str) -> DeviceFamily:
        for entry in self._entries:
            if entry.pattern.search(device_name):
                return entry.family
        compact_name = "".join(character for character in device_name if character.isalnum())
        tray_label = compact_name[:5] or "BT"
        return DeviceFamily("Unknown", device_name, tray_label)
