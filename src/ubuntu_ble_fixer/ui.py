"""GTK AppIndicator interface."""

from __future__ import annotations

import subprocess
import time

import gi

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3 as AppIndicator
except ValueError:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3 as AppIndicator
from gi.repository import GLib, Gtk

from ubuntu_ble_fixer.i18n import Translator
from ubuntu_ble_fixer.models import AudioProfile, BluetoothDevice
from ubuntu_ble_fixer.pactl import AudioBackendError
from ubuntu_ble_fixer.reporting import ReportBuilder
from ubuntu_ble_fixer.service import CodecManager, ProfileSelectionError
from ubuntu_ble_fixer.system_info import SystemInspector


APP_ID = "ubuntu-ble-fixer"


class TrayApplication:
    def __init__(
        self,
        manager: CodecManager,
        inspector: SystemInspector,
        translator: Translator | None = None,
    ) -> None:
        self._manager = manager
        self._inspector = inspector
        self._translate = translator or Translator()
        self._signature: tuple[object, ...] | None = None
        self._pending: dict[str, tuple[str, float]] = {}

        self._indicator = AppIndicator.Indicator.new(
            APP_ID,
            "audio-headset-bluetooth-symbolic",
            AppIndicator.IndicatorCategory.HARDWARE,
        )
        self._indicator.set_status(AppIndicator.IndicatorStatus.ACTIVE)
        self._indicator.set_title("Ubuntu BLE Fixer")
        self.refresh(force=True)
        GLib.timeout_add_seconds(3, self.refresh)

    def run(self) -> None:
        Gtk.main()

    def refresh(self, force: bool = False) -> bool:
        error: str | None = None
        try:
            devices = self._manager.devices()
        except AudioBackendError as backend_error:
            devices = ()
            error = str(backend_error)

        signature = (
            error,
            tuple(sorted(self._pending.items())),
            tuple(
                (
                    device.card_name,
                    device.active_profile,
                    tuple((profile.name, profile.available) for profile in device.profiles),
                )
                for device in devices
            ),
        )
        if force or signature != self._signature:
            self._signature = signature
            self._render(devices, error)
        return True

    def _render(self, devices: tuple[BluetoothDevice, ...], error: str | None) -> None:
        menu = Gtk.Menu()
        if error:
            status = Gtk.MenuItem(label=f"{self._translate('audio_error')}: {error}")
            status.set_sensitive(False)
            menu.append(status)
            self._indicator.set_label("BT !", "BT aptX HD")
        elif not devices:
            status = Gtk.MenuItem(label=self._translate("no_device"))
            status.set_sensitive(False)
            menu.append(status)
            self._indicator.set_label("BT —", "BT aptX HD")
        else:
            connected = tuple(device for device in devices if device.connected)
            primary = connected[0] if connected else devices[0]
            active_codec = primary.active.codec if primary.active else "—"
            tray_name = self._manager.family(primary).tray_label
            label = f"{tray_name} {active_codec}" if len(devices) == 1 else f"BT {len(devices)}"
            self._indicator.set_label(label, "BT aptX HD")

            for index, device in enumerate(devices):
                if len(devices) == 1:
                    self._append_device_menu(menu, device, include_heading=True)
                else:
                    device_item = Gtk.MenuItem(label=device.display_name)
                    submenu = Gtk.Menu()
                    self._append_device_menu(submenu, device, include_heading=False)
                    device_item.set_submenu(submenu)
                    menu.append(device_item)
                if index < len(devices) - 1 and len(devices) == 1:
                    menu.append(Gtk.SeparatorMenuItem())

        menu.append(Gtk.SeparatorMenuItem())
        report_item = Gtk.MenuItem(label=self._translate("system_report"))
        report_item.connect("activate", self._show_report)
        menu.append(report_item)

        settings_item = Gtk.MenuItem(label=self._translate("sound_settings"))
        settings_item.connect("activate", self._open_sound_settings)
        menu.append(settings_item)

        refresh_item = Gtk.MenuItem(label=self._translate("refresh"))
        refresh_item.connect("activate", lambda _item: self.refresh(force=True))
        menu.append(refresh_item)

        menu.append(Gtk.SeparatorMenuItem())
        quit_item = Gtk.MenuItem(label=self._translate("quit"))
        quit_item.connect("activate", lambda _item: Gtk.main_quit())
        menu.append(quit_item)

        menu.show_all()
        self._indicator.set_menu(menu)

    def _append_device_menu(self, menu: Gtk.Menu, device: BluetoothDevice, include_heading: bool) -> None:
        if include_heading:
            heading = Gtk.MenuItem(label=device.display_name)
            heading.set_sensitive(False)
            menu.append(heading)

        active = device.active.codec if device.active else self._translate("disconnected")
        status = Gtk.MenuItem(label=f"{self._translate('active')}: {active}")
        status.set_sensitive(False)
        menu.append(status)
        pending = self._pending.get(device.card_name)
        if pending:
            requested = next(
                (profile.codec for profile in device.profiles if profile.name == pending[0]),
                pending[0],
            )
            changing = Gtk.MenuItem(label=f"{self._translate('changing')}: {requested}")
            changing.set_sensitive(False)
            menu.append(changing)
        menu.append(Gtk.SeparatorMenuItem())

        group: Gtk.RadioMenuItem | None = None
        for profile in device.selectable_profiles:
            if group is None:
                item = Gtk.RadioMenuItem.new_with_label(None, profile.codec)
                group = item
            else:
                item = Gtk.RadioMenuItem.new_with_label_from_widget(group, profile.codec)
            item.set_active(profile.name == device.active_profile)
            item.connect("toggled", self._change_profile, device, profile)
            menu.append(item)

        if not device.selectable_profiles:
            unavailable = Gtk.MenuItem(label=self._translate("disconnected"))
            unavailable.set_sensitive(False)
            menu.append(unavailable)

    def _change_profile(
        self,
        item: Gtk.RadioMenuItem,
        device: BluetoothDevice,
        profile: AudioProfile,
    ) -> None:
        if not item.get_active() or profile.name == device.active_profile:
            return
        try:
            self._manager.change_profile(device, profile.name)
        except (AudioBackendError, ProfileSelectionError) as error:
            self._notify(self._translate("change_failed"), str(error), "critical")
        else:
            self._pending[device.card_name] = (profile.name, time.monotonic() + 8)
            self.refresh(force=True)
            GLib.timeout_add(200, self._poll_profile_change, device, profile)

    def _poll_profile_change(self, device: BluetoothDevice, profile: AudioProfile) -> bool:
        pending = self._pending.get(device.card_name)
        if not pending or pending[0] != profile.name:
            return False
        try:
            current = next(
                (
                    candidate
                    for candidate in self._manager.devices()
                    if candidate.card_name == device.card_name
                ),
                None,
            )
        except AudioBackendError as error:
            self._pending.pop(device.card_name, None)
            self._notify(self._translate("change_failed"), str(error), "critical")
            self.refresh(force=True)
            return False

        if current and current.active_profile == profile.name:
            self._pending.pop(device.card_name, None)
            self._notify(self._translate("changed"), f"{device.display_name}: {profile.codec}")
            self.refresh(force=True)
            return False
        if time.monotonic() >= pending[1]:
            self._pending.pop(device.card_name, None)
            self._notify(
                self._translate("change_failed"),
                self._translate("change_timeout"),
                "critical",
            )
            self.refresh(force=True)
            return False
        return True

    def _show_report(self, _item: Gtk.MenuItem) -> None:
        try:
            devices = self._manager.devices()
            report = ReportBuilder(self._manager).text(self._inspector.snapshot(), devices)
        except AudioBackendError as error:
            report = str(error)
        dialog = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Ubuntu BLE Fixer",
        )
        dialog.format_secondary_text(report)
        dialog.run()
        dialog.destroy()

    @staticmethod
    def _open_sound_settings(_item: Gtk.MenuItem) -> None:
        try:
            subprocess.Popen(
                ["pavucontrol", "--tab=5"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            pass

    @staticmethod
    def _notify(title: str, message: str, urgency: str = "normal") -> None:
        try:
            subprocess.Popen(
                ["notify-send", "-a", "Ubuntu BLE Fixer", "-u", urgency, title, message],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            pass
