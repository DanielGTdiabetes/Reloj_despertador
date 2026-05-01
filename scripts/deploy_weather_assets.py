import paramiko
import os

def deploy_weather_assets():
    host = '192.168.0.204'
    user = 'dani'
    password = '26021980'
    remote_root = '/home/dani/reloj_despertador'
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(host, username=user, password=password)
    
    print("1. Ensuring folders...")
    ssh.exec_command(f'mkdir -p {remote_root}/src/assets/weather')
    
    sftp = ssh.open_sftp()
    
    print("2. Uploading weather_icons.py...")
    sftp.put('src/ui/weather_icons.py', f'{remote_root}/src/ui/weather_icons.py')
    
    print("3. Uploading Weather PNGs...")
    weather_dir = 'src/assets/weather'
    for f in os.listdir(weather_dir):
        if f.endswith('.png'):
            src = os.path.join(weather_dir, f)
            dst = f"{remote_root}/src/assets/weather/{f}"
            sftp.put(src, dst)
            print(f"  Uploaded weather icon {f}")
            
    sftp.close()
    
    print("4. Restarting service...")
    ssh.exec_command(f'echo "{password}" | sudo -S systemctl restart reloj.service')
    ssh.close()
    print("Done!")

if __name__ == "__main__":
    deploy_weather_assets()
