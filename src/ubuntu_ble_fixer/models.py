"""Domain models shared by the command line and tray interfaces."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AudioProfile:
    name: str
    label: str
    codec: str
    available: bool

    @property
    def is_a2dp(self) -> bool:
        return self.name.startswith(("a2dp-", "a2dp_"))


@dataclass(frozen=True, slots=True)
class BluetoothDevice:
    card_name: str
    display_name: str
    address: str
    active_profile: str
    profiles: tuple[AudioProfile, ...]

    @property
    def connected(self) -> bool:
        return self.active_profile != "off"

    @property
    def active(self) -> AudioProfile | None:
        return next((profile for profile in self.profiles if profile.name == self.active_profile), None)

    @property
    def selectable_profiles(self) -> tuple[AudioProfile, ...]:
        return tuple(profile for profile in self.profiles if profile.available and profile.is_a2dp)


@dataclass(frozen=True, slots=True)
class DeviceFamily:
    vendor: str
    family: str
    tray_label: str


@dataclass(frozen=True, slots=True)
class OperatingSystem:
    name: str
    version_id: str
    pretty_name: str
    supported: bool


@dataclass(frozen=True, slots=True)
class SystemSnapshot:
    operating_system: OperatingSystem
    audio_server: str
    desktop: str
    session_type: str
