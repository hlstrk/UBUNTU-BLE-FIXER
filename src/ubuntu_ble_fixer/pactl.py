"""PulseAudio-compatible backend used by PipeWire and PulseAudio."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Sequence

from ubuntu_ble_fixer.models import AudioProfile, BluetoothDevice


class AudioBackendError(RuntimeError):
    pass


Runner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


def _default_runner(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        arguments,
        capture_output=True,
        text=True,
        timeout=8,
        check=False,
    )


class PactlBackend:
    def __init__(self, runner: Runner | None = None) -> None:
        self._runner = runner or _default_runner

    def list_devices(self) -> tuple[BluetoothDevice, ...]:
        result = self._run(("pactl", "list", "cards"))
        return self.parse_cards(result.stdout)

    def server_name(self) -> str:
        result = self._run(("pactl", "info"))
        match = re.search(r"^Server Name:\s*(.+)$", result.stdout, re.MULTILINE)
        return match.group(1).strip() if match else "Unknown"

    def set_profile(self, card_name: str, profile_name: str) -> None:
        self._run(("pactl", "set-card-profile", card_name, profile_name))

    def _run(self, arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
        try:
            result = self._runner(arguments)
        except (OSError, subprocess.TimeoutExpired) as error:
            raise AudioBackendError(str(error)) from error
        if result.returncode != 0:
            message = result.stderr.strip() or f"Command failed: {' '.join(arguments)}"
            raise AudioBackendError(message)
        return result

    @staticmethod
    def parse_cards(output: str) -> tuple[BluetoothDevice, ...]:
        devices: list[BluetoothDevice] = []
        blocks = re.split(r"(?=^Card #\d+\s*$)", output, flags=re.MULTILINE)
        for block in blocks:
            name_match = re.search(r"^\s*Name:\s*(\S+)", block, re.MULTILINE)
            if not name_match:
                continue
            card_name = name_match.group(1)
            is_bluez = card_name.startswith("bluez_card.") or 'device.api = "bluez5"' in block
            if not is_bluez:
                continue

            description = PactlBackend._property(block, "device.description")
            alias = PactlBackend._property(block, "device.alias")
            address = PactlBackend._property(block, "api.bluez5.address")
            active_match = re.search(r"^\s*Active Profile:\s*(\S+)", block, re.MULTILINE)
            profiles_text = block.partition("\n\tProfiles:")[2].partition("\n\tActive Profile:")[0]
            profiles = PactlBackend._parse_profiles(profiles_text)
            devices.append(
                BluetoothDevice(
                    card_name=card_name,
                    display_name=description or alias or card_name,
                    address=address,
                    active_profile=active_match.group(1) if active_match else "off",
                    profiles=profiles,
                )
            )
        return tuple(devices)

    @staticmethod
    def _property(block: str, property_name: str) -> str:
        match = re.search(
            rf'^\s*{re.escape(property_name)}\s*=\s*"([^"]*)"',
            block,
            re.MULTILINE,
        )
        return match.group(1) if match else ""

    @staticmethod
    def _parse_profiles(section: str) -> tuple[AudioProfile, ...]:
        profiles: list[AudioProfile] = []
        pattern = re.compile(
            r"^\s+([^:\s]+):\s+(.+?)\s+"
            r"\(sinks:.*?available:\s*(yes|no|unknown)\)\s*$",
            re.MULTILINE,
        )
        for match in pattern.finditer(section):
            profile_name, label, availability = match.groups()
            codec_match = re.search(r"codec\s+([^)]+)", label, re.IGNORECASE)
            codec = codec_match.group(1).strip() if codec_match else profile_name
            profiles.append(
                AudioProfile(
                    name=profile_name,
                    label=label,
                    codec=codec,
                    available=availability != "no",
                )
            )
        return tuple(profiles)
