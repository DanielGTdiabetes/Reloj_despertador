"""
Bring-up aislado de la pantalla rectangular ST7789P3 — VERSIÓN DIAGNÓSTICO.

Uso (en la Pi, con reloj.service parado):
    sudo systemctl stop reloj.service
    cd /home/dani/reloj_despertador
    python3 tools/bringup_rect.py
    python3 tools/bringup_rect.py --hold        # espera 30s antes de cleanup
    python3 tools/bringup_rect.py --swap-offsets # prueba offsets invertidos
    python3 tools/bringup_rect.py --slow-spi     # init y frames a 1 MHz

Salida esperada:
    [ST7789] RDDID = XXXXXX  (si HW responde; suele ser 000000 en este panel)
    Secuencia visual: rojo → verde → azul → blanco → negro (1s cada uno).

Si no se ve nada y la backlight queda apagada → init falló.
Si se ve solo backlight blanca → el chip no respondió al init pese a que la
secuencia SPI no lanzó error. Suele apuntar a fallo HW de DC=GPIO22 o
RST=GPIO27 (cable no llega al panel).
"""

from __future__ import annotations

import argparse
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
    parser = argparse.ArgumentParser(description="Bringup ST7789 con opciones de diagnóstico")
    parser.add_argument("--hold", action="store_true", help="Espera 30s antes de cleanup para observar")
    parser.add_argument("--swap-offsets", action="store_true", help="Prueba col_offset=82, row_offset=18")
    parser.add_argument("--slow-spi", action="store_true", help="Usa 1 MHz para init y frames")
    args = parser.parse_args()

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    col_offset = 82 if args.swap_offsets else 18
    row_offset = 18 if args.swap_offsets else 82

    print("[BRINGUP] opening /dev/spidev0.0")
    print("[BRINGUP] using manual CS GPIO16")
    print("[BRINGUP] spi.no_cs=True")
    print("[BRINGUP] DC GPIO22")
    print("[BRINGUP] RST GPIO27")
    print("[BRINGUP] BL GPIO23 active LOW")
    print(f"[bringup_rect] col_offset={col_offset}, row_offset={row_offset}")
    print(f"[bringup_rect] slow_spi={args.slow_spi}")
    print(f"[bringup_rect] hold={args.hold}")

    original_output = GPIO.output
    def patched_output(pin, state):
        if pin == 16:
            state_str = "HIGH" if state else "LOW"
            print(f"[BRINGUP] CS GPIO16 state changed to: {state_str}")
        original_output(pin, state)
    GPIO.output = patched_output

    GPIO.setup(22, GPIO.OUT, initial=GPIO.HIGH)
    print(f"[BRINGUP] DC GPIO22 state before init: {GPIO.input(22)}")

    display = None
    try:
        display = ST7789Display(
            spi_port=0,
            spi_device=0,
            cs_pin=16,
            dc_pin=22,
            rst_pin=27,
            bl_pin=23,
            col_offset=col_offset,
            row_offset=row_offset,
        )

        print(f"[BRINGUP] DC GPIO22 state after init: {GPIO.input(22)}")

        if args.slow_spi:
            # Forzar velocidad baja en el perfil SPI
            bus = display._bus
            for profile in bus._profiles.values():
                object.__setattr__(profile, "init_speed_hz", 1_000_000)
                object.__setattr__(profile, "frame_speed_hz", 1_000_000)
            print("[bringup_rect] SPI speed forzado a 1 MHz")

        for name, color in COLORS:
            img = Image.new("RGB", (display.WIDTH, display.HEIGHT), color)
            print(f"[bringup_rect] mostrando {name}...")
            display.display(img)
            time.sleep(1.0)

        print("[bringup_rect] secuencia de colores OK")

        if args.hold:
            print(f"[bringup_rect] HOLD: esperando 30s antes de cleanup...")
            print(f"[bringup_rect] Observa la pantalla. Debería mostrar negro (último color).")
            time.sleep(30)

        return 0
    except Exception:
        import traceback
        traceback.print_exc()
        return 1
    finally:
        if display:
            print("[bringup_rect] llamando a display.cleanup()...")
            display.cleanup()
        GPIO.cleanup()
        print("[bringup_rect] GPIO cleanup done")


if __name__ == "__main__":
    sys.exit(main())
