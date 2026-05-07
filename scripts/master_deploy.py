
import errno
import json
import os

import paramiko

def master_deploy():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.204', username='dani', password='26021980')
    
    sftp = ssh.open_sftp()
    
    # 1. Estructura
    ssh.exec_command("mkdir -p /home/dani/reloj_despertador/src/ui")
    ssh.exec_command("mkdir -p /home/dani/reloj_despertador/src/hardware")
    ssh.exec_command("mkdir -p /home/dani/reloj_despertador/src/services")
    ssh.exec_command("mkdir -p /home/dani/reloj_despertador/config")
    ssh.exec_command("mkdir -p /home/dani/reloj_despertador/src/assets/menu_icons")

    def upload_if_exists(local, remote):
        if os.path.exists(local):
            print(f"Uploading {local}...")
            sftp.put(local, remote)
        else:
            print(f"Skipping missing file: {local}")

    def remote_exists(remote):
        try:
            sftp.stat(remote)
            return True
        except OSError as exc:
            if getattr(exc, "errno", None) in (errno.ENOENT, None):
                return False
            raise

    def sync_config_safely(local, remote):
        if not os.path.exists(local):
            print(f"Skipping missing file: {local}")
            return

        if not remote_exists(remote):
            print(f"Seeding missing remote config from {local}...")
            sftp.put(local, remote)
            return

        with open(local, encoding="utf-8") as local_file:
            local_config = json.load(local_file)

        with sftp.open(remote, "r") as remote_file:
            remote_data = remote_file.read()
        if isinstance(remote_data, bytes):
            remote_data = remote_data.decode("utf-8")
        remote_config = json.loads(remote_data)

        local_ups = local_config.get("ups", {})
        remote_ups = remote_config.setdefault("ups", {})
        changed = False

        for key, value in local_ups.items():
            if key not in remote_ups:
                remote_ups[key] = value
                changed = True

        if not changed:
            print("Remote config already exists; preserving runtime settings.")
            return

        tmp_remote = f"{remote}.tmp"
        with sftp.open(tmp_remote, "w") as remote_file:
            json.dump(remote_config, remote_file, indent=4, ensure_ascii=False)
            remote_file.write("\n")
        sftp.rename(tmp_remote, remote)
        print("Merged missing UPS config defaults without overwriting runtime settings.")

    # 2. Cerebro y configuración
    core_files = ["app.py", "main.py", "paths.py", "config_loader.py", "runtime_flags.py"]
    for f in core_files:
        upload_if_exists(os.path.join("src", f), f"/home/dani/reloj_despertador/src/{f}")
    sync_config_safely("config/config.json", "/home/dani/reloj_despertador/config/config.json")
    upload_if_exists("requirements.txt", "/home/dani/reloj_despertador/requirements.txt")
    upload_if_exists("diag_battery.py", "/home/dani/reloj_despertador/diag_battery.py")

    # 3. Hardware y servicio mínimo de UPS/batería
    hw_files = [
        "__init__.py", "rotary_encoder.py", "audio.py", "gc9a01.py",
        "st7789.py", "spi_bus.py", "ups_hat.py",
    ]
    for f in hw_files:
        upload_if_exists(os.path.join("src", "hardware", f), f"/home/dani/reloj_despertador/src/hardware/{f}")

    service_files = ["__init__.py", "battery.py"]
    for f in service_files:
        upload_if_exists(os.path.join("src", "services", f), f"/home/dani/reloj_despertador/src/services/{f}")

    # 3b. Scripts de auto-arranque UPS HAT
    ups_scripts = [
        "ups_watchdog.py",
        "ups_auto_start.py",
        "ups-watchdog.service",
        "install_ups_auto_start.sh",
    ]
    for f in ups_scripts:
        upload_if_exists(os.path.join("scripts", f), f"/home/dani/reloj_despertador/scripts/{f}")

    # 4. Interfaz
    ui_files = ["round_home.py", "rect_ui.py", "theme.py", "weather_icons.py", "__init__.py"]
    for f in ui_files:
        local = os.path.join("src", "ui", f)
        if os.path.exists(local):
            sftp.put(local, f"/home/dani/reloj_despertador/src/ui/{f}")

    # 5. Iconos
    icon_files = ["alarm.png", "alarm_clock.png", "brightness.png", "location.png", "sync.png", "weather.png", "wifi.png"]
    for f in icon_files:
        local = os.path.join("src", "assets", "menu_icons", f)
        if os.path.exists(local):
            sftp.put(local, f"/home/dani/reloj_despertador/src/assets/menu_icons/{f}")
    
    ssh.exec_command("cp /home/dani/reloj_despertador/src/assets/menu_icons/alarm.png /home/dani/reloj_despertador/src/assets/menu_icons/toggle_alarm.png")
            
    sftp.close()

    def run_sudo(cmd):
        _, stdout, stderr = ssh.exec_command(f"echo '26021980' | sudo -S sh -c '{cmd}'", timeout=60)
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        rc  = stdout.channel.recv_exit_status()
        return rc, out, err

    # Instalar y arrancar ups-watchdog.service
    print("Installing ups-watchdog service...")
    rc, out, err = run_sudo(
        "chmod +x /home/dani/reloj_despertador/scripts/install_ups_auto_start.sh && "
        "bash /home/dani/reloj_despertador/scripts/install_ups_auto_start.sh"
    )
    if out:
        print(out)
    if rc != 0:
        print(f"  AVISO: instalador terminó con rc={rc}. {err}")

    print("Restarting service...")
    run_sudo("systemctl restart reloj.service")
    ssh.close()
    print("MASTER DEPLOY COMPLETED!")

if __name__ == '__main__':
    master_deploy()
