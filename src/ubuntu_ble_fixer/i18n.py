"""Small built-in translation table for installer-facing application text."""

from __future__ import annotations

import os


MESSAGES = {
    "en": {
        "no_device": "No Bluetooth audio device found",
        "active": "Active",
        "disconnected": "Disconnected",
        "refresh": "Refresh",
        "sound_settings": "Open sound settings",
        "system_report": "System report",
        "quit": "Quit",
        "changed": "Codec changed",
        "changing": "Changing codec",
        "change_failed": "Codec change failed",
        "change_timeout": "The headset did not activate the requested codec in time",
        "audio_error": "Audio service error",
    },
    "tr": {
        "no_device": "Bluetooth ses cihazı bulunamadı",
        "active": "Aktif",
        "disconnected": "Bağlı değil",
        "refresh": "Yenile",
        "sound_settings": "Ses ayarlarını aç",
        "system_report": "Sistem raporu",
        "quit": "Kapat",
        "changed": "Codec değiştirildi",
        "changing": "Codec değiştiriliyor",
        "change_failed": "Codec değiştirilemedi",
        "change_timeout": "Kulaklık istenen codec'i zamanında etkinleştirmedi",
        "audio_error": "Ses servisi hatası",
    },
}


class Translator:
    def __init__(self, language: str | None = None) -> None:
        locale = language or os.environ.get("LANG", "en")
        self.language = "tr" if locale.casefold().startswith("tr") else "en"

    def __call__(self, key: str) -> str:
        return MESSAGES[self.language].get(key, key)
