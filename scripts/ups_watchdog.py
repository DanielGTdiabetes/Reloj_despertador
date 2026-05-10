#!/usr/bin/env python3
"""
ups_watchdog.py — Watchdog del DFR0528 UPS HAT.

Envía un latido I2C al MCU del HAT cada BEAT_INTERVAL segundos. Mientras
el latido llega, el HAT sabe que la Pi está encendida y en buen estado.
Cuando el latido se detiene (apagado, cuelgue, o fallo), el HAT espera el
tiempo configurado con set_auto_restart() y luego enciende la Pi de nuevo.

Al recibir SIGTERM (systemd stop), configura el auto-arranque antes de salir
para que el HAT sepa que debe volver a encender la Pi cuando vuelva la corriente.

Uso (normalmente via systemd, ver ups-watchdog.service):
    sudo python3 scripts/ups_watchdog.py
"""

import os
import signal
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

BEAT_INTERVAL       = 5    # segundos entre latidos (MCU espera ≤10s)
AUTO_RESTART_MINUTES = 1   # minutos hasta el arranque automático tras apagado
I2C_BUS     = 1
I2C_ADDRESS = 0x10

_running = True


def _on_sigterm(signum, frame):
    global _running
    _running = False


def main():
    global _running

    try:
        from hardware.ups_hat import UPSHat
    except ImportError as exc:
        print(f"[watchdog] Error de importación: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        hat = UPSHat(bus=I2C_BUS, address=I2C_ADDRESS)
        hat.open()
    except Exception as exc:
        print(f"[watchdog] HAT no disponible: {exc}", file=sys.stderr)
        sys.exit(0)   # salida limpia — el servicio no debe reintentar en bucle

    # Configurar auto-arranque al inicio (persiste en flash del MCU)
    try:
        hat.set_auto_restart(minutes=AUTO_RESTART_MINUTES)
        print(f"[watchdog] Auto-arranque configurado: {AUTO_RESTART_MINUTES} min")
    except Exception as exc:
        print(f"[watchdog] Aviso: no se pudo configurar auto-arranque: {exc}", file=sys.stderr)

    signal.signal(signal.SIGTERM, _on_sigterm)
    signal.signal(signal.SIGINT,  _on_sigterm)

    print("[watchdog] Iniciando latido del HAT…")
    while _running:
        try:
            hat.send_watchdog()
        except Exception as exc:
            print(f"[watchdog] Error de latido: {exc}", file=sys.stderr)
        time.sleep(BEAT_INTERVAL)

    # Al apagarse, señalizar shutdown al MCU antes de cerrar
    print("[watchdog] Señalizando shutdown al HAT…")
    try:
        hat.signal_shutdown()
    except Exception as exc:
        print(f"[watchdog] Aviso al señalizar shutdown: {exc}", file=sys.stderr)

    hat.close()
    print("[watchdog] Fin.")


if __name__ == "__main__":
    main()
