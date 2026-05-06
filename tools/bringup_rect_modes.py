"""
Herramienta interactiva para probar combinaciones de init (extendido/no),
COLMOD, MADCTL y offsets en la pantalla rectangular ST7789 (284x76).

Bug fix:
- Configura `GPIO.setmode(GPIO.BCM)` y `GPIO.setwarnings(False)` al inicio de `main()`
  antes de usar `SpiBus.instance().close()` o `ST7789Display`.
- Evita `GPIO.cleanup()` entre combinaciones: solo se hace al final del script.
- Cierra SPI (`SpiBus.instance().close()`) antes de `GPIO.cleanup()`.
"""

from __future__ import annotations

import inspect
import os
import sys
import time
from typing import Optional

import RPi.GPIO as GPIO
from PIL import Image, ImageDraw

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from src.hardware.spi_bus import SpiBus  # noqa: E402
from src.hardware.st7789 import ST7789Display  # noqa: E402

INIT_MODES = [False, True]
COLMODS = [0x05, 0x55]
MADCTLS = [0xA0, 0xA8, 0x70, 0x00, 0x60]
OFFSETS = [(18, 82), (82, 18), (0, 0)]

SPI_PORT = 0
SPI_DEVICE = 1
CS_PIN = 16


def _apply_extended_init_if_needed(display: ST7789Display, init_extended: bool) -> None:
    """
    Compatibilidad hacia atrás: algunas versiones de `ST7789Display` no aceptan
    `init_extended` como parámetro. En ese caso, si se solicita, enviamos aquí
    los comandos extra típicos del init extendido.
    """
    if not init_extended:
        return

    # Secuencia basada en la variante extendida usada en este proyecto.
    display._cd(0xB2, [0x0C, 0x0C, 0x00, 0x33, 0x33], init_phase=True)  # PORCTRL
    display._cd(0xB7, [0x35], init_phase=True)  # GCTRL
    display._cd(0xBB, [0x1F], init_phase=True)  # VCOMS
    display._cd(0xC0, [0x2C], init_phase=True)  # LCMCTRL
    display._cd(0xC2, [0x01], init_phase=True)  # VDVVRHEN
    display._cd(0xC3, [0x12], init_phase=True)  # VRHS
    display._cd(0xC4, [0x20], init_phase=True)  # VDVS
    display._cd(0xC6, [0x0F], init_phase=True)  # FRCTRL2
    display._cd(0xD0, [0xA4, 0xA1], init_phase=True)  # PWCTRL1


def _create_display(
    *,
    init_ext: bool,
    colmod: int,
    madctl: int,
    offset: tuple[int, int],
) -> ST7789Display:
    """
    Crea una instancia de `ST7789Display` soportando dos APIs:
    - Nueva: acepta `init_extended`, `madctl_val`, `colmod_val`
    - Antigua: no los acepta; se aplican después vía `_cd()`
    """
    sig = inspect.signature(ST7789Display.__init__)
    supports_params = {"init_extended", "madctl_val", "colmod_val"}.issubset(sig.parameters.keys())

    if supports_params:
        return ST7789Display(
            spi_port=SPI_PORT,
            spi_device=SPI_DEVICE,
            cs_pin=CS_PIN,
            col_offset=offset[0],
            row_offset=offset[1],
            init_extended=init_ext,
            madctl_val=madctl,
            colmod_val=colmod,
        )

    display = ST7789Display(
        spi_port=SPI_PORT,
        spi_device=SPI_DEVICE,
        cs_pin=CS_PIN,
        col_offset=offset[0],
        row_offset=offset[1],
    )

    _apply_extended_init_if_needed(display, init_ext)
    display._cd(display.CMD_MADCTL, [madctl], init_phase=True)
    display._cd(display.CMD_COLMOD, [colmod], init_phase=True)
    return display


def test_config(init_ext: bool, colmod: int, madctl: int, offset: tuple[int, int]) -> bool:
    print("=" * 60)
    print("Probando configuración:")
    print(f"  init_extended : {init_ext} (False = Mínima, True = Extendida)")
    print(f"  colmod        : 0x{colmod:02X}")
    print(f"  madctl        : 0x{madctl:02X}")
    print(f"  col_offset    : {offset[0]}")
    print(f"  row_offset    : {offset[1]}")
    print(f"  spi_device    : {SPI_DEVICE}")
    print(f"  cs_pin        : {CS_PIN}")
    print("  velocidad SPI : 24MHz (frame) / 4MHz (init)")
    print("-" * 60)

    display: Optional[ST7789Display] = None
    try:
        # Forzar un bus limpio entre combinaciones (pero sin tocar GPIO.cleanup).
        SpiBus.instance().close()
        time.sleep(0.1)

        display = _create_display(init_ext=init_ext, colmod=colmod, madctl=madctl, offset=offset)

        # Imagen de prueba: borde + cruz + textos (offset/orientación).
        img = Image.new("RGB", (ST7789Display.WIDTH, ST7789Display.HEIGHT), "black")
        draw = ImageDraw.Draw(img)

        draw.rectangle(
            (0, 0, ST7789Display.WIDTH - 1, ST7789Display.HEIGHT - 1),
            outline="red",
            width=2,
        )
        draw.line((0, 0, ST7789Display.WIDTH - 1, ST7789Display.HEIGHT - 1), fill="green", width=1)
        draw.line((0, ST7789Display.HEIGHT - 1, ST7789Display.WIDTH - 1, 0), fill="green", width=1)

        draw.text((10, 10), f"MADCTL: 0x{madctl:02X}", fill="white")
        draw.text((10, 30), f"EXT: {init_ext}", fill="white")
        draw.text((10, 50), f"OFF: {offset[0]},{offset[1]}", fill="white")

        display.display(img)
        display.set_brightness(50)

        print(">>> Observa la pantalla.")
        print(">>> ENTER = siguiente · 'q' + ENTER = salir")
        cmd = input().strip().lower()

        return cmd != "q"
    except Exception as exc:
        print(f"ERROR al inicializar o probar: {exc}")
        print(">>> ENTER = continuar · 'q' + ENTER = salir")
        cmd = input().strip().lower()
        return cmd != "q"
    finally:
        # No hacemos GPIO.cleanup aquí: solo al final del script.
        if display is not None:
            try:
                display.cleanup()
            except Exception:
                pass
        try:
            SpiBus.instance().close()
        except Exception:
            pass


def main() -> int:
    print("Iniciando herramienta interactiva de prueba ST7789...")
    print("Se iterará por todas las combinaciones.")

    # Requerido: configurar modo GPIO ANTES de usar SpiBus/ST7789Display.
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    try:
        for ext in INIT_MODES:
            for cm in COLMODS:
                for md in MADCTLS:
                    for off in OFFSETS:
                        if not test_config(ext, cm, md, off):
                            print("Pruebas canceladas por el usuario.")
                            return 0

        print("Todas las combinaciones han sido probadas.")
        return 0
    finally:
        # Requerido: cerrar SPI antes del cleanup de GPIO.
        try:
            SpiBus.instance().close()
        except Exception:
            pass
        GPIO.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())

