"""
Bring-up aislado de la pantalla rectangular ST7789P3.

Uso (en la Pi, con reloj.service parado):
    sudo systemctl stop reloj.service
    cd /home/dani/reloj_despertador
    python3 tools/bringup_rect.py

Salida esperada:
    [ST7789] RDDID = XXXXXX  (si HW responde; suele ser 000000 en este panel)
    Secuencia visual: rojo → verde → azul → blanco → negro (1s cada uno).

Si no se ve nada y la backlight queda apagada → init falló.
Si se ve solo backlight blanca → el chip no respondió al init pese a que la
secuencia SPI no lanzó error. Suele apuntar a fallo HW de DC=GPIO22 o
RST=GPIO27 (cable no llega al panel).
"""

from __future__ import annotations

import os
import sys
import time

import RPi.GPIO as GPIO
from PIL import Image

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.abspath(os.path.join(THIS_DIR, "..", "src"))
sys.path.insert(0, SRC_DIR)

from hardware.st7789 import ST7789Display  # noqa: E402

COLORS = [
    ("rojo",   (255, 0, 0)),
    ("verde",  (0, 255, 0)),
    ("azul",   (0, 0, 255)),
    ("blanco", (255, 255, 255)),
    ("negro",  (0, 0, 0)),
]


def main() -> int:
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    display = None
    try:
        display = ST7789Display(
            spi_port=0,
            spi_device=1,
            cs_pin=16,
            dc_pin=22,
            rst_pin=27,
            bl_pin=23,
            col_offset=82,
            row_offset=18,
        )

        for name, color in COLORS:
            img = Image.new("RGB", (display.WIDTH, display.HEIGHT), color)
            print(f"[bringup_rect] {name}")
            display.display(img)
            time.sleep(1.0)

        print("[bringup_rect] OK")
        return 0
    except Exception:
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if display:
            display.cleanup()
        GPIO.cleanup()


if __name__ == "__main__":
    sys.exit(main())
