#!/usr/bin/env python3
"""
ups_auto_start.py — Configura el DFR0528 UPS HAT para auto-arranque.

Ejecutar una vez en cada arranque de la Pi (via systemd o rc.local).
Escribe el timer de auto-arranque en el MCU del HAT. El MCU guarda este
valor en memoria no volátil, de forma que persiste aunque la batería se
agote por completo: cuando vuelve la corriente externa, el HAT arranca
la Pi automáticamente sin necesidad de pulsar el botón.

Uso:
    sudo python3 /home/pi/Reloj_despertador/scripts/ups_auto_start.py

El script también puede usarse para diagnosticar el estado del HAT:
    python3 scripts/ups_auto_start.py --info
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

AUTO_RESTART_MINUTES = 1   # Minutos de espera antes de arrancar (mínimo 1)
I2C_BUS     = 1
I2C_ADDRESS = 0x10


def configure(minutes: int = AUTO_RESTART_MINUTES) -> bool:
    try:
        from hardware.ups_hat import UPSHat
        hat = UPSHat(bus=I2C_BUS, address=I2C_ADDRESS)
        hat.open()
        hat.set_auto_restart(minutes=minutes)
        current = hat.read_auto_restart()
        ver = hat.read_version()
        soc = hat.read_soc()
        hat.close()
        print(f"[UPS] HAT {ver} — SOC={soc:.0f}%")
        print(f"[UPS] Auto-arranque configurado: {current} min tras corte de corriente")
        return True
    except Exception as exc:
        print(f"[UPS] ERROR: {exc}", file=sys.stderr)
        return False


def info() -> None:
    try:
        from hardware.ups_hat import UPSHat
        hat = UPSHat(bus=I2C_BUS, address=I2C_ADDRESS)
        hat.open()
        data = hat.read_all()
        timer = hat.read_auto_restart()
        hat.close()
        print(f"  Versión  : {data['version']}")
        print(f"  Voltaje  : {data['voltage_mv']:.0f} mV")
        print(f"  SOC      : {data['soc']:.1f}%")
        print(f"  Timer    : {timer} min  ({'configurado' if timer > 0 else 'DESACTIVADO'})")
    except Exception as exc:
        print(f"[UPS] No se pudo leer el HAT: {exc}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configurar auto-arranque del UPS HAT DFR0528")
    parser.add_argument("--info", action="store_true", help="Solo mostrar estado, no configurar")
    parser.add_argument("--minutes", type=int, default=AUTO_RESTART_MINUTES,
                        help=f"Minutos de espera antes de arrancar (default: {AUTO_RESTART_MINUTES})")
    args = parser.parse_args()

    if args.info:
        info()
    else:
        ok = configure(args.minutes)
        sys.exit(0 if ok else 1)
