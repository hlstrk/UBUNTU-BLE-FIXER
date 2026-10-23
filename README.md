# Ubuntu BLE Fixer

[Türkçe](README.tr.md)

Ubuntu BLE Fixer adds a codec selector to the desktop tray. It reads the Bluetooth audio profiles exposed by PipeWire or PulseAudio and lets you switch profiles without opening a terminal.

## Features

- Detects Ubuntu version, audio server, desktop session, and Bluetooth audio cards during setup.
- Lists the codecs that the connected headset and Linux audio stack negotiated.
- Runs as an unprivileged `systemd --user` service.
- Supports PipeWire and PulseAudio through their `pactl` interface.
- Includes a CLI for status reports and codec changes.
- Keeps all runtime data on the computer. The tray process makes no network requests and collects no analytics.

## Requirements

- Ubuntu 22.04 or newer
- A desktop session with AppIndicator support
- A Bluetooth headset paired through Ubuntu Settings

The installer adds the required Ubuntu packages. It shows the detected system and package list before it asks for confirmation.

## Install

Run:

```bash
curl -fsSL https://raw.githubusercontent.com/hlstrk/UBUNTU-BLE-FIXER/main/install.sh | bash
```

The installer asks for confirmation and requests `sudo` only when Ubuntu packages are missing. It installs the application under `~/.local`, then enables a user service.

Use `--yes` for an unattended install:

```bash
curl -fsSL https://raw.githubusercontent.com/hlstrk/UBUNTU-BLE-FIXER/main/install.sh | bash -s -- --yes
```

Inspect the script before running it:

```bash
curl -fsSL https://raw.githubusercontent.com/hlstrk/UBUNTU-BLE-FIXER/main/install.sh -o /tmp/ubuntu-ble-fixer-install.sh
less /tmp/ubuntu-ble-fixer-install.sh
bash /tmp/ubuntu-ble-fixer-install.sh
```

## Use

Click the headset icon in the desktop tray and select a codec. The menu marks the active codec and refreshes when a headset connects or disconnects.

The CLI exposes the same controls:

```bash
ubuntu-ble-fixer status
ubuntu-ble-fixer doctor
ubuntu-ble-fixer set aptx --device "MOMENTUM 4"
ubuntu-ble-fixer set ldac --device "WH-1000XM5"
ubuntu-ble-fixer status --json
```

PipeWire and PulseAudio decide which profiles appear. Ubuntu BLE Fixer cannot add a codec that the Bluetooth adapter, headset, or installed audio stack does not advertise.

## Headset support

The application works with any BlueZ audio card that exposes A2DP profiles through `pactl`. It recognizes these product families for shorter tray labels:

| Vendor | Families |
| --- | --- |
| Sennheiser | MOMENTUM 4 |
| Sony | WH-1000XM3 through XM6, WF-1000XM3 through XM6 |
| Bose | QuietComfort and QC models |
| Apple | AirPods and AirPods Max |
| Samsung | Galaxy Buds |
| JBL | Tour, Live, Tune, and Quantum |
| Anker | Soundcore and Space models |

Unknown models use their Bluetooth name and retain full codec switching support.

## Installation layout

| Path | Purpose |
| --- | --- |
| `~/.local/share/ubuntu-ble-fixer` | Python application |
| `~/.local/bin/ubuntu-ble-fixer` | Command-line launcher |
| `~/.config/systemd/user/ubuntu-ble-fixer.service` | Tray service |

Manage the service with:

```bash
systemctl --user status ubuntu-ble-fixer.service
systemctl --user restart ubuntu-ble-fixer.service
journalctl --user -u ubuntu-ble-fixer.service -n 50
```

## Uninstall

Run the installed uninstaller:

```bash
~/.local/share/ubuntu-ble-fixer/uninstall.sh
```

The uninstaller removes the user service and application files. It leaves Ubuntu packages in place because another desktop application may use them.

## Troubleshooting

Run the system report first:

```bash
ubuntu-ble-fixer doctor
```

If the tray icon does not appear, confirm that the service runs and that the AppIndicator extension is enabled:

```bash
systemctl --user status ubuntu-ble-fixer.service
gnome-extensions enable ubuntu-appindicators@ubuntu.com
systemctl --user restart ubuntu-ble-fixer.service
```

If a codec is missing, reconnect the headset and check `pactl list cards`. The codec must appear as an available A2DP profile before the application can select it.

## Development

Ubuntu BLE Fixer uses Python 3.10 or newer. Runtime integration depends on PyGObject and Ayatana AppIndicator packages supplied by Ubuntu.

```bash
git clone https://github.com/hlstrk/UBUNTU-BLE-FIXER.git
cd UBUNTU-BLE-FIXER
PYTHONPATH=src python3 -m unittest discover -s tests -v
bash -n install.sh uninstall.sh bin/ubuntu-ble-fixer
./install.sh --dry-run
```

The source separates device parsing, model recognition, codec operations, system inspection, reporting, and GTK presentation. Tests use fake backends and do not need a Bluetooth device.

## License

[MIT](LICENSE)
