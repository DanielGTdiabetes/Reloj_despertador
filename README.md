# Reloj Despertador - Raspberry Pi Zero W

## Causa probable del fallo de pantalla blanca ST7789
Tras optimizar el arranque, el servicio puede iniciar antes de que SPI/GPIO estén estables. Si el CS manual (GPIO16) o el reset/backlight de la ST7789 quedan en estado no seguro durante boot, la pantalla puede quedarse en blanco aunque el código antiguo sea correcto.

## Cambios de robustez aplicados
- Bus SPI centralizado con lock global y transacciones seguras (`try/finally`, todos los CS en HIGH al salir).
- Inicialización temprana de CS conocidos y perfiles por dispositivo.
- ST7789 con init robusta, delays mayores, backlight apagado durante init y reintento automático.
- Validación de configuración de pantallas al arranque (dimensiones/pines duplicados/uso I2C reservado).
- Modo diagnóstico para arrancar solo ST7789 (`boot.diag_only_rect=true`).
- `startup_delay_seconds` configurable para mitigar carreras de boot.
- Servicio systemd con `preflight` de `/dev/spidev*`, `/dev/gpiomem`, e I2C opcional.

## Tabla de pines (auditada)
| GPIO | Función | Dirección | Periférico | Riesgo |
|---|---|---|---|---|
| 10 | SPI0 MOSI | OUT | GC9A01 + ST7789 | Compartido (normal) |
| 11 | SPI0 SCLK | OUT | GC9A01 + ST7789 | Compartido (normal) |
| 8  | CS GC9A01 (manual) | OUT | GC9A01 | Bajo |
| 16 | CS ST7789 (manual) | OUT | ST7789 | Crítico en boot (se fija HIGH al inicio) |
| 25 | DC GC9A01 | OUT | GC9A01 | Bajo |
| 26 | RST GC9A01 | OUT | GC9A01 | Bajo |
| 22 | DC ST7789 | OUT | ST7789 | Bajo |
| 27 | RST ST7789 | OUT | ST7789 | Medio (timing reset) |
| 23 | BL ST7789 | OUT/PWM | ST7789 | Medio (encender solo tras init) |
| 5,6,13 | Encoder | IN | UI | Bajo |
| 18,19,21 | I2S MAX98357A | ALT | Audio | Alto si se cambian overlays |
| 2,3 | I2C SDA/SCL | ALT | UPS futuro | Reservados, no reutilizar |

## Configuración recomendada de boot
Usar en `/boot/firmware/config.txt` (o `/boot/config.txt` según distro):
- `dtparam=spi=on`
- `dtparam=i2c_arm=on`
- `dtoverlay=max98357a`
- `dtoverlay=watchdog=on`

## Configuración app (extracto)
`config/config.json`:
- `displays.rect.col_offset=82`
- `displays.rect.row_offset=18`
- `boot.startup_delay_seconds=3`
- `boot.diag_only_rect=false`
- `ups.enabled / i2c_bus / i2c_address / poll_interval`

## Test mínimo ST7789 solo
```bash
DISABLE_ROUND=1 DISABLE_AUDIO=1 DISABLE_WEATHER=1 python3 tools/bringup_rect.py
```

## Test mínimo alternando ambas
```bash
python3 tools/bringup_round.py &
python3 tools/bringup_rect.py
```

## Despliegue en Raspberry Pi
```bash
git pull
sudo cp scripts/reloj.service /etc/systemd/system/reloj.service
sudo cp scripts/preflight_hw.sh /usr/local/bin/reloj-preflight.sh
sudo sed -i 's#ExecStartPre=.*#ExecStartPre=/bin/bash /home/dani/reloj_despertador/scripts/preflight_hw.sh#' /etc/systemd/system/reloj.service
sudo systemctl daemon-reload
sudo systemctl enable reloj.service
sudo systemctl restart reloj.service
journalctl -u reloj.service -f
```

## Rollback rápido
```bash
git log --oneline -n 5
git reset --hard <commit_bueno>
sudo systemctl restart reloj.service
```

## Checklist tras reinicio en frío
- Aparece log `[BOOT] preflight OK`.
- Aparecen logs `[GC9A01] init OK` y `[ST7789] init OK`.
- ST7789 sale de blanco y pinta primer frame.
- Encoder responde.
- Audio I2S sigue operativo.
- Si no hay red, reloj/UI arrancan igualmente.
- Si UPS no está conectado, app continúa sin error fatal.
