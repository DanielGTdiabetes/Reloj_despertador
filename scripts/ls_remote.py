
import paramiko

def list_remote_files():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.204', username='dani', password='26021980')
    
    stdin, stdout, stderr = ssh.exec_command("ls -R /home/dani/reloj_despertador/src")
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == '__main__':
    list_remote_files()
