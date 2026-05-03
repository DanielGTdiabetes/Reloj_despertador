#!/usr/bin/env bash
# optimize_boot.sh — Ejecutar UNA VEZ en la Pi Zero W como root.
# Desactiva servicios innecesarios y aplica parámetros de kernel para
# reducir el tiempo de arranque en ~15-25 segundos.
#
# Uso: sudo bash scripts/optimize_boot.sh
# Requiere: reiniciar tras completar.

set -euo pipefail

log()  { echo "[boot-opt] $*"; }
warn() { echo "[boot-opt] WARN: $*"; }

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: ejecutar como root (sudo bash $0)"
    exit 1
fi

# ── 1. Servicios a deshabilitar ───────────────────────────────────────────────
# Bluetooth (Pi Zero W no lo usa aquí, ahorra ~2s y conflictos HCI)
DISABLE_SERVICES=(
    bluetooth.service
    hciuart.service
    ModemManager.service
    triggerhappy.service
    raspi-config.service
    apt-daily.service
    apt-daily.timer
    apt-daily-upgrade.service
    apt-daily-upgrade.timer
    man-db.timer
    motd-news.timer
    fstrim.timer
)

for svc in "${DISABLE_SERVICES[@]}"; do
    if systemctl list-unit-files --quiet "$svc" 2>/dev/null | grep -q "$svc"; then
        systemctl disable --now "$svc" 2>/dev/null || true
        systemctl mask "$svc" 2>/dev/null || true
        log "masked $svc"
    else
        log "skip (not found): $svc"
    fi
done

# ── 2. Parámetros de kernel (cmdline.txt) ────────────────────────────────────
CMDLINE_FILE=""
for f in /boot/firmware/cmdline.txt /boot/cmdline.txt; do
    [[ -f $f ]] && { CMDLINE_FILE=$f; break; }
done

if [[ -z $CMDLINE_FILE ]]; then
    warn "cmdline.txt no encontrado, saltando parámetros de kernel"
else
    log "cmdline: $CMDLINE_FILE"
    CURRENT=$(cat "$CMDLINE_FILE")

    # quiet: suprime mensajes de kernel en consola (ahorra ~0.5s de UART)
    # loglevel=3: solo errores a consola (warnings al journal)
    # fastboot: omite fsck en disco limpio
    PARAMS=("quiet" "loglevel=3" "fastboot")

    UPDATED="$CURRENT"
    for p in "${PARAMS[@]}"; do
        if ! echo "$UPDATED" | grep -qw "$p"; then
            UPDATED="$UPDATED $p"
            log "cmdline: añadido '$p'"
        else
            log "cmdline: '$p' ya presente"
        fi
    done

    if [[ "$UPDATED" != "$CURRENT" ]]; then
        cp "$CMDLINE_FILE" "${CMDLINE_FILE}.bak"
        # cmdline.txt debe ser una sola línea
        echo "$UPDATED" | tr -s ' ' | sed 's/[[:space:]]*$//' > "$CMDLINE_FILE"
        log "cmdline.txt actualizado (backup en ${CMDLINE_FILE}.bak)"
    fi
fi

# ── 3. systemd-networkd en lugar de dhcpcd (opcional) ───────────────────────
# dhcpcd tarda ~8s. Si se migra a systemd-networkd/networkd-dispatcher
# se puede ganar hasta 5s adicionales. NO se hace automáticamente porque
# requiere configurar la interfaz wlan0 manualmente.
log ""
log "INFO: Para ganar ~5s más, considera migrar de dhcpcd a systemd-networkd."
log "      Ver: https://www.raspberrypi.com/documentation/computers/configuration.html"

# ── 4. Verificar estado ────────────────────────────────────────────────────────
log ""
log "Optimizaciones aplicadas. Analiza el arranque tras reiniciar con:"
log "  systemd-analyze"
log "  systemd-analyze blame | head -20"
log "  systemd-analyze critical-chain reloj.service"
log ""
log "Reinicia ahora con: sudo reboot"
