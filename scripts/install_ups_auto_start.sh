#!/usr/bin/env bash
# install_ups_auto_start.sh — Instala el watchdog del UPS HAT en la Raspberry Pi.
#
# Ejecutar en la Pi como root (o con sudo):
#   sudo bash scripts/install_ups_auto_start.sh
#
# Qué hace:
#   1. Copia el servicio systemd ups-watchdog.service a /etc/systemd/system/
#   2. Lo habilita para que arranque en cada boot
#   3. Lo inicia ahora mismo
#   4. Verifica que el HAT responde y que el auto-arranque está configurado
#
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_SRC="$SCRIPT_DIR/ups-watchdog.service"
SERVICE_DST="/etc/systemd/system/ups-watchdog.service"

echo "=== Instalando UPS HAT watchdog ==="

# 1. Verificar dependencias
if ! python3 -c "import smbus2" 2>/dev/null; then
    echo "Instalando smbus2..."
    pip3 install smbus2
fi

# 2. Verificar que el HAT responde antes de instalar
echo "Comprobando comunicación con el HAT..."
python3 "$SCRIPT_DIR/ups_auto_start.py" --info || {
    echo "ERROR: No se detectó el UPS HAT en I2C. Verifica que:"
    echo "  - El HAT está conectado a la Pi Zero"
    echo "  - I2C está habilitado (sudo raspi-config → Interface Options → I2C)"
    echo "  - smbus2 está instalado: pip3 install smbus2"
    exit 1
}

# 3. Instalar servicio systemd
echo "Instalando servicio systemd..."
cp "$SERVICE_SRC" "$SERVICE_DST"
chmod 644 "$SERVICE_DST"

# Ajustar la ruta del proyecto en el servicio si no es /home/pi/Reloj_despertador
if [ "$PROJECT_DIR" != "/home/pi/Reloj_despertador" ]; then
    sed -i "s|/home/pi/Reloj_despertador|$PROJECT_DIR|g" "$SERVICE_DST"
    echo "Rutas ajustadas a: $PROJECT_DIR"
fi

# 4. Habilitar e iniciar
systemctl daemon-reload
systemctl enable ups-watchdog.service
systemctl start ups-watchdog.service

echo ""
echo "=== Instalación completada ==="
systemctl status ups-watchdog.service --no-pager
echo ""
echo "El HAT ahora arrancará la Pi automáticamente 1 minuto después"
echo "de que vuelva la corriente o la batería se recupere."
echo ""
echo "Para cambiar el tiempo de espera, edita AUTO_RESTART_MINUTES"
echo "en scripts/ups_watchdog.py y reinicia el servicio:"
echo "  sudo systemctl restart ups-watchdog.service"
