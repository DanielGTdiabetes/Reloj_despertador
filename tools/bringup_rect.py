"""
Bring-up aislado de la pantalla rectangular ST7789P3 — VERSIÓN DIAGNÓSTICO.

Uso (en la Pi, con reloj.service parado):
    sudo systemctl stop reloj.service
    cd /home/dani/reloj_despertador
    python3 tools/bringup_rect.py
    python3 tools/bringup_rect.py --hold        # espera 30s antes de cleanup
    python3 tools/bringup_rect.py --swap-offsets # prueba offsets invertidos
    python3 tools/bringup_rect.py --slow-spi     # init y frames a 1 MHz
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import RPi.GPIO as GPIO
import spidev
from PIL import Image
import numpy as np

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

    CS_PIN = 16
    DC_PIN = 22
    RST_PIN = 27
    BL_PIN = 23

    GPIO.setup(CS_PIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(DC_PIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(RST_PIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(BL_PIN, GPIO.OUT, initial=GPIO.HIGH)

    pwm = GPIO.PWM(BL_PIN, 200)
    pwm.start(100)

    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 1000000 if args.slow_spi else 24000000
    spi.mode = 0
    spi.no_cs = True

    def write_cmd(cmd, data=None):
        GPIO.output(CS_PIN, GPIO.LOW)
        GPIO.output(DC_PIN, GPIO.LOW)
        spi.writebytes([cmd])
        if data:
            GPIO.output(DC_PIN, GPIO.HIGH)
            spi.writebytes(list(data))
        GPIO.output(CS_PIN, GPIO.HIGH)

    def set_window(xs, ys, xe, ye):
        write_cmd(0x2A, [xs >> 8, xs & 0xFF, xe >> 8, xe & 0xFF])
        write_cmd(0x2B, [ys >> 8, ys & 0xFF, ye >> 8, ye & 0xFF])

    try:
        # Init Sequence
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.02)
        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.12)
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.2)

        write_cmd(0x01) # SWRESET
        time.sleep(0.18)
        write_cmd(0x11) # SLPOUT
        time.sleep(0.15)
        
        write_cmd(0x36, [0xA0]) # MADCTL (RGB order)
        write_cmd(0x3A, [0x05]) # COLMOD
        write_cmd(0x20) # INVOFF (Normal colors)
        write_cmd(0x13) # NORON
        time.sleep(0.01)
        write_cmd(0x29) # DISPON
        time.sleep(0.1)

        WIDTH = 284
        HEIGHT = 76

        for name, color in COLORS:
            img = Image.new("RGB", (WIDTH, HEIGHT), color)
            arr = np.asarray(img, dtype=np.uint8)
            rgb565 = (((arr[..., 0].astype(np.uint16) & 0xF8) << 8) | ((arr[..., 1].astype(np.uint16) & 0xFC) << 3) | (arr[..., 2].astype(np.uint16) >> 3))
            
            set_window(col_offset, row_offset, col_offset + WIDTH - 1, row_offset + HEIGHT - 1)
            
            GPIO.output(CS_PIN, GPIO.LOW)
            GPIO.output(DC_PIN, GPIO.LOW)
            spi.writebytes([0x2C]) # RAMWR
            GPIO.output(DC_PIN, GPIO.HIGH)
            spi.writebytes2(rgb565.astype(">u2").tobytes())
            GPIO.output(CS_PIN, GPIO.HIGH)

            pwm.ChangeDutyCycle(20) # Turn backlight on
            
            print(f"[bringup_rect] mostrando {name}...")
            time.sleep(1.0)

        print("[bringup_rect] secuencia de colores OK")

        if args.hold:
            print(f"[bringup_rect] HOLD: esperando 30s antes de cleanup...")
            time.sleep(30)

        return 0
    except Exception:
        import traceback
        traceback.print_exc()
        return 1
    finally:
        write_cmd(0x28) # DISPOFF
        write_cmd(0x10) # SLPIN
        pwm.ChangeDutyCycle(100)
        pwm.stop()
        spi.close()
        GPIO.cleanup()
        print("[bringup_rect] GPIO cleanup done")

if __name__ == "__main__":
    sys.exit(main())
