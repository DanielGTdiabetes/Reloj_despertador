"""
Bring-up aislado de la pantalla redonda GC9A01.

Uso (en la Pi, con reloj.service parado):
    sudo systemctl stop reloj.service
    cd /home/dani/reloj_despertador
    python3 tools/bringup_round.py

Salida esperada:
    [GC9A01] RDDID = XXXXXX  (no 000000 ni ffffff)
    Secuencia visual: rojo → verde → azul → blanco → negro (1s cada uno).
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

from hardware.gc9a01 import GC9A01  # noqa: E402

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
        display = GC9A01(
            spi_port=0,
            spi_device=0,
            cs_pin=8,
            dc_pin=25,
            rst_pin=26,
            bl_pin=None,
        )

        for name, color in COLORS:
            img = Image.new("RGB", (display.WIDTH, display.HEIGHT), color)
            print(f"[bringup_round] {name}")
            display.display(img)
            time.sleep(1.0)

        print("[bringup_round] OK")
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
