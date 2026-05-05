"""
Diagnóstico GPIO/DC/RST/BL para ST7789.

Ejecutar EN LA PI con:
    python3 tools/gpio_diag.py

Verifica que los pines responden correctamente antes de tocar SPI.
"""

from __future__ import annotations

import sys
import time

import RPi.GPIO as GPIO

DC_PIN  = 22
RST_PIN = 27
BL_PIN  = 23


def main() -> int:
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    all_ok = True

    print("=" * 60)
    print("  GPIO Diagnostic — ST7789")
    print("=" * 60)

    print(f"\n[1] Configurando GPIO{DC_PIN} (DC) como OUTPUT...")
    try:
        GPIO.setup(DC_PIN, GPIO.OUT, initial=GPIO.HIGH)
        print(f"    HIGH → ", end="")
        GPIO.output(DC_PIN, GPIO.HIGH)
        time.sleep(0.5)
        val = GPIO.input(DC_PIN)
        print(f"lectura={val} {'OK' if val else 'FALLO'}")
        if not val:
            all_ok = False

        print(f"    LOW  → ", end="")
        GPIO.output(DC_PIN, GPIO.LOW)
        time.sleep(0.5)
        val = GPIO.input(DC_PIN)
        print(f"lectura={val} {'OK' if not val else 'FALLO'}")
        if val:
            all_ok = False
    except Exception as exc:
        print(f"    FALLO: {exc}")
        all_ok = False

    print(f"\n[2] Configurando GPIO{RST_PIN} (RST) como OUTPUT...")
    try:
        GPIO.setup(RST_PIN, GPIO.OUT, initial=GPIO.HIGH)
        print(f"    HIGH → ", end="")
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.5)
        val = GPIO.input(RST_PIN)
        print(f"lectura={val} {'OK' if val else 'FALLO'}")
        if not val:
            all_ok = False

        print(f"    LOW  → ", end="")
        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.5)
        val = GPIO.input(RST_PIN)
        print(f"lectura={val} {'OK' if not val else 'FALLO'}")
        if val:
            all_ok = False
    except Exception as exc:
        print(f"    FALLO: {exc}")
        all_ok = False

    print(f"\n[3] Configurando GPIO{BL_PIN} (BL) como OUTPUT...")
    try:
        GPIO.setup(BL_PIN, GPIO.OUT, initial=GPIO.HIGH)
        print(f"    HIGH → ", end="")
        GPIO.output(BL_PIN, GPIO.HIGH)
        time.sleep(0.5)
        val = GPIO.input(BL_PIN)
        print(f"lectura={val} {'OK' if val else 'FALLO'}")
        if not val:
            all_ok = False

        print(f"    LOW  → ", end="")
        GPIO.output(BL_PIN, GPIO.LOW)
        time.sleep(0.5)
        val = GPIO.input(BL_PIN)
        print(f"lectura={val} {'OK' if not val else 'FALLO'}")
        if val:
            all_ok = False
    except Exception as exc:
        print(f"    FALLO: {exc}")
        all_ok = False

    print(f"\n[4] Secuencia RST (reset físico del panel)...")
    try:
        GPIO.setup(RST_PIN, GPIO.OUT, initial=GPIO.HIGH)
        print(f"    RST HIGH  (200ms)...")
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.20)
        print(f"    RST LOW   (120ms)...")
        GPIO.output(RST_PIN, GPIO.LOW)
        time.sleep(0.12)
        print(f"    RST HIGH  (200ms)...")
        GPIO.output(RST_PIN, GPIO.HIGH)
        time.sleep(0.20)
        print(f"    [OK] Secuencia completada")
    except Exception as exc:
        print(f"    FALLO: {exc}")
        all_ok = False

    print(f"\n[5] Backlight PWM test...")
    try:
        GPIO.setup(BL_PIN, GPIO.OUT, initial=GPIO.HIGH)
        pwm = GPIO.PWM(BL_PIN, 200)

        for duty in (100, 50, 0, 100):
            pwm.start(duty)
            print(f"    BL duty={duty}% (debería cambiar brillo visible)")
            time.sleep(1.0)

        pwm.stop()
        print(f"    [OK] PWM funcional")
    except Exception as exc:
        print(f"    FALLO: {exc}")
        all_ok = False

    print(f"\n" + "=" * 60)
    if all_ok:
        print("  RESULTADO: TODO OK")
    else:
        print("  RESULTADO: HAY PROBLEMAS — revisar arriba")
    print("=" * 60)

    GPIO.cleanup()
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())