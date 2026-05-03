"""
deploy_moon_assets.py — Despliega mejoras de luna en modo noche.
Sube: weather_icons.py, round_home.py y todos los PNGs procesados.
"""
import paramiko
import os
import time

PI_HOST = "192.168.0.204"
PI_USER = "dani"
PI_PASS = "26021980"
REMOTE_BASE = "/home/dani/reloj_despertador"


def run(ssh, cmd):
    _, stdout, stderr = ssh.exec_command(cmd)
    stdout.channel.recv_exit_status()
    return stdout.read().decode().strip()


def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(PI_HOST, username=PI_USER, password=PI_PASS)
    sftp = ssh.open_sftp()

    # Directorios necesarios
    run(ssh, f"mkdir -p {REMOTE_BASE}/src/assets/moon_phases/processed")

    # UI
    for fname in ("weather_icons.py", "round_home.py"):
        local = os.path.join("src", "ui", fname)
        remote = f"{REMOTE_BASE}/src/ui/{fname}"
        sftp.put(local, remote)
        print(f"  UI   {fname}")

    # PNGs procesados
    processed_dir = os.path.join("src", "assets", "moon_phases", "processed")
    for png in sorted(os.listdir(processed_dir)):
        if not png.endswith(".png"):
            continue
        local = os.path.join(processed_dir, png)
        remote = f"{REMOTE_BASE}/src/assets/moon_phases/processed/{png}"
        sftp.put(local, remote)
        print(f"  PNG  {png}")

    sftp.close()

    print("\nReiniciando servicio...")
    _, stdout, _ = ssh.exec_command(
        f"echo '{PI_PASS}' | sudo -S systemctl restart reloj.service",
        get_pty=True,
    )
    stdout.channel.recv_exit_status()
    time.sleep(3)

    status = run(ssh, "systemctl is-active reloj.service")
    print(f"Servicio: {status}")

    ssh.close()
    print("Deploy completado.")


if __name__ == "__main__":
    main()
