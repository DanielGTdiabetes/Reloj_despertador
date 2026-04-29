# Cableado - Reloj Despertador Pi Zero W

## Resumen

Ambas pantallas usan SPI0:

- GC9A01 redonda en CE0, GPIO8.
- ST7789P3 rectangular en CE1, GPIO7.

Esto deja libres los GPIO18, GPIO19 y GPIO21 para el audio I2S MAX98357A.

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
| CS | GPIO7 | 26 | SPI0 CE1 |
| DC | GPIO22 | 15 | Data/command |
| RST | GPIO27 | 13 | Reset |
| BL | GPIO23 | 16 | Backlight activo LOW |

Config:

```json
{
  "spi_port": 0,
  "spi_device": 1,
  "cs_pin": 7,
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
| SPI | spi0.1 |
| Velocidad | 4 MHz |
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

## /boot/firmware/config.txt

Estado esperado:

```ini
dtparam=spi=on
dtparam=i2s=on
dtoverlay=max98357a
```

No usar:

```ini
dtparam=audio=on
dtoverlay=spi1-3cs
```

Motivo: SPI1 comparte GPIO21 con PCM_DOUT. Si SPI1 se activa, entra en
conflicto con el MAX98357A. Por eso las dos pantallas van en SPI0.
