"""
Bringup rectángulo ST7789 — matriz de 4 combinaciones SPI/CS.

PRUEBA A: spi0.1 + CS manual GPIO16 + no_cs=True   (config actual)
PRUEBA B: spi0.1 + CS hardware CE1/GPIO7  + no_cs=False
PRUEBA C: spi0.0 + CS manual GPIO16 + no_cs=True
PRUEBA D: spi0.0 + CS hardware CE0/GPIO8 + no_cs=False

Uso:
    sudo systemctl stop reloj.service
    python3 tools/bringup_rect_matrix.py

Cada prueba muestra ROJO→VERDE→AZUL (2s cada uno).
Al final pregunta al usuario qué combinación se vio.

IMPORTANTE: Cada prueba reinicia completamente el SpiBus singleton
y los pines GPIO para evitar interferencias entre pruebas.
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

# Importamos las clases base pero NO usamos ST7789Display directamente
# porque su nombre SPI fijo "st7789" colisiona entre pruebas.
# En su lugar, creamos instancias con nombres únicos.
from hardware.spi_bus import SpiBus, SpiDeviceProfile  # noqa: E402

DC_PIN, RST_PIN, BL_PIN = 22, 27, 23
COL_OFFSET, ROW_OFFSET = 18, 82
WIDTH, HEIGHT = 284, 76

# Comandos ST7789
CMD_SWRESET = 0x01
CMD_SLPOUT = 0x11
CMD_NORON = 0x13
CMD_DISPOFF = 0x28
CMD_DISPON = 0x29
CMD_CASET = 0x2A
CMD_RASET = 0x2B
CMD_RAMWR = 0x2C
CMD_MADCTL = 0x36
CMD_COLMOD = 0x3A

COLORS_RGB = [
    ("ROJO",   (255, 0, 0)),
    ("VERDE",  (0, 255, 0)),
    ("AZUL",   (0, 0, 255)),
]


def rgb_to_rgb565_be(r, g, b):
    """Convierte un color RGB a 2 bytes RGB565 big-endian."""
    val = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return [(val >> 8) & 0xFF, val & 0xFF]


def fill_buffer(color_rgb):
    """Crea un buffer RGB565 big-endian lleno de un color."""
    two_bytes = rgb_to_rgb565_be(*color_rgb)
    return (two_bytes * (WIDTH * HEIGHT))[:2 * WIDTH * HEIGHT]


def hard_reset():
    """Secuencia de reset hardware."""
    GPIO.output(RST_PIN, GPIO.HIGH)
    time.sleep(0.02)
    GPIO.output(RST_PIN, GPIO.LOW)
    time.sleep(0.12)
    GPIO.output(RST_PIN, GPIO.HIGH)
    time.sleep(0.20)


def spi_cmd(spi, cmd):
    """Envía un comando SPI (DC=LOW)."""
    GPIO.output(DC_PIN, GPIO.LOW)
    spi.writebytes([cmd])


def spi_data(spi, data):
    """Envía datos SPI (DC=HIGH)."""
    GPIO.output(DC_PIN, GPIO.HIGH)
    spi.writebytes2(data)


def spi_cd(spi, cmd, data=None):
    """Envía comando + datos en UNA sola transacción (CS no toggle)."""
    GPIO.output(DC_PIN, GPIO.LOW)
    spi.writebytes([cmd])
    if data is not None:
        GPIO.output(DC_PIN, GPIO.HIGH)
        spi.writebytes2(data)


def init_st7789(spi):
    """Inicializa el ST7789 usando transacciones correctas (cmd+data juntos)."""
    hard_reset()

    spi_cmd(spi, CMD_SWRESET); time.sleep(0.18)
    spi_cmd(spi, CMD_SLPOUT); time.sleep(0.15)
    spi_cd(spi, CMD_MADCTL, [0xA0])
    spi_cd(spi, CMD_COLMOD, [0x05])
    spi_cmd(spi, 0x20)  # INVOFF
    spi_cmd(spi, CMD_NORON)
    spi_cmd(spi, CMD_DISPON)
    time.sleep(0.10)


def set_window(spi, col_off, row_off, w, h):
    """Configura la ventana de escritura."""
    xs, ys = col_off, row_off
    xe, ye = xs + w - 1, ys + h - 1
    spi_cd(spi, CMD_CASET, [xs >> 8, xs & 0xFF, xe >> 8, xe & 0xFF])
    spi_cd(spi, CMD_RASET, [ys >> 8, ys & 0xFF, ye >> 8, ye & 0xFF])


def send_frame(spi, buf):
    """Envía un frame completo."""
    set_window(spi, COL_OFFSET, ROW_OFFSET, WIDTH, HEIGHT)
    spi_cmd(spi, CMD_RAMWR)
    GPIO.output(DC_PIN, GPIO.HIGH)
    spi.writebytes2(buf)


def run_test(label, spi_port, spi_device, cs_pin, use_hw_cs):
    """
    Ejecuta una prueba de bringup.

    use_hw_cs=True  → CS hardware del spidev (no_cs=False, CS gestionado por kernel)
    use_hw_cs=False → CS manual con GPIO (no_cs=True, CS gestionado por nosotros)
    """
    import spidev

    print(f"\n{'='*60}")
    print(f"  PRUEBA {label}: spi{spi_port}.{spi_device}  CS={'HW GPIO'+str(cs_pin) if use_hw_cs else 'MANUAL GPIO'+str(cs_pin)}")
    print(f"{'='*60}")

    # Abrir spidev
    spi = spidev.SpiDev()
    try:
        spi.open(spi_port, spi_device)
        spi.no_cs = not use_hw_cs
        spi.mode = 0
        spi.bits_per_word = 8
        spi.max_speed_hz = 4_000_000  # Init speed
    except Exception as exc:
        print(f"  [FALLO] No se pudo abrir spidev{spi_port}.{spi_device}: {exc}")
        return False

    # Configurar pines
    GPIO.setup(DC_PIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(RST_PIN, GPIO.OUT, initial=GPIO.HIGH)
    GPIO.setup(BL_PIN, GPIO.OUT, initial=GPIO.HIGH)

    if not use_hw_cs:
        GPIO.setup(cs_pin, GPIO.OUT, initial=GPIO.HIGH)

    # Backlight ON (active LOW → duty 0 = full brightness)
    pwm = GPIO.PWM(BL_PIN, 200)
    pwm.start(0)
    time.sleep(0.1)

    print(f"  spidev{spi_port}.{spi_device} abierto, no_cs={not use_hw_cs}")
    print(f"  BL ON (PWM 0%), RST HIGH, DC HIGH")

    # Init
    try:
        if use_hw_cs:
            # CS hardware: el kernel lo gestiona automáticamente
            init_st7789(spi)
        else:
            # CS manual: envolver cada operación
            GPIO.output(cs_pin, GPIO.LOW)
            init_st7789(spi)
            GPIO.output(cs_pin, GPIO.HIGH)

        print(f"  [ST7789] init enviado")
    except Exception as exc:
        print(f"  [FALLO] Init falló: {exc}")
        pwm.stop()
        spi.close()
        return False

    # Mostrar colores
    try:
        for color_name, color_rgb in COLORS_RGB:
            buf = fill_buffer(color_rgb)

            if use_hw_cs:
                send_frame(spi, buf)
            else:
                GPIO.output(cs_pin, GPIO.LOW)
                send_frame(spi, buf)
                GPIO.output(cs_pin, GPIO.HIGH)

            print(f"    {color_name} visible? (2s)")
            time.sleep(2.0)
    except Exception as exc:
        print(f"  [FALLO] Envío de frame falló: {exc}")
        pwm.stop()
        spi.close()
        return False

    # Cleanup
    pwm.stop()
    try:
        if use_hw_cs:
            spi_cmd(spi, CMD_DISPOFF)
            spi_cmd(spi, CMD_SLPIN)
        else:
            GPIO.output(cs_pin, GPIO.LOW)
            spi_cmd(spi, CMD_DISPOFF)
            spi_cmd(spi, CMD_SLPIN)
            GPIO.output(cs_pin, GPIO.HIGH)
    except Exception:
        pass

    spi.close()
    GPIO.output(BL_PIN, GPIO.HIGH)  # BL off

    print(f"  [OK] Prueba {label} completada")
    return True


def main() -> int:
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    results = {}

    # A: spi0.1 + CS manual GPIO16 + no_cs=True
    results["A"] = run_test("A", 0, 1, 16, use_hw_cs=False)

    # B: spi0.1 + CS hardware CE1/GPIO7 + no_cs=False
    results["B"] = run_test("B", 0, 1, 7, use_hw_cs=True)

    # C: spi0.0 + CS manual GPIO16 + no_cs=True
    results["C"] = run_test("C", 0, 0, 16, use_hw_cs=False)

    # D: spi0.0 + CS hardware CE0/GPIO8 + no_cs=False
    results["D"] = run_test("D", 0, 0, 8, use_hw_cs=True)

    print(f"\n{'='*60}")
    print("  RESUMEN DE PRUEBAS:")
    print(f"    A (spi0.1 + CS16 manual):      {'OK' if results['A'] else 'FALLO'}")
    print(f"    B (spi0.1 + CS7 hardware):     {'OK' if results['B'] else 'FALLO'}")
    print(f"    C (spi0.0 + CS16 manual):      {'OK' if results['C'] else 'FALLO'}")
    print(f"    D (spi0.0 + CS8 hardware):     {'OK' if results['D'] else 'FALLO'}")
    print(f"{'='*60}")

    print("\n  PREGUNTA: ¿Cuál combinación mostró colores en la pantalla?")
    print("  Responde A, B, C, D, o 'ninguna' si no se vio nada.")
    print("  Si se vio en varias, indica cuáles.")

    GPIO.cleanup()
    return 0


if __name__ == "__main__":
    sys.exit(main())
