#!/usr/bin/env bash
set -euo pipefail
# Solo spidev0.0 — el ST7789 usa CS manual en GPIO16, no necesita /dev/spidev0.1
for dev in /dev/spidev0.0; do
  if [ ! -e "$dev" ]; then
    echo "[BOOT] missing $dev"
    exit 1
  fi
done
if [ -e /dev/i2c-1 ]; then
  echo "[BOOT] i2c bus available"
fi
if [ ! -e /dev/gpiomem ]; then
  echo "[BOOT] missing /dev/gpiomem"
  exit 1
fi
echo "[BOOT] preflight OK"
