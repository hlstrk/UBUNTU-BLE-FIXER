"""Application services for device selection and codec changes."""

from __future__ import annotations

import re
import time
from typing import Protocol

from ubuntu_ble_fixer.catalog import DeviceCatalog
from ubuntu_ble_fixer.models import AudioProfile, BluetoothDevice, DeviceFamily


class Backend(Protocol):
    def list_devices(self) -> tuple[BluetoothDevice, ...]: ...

    def set_profile(self, card_name: str, profile_name: str) -> None: ...


class DeviceSelectionError(ValueError):
    pass


class ProfileSelectionError(ValueError):
    pass


class CodecManager:
    def __init__(self, backend: Backend, catalog: DeviceCatalog | None = None) -> None:
        self._backend = backend
        self._catalog = catalog or DeviceCatalog()

    def devices(self) -> tuple[BluetoothDevice, ...]:
        return self._backend.list_devices()

    def family(self, device: BluetoothDevice) -> DeviceFamily:
        return self._catalog.identify(device.display_name)

    def select_device(self, query: str | None = None) -> BluetoothDevice:
        devices = self.devices()
        if not devices:
            raise DeviceSelectionError("No Bluetooth audio device found.")
        if query is None:
            if len(devices) == 1:
                return devices[0]
            raise DeviceSelectionError("More than one device found. Use --device NAME.")

        normalized = query.casefold()
        exact = tuple(
            device
            for device in devices
            if normalized
            in {
                device.display_name.casefold(),
                device.card_name.casefold(),
                device.address.casefold(),
            }
        )
        if len(exact) == 1:
            return exact[0]
        partial = tuple(device for device in devices if normalized in device.display_name.casefold())
        if len(partial) == 1:
            return partial[0]
        if not exact and not partial:
            raise DeviceSelectionError(f"Device not found: {query}")
        raise DeviceSelectionError(f"Device name is ambiguous: {query}")

    def change_profile(
        self,
        device: BluetoothDevice,
        requested: str,
        *,
        wait: bool = False,
        timeout: float = 8,
        poll_interval: float = 0.2,
    ) -> AudioProfile:
        profile = self.resolve_profile(device, requested)
        if not profile.available:
            raise ProfileSelectionError(f"Profile is unavailable: {profile.name}")
        self._backend.set_profile(device.card_name, profile.name)
        if wait:
            self.wait_for_profile(device.card_name, profile.name, timeout, poll_interval)
        return profile

    def wait_for_profile(
        self,
        card_name: str,
        profile_name: str,
        timeout: float = 8,
        poll_interval: float = 0.2,
    ) -> BluetoothDevice:
        deadline = time.monotonic() + timeout
        while True:
            device = next(
                (candidate for candidate in self.devices() if candidate.card_name == card_name),
                None,
            )
            if device and device.active_profile == profile_name:
                return device
            if time.monotonic() >= deadline:
                raise ProfileSelectionError(
                    f"Profile request timed out: {profile_name}. The Bluetooth device may have disconnected."
                )
            time.sleep(poll_interval)

    @staticmethod
    def resolve_profile(device: BluetoothDevice, requested: str) -> AudioProfile:
        normalized = CodecManager._normalize(requested)
        matches = tuple(
            profile
            for profile in device.profiles
            if normalized in {
                CodecManager._normalize(profile.name),
                CodecManager._normalize(profile.codec),
            }
        )
        if len(matches) == 1:
            return matches[0]
        if not matches:
            raise ProfileSelectionError(f"Codec or profile not found: {requested}")
        available = tuple(profile for profile in matches if profile.available)
        if len(available) == 1:
            return available[0]
        names = ", ".join(profile.name for profile in matches)
        raise ProfileSelectionError(f"Codec matches multiple profiles: {names}")

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.casefold())
