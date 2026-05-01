
import paramiko

def list_remote_audio():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.204', username='dani', password='26021980')
    
    print("Searching for audio files on Raspberry Pi...")
    stdin, stdout, stderr = ssh.exec_command("find /home/dani/reloj_despertador -name '*.wav' -o -name '*.mp3'")
    print(stdout.read().decode())
    
    ssh.close()

if __name__ == '__main__':
    list_remote_audio()
