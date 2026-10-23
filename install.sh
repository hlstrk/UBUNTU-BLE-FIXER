#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="Ubuntu BLE Fixer"
REPOSITORY="hlstrk/UBUNTU-BLE-FIXER"
BRANCH="main"
ASSUME_YES=0
DRY_RUN=0
TEMP_DIR=""

if [[ "${LANG:-en}" == tr* ]]; then
    MSG_OS="İşletim sistemi"
    MSG_AUDIO="Ses sunucusu"
    MSG_DESKTOP="Masaüstü"
    MSG_PACKAGES="Kurulacak paketler"
    MSG_HEADSETS="Bulunan Bluetooth ses cihazları"
    MSG_NO_HEADSET="bulunamadı; eşleştirdikten sonra otomatik algılanacak"
    MSG_PATH="Kurulum dizini"
    MSG_CONFIRM="Kuruluma devam edilsin mi? [E/h]"
    MSG_CANCEL="Kurulum iptal edildi."
    MSG_DONE="Kurulum tamamlandı."
    MSG_ROOT="Bu betiği sudo ile çalıştırmayın. Gereken paketler için sudo ayrıca sorulur."
    MSG_UNSUPPORTED="Ubuntu 22.04 veya daha yeni bir sürüm gerekiyor."
else
    MSG_OS="Operating system"
    MSG_AUDIO="Audio server"
    MSG_DESKTOP="Desktop"
    MSG_PACKAGES="Packages to install"
    MSG_HEADSETS="Bluetooth audio devices"
    MSG_NO_HEADSET="none; the service will detect them after pairing"
    MSG_PATH="Install directory"
    MSG_CONFIRM="Continue with the installation? [Y/n]"
    MSG_CANCEL="Installation cancelled."
    MSG_DONE="Installation complete."
    MSG_ROOT="Do not run this script with sudo. It requests sudo for system packages when needed."
    MSG_UNSUPPORTED="Ubuntu 22.04 or newer is required."
fi

usage() {
    cat <<'EOF'
Usage: ./install.sh [--yes] [--dry-run]

  --yes      Skip the confirmation prompt
  --dry-run  Print the installation plan without changing the system
EOF
}

cleanup() {
    if [[ -n "${TEMP_DIR}" && -d "${TEMP_DIR}" ]]; then
        rm -rf -- "${TEMP_DIR}"
    fi
}
trap cleanup EXIT

while (($#)); do
    case "$1" in
        --yes|-y) ASSUME_YES=1 ;;
        --dry-run) DRY_RUN=1 ;;
        --help|-h) usage; exit 0 ;;
        *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
    esac
    shift
done

if ((EUID == 0)); then
    printf '%s\n' "${MSG_ROOT}" >&2
    exit 1
fi

if [[ ! -r /etc/os-release ]]; then
    printf 'Cannot read /etc/os-release.\n' >&2
    exit 1
fi

# shellcheck disable=SC1091
source /etc/os-release
OS_ID="${ID:-unknown}"
OS_VERSION="${VERSION_ID:-0}"
OS_PRETTY="${PRETTY_NAME:-${OS_ID} ${OS_VERSION}}"
if [[ "${OS_ID}" != "ubuntu" ]] || ! dpkg --compare-versions "${OS_VERSION}" ge "22.04"; then
    printf '%s Detected: %s\n' "${MSG_UNSUPPORTED}" "${OS_PRETTY}" >&2
    exit 1
fi

SCRIPT_SOURCE="${BASH_SOURCE[0]:-}"
if [[ -n "${SCRIPT_SOURCE}" ]]; then
    SCRIPT_DIR="$(cd -- "$(dirname -- "${SCRIPT_SOURCE}")" 2>/dev/null && pwd || true)"
else
    SCRIPT_DIR=""
fi

if [[ -n "${SCRIPT_DIR}" && -f "${SCRIPT_DIR}/src/ubuntu_ble_fixer/__init__.py" ]]; then
    SOURCE_DIR="${SCRIPT_DIR}"
else
    command -v curl >/dev/null 2>&1 || {
        printf 'curl is required to download %s.\n' "${APP_NAME}" >&2
        exit 1
    }
    TEMP_DIR="$(mktemp -d)"
    ARCHIVE_URL="https://github.com/${REPOSITORY}/archive/refs/heads/${BRANCH}.tar.gz"
    curl --fail --silent --show-error --location "${ARCHIVE_URL}" |
        tar -xz --strip-components=1 -C "${TEMP_DIR}"
    SOURCE_DIR="${TEMP_DIR}"
fi

APP_USER_HOME="${HOME:?HOME is not set}"
APP_DATA_HOME="${XDG_DATA_HOME:-${APP_USER_HOME}/.local/share}"
APP_CONFIG_HOME="${XDG_CONFIG_HOME:-${APP_USER_HOME}/.config}"
APP_DATA_DIR="${APP_DATA_HOME}/ubuntu-ble-fixer"
APP_BIN_DIR="${APP_USER_HOME}/.local/bin"
APP_BIN="${APP_BIN_DIR}/ubuntu-ble-fixer"
UNIT_DIR="${APP_CONFIG_HOME}/systemd/user"
UNIT_PATH="${UNIT_DIR}/ubuntu-ble-fixer.service"

