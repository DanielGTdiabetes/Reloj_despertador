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
# git primero — necesario para clonar/actualizar el repositorio
apt-get install -y git
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
  pigpio \
  python3-pigpio

echo "[bootstrap] git version: $(git --version)"

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

# Habilitar interfaces (descomentar si existen, añadir si no)
function enable_dtparam() {
    local param=$1
    if grep -q "^#\?${param}" "$BOOT_CONFIG"; then
        sed -i "s/^#\?${param}/${param}/" "$BOOT_CONFIG"
    else
        echo "${param}" >> "$BOOT_CONFIG"
    fi
}

function enable_overlay() {
    local overlay=$1
    grep -q "^${overlay}" "$BOOT_CONFIG" || echo "${overlay}" >> "$BOOT_CONFIG"
}

enable_dtparam "dtparam=spi=on"
enable_overlay "dtoverlay=spi0-2cs"
enable_dtparam "dtparam=i2c_arm=on"

# GPIO18 se usa para PWM del backlight ST7789; eliminar overlays I2S/MAX98357A
# que reclamarían ese pin y dejarían la pantalla apagada.
sed -i 's/^[[:space:]]*dtparam=i2s=on/# dtparam=i2s=on/' "$BOOT_CONFIG"
sed -i '/^[[:space:]]*dtoverlay=max98357a/d' "$BOOT_CONFIG"

echo "[bootstrap] Generating alarm sounds..."
python3 - <<'PY'
import wave, struct, math, os

def generate_marimba_alarm(filepath):
    sample_rate = 44100
    os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
    note_freqs = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9, 523.3]
    note_dur, gap_dur, repeats, pause_dur = 0.35, 0.04, 3, 0.6

    def make_note(freq, duration):
        n = int(sample_rate * duration)
        samples = []
        for i in range(n):
            t = i / sample_rate
            val = math.sin(2 * math.pi * freq * t) + 0.18 * math.sin(2 * math.pi * freq * 2 * t)
            attack = min(t / 0.005, 1.0)
            decay  = math.exp(-4.5 * t / duration)
            samples.append(struct.pack('<h', int(val * attack * decay * 0.55 * 32767)))
        return samples

    def make_silence(duration):
        return [struct.pack('<h', 0)] * int(sample_rate * duration)

    all_samples = []
    for _ in range(repeats):
        for freq in note_freqs:
            all_samples += make_note(freq, note_dur)
            all_samples += make_silence(gap_dur)
        all_samples += make_silence(pause_dur)

    with wave.open(filepath, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        for s in all_samples:
            f.writeframesraw(s)
    print(f"[bootstrap] Generated {filepath} ({os.path.getsize(filepath)} bytes)")

base = "/home/dani/reloj_despertador/src/assets"
generate_marimba_alarm(f"{base}/sounds/alarm1.wav")
generate_marimba_alarm(f"{base}/sounds/beep.wav")
generate_marimba_alarm(f"{base}/alarm.wav")
PY

echo "[bootstrap] Installing systemd service..."
install -m 0644 "$SERVICE_SRC" "$SERVICE_DST"

echo "[bootstrap] Installing UPS HAT watchdog service..."
UPS_SERVICE_SRC="$APP_DIR/scripts/ups-watchdog.service"
UPS_SERVICE_DST="/etc/systemd/system/ups-watchdog.service"
if [ -f "$UPS_SERVICE_SRC" ]; then
    install -m 0644 "$UPS_SERVICE_SRC" "$UPS_SERVICE_DST"
    # Asegurar que las rutas apuntan a $APP_DIR
    sed -i "s|/home/pi/Reloj_despertador|$APP_DIR|g" "$UPS_SERVICE_DST"
    systemctl enable ups-watchdog.service
    echo "[bootstrap] ups-watchdog.service habilitado"
else
    echo "[bootstrap] AVISO: ups-watchdog.service no encontrado, omitiendo"
fi

systemctl daemon-reload
systemctl enable pigpiod
systemctl start pigpiod
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
    "pigpio",
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

echo "[bootstrap] Configuring UPS HAT auto power-on..."
python3 "$APP_DIR/scripts/ups_auto_start.py" && \
    echo "[bootstrap] UPS auto-arranque configurado OK" || \
    echo "[bootstrap] AVISO: UPS HAT no detectado (normal si el HAT no está instalado todavía)"

echo "[bootstrap] Starting reloj.service..."
systemctl restart reloj.service
systemctl --no-pager -l status reloj.service || true

if systemctl is-enabled ups-watchdog.service &>/dev/null; then
    systemctl restart ups-watchdog.service
    echo "[bootstrap] ups-watchdog.service iniciado"
fi

echo "[bootstrap] Done. Reboot if SPI/I2S was just enabled."
