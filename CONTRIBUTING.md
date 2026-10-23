# Contributing

Open an issue before changing user-facing behavior or adding an Ubuntu release. Include the Ubuntu version, desktop session, audio server from `pactl info`, and the relevant Bluetooth card from `pactl list cards`.

## Development setup

Install the runtime packages:

```bash
sudo apt install python3 python3-gi gir1.2-gtk-3.0 gir1.2-ayatanaappindicator3-0.1 pulseaudio-utils
```

Run the checks:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests
bash -n install.sh uninstall.sh bin/ubuntu-ble-fixer
```

Keep system calls inside backend classes. Add parser fixtures for new `pactl` formats and unit tests for each behavior change.

## Pull requests

Describe the affected Ubuntu and audio server versions. Keep the pull request focused on one change and include terminal output for installation or service changes.
