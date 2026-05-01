import paramiko
import os
import sys
import time

def remote_bootstrap():
    host = '192.168.0.204'
    user = 'dani'
    password = '26021980'
    remote_path = '/home/dani/reloj_despertador'
    backup_file = 'backup_FUNCIONAL_dual_display_2026-05-01.tar.gz'

    print(f"--- Iniciando Restauración desde Cero en {host} ---")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Conectando a {host}...")
        ssh.connect(host, username=user, password=password)
        
        print("Creando directorio de la aplicación...")
        ssh.exec_command(f"mkdir -p {remote_path}")
        
        print(f"Subiendo backup funcional: {backup_file}...")
        sftp = ssh.open_sftp()
        sftp.put(backup_file, f"{remote_path}/{backup_file}")
        sftp.close()
        
        print("Extrayendo backup y ejecutando bootstrap...")
        # Usamos -S para pasar la contraseña a sudo
        bootstrap_cmd = f"""
cd {remote_path}
tar -xzf {backup_file}
echo "{password}" | sudo -S bash scripts/bootstrap_fresh_pi.sh
"""
        stdin, stdout, stderr = ssh.exec_command(bootstrap_cmd)
        
        # Monitorear la salida del bootstrap
        for line in stdout:
            print(f"[PI] {line.strip()}")
            
        err = stderr.read().decode()
        if err and "sudo" not in err: # Ignorar avisos de sudo
            print(f"ERRORES: {err}")

        print("\n--- Bootstrap completado. Reiniciando la Pi para aplicar cambios de hardware... ---")
        ssh.exec_command(f'echo "{password}" | sudo -S reboot')
        
    except Exception as e:
        print(f"Error durante la restauración: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    remote_bootstrap()
