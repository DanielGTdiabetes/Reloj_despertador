#!/usr/bin/env bash
set -e
set -u
set -o pipefail

APP_DIR="/home/dani/reloj_despertador"
SERVICE_SRC="$APP_DIR/scripts/reloj.service"
SERVICE_DST="/etc/systemd/system/reloj.service"

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this script with sudo."
  exit 1
fi

cd "$APP_DIR"

echo "[bootstrap] Installing system packages..."
apt-get update
apt-get install -y \
  python3-pip \
  python3-dev \
  python3-pil \
  python3-numpy \
  python3-rpi.gpio \
  python3-spidev \
  python3-pygame \
  python3-requests \
  python3-dateutil \
  python3-ephem \
  python3-tz \
  python3-ntplib \
  python3-smbus2 \
  python3-venv \
  i2c-tools \
  alsa-utils \
  git

echo "[bootstrap] Installing optional Python requirements..."
pip3 install --break-system-packages -r requirements.txt || \
  echo "[bootstrap] pip requirements skipped; using Raspberry Pi OS packages where available."

BOOT_CONFIG="/boot/firmware/config.txt"
if [ ! -f "$BOOT_CONFIG" ]; then
  BOOT_CONFIG="/boot/config.txt"
fi

echo "[bootstrap] Configuring boot hardware in $BOOT_CONFIG..."
touch "$BOOT_CONFIG"
sed -i 's/^[[:space:]]*dtparam=audio=on/# dtparam=audio=on/' "$BOOT_CONFIG"

grep -q '^dtparam=spi=on' "$BOOT_CONFIG" || echo 'dtparam=spi=on' >> "$BOOT_CONFIG"
grep -q '^dtoverlay=spi0-2cs' "$BOOT_CONFIG" || echo 'dtoverlay=spi0-2cs' >> "$BOOT_CONFIG"
grep -q '^dtparam=i2c_arm=on' "$BOOT_CONFIG" || echo 'dtparam=i2c_arm=on' >> "$BOOT_CONFIG"
grep -q '^dtparam=i2s=on' "$BOOT_CONFIG" || echo 'dtparam=i2s=on' >> "$BOOT_CONFIG"
grep -q '^dtoverlay=max98357a' "$BOOT_CONFIG" || echo 'dtoverlay=max98357a' >> "$BOOT_CONFIG"

echo "[bootstrap] Installing systemd service..."
install -m 0644 "$SERVICE_SRC" "$SERVICE_DST"
systemctl daemon-reload
systemctl enable reloj.service

echo "[bootstrap] Validating Python imports..."
python3 - <<'PY'
import importlib

modules = [
    "spidev",
    "PIL",
    "RPi.GPIO",
    "pygame",
    "requests",
    "numpy",
    "ephem",
    "pytz",
    "dateutil",
    "ntplib",
    "smbus2",
]

missing = []
for module in modules:
    try:
        importlib.import_module(module)
    except Exception as exc:
        missing.append(f"{module}: {exc}")

if missing:
    raise SystemExit("Missing imports:\n" + "\n".join(missing))
PY

echo "[bootstrap] Starting reloj.service..."
systemctl restart reloj.service
systemctl --no-pager -l status reloj.service || true

echo "[bootstrap] Done. Reboot if SPI/I2S was just enabled."
