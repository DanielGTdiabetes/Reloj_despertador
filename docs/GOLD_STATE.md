# Reloj Despertador - Gold State (Snapshot 2026-05-06)

Este documento describe la configuración exacta y validada que hace funcionar el sistema de doble pantalla. Úsalo como referencia absoluta para instalaciones limpias o depuración.

## 1. Hardware Snapshot

### Pantalla Rectangular (ST7789)
- **Resolución:** 284x76 píxeles.
- **Offsets de memoria:** `Col=18`, `Row=82` (Crucial para que la imagen no salga cortada).
- **Inversión de color:** `INVOFF` (Comando `0x20`). No usar negativo.
- **Orden de color:** `RGB` (MADCTL `0xA0`).
- **Velocidad SPI:** 16 MHz (Estable en Pi Zero W con cables cortos).
- **Pines:**
  - `CS`: GPIO 16 (Manual, modo `no_cs=True`).
  - `DC`: GPIO 22.
  - `RST`: GPIO 27.
  - `BL`: **GPIO 18** (hardware PWM0 via pigpio — movido desde GPIO23 el 2026-05-10).

### Pantalla Redonda (GC9A01)
- **Resolución:** 240x240 píxeles.
- **Inversión de color:** `INVON` (Comando `0x21`).
- **Pines:**
  - `CS`: GPIO 8 (Manual).
  - `DC`: GPIO 25.
  - `RST`: GPIO 26.

## 2. Configuración del Sistema (Raspberry Pi)

El archivo de boot config suele ser `/boot/firmware/config.txt` (o `/boot/config.txt` según distro).

### Mínimo imprescindible
```ini
dtparam=spi=on
dtoverlay=spi0-2cs
dtparam=i2c_arm=on
```

> ❌ `dtparam=i2s=on` y `dtoverlay=max98357a` **eliminados** (2026-05-10).  
> El MAX98357A causaba pantalla rectangular en blanco. Audio desactivado.  
> GPIO18 reasignado a BL ST7789 (hardware PWM0).

### Recomendado (pero no imprescindible para las pantallas)
```ini
dtoverlay=watchdog=on
camera_auto_detect=0
display_auto_detect=0
```

### Sudoers (WIFI scan)
La app escanea redes con `sudo -n /sbin/iwlist wlan0 scan`. En una instalación limpia, configura sudoers para permitir ese comando sin contraseña al usuario del servicio.

### systemd
- Servicio: `scripts/reloj.service` → `/etc/systemd/system/reloj.service`
- Preflight: `scripts/preflight_hw.sh` (verifica `/dev/spidev0.0`, `/dev/spidev0.1`, `/dev/gpiomem`)

## 3. Configuración de la Aplicación (`config/config.json`)

```json
{
    "displays": {
        "round": {
            "spi_port": 0,
            "spi_device": 0,
            "cs_pin": 8,
            "dc_pin": 25,
            "rst_pin": 26
        },
        "rect": {
            "spi_port": 0,
            "spi_device": 1,
            "cs_pin": 16,
            "dc_pin": 22,
            "rst_pin": 27,
            "bl_pin": 18,
            "col_offset": 18,
            "row_offset": 82
        }
    }
}
```

## 4. Instalación Limpia Automatizada

Para replicar este estado en una Pi recién formateada:

1. Instalar Raspberry Pi OS Lite (64-bit o 32-bit).
2. Clonar el repositorio.
3. Ejecutar desde tu PC local:
   ```bash
   python scripts/full_bootstrap_deploy.py
   ```
   Este script:
   - Limpia el directorio remoto.
   - Sube todos los archivos (src, config, scripts).
   - Instala paquetes de sistema (`spidev`, `Pillow`, `Rpi.GPIO`).
   - Configura el `/boot/config.txt` con los overlays necesarios.
   - Instala el servicio systemd y reinicia la Pi.

## 5. Verificación de Funcionamiento

- **Logs del sistema:** `journalctl -u reloj.service -f`
- **Diagnóstico SPI:** `python3 tools/spi_diag.py` (Debe detectar `/dev/spidev0.0` y `/dev/spidev0.1`).
- **Test Rectangular:** `python3 tools/bringup_rect.py` (Debe mostrar barras de colores correctas).
