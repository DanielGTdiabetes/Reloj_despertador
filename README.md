# Reloj Despertador - Raspberry Pi Zero W

## Arquitectura SPI

Ambas pantallas comparten SPI0:
- **GC9A01** (redonda 240x240): `/dev/spidev0.0`, CS manual GPIO8.
- **ST7789** (rectangular 284x76): `/dev/spidev0.1`, CS manual GPIO16.

La ST7789 usa `spi_device=1` con `no_cs=True` y CS manual por GPIO16.
Requiere `dtoverlay=spi0-2cs` en config.txt para que exista `/dev/spidev0.1`.
NO usar `spi0.0` para la ST7789.

## Estado Actual y Configuración "Gold"
El sistema está configurado y validado para funcionar con una pantalla redonda GC9A01 y una rectangular ST7789 compartiendo el bus SPI0.

Para ver los detalles exactos de offsets, pines y comandos de inicialización, consulta la [Documentación Gold State](docs/GOLD_STATE.md).

## Instalación Limpia (Snapshot)
Para dejar el sistema tal cual está ahora en una Raspberry Pi nueva:
1. Asegúrate de tener acceso SSH a la Pi.
2. Ejecuta el script de despliegue completo:
   ```bash
   python scripts/full_bootstrap_deploy.py
   ```
   Este script se encarga de subir los archivos, configurar el hardware (config.txt), instalar dependencias y activar el servicio.

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
- `dtoverlay=spi0-2cs`
- `dtparam=i2c_arm=on`
- `dtoverlay=max98357a`
- `dtoverlay=watchdog=on`

## Configuración app (extracto)
`config/config.json`:
- `displays.rect.spi_device=1` (NO 0)
- `displays.rect.col_offset=18`
- `displays.rect.row_offset=82`
- `boot.startup_delay_seconds=3`
- `boot.diag_only_rect=false`
- `ups.enabled / i2c_bus / i2c_address / poll_interval`

## Diagnóstico SPI
```bash
python3 tools/spi_diag.py
```
Verifica: `/dev/spidev0.0`, `/dev/spidev0.1`, GPIO16 disponible, overlay correcto.

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
- Aparecen logs `[ST7789] init OK` y `[GC9A01] init OK` (en ese orden).
- ST7789 sale de blanco y pinta primer frame.
- Encoder responde.
- Audio I2S sigue operativo.
- Si no hay red, reloj/UI arrancan igualmente.
- Si UPS no está conectado, app continúa sin error fatal.
