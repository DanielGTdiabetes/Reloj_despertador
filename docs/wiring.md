# Cableado - Reloj Despertador Pi Zero W

## Resumen

Ambas pantallas usan SPI0 con CS manual por GPIO:

- GC9A01 redonda: CS en GPIO8 (CE0 hardware).
- ST7789P3 rectangular: CS en **GPIO16, pin físico 36** (GPIO normal, NO CE hardware).

> [!IMPORTANT]
> **CAMBIO CRÍTICO 2026-05-02:** El CS del ST7789 se movió de GPIO7 (pin 26, CE1) a
> **GPIO16 (pin 36, GPIO normal)**. GPIO7 causaba un glitch en cold boot porque el
> kernel lo inicializa como CE1 al cargar el overlay SPI aunque no lo usemos.
> Con GPIO16 el kernel no lo toca y el bug de pantalla blanca en cold boot desaparece.
>
> El overlay de boot es ahora `dtoverlay=spi0-1cs` (solo expone CE0).
> Ambas pantallas usan `spi_device: 0` porque solo existe `/dev/spidev0.0`.

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
  "spi_device": 0,
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
| SPI | spi0.0 (unico device) |
| Velocidad | 32 MHz |
| Secuencia init | BuyDisplay / ER-TFTM2.25-1 |
| MADCTL | 0xA8 |
| COLMOD | 0x05 |
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

Estado correcto (tras fix cold boot):

```ini
dtoverlay=spi0-1cs
dtparam=i2c_arm=on
dtoverlay=max98357a
camera_auto_detect=0
display_auto_detect=0
```

No usar `dtparam=spi=on` — activa CE0 y CE1, y el kernel toca GPIO7 en boot.
No usar `dtoverlay=spi0-2cs` — mismo problema.
No usar `dtoverlay=spi1-3cs` — GPIO21 en conflicto con PCM_DOUT del MAX98357A.
