
import paramiko

def get_debug_logs():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.204', username='dani', password='26021980')
    
    # Buscamos mis líneas de [Debug] en el log
    stdin, stdout, stderr = ssh.exec_command("echo '26021980' | sudo -S journalctl -u reloj.service -n 100 | grep 'Debug'")
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == '__main__':
    get_debug_logs()
