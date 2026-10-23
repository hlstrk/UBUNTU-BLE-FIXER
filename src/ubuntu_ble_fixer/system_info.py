"""Ubuntu and desktop session inspection."""

from __future__ import annotations

import os
from pathlib import Path

from ubuntu_ble_fixer.models import OperatingSystem, SystemSnapshot
from ubuntu_ble_fixer.pactl import AudioBackendError, PactlBackend


class SystemInspector:
    def __init__(
        self,
        backend: PactlBackend,
        os_release_path: Path = Path("/etc/os-release"),
        environment: dict[str, str] | None = None,
    ) -> None:
        self._backend = backend
        self._os_release_path = os_release_path
        self._environment = environment if environment is not None else dict(os.environ)

    def snapshot(self) -> SystemSnapshot:
        operating_system = self.operating_system()
        try:
            audio_server = self._backend.server_name()
        except AudioBackendError as error:
            audio_server = f"Unavailable ({error})"
        return SystemSnapshot(
            operating_system=operating_system,
            audio_server=audio_server,
            desktop=self._environment.get("XDG_CURRENT_DESKTOP", "Unknown"),
            session_type=self._environment.get("XDG_SESSION_TYPE", "Unknown"),
        )

    def operating_system(self) -> OperatingSystem:
        values = self.parse_os_release(self._os_release_path.read_text(encoding="utf-8"))
        system_id = values.get("ID", "unknown")
        version_id = values.get("VERSION_ID", "0")
        supported = system_id == "ubuntu" and self._version_tuple(version_id) >= (22, 4)
        return OperatingSystem(
            name=values.get("NAME", system_id),
            version_id=version_id,
            pretty_name=values.get("PRETTY_NAME", system_id),
            supported=supported,
        )

    @staticmethod
    def parse_os_release(content: str) -> dict[str, str]:
        values: dict[str, str] = {}
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key] = value.strip().strip('"').strip("'")
        return values

    @staticmethod
    def _version_tuple(version: str) -> tuple[int, ...]:
        parts = []
        for part in version.split("."):
            digits = "".join(character for character in part if character.isdigit())
            parts.append(int(digits or 0))
        return tuple(parts)
