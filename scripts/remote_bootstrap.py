import paramiko
import os
import sys
import time

# Forzar salida en UTF-8 para evitar errores de codificación con barras de progreso
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def remote_bootstrap():
    host = '192.168.0.204'
    user = 'dani'
    password = '26021980'
    remote_path = '/home/dani/reloj_despertador'
    backup_file = 'backup_FUNCIONAL_dual_display_2026-05-01.tar.gz'

    print(f"--- Re-intentando Restauración (Fix encoding) en {host} ---", flush=True)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Conectando a {host}...", flush=True)
        ssh.connect(host, username=user, password=password, timeout=10)
        
        print("El directorio y el backup ya deberían estar allí. Ejecutando bootstrap...", flush=True)
        bootstrap_cmd = f"""
cd {remote_path}
echo "{password}" | sudo -S bash scripts/bootstrap_fresh_pi.sh
"""
        stdin, stdout, stderr = ssh.exec_command(bootstrap_cmd, get_pty=True)
        
        # Leemos línea a línea con manejo de errores de encoding
        while True:
            try:
                line = stdout.readline()
                if not line:
                    break
                print(f"[PI] {line.strip()}", flush=True)
            except UnicodeDecodeError:
                continue # Saltar líneas con caracteres extraños (barras de progreso)
            
        print("\n--- Bootstrap finalizado con éxito. Aplicando REBOOT... ---", flush=True)
        ssh.exec_command(f'echo "{password}" | sudo -S reboot')
        print("La Pi se está reiniciando. Espera 30 segundos y comprueba las pantallas.", flush=True)
        
    except Exception as e:
        print(f"Error: {e}", flush=True)
    finally:
        ssh.close()

if __name__ == "__main__":
    remote_bootstrap()
