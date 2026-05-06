# Cableado - Reloj Despertador Pi Zero W

## Resumen

Ambas pantallas comparten SPI0 con CS manual por GPIO:

- GC9A01 redonda: usa `/dev/spidev0.0`, CS manual en GPIO8 (CE0).
- ST7789 rectangular: usa `/dev/spidev0.1`, CS manual en **GPIO16, pin físico 36** (GPIO normal, NO CE hardware).

> [!IMPORTANT]
> **CONFIGURACIÓN DEFINITIVA (2026-05-06):**
> - ST7789 usa `spi_device=1` → `/dev/spidev0.1` como endpoint SPI.
> - CS real = GPIO16 (manual), NO GPIO7/CE1.
> - `no_cs=True` en spidev desactiva el CS hardware del kernel; el CS lo controla Python por GPIO.
> - `no_cs=True` NO convierte spidev0.0 y spidev0.1 en equivalentes: cada device es un handle distinto al driver SPI del kernel.
> - Overlay requerido: `dtoverlay=spi0-2cs` (debe existir `/dev/spidev0.1`).
> - NO usar `spi0.0` para ST7789.

## GC9A01 - Pantalla Redonda 240x240

| Pin pantalla | GPIO | Pin fisico | Notas |
|---|---:|---:|---|
| VCC | - | 1 | 3.3V |
| GND | - | 6 | GND |
| DIN / MOSI | GPIO10 | 19 | SPI0 MOSI |
| CLK / SCK | GPIO11 | 23 | SPI0 SCLK |
| CS | GPIO8 | 24 | SPI0 CE0 |
| DC | GPIO25 | 22 | Data/command |
| RST | GPIO26 | 37 | Reset |
| BL | - | - | Sin control por software |

Config:

```json
{
  "spi_port": 0,
  "spi_device": 0,
  "cs_pin": 8,
  "dc_pin": 25,
  "rst_pin": 26,
  "bl_pin": null
}
```

## ST7789P3 - Pantalla Rectangular 284x76

| Pin pantalla | GPIO | Pin fisico | Notas |
|---|---:|---:|---|
| VCC | - | 17 | 3.3V |
| GND | - | 20 | GND |
| MOSI | GPIO10 | 19 | Compartido con GC9A01 |
| SCK | GPIO11 | 23 | Compartido con GC9A01 |
| CS | **GPIO16** | **36** | GPIO normal, NO CE hardware |
| DC | GPIO22 | 15 | Data/command |
| RST | GPIO27 | 13 | Reset |
| BL | GPIO23 | 16 | Backlight activo LOW |

Config:

```json
{
  "spi_port": 0,
  "spi_device": 1,
  "cs_pin": 16,
  "dc_pin": 22,
  "rst_pin": 27,
  "bl_pin": 23,
  "col_offset": 18,
  "row_offset": 82
}
```

Parametros criticos del driver:

| Parametro | Valor |
|---|---:|
| Tamano logico | 284x76 |
| SPI | spi0.1 (`/dev/spidev0.1`) |
| CS manual | GPIO16 |
| no_cs | True (CS por GPIO, no kernel) |
| Velocidad init | 4 MHz |
| Velocidad frame | 16 MHz |
| Secuencia init | BuyDisplay / ER-TFTM2.25-1 |
| MADCTL | 0xA0 |
| COLMOD | 0x05 |
| Inversión | INVOFF (0x20) |
| col_offset | 18 |
| row_offset | 82 |
| Backlight | Activo LOW |

## Encoder Rotatorio

| Pin encoder | GPIO | Pin fisico |
|---|---:|---:|
| CLK / A | GPIO5 | 29 |
| DT / B | GPIO6 | 31 |
| SW | GPIO13 | 33 |
| VCC | - | 1 o 17 |
| GND | - | 9 |

Nota: el driver usa polling. No usa `GPIO.add_event_detect`, porque ese metodo
fallaba bajo systemd en esta instalacion.

## MAX98357A - Audio I2S

| Pin modulo | GPIO | Pin fisico | Senal |
|---|---:|---:|---|
| VIN | - | 2 o 4 | 5V |
| GND | - | 14 | GND |
| BCLK | GPIO18 | 12 | PCM_CLK |
| LRC | GPIO19 | 35 | PCM_FS |
| DIN | GPIO21 | 40 | PCM_DOUT |
| SD | - | sin conectar | Ganancia maxima |

## DFR0528 UPS HAT

El HAT se conecta directamente al header de 40 pines — **sin cableado adicional**.
Usa los pines I2C del propio header:

| Señal | GPIO | Pin físico | Notas |
|-------|------|-----------|-------|
| SDA   | GPIO2 | 3        | I2C bus 1, ya habilitado |
| SCL   | GPIO3 | 5        | I2C bus 1, ya habilitado |
| VCC   | —     | 2 ó 4    | 5V del header |
| GND   | —     | 6        | GND |

Dirección I2C: `0x10` (verificar con `i2cdetect -y 1` tras instalar)

Ver documentación completa en `docs/ups_hat.md`.

---

## /boot/firmware/config.txt

Estado correcto:

```ini
dtparam=spi=on
dtoverlay=spi0-2cs
dtparam=i2c_arm=on
dtparam=i2s=on
dtoverlay=max98357a
camera_auto_detect=0
display_auto_detect=0
```

Notas:
- `dtoverlay=spi0-2cs` crea `/dev/spidev0.0` y `/dev/spidev0.1`.
- `dtparam=spi=on` también activa SPI0; `spi0-2cs` asegura que ambos CE existan.
- NO usar `dtoverlay=spi0-1cs` — solo crea `/dev/spidev0.0`, la ST7789 necesita `/dev/spidev0.1`.
- NO usar `dtoverlay=spi1-3cs` — GPIO21 en conflicto con PCM_DOUT del MAX98357A.
