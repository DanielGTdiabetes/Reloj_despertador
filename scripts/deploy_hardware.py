
import paramiko
import os

def deploy_hardware_drivers():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('192.168.0.204', username='dani', password='26021980')
    
    sftp = ssh.open_sftp()
    
    drivers = ["gc9a01.py", "st7789.py"]
    for driver in drivers:
        local = os.path.join("src", "hardware", driver)
        remote = f"/home/dani/reloj_despertador/src/hardware/{driver}"
        print(f"Uploading driver: {driver}...")
        sftp.put(local, remote)
        
    sftp.close()
    
    print("Restarting service to apply PWM changes...")
    ssh.exec_command("echo '26021980' | sudo -S systemctl restart reloj.service")
    ssh.close()
    print("Hardware drivers deployed successfully!")

if __name__ == '__main__':
    deploy_hardware_drivers()
