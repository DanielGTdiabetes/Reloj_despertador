import paramiko
import os

def deploy_premium():
    host = '192.168.0.204'
    user = 'dani'
    password = '26021980'
    remote_root = '/home/dani/reloj_despertador'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)
    
    print("1. Cleaning remote UI...")
    ssh.exec_command(f'rm -rf {remote_root}/src/ui {remote_root}/src/assets/menu_icons')
    ssh.exec_command(f'mkdir -p {remote_root}/src/ui {remote_root}/src/assets/menu_icons')
    
    sftp = ssh.open_sftp()
    
    print("2. Uploading UI files...")
    ui_files = ['round_home.py', 'rect_ui.py', 'theme.py', 'weather_icons.py']
    for f in ui_files:
        src = os.path.join('src', 'ui', f)
        dst = f"{remote_root}/src/ui/{f}"
        sftp.put(src, dst)
        print(f"  Uploaded {f}")
        
    print("3. Uploading Icons...")
    icon_dir = 'src/assets/menu_icons'
    for f in os.listdir(icon_dir):
        if f.endswith('.png'):
            src = os.path.join(icon_dir, f)
            dst = f"{remote_root}/src/assets/menu_icons/{f}"
            sftp.put(src, dst)
            print(f"  Uploaded icon {f}")
            
    sftp.close()
    
    print("4. Restarting service...")
    ssh.exec_command(f'echo "{password}" | sudo -S systemctl restart reloj.service')
    ssh.close()
    print("Done!")

if __name__ == "__main__":
    deploy_premium()
