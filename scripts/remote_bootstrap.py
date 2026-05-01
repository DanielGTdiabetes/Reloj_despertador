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

    print(f"--- Iniciando Restauración en {host} ---", flush=True)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Conectando a {host}...", flush=True)
        ssh.connect(host, username=user, password=password, timeout=10)
        
        print("Creando directorio...", flush=True)
        ssh.exec_command(f"mkdir -p {remote_path}")
        
        print(f"Subiendo {backup_file}...", flush=True)
        sftp = ssh.open_sftp()
        sftp.put(backup_file, f"{remote_path}/{backup_file}")
        sftp.close()
        
        print("Extrayendo y ejecutando bootstrap (esto tardará unos minutos)...", flush=True)
        bootstrap_cmd = f"""
cd {remote_path}
tar -xzf {backup_file}
echo "{password}" | sudo -S bash scripts/bootstrap_fresh_pi.sh
"""
        stdin, stdout, stderr = ssh.exec_command(bootstrap_cmd, get_pty=True)
        
        # Leemos línea a línea para ver el progreso real
        for line in iter(stdout.readline, ""):
            print(f"[PI] {line.strip()}", flush=True)
            
        print("\n--- Finalizado. Reiniciando... ---", flush=True)
        ssh.exec_command(f'echo "{password}" | sudo -S reboot')
        
    except Exception as e:
        print(f"Error: {e}", flush=True)
    finally:
        ssh.close()

if __name__ == "__main__":
    remote_bootstrap()
