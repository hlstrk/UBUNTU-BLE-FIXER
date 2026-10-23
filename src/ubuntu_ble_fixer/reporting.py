"""Text and JSON reports for diagnostics."""

from __future__ import annotations

import json

from ubuntu_ble_fixer.models import BluetoothDevice, SystemSnapshot
from ubuntu_ble_fixer.service import CodecManager


class ReportBuilder:
    def __init__(self, manager: CodecManager) -> None:
        self._manager = manager

    def text(self, snapshot: SystemSnapshot, devices: tuple[BluetoothDevice, ...]) -> str:
        support = "supported" if snapshot.operating_system.supported else "unsupported"
        lines = [
            f"OS: {snapshot.operating_system.pretty_name} ({support})",
            f"Audio server: {snapshot.audio_server}",
            f"Desktop: {snapshot.desktop} / {snapshot.session_type}",
            f"Bluetooth audio devices: {len(devices)}",
        ]
        for device in devices:
            family = self._manager.family(device)
            active = device.active.codec if device.active else device.active_profile
            codecs = ", ".join(profile.codec for profile in device.selectable_profiles) or "none"
            lines.extend(
                (
                    f"  {device.display_name}",
                    f"    Vendor/family: {family.vendor} / {family.family}",
                    f"    Address: {device.address or 'unknown'}",
                    f"    Active: {active}",
                    f"    Available A2DP codecs: {codecs}",
                )
            )
        return "\n".join(lines)

    def json(self, snapshot: SystemSnapshot, devices: tuple[BluetoothDevice, ...]) -> str:
        payload = {
            "system": {
                "os": snapshot.operating_system.pretty_name,
                "version": snapshot.operating_system.version_id,
                "supported": snapshot.operating_system.supported,
                "audio_server": snapshot.audio_server,
                "desktop": snapshot.desktop,
                "session_type": snapshot.session_type,
            },
            "devices": [
                {
                    "name": device.display_name,
                    "card": device.card_name,
                    "address": device.address,
                    "connected": device.connected,
                    "active_profile": device.active_profile,
                    "active_codec": device.active.codec if device.active else None,
                    "profiles": [
                        {
                            "name": profile.name,
                            "codec": profile.codec,
                            "available": profile.available,
                        }
                        for profile in device.profiles
                    ],
                }
                for device in devices
            ],
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)
