"""
Diagnóstico SPI para Reloj Despertador.

Verifica que el sistema está configurado correctamente para dual-display:
  - /dev/spidev0.0 existe (GC9A01)
  - /dev/spidev0.1 existe (ST7789)
  - GPIO16 disponible como salida manual
  - Overlay esperado: spi0-2cs

Uso:
    python3 tools/spi_diag.py
"""

from __future__ import annotations

import os
import sys
import subprocess


def check_file(path: str, label: str) -> bool:
    exists = os.path.exists(path)
    status = "OK" if exists else "FALTA"
    print(f"  [{status}] {label}: {path}")
    return exists


def check_gpio16() -> bool:
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(16, GPIO.OUT, initial=GPIO.HIGH)
        val = GPIO.input(16)
        GPIO.cleanup(16)
        print(f"  [OK] GPIO16 disponible como salida (lectura={val})")
        return True
    except Exception as exc:
        print(f"  [FALLO] GPIO16 no disponible: {exc}")
        return False


def check_overlay() -> bool:
    candidates = [
        "/boot/firmware/config.txt",
        "/boot/config.txt",
    ]
    found = False
    for path in candidates:
        if not os.path.exists(path):
            continue
        try:
            content = open(path).read()
        except Exception:
            continue
        if "spi0-2cs" in content:
            print(f"  [OK] dtoverlay=spi0-2cs encontrado en {path}")
            found = True
        elif "spi=on" in content and "spi0-1cs" not in content:
            print(f"  [WARN] dtparam=spi=on en {path} (puede crear 2 CS, pero no se confirma spi0-2cs)")
            found = True
        elif "spi0-1cs" in content:
            print(f"  [FALLO] dtoverlay=spi0-1cs en {path} — solo crea /dev/spidev0.0, se necesita spi0-2cs")
            found = False
        else:
            print(f"  [WARN] {path} existe pero no se encontró configuración SPI clara")
    if not found:
        print(f"  [FALLO] No se encontró config.txt en ninguna ruta esperada")
    return found


def check_spidev_module() -> bool:
    try:
        import spidev
        print(f"  [OK] Módulo spidev disponible (v{getattr(spidev, '__version__', '?')})")
        return True
    except ImportError:
        print(f"  [FALLO] Módulo spidev no instalado")
        return False


def main() -> int:
    print("=" * 60)
    print("  Diagnóstico SPI — Reloj Despertador")
    print("=" * 60)

    results = []

    print("\n[1] Dispositivos SPI:")
    results.append(check_file("/dev/spidev0.0", "GC9A01 spidev0.0"))
    results.append(check_file("/dev/spidev0.1", "ST7789 spidev0.1"))

    print("\n[2] Módulo spidev:")
    results.append(check_spidev_module())

    print("\n[3] GPIO16 (CS manual ST7789):")
    results.append(check_gpio16())

    print("\n[4] Overlay de boot:")
    results.append(check_overlay())

    print("\n[5] Configuración ST7789 esperada:")
    print("  spi_port   = 0")
    print("  spi_device = 1  → /dev/spidev0.1")
    print("  cs_pin     = 16 (GPIO manual)")
    print("  no_cs      = True")

    print("\n" + "=" * 60)
    if all(results):
        print("  RESULTADO: TODO OK")
        print("=" * 60)
        return 0
    else:
        print("  RESULTADO: HAY PROBLEMAS — revisar los [FALLO] de arriba")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
