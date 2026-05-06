import paramiko
import sys

def verify_service(host, user, password):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(host, username=user, password=password, timeout=10)
        
        print("--- RELOJ SERVICE STATUS ---")
        stdin, stdout, stderr = ssh.exec_command("systemctl status reloj.service")
        print(stdout.read().decode('utf-8', 'ignore').encode('ascii', 'ignore').decode('ascii'))
        
        print("--- RECENT LOGS ---")
        stdin, stdout, stderr = ssh.exec_command("journalctl -u reloj.service -n 20 --no-pager")
        print(stdout.read().decode('utf-8', 'ignore').encode('ascii', 'ignore').decode('ascii'))
        
        print("--- HARDWARE CHECK ---")
        stdin, stdout, stderr = ssh.exec_command("ls /dev/i2c* /dev/spidev*")
        print(stdout.read().decode('utf-8', 'ignore').encode('ascii', 'ignore').decode('ascii'))
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        ssh.close()

if __name__ == "__main__":
    verify_service('192.168.0.204', 'dani', '26021980')
