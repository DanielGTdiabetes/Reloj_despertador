"""
deploy_face_anim.py — Sube los clips .npy y face_anim.py a la Pi Zero W.

Flujo completo:
    1. python scripts/render_eye_frames.py
    2. python scripts/render_mouth_frames.py
    3. python scripts/deploy_face_anim.py        ← este script
"""
import os
import time

import paramiko

PI_HOST    = "192.168.0.204"
PI_USER    = "dani"
PI_PASS    = "26021980"
REMOTE_BASE = "/home/dani/reloj_despertador"

LOCAL_ANIM  = os.path.join(os.path.dirname(__file__), "..", "src", "assets", "animations")
REMOTE_ANIM = f"{REMOTE_BASE}/src/assets/animations"


def run(ssh, cmd: str) -> str:
    _, stdout, stderr = ssh.exec_command(cmd)
    stdout.channel.recv_exit_status()
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    if err:
        print(f"  [stderr] {err}")
    return out


def main() -> None:
    # ── Validate local assets ─────────────────────────────────────────────────
    if not os.path.isdir(LOCAL_ANIM):
        print(f"ERROR: {LOCAL_ANIM} no existe.")
        print("Ejecuta primero render_eye_frames.py y render_mouth_frames.py")
        return

    npy_files = [f for f in os.listdir(LOCAL_ANIM) if f.endswith(".npy")]
    if not npy_files:
        print(f"ERROR: no hay archivos .npy en {LOCAL_ANIM}")
        return

    print(f"Clips a subir: {len(npy_files)}")
    total_mb = sum(
        os.path.getsize(os.path.join(LOCAL_ANIM, f)) for f in npy_files
    ) / 1_048_576
    print(f"Tamaño total: {total_mb:.1f} MB\n")

    # ── SSH / SFTP ────────────────────────────────────────────────────────────
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Conectando a {PI_HOST} …")
    ssh.connect(PI_HOST, username=PI_USER, password=PI_PASS)
    sftp = ssh.open_sftp()

    # Create remote animation directory
    run(ssh, f"mkdir -p {REMOTE_ANIM}")

    # ── Upload .npy clips ─────────────────────────────────────────────────────
    print("Subiendo clips …")
    for fname in sorted(npy_files):
        local  = os.path.join(LOCAL_ANIM, fname)
        remote = f"{REMOTE_ANIM}/{fname}"
        size   = os.path.getsize(local) / 1_048_576
        print(f"  {fname:<30}  {size:.1f} MB", end=" … ", flush=True)
        sftp.put(local, remote)
        print("OK")

    # ── Upload face_anim.py ───────────────────────────────────────────────────
    print("\nSubiendo face_anim.py …")
    local_fa  = os.path.join(os.path.dirname(__file__), "..", "src", "ui", "face_anim.py")
    remote_fa = f"{REMOTE_BASE}/src/ui/face_anim.py"
    sftp.put(local_fa, remote_fa)
    print("  face_anim.py  OK")

    # ── Upload app.py (contains FaceAnimator integration) ────────────────────
    print("Subiendo app.py …")
    local_app  = os.path.join(os.path.dirname(__file__), "..", "src", "app.py")
    remote_app = f"{REMOTE_BASE}/src/app.py"
    sftp.put(local_app, remote_app)
    print("  app.py  OK")

    sftp.close()

    # ── Verify disk space on Pi ───────────────────────────────────────────────
    df = run(ssh, "df -h /home")
    print(f"\nDisco Pi:\n{df}")

    # ── Restart service ───────────────────────────────────────────────────────
    print("\nReiniciando reloj.service …")
    _, stdout, _ = ssh.exec_command(
        f"echo '{PI_PASS}' | sudo -S systemctl restart reloj.service",
        get_pty=True,
    )
    stdout.channel.recv_exit_status()
    time.sleep(4)

    status = run(ssh, "systemctl is-active reloj.service")
    color  = "\033[92m" if status == "active" else "\033[91m"
    print(f"Servicio: {color}{status}\033[0m")

    if status != "active":
        print("\nÚltimas líneas del log:")
        log = run(ssh, "journalctl -u reloj.service -n 30 --no-pager")
        print(log)

    ssh.close()
    print("\nDeploy completado.")


if __name__ == "__main__":
    main()
