
import paramiko
import os

def master_deploy():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.204', username='dani', password='26021980')
    
    sftp = ssh.open_sftp()
    
    # Asegurar carpetas
    ssh.exec_command("mkdir -p /home/dani/reloj_despertador/src/ui")
    ssh.exec_command("mkdir -p /home/dani/reloj_despertador/src/assets/menu_icons")
    
    # Subir app.py (Cerebro)
    print("Uploading app.py...")
    sftp.put("src/app.py", "/home/dani/reloj_despertador/src/app.py")
    
    # Subir UI
    ui_files = ["round_home.py", "rect_ui.py", "theme.py", "weather_icons.py", "__init__.py"]
    for f in ui_files:
        local = os.path.join("src", "ui", f)
        if os.path.exists(local):
            sftp.put(local, f"/home/dani/reloj_despertador/src/ui/{f}")

    # Subir Iconos
    icon_files = ["alarm.png", "brightness.png", "location.png", "sync.png", "weather.png", "wifi.png"]
    for f in icon_files:
        local = os.path.join("src", "assets", "menu_icons", f)
        if os.path.exists(local):
            sftp.put(local, f"/home/dani/reloj_despertador/src/assets/menu_icons/{f}")
    
    # DUPLICAR icono de alarma para el botón ON/OFF
    print("Mapping toggle_alarm icon...")
    ssh.exec_command("cp /home/dani/reloj_despertador/src/assets/menu_icons/alarm.png /home/dani/reloj_despertador/src/assets/menu_icons/toggle_alarm.png")
            
    sftp.close()
    
    print("Restarting service...")
    ssh.exec_command("echo '26021980' | sudo -S systemctl restart reloj.service")
    ssh.close()
    print("DEPLOY COMPLETED!")

if __name__ == '__main__':
    master_deploy()
