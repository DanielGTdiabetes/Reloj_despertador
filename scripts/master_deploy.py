
import paramiko
import os

def master_deploy():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.204', username='dani', password='26021980')
    
    sftp = ssh.open_sftp()
    
    # 1. Asegurar estructura de carpetas
    ssh.exec_command("mkdir -p /home/dani/reloj_despertador/src/ui")
    ssh.exec_command("mkdir -p /home/dani/reloj_despertador/src/hardware")
    ssh.exec_command("mkdir -p /home/dani/reloj_despertador/src/assets/menu_icons")
    
    # 2. Subir CEREBRO (app.py)
    print("Uploading app.py (The brain)...")
    sftp.put("src/app.py", "/home/dani/reloj_despertador/src/app.py")
    
    # 3. Subir INTERFAZ (ui/)
    ui_files = ["round_home.py", "rect_ui.py", "theme.py", "weather_icons.py", "__init__.py"]
    for f in ui_files:
        local = os.path.join("src", "ui", f)
        if os.path.exists(local):
            print(f"Uploading UI: {f}...")
            sftp.put(local, f"/home/dani/reloj_despertador/src/ui/{f}")

    # 4. Subir DRIVERS (hardware/)
    hw_files = ["gc9a01.py", "st7789.py"]
    for f in hw_files:
        local = os.path.join("src", "hardware", f)
        print(f"Uploading HW: {f}...")
        sftp.put(local, f"/home/dani/reloj_despertador/src/hardware/{f}")

    # 5. Subir ICONOS (assets/menu_icons/)
    icon_files = ["alarm.png", "brightness.png", "location.png", "sync.png", "weather.png", "wifi.png", "toggle_alarm.png"]
    for f in icon_files:
        local = os.path.join("src", "assets", "menu_icons", f)
        if os.path.exists(local):
            print(f"Uploading Icon: {f}...")
            sftp.put(local, f"/home/dani/reloj_despertador/src/assets/menu_icons/{f}")
        else:
            print(f"Warning: Icon {f} not found locally at {local}")
            
    sftp.close()
    
    print("Restarting everything...")
    ssh.exec_command("echo '26021980' | sudo -S systemctl restart reloj.service")
    ssh.close()
    print("MASTER DEPLOY COMPLETED!")

if __name__ == '__main__':
    master_deploy()
