
import paramiko
import os
from datetime import datetime

def create_system_snapshot():
    now = datetime.now().strftime("%Y-%m-%d_%H-%M")
    backup_name = f"BACKUP_PREMIUM_FINAL_{now}.tar.gz"
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.204', username='dani', password='26021980')
    
    print(f"Creating remote backup: {backup_name}...")
    # Comprimimos la carpeta del proyecto en la Pi
    cmd = f"tar -czf /home/dani/{backup_name} -C /home/dani/reloj_despertador ."
    ssh.exec_command(cmd)
    
    # Descargamos el backup al PC local
    sftp = ssh.open_sftp()
    local_path = os.path.join(os.getcwd(), "backups", backup_name)
    if not os.path.exists("backups"): os.makedirs("backups")
    
    print(f"Downloading to {local_path}...")
    sftp.get(f"/home/dani/{backup_name}", local_path)
    sftp.close()
    ssh.close()
    
    print("\n✅ Backup de seguridad completado y guardado en la carpeta 'backups' de tu PC.")
    return local_path

if __name__ == '__main__':
    create_system_snapshot()
