
import paramiko

def get_python_error():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.204', username='dani', password='26021980')
    
    # Buscamos el traceback de Python en los logs
    stdin, stdout, stderr = ssh.exec_command("echo '26021980' | sudo -S journalctl -u reloj.service -n 20 --no-pager")
    lines = stdout.read().decode('utf-8', errors='ignore')
    print(lines)
    
    ssh.close()

if __name__ == '__main__':
    get_python_error()
