
import paramiko

def restore_original_offsets():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.204', username='dani', password='26021980')
    
    # Forzamos los valores originales que estaban bien
    cmd = "sed -i 's/\"col_offset\": [0-9]*/\"col_offset\": 18/' /home/dani/reloj_despertador/config/config.json"
    ssh.exec_command(cmd)
    cmd2 = "sed -i 's/\"row_offset\": [0-9]*/\"row_offset\": 82/' /home/dani/reloj_despertador/config/config.json"
    ssh.exec_command(cmd2)
    
    # Reiniciamos el servicio
    ssh.exec_command("echo '26021980' | sudo -S systemctl restart reloj.service")
    ssh.close()
    print("Original hardware offsets (18, 82) restored.")

if __name__ == '__main__':
    restore_original_offsets()
