#!/usr/bin/env bash
set -Eeuo pipefail

if ((EUID == 0)); then
    printf 'Do not run this script with sudo.\n' >&2
    exit 1
fi

APP_USER_HOME="${HOME:?HOME is not set}"
APP_DATA_HOME="${XDG_DATA_HOME:-${APP_USER_HOME}/.local/share}"
APP_CONFIG_HOME="${XDG_CONFIG_HOME:-${APP_USER_HOME}/.config}"
APP_DATA_DIR="${APP_DATA_HOME}/ubuntu-ble-fixer"
APP_BIN="${APP_USER_HOME}/.local/bin/ubuntu-ble-fixer"
UNIT_PATH="${APP_CONFIG_HOME}/systemd/user/ubuntu-ble-fixer.service"

case "${APP_DATA_DIR}" in
    "${APP_USER_HOME}/.local/share/ubuntu-ble-fixer"|"${XDG_DATA_HOME:-/nonexistent}/ubuntu-ble-fixer") ;;
    *) printf 'Refusing to remove unexpected path: %s\n' "${APP_DATA_DIR}" >&2; exit 1 ;;
esac

systemctl --user disable --now ubuntu-ble-fixer.service >/dev/null 2>&1 || true
rm -f -- "${UNIT_PATH}" "${APP_BIN}"
rm -rf -- "${APP_DATA_DIR}"
systemctl --user daemon-reload

printf 'Ubuntu BLE Fixer removed. System packages were left installed.\n'
