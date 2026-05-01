
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
    ssh.exec_command("mkdir -p /home/dani/reloj_despertador/src/assets/menu_icons")
    
    # 2. Cerebro
    print("Uploading app.py...")
    sftp.put("src/app.py", "/home/dani/reloj_despertador/src/app.py")
    
    # 3. Hardware (ESTO FALTABA)
    hw_files = ["rotary_encoder.py", "audio.py", "gc9a01.py", "st7789.py", "spi_bus.py"]
    for f in hw_files:
        local = os.path.join("src", "hardware", f)
        if os.path.exists(local):
            print(f"Uploading HW: {f}...")
            sftp.put(local, f"/home/dani/reloj_despertador/src/hardware/{f}")

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
