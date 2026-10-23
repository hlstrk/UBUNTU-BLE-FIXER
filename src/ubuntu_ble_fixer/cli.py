"""Command-line entry point."""

from __future__ import annotations

import argparse
import sys

from ubuntu_ble_fixer import __version__
from ubuntu_ble_fixer.catalog import DeviceCatalog
from ubuntu_ble_fixer.pactl import AudioBackendError, PactlBackend
from ubuntu_ble_fixer.reporting import ReportBuilder
from ubuntu_ble_fixer.service import CodecManager, DeviceSelectionError, ProfileSelectionError
from ubuntu_ble_fixer.system_info import SystemInspector


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ubuntu-ble-fixer",
        description="Inspect Bluetooth headphones and switch their audio codec profile.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", aliases=["list"], help="Show system and headset status")
    status.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    doctor = subparsers.add_parser("doctor", help="Run installation and device checks")
    doctor.add_argument("--json", action="store_true", help="Print machine-readable JSON")

    change = subparsers.add_parser("set", help="Change a codec or pactl profile")
    change.add_argument("codec", help="Codec name or pactl profile, such as aptX or a2dp-sink-aptx")
    change.add_argument("--device", help="Device name, Bluetooth address, or card name")

    subparsers.add_parser("tray", help="Run the system tray application")
    return parser


def main(arguments: list[str] | None = None) -> int:
    parser = build_parser()
    options = parser.parse_args(arguments)
    backend = PactlBackend()
    manager = CodecManager(backend, DeviceCatalog())
    inspector = SystemInspector(backend)

    try:
        if options.command in {"status", "list", "doctor"}:
            snapshot = inspector.snapshot()
            devices = manager.devices()
            builder = ReportBuilder(manager)
            print(builder.json(snapshot, devices) if options.json else builder.text(snapshot, devices))
            if options.command == "doctor" and not snapshot.operating_system.supported:
                return 2
            return 0

        if options.command == "set":
            device = manager.select_device(options.device)
            profile = manager.change_profile(device, options.codec, wait=True)
            print(f"{device.display_name}: {profile.codec} ({profile.name})")
            return 0

        if options.command == "tray":
            from ubuntu_ble_fixer.ui import TrayApplication

            TrayApplication(manager, inspector).run()
            return 0
    except (AudioBackendError, DeviceSelectionError, ProfileSelectionError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    parser.error(f"Unknown command: {options.command}")
    return 2
