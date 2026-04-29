import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.204', username='dani', password='26021980')

# Restart the service
print("Restarting service...")
stdin, stdout, stderr = ssh.exec_command('sudo -S systemctl restart reloj.service <<< "26021980" 2>&1')
print(f"  {stdout.read().decode()}{stderr.read().decode()}")

import time
time.sleep(8)

# Check status
print("\nService status:")
stdin, stdout, stderr = ssh.exec_command('SYSTEMD_COLORS=0 sudo -S systemctl status reloj.service --no-pager <<< "26021980" 2>&1')
status = stdout.read().decode().encode('ascii', 'replace').decode('ascii')
print(status)

# Check recent logs
print("\nRecent logs:")
stdin, stdout, stderr = ssh.exec_command('sudo -S journalctl -u reloj.service --no-pager -n 15 <<< "26021980" 2>&1')
logs = stdout.read().decode().encode('ascii', 'replace').decode('ascii')
print(logs)

# Check if process is running
print("\nPython processes:")
stdin, stdout, stderr = ssh.exec_command('ps aux | grep python | grep -v grep')
print(stdout.read().decode())

ssh.close()
