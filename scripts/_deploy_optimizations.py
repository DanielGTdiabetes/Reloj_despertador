"""Deploy de optimizaciones: boot, watchdog, SD protection. Ejecutar desde Windows."""
import os
import sys
import time
import paramiko

HOST = "192.168.0.204"
USER = "dani"
PASS = "26021980"
REMOTE_BASE = "/home/dani/reloj_despertador"

def run(ssh, cmd, sudo=False, timeout=60):
    if sudo:
        cmd = f"echo '{PASS}' | sudo -S bash -c \"{cmd}\""
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", errors="replace").strip()
    err = stderr.read().decode("utf-8", errors="replace").strip()
    rc = stdout.channel.recv_exit_status()
    return rc, out, err

def put(sftp, local, remote):
    print(f"  upload: {os.path.basename(local)} -> {remote}")
    sftp.put(local, remote)

def main():
    print(f"Conectando a {HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASS, timeout=15)
    sftp = ssh.open_sftp()

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # ── 1. Subir archivos modificados ────────────────────────────────────────
    print("\n[1/5] Subiendo archivos...")
    put(sftp, os.path.join(base, "src", "app.py"), f"{REMOTE_BASE}/src/app.py")
    put(sftp, os.path.join(base, "scripts", "reloj.service"), f"{REMOTE_BASE}/scripts/reloj.service")
    put(sftp, os.path.join(base, "scripts", "optimize_boot.sh"), f"{REMOTE_BASE}/scripts/optimize_boot.sh")
    put(sftp, os.path.join(base, "scripts", "setup_sd_protection.sh"), f"{REMOTE_BASE}/scripts/setup_sd_protection.sh")

    # ── 2. Aplicar boot_config.txt → /boot/firmware/config.txt ──────────────
    print("\n[2/5] Actualizando /boot/firmware/config.txt...")
    # Subir primero al home del usuario
    put(sftp, os.path.join(base, "config", "boot_config.txt"), f"/home/dani/boot_config_new.txt")
    rc, out, err = run(ssh, "cp /home/dani/boot_config_new.txt /boot/firmware/config.txt && rm /home/dani/boot_config_new.txt", sudo=True)
    if rc != 0:
        print(f"  WARN: {err}")
    else:
        print("  OK")

    # ── 3. Instalar y recargar servicio systemd ──────────────────────────────
    print("\n[3/5] Instalando reloj.service...")
    cmds = [
        f"cp {REMOTE_BASE}/scripts/reloj.service /etc/systemd/system/reloj.service",
        "systemctl daemon-reload",
        "systemctl enable reloj.service",
    ]
    for cmd in cmds:
        rc, out, err = run(ssh, cmd, sudo=True)
        status = "OK" if rc == 0 else f"WARN ({err.splitlines()[-1] if err else 'error'})"
        print(f"  {cmd.split()[0]}... {status}")

    # ── 4. Ejecutar optimize_boot.sh ─────────────────────────────────────────
    print("\n[4/5] Ejecutando optimize_boot.sh...")
    run(ssh, f"chmod +x {REMOTE_BASE}/scripts/optimize_boot.sh {REMOTE_BASE}/scripts/setup_sd_protection.sh", sudo=False)
    rc, out, err = run(ssh, f"bash {REMOTE_BASE}/scripts/optimize_boot.sh", sudo=True, timeout=120)
    for line in out.splitlines():
        print(f"  {line}")
    if rc != 0 and err:
        print(f"  ERR: {err[:300]}")

    # ── 5. Ejecutar setup_sd_protection.sh ───────────────────────────────────
    print("\n[5/5] Ejecutando setup_sd_protection.sh (puede tardar si descarga log2ram)...")
    rc, out, err = run(ssh, f"bash {REMOTE_BASE}/scripts/setup_sd_protection.sh", sudo=True, timeout=300)
    for line in out.splitlines():
        print(f"  {line}")
    if rc != 0 and err:
        print(f"  ERR: {err[:300]}")

    sftp.close()

    # ── Reboot ───────────────────────────────────────────────────────────────
    print("\nReiniciando la Pi...")
    try:
        ssh.exec_command("echo '26021980' | sudo -S reboot", timeout=5)
    except Exception:
        pass
    ssh.close()
    print("Pi reiniciando. Espera ~60s y verifica con:")
    print(f"  ssh dani@{HOST}")
    print(f"  systemctl status reloj")
    print(f"  journalctl -u reloj -n 30")

if __name__ == "__main__":
    main()
