#!/usr/bin/env python3
"""
deploy_ups_auto_start.py — Despliega el auto-arranque del UPS HAT en la Pi Zero W.

Transfiere los archivos modificados y ejecuta el instalador del servicio watchdog.
Ejecutar desde el PC de desarrollo (no desde la Pi).

Uso:
    python3 scripts/deploy_ups_auto_start.py
    python3 scripts/deploy_ups_auto_start.py --check   # solo verificar estado
"""

import argparse
import os
import sys

PI_HOST = "192.168.0.204"
PI_USER = "dani"
PI_PASS = "26021980"
PI_PATH = "/home/dani/reloj_despertador"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES = [
    ("src/hardware/ups_hat.py",          f"{PI_PATH}/src/hardware/ups_hat.py"),
    ("src/services/battery.py",          f"{PI_PATH}/src/services/battery.py"),
    ("scripts/ups_watchdog.py",          f"{PI_PATH}/scripts/ups_watchdog.py"),
    ("scripts/ups_auto_start.py",        f"{PI_PATH}/scripts/ups_auto_start.py"),
    ("scripts/ups-watchdog.service",     f"{PI_PATH}/scripts/ups-watchdog.service"),
    ("scripts/install_ups_auto_start.sh",f"{PI_PATH}/scripts/install_ups_auto_start.sh"),
]


def connect():
    import paramiko
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(PI_HOST, username=PI_USER, password=PI_PASS, timeout=15)
    return client


def run(client, cmd, sudo=False):
    if sudo:
        cmd = f"echo '{PI_PASS}' | sudo -S sh -c '{cmd}'"
    stdin, stdout, stderr = client.exec_command(cmd, timeout=60)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    rc  = stdout.channel.recv_exit_status()
    return rc, out, err


def deploy():
    try:
        import paramiko
    except ImportError:
        print("Instalando paramiko…")
        os.system(f"{sys.executable} -m pip install paramiko -q")
        import paramiko

    print(f"Conectando a {PI_USER}@{PI_HOST}…")
    try:
        client = connect()
    except Exception as exc:
        print(f"ERROR: No se pudo conectar a la Pi: {exc}")
        print(f"  ¿Está la Pi encendida y en la red? Verifica: ssh {PI_USER}@{PI_HOST}")
        return False

    sftp = client.open_sftp()

    print("\n── Transfiriendo archivos ──────────────────────────────")
    for local_rel, remote in FILES:
        local = os.path.join(PROJECT_ROOT, local_rel)
        if not os.path.exists(local):
            print(f"  AVISO: {local_rel} no encontrado, omitiendo")
            continue
        try:
            sftp.put(local, remote)
            print(f"  OK  {local_rel}")
        except Exception as exc:
            print(f"  ERR {local_rel}: {exc}")

    sftp.close()

    print("\n── Instalando servicio ups-watchdog ────────────────────")
    rc, out, err = run(
        client,
        f"chmod +x {PI_PATH}/scripts/install_ups_auto_start.sh && "
        f"bash {PI_PATH}/scripts/install_ups_auto_start.sh",
        sudo=True,
    )
    if out:
        print(out)
    if err and "sudo" not in err.lower():
        print(f"stderr: {err}", file=sys.stderr)

    if rc != 0:
        print(f"\nERROR: el instalador terminó con código {rc}")
        print("Prueba manualmente en la Pi:")
        print(f"  sudo bash {PI_PATH}/scripts/install_ups_auto_start.sh")
        client.close()
        return False

    print("\n── Reiniciando reloj.service ───────────────────────────")
    rc, out, err = run(client, "systemctl restart reloj.service", sudo=True)
    print("  OK" if rc == 0 else f"  AVISO (rc={rc}): {err}")

    print("\n── Estado final ────────────────────────────────────────")
    rc, out, _ = run(client, "systemctl is-active ups-watchdog.service reloj.service")
    print(out)

    rc, out, _ = run(
        client,
        f"python3 {PI_PATH}/scripts/ups_auto_start.py --info",
    )
    print(out)

    client.close()
    print("\n✓ Deploy completado.")
    return True


def check():
    print(f"Conectando a {PI_USER}@{PI_HOST}…")
    try:
        client = connect()
    except Exception as exc:
        print(f"ERROR: {exc}")
        return

    print("\n── Servicios ────────────────────────────────────────────")
    _, out, _ = run(client, "systemctl status ups-watchdog.service reloj.service --no-pager -l")
    print(out)

    print("\n── Estado del HAT ───────────────────────────────────────")
    rc, out, err = run(
        client,
        f"python3 /home/dani/reloj_despertador/scripts/ups_auto_start.py --info",
    )
    print(out or err)

    print("\n── Últimas líneas del log ───────────────────────────────")
    _, out, _ = run(client, "journalctl -u ups-watchdog.service -n 20 --no-pager")
    print(out)

    client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Despliega auto-arranque UPS HAT en la Pi")
    parser.add_argument("--check", action="store_true", help="Solo verificar estado, no desplegar")
    args = parser.parse_args()

    if args.check:
        check()
    else:
        ok = deploy()
        sys.exit(0 if ok else 1)
