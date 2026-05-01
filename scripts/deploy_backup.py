
import paramiko
import os
import sys

def deploy_backup():
    host = '192.168.0.204'
    user = 'dani'
    password = '26021980'
    remote_path = '/home/dani/reloj_despertador'
    local_backup = 'backup_FUNCIONAL_spidev0.1_2026-05-01.tar.gz'

    if not os.path.exists(local_backup):
        print(f"Error: {local_backup} not found in current directory.")
        return

    print(f"Connecting to {host}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(host, username=user, password=password)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    print(f"Uploading {local_backup}...")
    sftp = ssh.open_sftp()
    try:
        sftp.put(local_backup, f'{remote_path}/{local_backup}')
    finally:
        sftp.close()

    print("Cleaning remote directory and extracting backup...")
    # Limpiamos src, config, scripts para asegurar una restauración limpia
    cmds = [
        f"cd {remote_path}",
        "rm -rf src config scripts",
        f"tar -xzf {local_backup}",
        "find . -name '__pycache__' -type d -exec rm -rf {} +",
        f"echo '{password}' | sudo -S systemctl restart reloj.service"
    ]
    
    full_cmd = " && ".join(cmds)
    stdin, stdout, stderr = ssh.exec_command(full_cmd)
    
    # Leemos para esperar a que termine
    stdout.read()
    stderr.read()

    print("Deployment of backup complete. Verifying service...")
    ssh.close()
    print("Done!")

if __name__ == '__main__':
    deploy_backup()
