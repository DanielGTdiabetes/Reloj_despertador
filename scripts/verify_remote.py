
import paramiko

def check_remote_app():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.204', username='dani', password='26021980')
    
    print("Checking app.py content on Pi...")
    stdin, stdout, stderr = ssh.exec_command("grep 'Debug' /home/dani/reloj_despertador/src/app.py")
    print(stdout.read().decode())
    
    print("Checking rotary_encoder.py content on Pi...")
    stdin, stdout, stderr = ssh.exec_command("grep 'TRANSITIONS' /home/dani/reloj_despertador/src/hardware/rotary_encoder.py")
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == '__main__':
    check_remote_app()
