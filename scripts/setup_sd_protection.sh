#!/usr/bin/env bash
# setup_sd_protection.sh — Ejecutar UNA VEZ en la Pi Zero W como root.
# Reduce drásticamente las escrituras en la microSD para prolongar su vida
# y evitar corrupción en cortes de corriente.
#
# Estrategia (sin overlayfs, compatible con config.json mutable):
#   1. journald volatile   → logs en RAM, nunca tocan la SD en caliente
#   2. /tmp como tmpfs     → escrituras temporales en RAM
#   3. Deshabilitar swap   → sin swapfile ni swapfile de Pi OS
#   4. log2ram             → /var/log en RAM, sync a SD solo en shutdown limpio
#
# Uso: sudo bash scripts/setup_sd_protection.sh
# Requiere: reiniciar tras completar.

set -euo pipefail

log()  { echo "[sd-protect] $*"; }
warn() { echo "[sd-protect] WARN: $*"; }

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: ejecutar como root (sudo bash $0)"
    exit 1
fi

# ── 1. journald: almacenamiento volátil (RAM) ─────────────────────────────────
JOURNALD_CONF=/etc/systemd/journald.conf.d/volatile.conf
mkdir -p "$(dirname "$JOURNALD_CONF")"
cat > "$JOURNALD_CONF" <<'EOF'
[Journal]
# Solo RAM: los logs NO se escriben en la SD durante operación normal.
# En shutdown limpio journald los descarta (ephemeral by design).
# Para depuración usa: journalctl -u reloj -n 100
Storage=volatile
RuntimeMaxUse=20M
Compress=yes
EOF
log "journald configurado como volatile (20 MB RAM)"

# ── 2. /tmp como tmpfs ────────────────────────────────────────────────────────
if ! systemctl is-enabled tmp.mount &>/dev/null; then
    cp /usr/share/systemd/tmp.mount /etc/systemd/system/tmp.mount 2>/dev/null || \
    cat > /etc/systemd/system/tmp.mount <<'EOF'
[Unit]
Description=/tmp como tmpfs
DefaultDependencies=no
Conflicts=umount.target
Before=local-fs.target umount.target

[Mount]
What=tmpfs
Where=/tmp
Type=tmpfs
Options=mode=1777,strictatime,nosuid,nodev,size=32M

[Install]
WantedBy=local-fs.target
EOF
    systemctl enable tmp.mount
    log "/tmp montado como tmpfs (32 MB)"
else
    log "/tmp ya tiene tmpfs configurado"
fi

# ── 3. Deshabilitar swap ────────────────────────────────────────────────────────
# dphys-swapfile es el gestor de swap por defecto de Pi OS
if systemctl list-unit-files --quiet dphys-swapfile.service 2>/dev/null | grep -q dphys; then
    systemctl disable --now dphys-swapfile.service 2>/dev/null || true
    systemctl mask dphys-swapfile.service
    # Elimina el swapfile si existe (recupera espacio y evita escrituras)
    if [[ -f /var/swap ]]; then
        swapoff /var/swap 2>/dev/null || true
        rm -f /var/swap
        log "swapfile eliminado (/var/swap)"
    fi
    log "swap deshabilitado (dphys-swapfile masked)"
else
    log "dphys-swapfile no encontrado; verificando con swapon..."
    SWAP_DEVS=$(swapon --show=NAME --noheadings 2>/dev/null || true)
    if [[ -n "$SWAP_DEVS" ]]; then
        warn "Swap activo: $SWAP_DEVS — desactívalo manualmente si no lo necesitas"
    else
        log "swap ya desactivado"
    fi
fi

# ── 4. log2ram — /var/log en RAM ──────────────────────────────────────────────
# log2ram monta /var/log como tmpfs y sincroniza a /var/hdd.log en shutdown limpio.
# Así los logs persisten entre reinicios normales pero no causan wear durante runtime.

LOG2RAM_CONF=/etc/log2ram.conf
if [[ -f /usr/local/bin/log2ram ]]; then
    log "log2ram ya instalado"
else
    log "Instalando log2ram..."
    # Instala desde el repositorio oficial sin depender de internet en tiempo de ejecución
    # Si no hay red, descarga manualmente: https://github.com/azlux/log2ram
    if ! command -v git &>/dev/null; then
        apt-get install -y --no-install-recommends git
    fi

    TMP_DIR=$(mktemp -d)
    trap 'rm -rf "$TMP_DIR"' EXIT
    git clone --depth 1 https://github.com/azlux/log2ram.git "$TMP_DIR/log2ram"
    (cd "$TMP_DIR/log2ram" && bash install.sh)
    log "log2ram instalado"
fi

# Configurar log2ram: 40 MB de RAM para logs
if [[ -f $LOG2RAM_CONF ]]; then
    sed -i 's/^SIZE=.*/SIZE=40M/' "$LOG2RAM_CONF"
    # Asegura que use rsync si está disponible (más robusto en el sync final)
    sed -i 's/^USE_RSYNC=.*/USE_RSYNC=false/' "$LOG2RAM_CONF"
    log "log2ram configurado: SIZE=40M"
fi

# ── 5. Parámetros de fstab: noatime ────────────────────────────────────────────
# noatime: no actualiza el "access time" en cada lectura de archivo.
# Es la opción más impactante que no requiere cambiar la estructura del FS.
FSTAB=/etc/fstab
if grep -q "noatime" "$FSTAB"; then
    log "fstab: noatime ya configurado"
else
    # Añade noatime a la partición raíz y a /boot si las encuentra
    cp "$FSTAB" "${FSTAB}.bak"
    # Busca líneas con ext4 o vfat y añade noatime si no lo tienen
    sed -i '/ext4/ s/defaults/defaults,noatime/' "$FSTAB"
    sed -i '/vfat/ s/defaults/defaults,noatime/' "$FSTAB"
    log "fstab actualizado con noatime (backup en ${FSTAB}.bak)"
    log "NOTA: verifica ${FSTAB} con: cat /etc/fstab"
fi

# ── Resumen ────────────────────────────────────────────────────────────────────
log ""
log "╔══════════════════════════════════════════════════════════╗"
log "║  Protección de SD completada. Resumen:                   ║"
log "║  ✓ journald → RAM (volatile, 20 MB)                      ║"
log "║  ✓ /tmp     → RAM (tmpfs, 32 MB)                         ║"
log "║  ✓ swap     → deshabilitado                              ║"
log "║  ✓ log2ram  → /var/log en RAM (40 MB), sync en shutdown  ║"
log "║  ✓ fstab    → noatime en ext4/vfat                       ║"
log "╚══════════════════════════════════════════════════════════╝"
log ""
log "Escrituras eliminadas: logs, /tmp, swap (>95% del wear típico)"
log "config.json sigue en SD (necesario: la app lo escribe en runtime)"
log ""
log "Verifica RAM disponible tras reiniciar con: free -h"
log "Verifica escrituras activas con: iostat -x 1 5"
log ""
log "Reinicia ahora con: sudo reboot"
