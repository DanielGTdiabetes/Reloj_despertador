
import paramiko
import os

def rebuild_ui_folder():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.204', username='dani', password='26021980')
    
    print("Creating src/ui directory...")
    ssh.exec_command("mkdir -p /home/dani/reloj_despertador/src/ui")
    ssh.exec_command("touch /home/dani/reloj_despertador/src/ui/__init__.py")
    
    sftp = ssh.open_sftp()
    files = ["round_home.py", "rect_ui.py", "theme.py", "weather_icons.py"]
    for f in files:
        local = os.path.join("src", "ui", f)
        remote = f"/home/dani/reloj_despertador/src/ui/{f}"
        print(f"Uploading {f}...")
        sftp.put(local, remote)
        
    sftp.close()
    
    print("Restarting service...")
    ssh.exec_command("echo '26021980' | sudo -S systemctl restart reloj.service")
    ssh.close()
    print("Done!")

if __name__ == '__main__':
    rebuild_ui_folder()