AUDIO_SERVER="Not available"
if command -v pactl >/dev/null 2>&1; then
    AUDIO_SERVER="$(pactl info 2>/dev/null | sed -n 's/^Server Name: //p' | head -n1)"
    AUDIO_SERVER="${AUDIO_SERVER:-Not running}"
fi
DESKTOP="${XDG_CURRENT_DESKTOP:-Unknown} / ${XDG_SESSION_TYPE:-Unknown}"
HEADSETS=()
if command -v pactl >/dev/null 2>&1; then
    mapfile -t HEADSETS < <(
        pactl list cards 2>/dev/null |
            awk '
                /^Card #[0-9]+/ { bluetooth = 0 }
                /^[[:space:]]*Name: bluez_card/ { bluetooth = 1 }
                bluetooth && /device.description = "/ {
                    line = $0
                    sub(/^.*device.description = "/, "", line)
                    sub(/".*$/, "", line)
                    print line
                    bluetooth = 0
                }
            '
    )
fi

PACKAGES=(
    python3
    python3-gi
    gir1.2-gtk-3.0
    gir1.2-ayatanaappindicator3-0.1
    pulseaudio-utils
    libnotify-bin
    pavucontrol
)
if [[ "${AUDIO_SERVER}" == *PipeWire* ]] || dpkg --compare-versions "${OS_VERSION}" ge "23.10"; then
    PACKAGES+=(libspa-0.2-bluetooth wireplumber)
else
    PACKAGES+=(pulseaudio-module-bluetooth)
fi
if [[ "${XDG_CURRENT_DESKTOP:-}" == *GNOME* ]]; then
    PACKAGES+=(gnome-shell-extension-appindicator)
fi

MISSING_PACKAGES=()
for package in "${PACKAGES[@]}"; do
    if ! dpkg-query -W -f='${db:Status-Abbrev}' "${package}" 2>/dev/null | grep -q '^ii'; then
        MISSING_PACKAGES+=("${package}")
    fi
done

printf '\n%s %s\n' "${APP_NAME}" "1.0.0"
printf '%s: %s\n' "${MSG_OS}" "${OS_PRETTY}"
printf '%s: %s\n' "${MSG_AUDIO}" "${AUDIO_SERVER}"
printf '%s: %s\n' "${MSG_DESKTOP}" "${DESKTOP}"
printf '%s: %s\n' "${MSG_PATH}" "${APP_DATA_DIR}"
if ((${#HEADSETS[@]})); then
    printf '%s: %s\n' "${MSG_HEADSETS}" "${HEADSETS[*]}"
else
    printf '%s: %s\n' "${MSG_HEADSETS}" "${MSG_NO_HEADSET}"
fi
if ((${#MISSING_PACKAGES[@]})); then
    printf '%s: %s\n' "${MSG_PACKAGES}" "${MISSING_PACKAGES[*]}"
else
    printf '%s: %s\n' "${MSG_PACKAGES}" "none"
fi
printf '\n'

if ((DRY_RUN)); then
    exit 0
fi

if ((!ASSUME_YES)) && [[ -r /dev/tty ]]; then
    read -r -p "${MSG_CONFIRM} " reply </dev/tty
    if [[ -n "${reply}" && ! "${reply}" =~ ^[YyEe]$ ]]; then
        printf '%s\n' "${MSG_CANCEL}"
        exit 0
    fi
fi

if ((${#MISSING_PACKAGES[@]})); then
    sudo -v
    sudo apt-get update
    sudo apt-get install -y "${MISSING_PACKAGES[@]}"
fi

install -d -m 0755 "${APP_DATA_DIR}/ubuntu_ble_fixer" "${APP_BIN_DIR}" "${UNIT_DIR}"
while IFS= read -r -d '' source_file; do
    relative_path="${source_file#${SOURCE_DIR}/src/ubuntu_ble_fixer/}"
    install -D -m 0644 "${source_file}" "${APP_DATA_DIR}/ubuntu_ble_fixer/${relative_path}"
done < <(find "${SOURCE_DIR}/src/ubuntu_ble_fixer" -type f -name '*.py' -print0)
install -m 0755 "${SOURCE_DIR}/bin/ubuntu-ble-fixer" "${APP_BIN}"
install -m 0644 "${SOURCE_DIR}/systemd/ubuntu-ble-fixer.service" "${UNIT_PATH}"
install -m 0755 "${SOURCE_DIR}/uninstall.sh" "${APP_DATA_DIR}/uninstall.sh"

# Remove the pre-release MOMENTUM 4 prototype if it exists.
LEGACY_UNIT="${UNIT_DIR}/momentum4-codec-indicator.service"
if [[ -f "${LEGACY_UNIT}" ]]; then
    systemctl --user disable --now momentum4-codec-indicator.service >/dev/null 2>&1 || true
    rm -f -- "${LEGACY_UNIT}"
fi

systemctl --user daemon-reload
systemctl --user enable ubuntu-ble-fixer.service >/dev/null
if [[ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]]; then
    systemctl --user restart ubuntu-ble-fixer.service
fi

printf '\n%s\n' "${MSG_DONE}"
printf 'Command: %s status\n' "${APP_BIN}"
printf 'Service: systemctl --user status ubuntu-ble-fixer.service\n\n'
"${APP_BIN}" doctor || true
