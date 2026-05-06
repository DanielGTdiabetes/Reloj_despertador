
import paramiko
import os

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

    # 2. Cerebro y configuración
    core_files = ["app.py", "main.py", "paths.py", "config_loader.py", "runtime_flags.py"]
    for f in core_files:
        upload_if_exists(os.path.join("src", f), f"/home/dani/reloj_despertador/src/{f}")
    upload_if_exists("config/config.json", "/home/dani/reloj_despertador/config/config.json")
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
    
    print("Restarting service...")
    ssh.exec_command("echo '26021980' | sudo -S systemctl restart reloj.service")
    ssh.close()
    print("MASTER DEPLOY COMPLETED!")

if __name__ == '__main__':
    master_deploy()
