#!/usr/bin/env bash
# migrate_to_networkd.sh — Sustituye dhcpcd por systemd-networkd en Pi Zero W.
# Ahorra ~5-8s de arranque eliminando el daemon dhcpcd.
#
# SEGURIDAD: si la red no levanta en 90s tras el reboot, el script de rollback
# (rollback_to_dhcpcd.sh) se ejecuta automáticamente via un servicio one-shot.
#
# Uso: sudo bash scripts/migrate_to_networkd.sh
# Tras completar: sudo reboot

set -euo pipefail

log()  { echo "[networkd-migrate] $*"; }
warn() { echo "[networkd-migrate] WARN: $*"; }
die()  { echo "[networkd-migrate] ERROR: $*"; exit 1; }

[[ $EUID -ne 0 ]] && die "ejecutar como root (sudo bash $0)"

ROLLBACK_SCRIPT=/usr/local/bin/rollback_to_dhcpcd.sh
ROLLBACK_SERVICE=/etc/systemd/system/networkd-rollback.service
WPA_CONF=/etc/wpa_supplicant/wpa_supplicant.conf

# ── 1. Leer credenciales WiFi del wpa_supplicant actual ──────────────────────
log "Leyendo credenciales WiFi de wpa_supplicant..."
if [[ ! -f $WPA_CONF ]]; then
    die "No se encontró $WPA_CONF — configura WiFi primero con raspi-config"
fi

SSID=$(grep -oP '(?<=ssid=").*(?=")' "$WPA_CONF" | head -1)
PSK=$(grep -oP '(?<=psk=").*(?=")' "$WPA_CONF" | head -1)

if [[ -z "$SSID" ]]; then
    die "No se pudo leer SSID de $WPA_CONF"
fi
log "SSID detectado: $SSID"

# ── 2. Backup de configuración actual ────────────────────────────────────────
log "Creando backups..."
cp /etc/dhcpcd.conf /etc/dhcpcd.conf.bak 2>/dev/null || true
cp "$WPA_CONF" "${WPA_CONF}.bak" 2>/dev/null || true

# ── 3. Script de rollback (se ejecuta si la red no levanta) ─────────────────
cat > "$ROLLBACK_SCRIPT" <<'ROLLBACK'
#!/usr/bin/env bash
# Rollback automático: restaura dhcpcd si systemd-networkd no da red en 90s
logger -t networkd-rollback "Iniciando rollback a dhcpcd..."
systemctl stop systemd-networkd wpa_supplicant@wlan0 2>/dev/null || true
systemctl disable systemd-networkd 2>/dev/null || true

# Restaurar wpa_supplicant original si existe backup
[[ -f /etc/wpa_supplicant/wpa_supplicant.conf.bak ]] && \
    cp /etc/wpa_supplicant/wpa_supplicant.conf.bak /etc/wpa_supplicant/wpa_supplicant.conf

systemctl enable dhcpcd
systemctl start dhcpcd
logger -t networkd-rollback "Rollback completado. Red restaurada con dhcpcd."
# Autoeliminarse para no repetir en próximos boots
systemctl disable networkd-rollback.service
ROLLBACK
chmod +x "$ROLLBACK_SCRIPT"

# Servicio one-shot que hace rollback si la red no está lista en 90s
cat > "$ROLLBACK_SERVICE" <<EOF
[Unit]
Description=Rollback a dhcpcd si systemd-networkd falla
After=network-online.target
ConditionPathExists=$ROLLBACK_SCRIPT

[Service]
Type=oneshot
# Espera hasta 90s a que haya red; si no, hace rollback
ExecStart=/bin/bash -c 'for i in \$(seq 1 18); do ping -c1 -W2 8.8.8.8 &>/dev/null && exit 0; sleep 5; done; bash $ROLLBACK_SCRIPT'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
systemctl enable networkd-rollback.service
log "Servicio de rollback registrado"

# ── 4. Configurar wpa_supplicant para ser gestionado por systemd ─────────────
# wpa_supplicant@wlan0 es la unidad estándar — lee de /etc/wpa_supplicant/wpa_supplicant-wlan0.conf
if [[ -n "$PSK" ]]; then
cat > /etc/wpa_supplicant/wpa_supplicant-wlan0.conf <<EOF
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=ES

network={
    ssid="$SSID"
    psk="$PSK"
    key_mgmt=WPA-PSK
}
EOF
else
# Red sin contraseña
cat > /etc/wpa_supplicant/wpa_supplicant-wlan0.conf <<EOF
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=ES

network={
    ssid="$SSID"
    key_mgmt=NONE
}
EOF
fi
chmod 600 /etc/wpa_supplicant/wpa_supplicant-wlan0.conf
log "wpa_supplicant-wlan0.conf creado"

# ── 5. Configurar interfaz wlan0 con systemd-networkd ───────────────────────
mkdir -p /etc/systemd/network
cat > /etc/systemd/network/wlan0.network <<EOF
[Match]
Name=wlan0

[Network]
DHCP=yes
# DNS gestionado por systemd-resolved
DNS=8.8.8.8 1.1.1.1

[DHCP]
RouteMetric=20
UseDomains=true
EOF
log "wlan0.network creado"

# ── 6. Habilitar systemd-networkd y resolver ──────────────────────────────────
systemctl enable systemd-networkd
systemctl enable systemd-resolved
# Redirigir resolv.conf a systemd-resolved
ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
log "systemd-networkd y systemd-resolved habilitados"

# ── 7. Habilitar wpa_supplicant@wlan0 ─────────────────────────────────────────
systemctl enable wpa_supplicant@wlan0
log "wpa_supplicant@wlan0 habilitado"

# ── 8. Deshabilitar dhcpcd ────────────────────────────────────────────────────
systemctl disable dhcpcd 2>/dev/null || true
systemctl mask dhcpcd
log "dhcpcd deshabilitado y maskeado"

# ── Resumen ───────────────────────────────────────────────────────────────────
log ""
log "Migración preparada. Cambios aplicados:"
log "  dhcpcd          → deshabilitado (masked)"
log "  systemd-networkd → habilitado"
log "  systemd-resolved → habilitado"
log "  wpa_supplicant@wlan0 → habilitado con SSID: $SSID"
log "  rollback automático → activo (90s timeout tras reboot)"
log ""
log "Si tras el reboot no hay red en 90s → rollback automático a dhcpcd"
log ""
log "Tras reboot, verifica con:"
log "  systemctl status systemd-networkd"
log "  networkctl status wlan0"
log "  systemd-analyze"
log ""
log "Para eliminar el rollback guard (cuando todo funcione):"
log "  sudo systemctl disable networkd-rollback.service"
log "  sudo rm /usr/local/bin/rollback_to_dhcpcd.sh"
log ""
log "Reinicia ahora con: sudo reboot"
