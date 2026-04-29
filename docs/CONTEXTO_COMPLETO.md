# Contexto Actual - Reloj Despertador Pi Zero W

Actualizado: 2026-04-28.

Este documento sustituye notas antiguas de diagnostico. La configuracion valida
de la pantalla rectangular es la de la variante `E`.

## Estado

- Proyecto local Windows: `D:\Reloj_despertador`
- Proyecto en Raspberry Pi: `/home/dani/reloj_despertador`
- Servicio: `reloj.service`
- Estado tras ultimo despliegue: `active`
- Pantalla redonda GC9A01: funciona.
- Pantalla rectangular ST7789P3: usa driver nuevo basado en variante `E`.
- Encoder: polling.
- Audio: MAX98357A por I2S.

## Pantalla Redonda GC9A01

| Senal | GPIO | Pin fisico |
|---|---:|---:|
| MOSI | GPIO10 | 19 |
| SCK | GPIO11 | 23 |
| CS | GPIO8 | 24 |
| DC | GPIO25 | 22 |
| RST | GPIO26 | 37 |
| BL | sin control | - |

Configuracion:

```json
{
  "spi_port": 0,
  "spi_device": 0,
  "dc_pin": 25,
  "rst_pin": 26,
  "bl_pin": null
}
```

## Pantalla Rectangular ST7789P3

| Senal | GPIO | Pin fisico | Notas |
|---|---:|---:|---|
| MOSI | GPIO10 | 19 | Compartido con GC9A01 |
| SCK | GPIO11 | 23 | Compartido con GC9A01 |
| CS | GPIO7 | 26 | SPI0 CE1 |
| DC / RS | GPIO22 | 15 | Data/command |
| RST | GPIO27 | 13 | Reset |
| BL | GPIO23 | 16 | Backlight activo LOW |

Configuracion valida:

```json
{
  "driver": "ST7789",
  "width": 284,
  "height": 76,
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

Parametros del driver:

- Secuencia de inicializacion: BuyDisplay / ER-TFTM2.25-1.
- `MADCTL=0xA8`.
- `COLMOD=0x05`.
- Tamano logico: `284x76`.
- Offsets: `col_offset=18`, `row_offset=82`.
- RGB565 en orden normal.
- SPI: `spi0.1`.
- Velocidad: `4 MHz`.
- CS: `GPIO7`, controlado por software (`spi.no_cs=True` cuando esta disponible).
- Backlight activo LOW.

## Hallazgo Que Corrigio La Rectangular

Las configuraciones anteriores de ST7789P3 quedan descartadas. Para continuar,
usar solo la variante `E` documentada arriba.

La primera salida reconocible aparecio despues de:

- Sustituir la pantalla rectangular por otra igual.
- Sustituir el cable de reset.
- Volver a poner CS en `GPIO7`.
- Probar patrones con varias orientaciones.

La variante `E` fue la que se vio mejor:

- `MADCTL=0xA8`.
- `width=284`, `height=76`.
- `col_offset=18`, `row_offset=82`.
- RGB565 sin intercambio de bytes.

## Sistema

`/boot/firmware/config.txt` esperado:

```ini
dtparam=spi=on
dtparam=i2s=on
dtoverlay=max98357a
```

No activar SPI1 para este proyecto: entra en conflicto con los pines I2S del
MAX98357A.

## Archivos Clave

- `src/main.py`: controlador principal.
- `src/hardware/gc9a01.py`: driver pantalla redonda.
- `src/hardware/st7789.py`: driver pantalla rectangular con configuracion `E`.
- `src/hardware/rotary_encoder.py`: encoder por polling.
- `src/hardware/audio.py`: audio I2S.
- `src/ui/round_home.py`: UI redonda.
- `src/ui/rect_ui.py`: UI rectangular.
- `config/config.json`: configuracion de pines y servicios.

## Pendiente

- Confirmar visualmente la app real con el driver permanente.
- Si la imagen sale pero no queda perfecta, ajustar UI/orientacion desde la base
  `MADCTL=0xA8`, no volver a la configuracion descartada.
