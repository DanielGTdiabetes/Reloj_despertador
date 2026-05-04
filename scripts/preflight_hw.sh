#!/usr/bin/env bash
set -euo pipefail
for dev in /dev/spidev0.0 /dev/spidev0.1; do
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
